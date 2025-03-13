/** @odoo-module */

import { _t } from "@web/core/l10n/translation"; // ok
import { PaymentInterface } from "@point_of_sale/app/payment/payment_interface"; // ok
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog"; // changed
import { sprintf } from "@web/core/utils/strings"; // ok
const { DateTime } = luxon;

export class PaymentTransact extends PaymentInterface {
    setup() {
        super.setup(...arguments);
        this.paymentLineResolvers = {};
    }

    send_payment_request(cid) {
        super.send_payment_request(cid);
        return this._transact_pay(cid);
    }
    send_payment_cancel(order, cid) {
        super.send_payment_cancel(order, cid);
        return this._transact_cancel();
    }

    set_most_recent_service_id(id) {
        this.most_recent_service_id = id;
    }

    pending_transact_line() {
        return this.pos.getPendingPaymentLine("transact");
    }

    _handle_odoo_connection_failure(data = {}) {
        // handle timeout
        var line = this.pending_transact_line();
        if (line) {
            line.set_payment_status("retry");
        }
        this._show_error(
            _t(
                "Could not connect to the Odoo server, please check your internet connection and try again."
            )
        );

        return Promise.reject(data); // prevent subsequent onFullFilled's from being called
    }

    _call_transact(data, operation = false) {
        // FIXME POSREF TIMEOUT 10000
        return this.env.services.orm.silent
            .call("pos.payment.method", "proxy_transact_request", [
                [this.payment_method.id],
                data,
                operation,
            ])
            .catch(this._handle_odoo_connection_failure.bind(this));
    }

    _transact_pay_data() {
        var order = this.pos.get_order();
        var config = this.pos.config;
        var line = order.selected_paymentline;
        if (line.amount<0) {
            var operation = 'DEV'
        }
        else {
            var operation = 'VTA'
        }
        var data = {
            Operacion: operation,
            MonedaISO: this.pos.currency.transact_currency_code,
            Monto: Math.abs(line.amount*100),
            FacturaNro: order.uid.split("-")[2],
            FacturaMonto: Math.abs(order.get_total_with_tax()*100),
            FacturaMontoIVA: Math.abs(order.get_total_tax()*100),
            FacturaConsumidorFinal: true,
        }
        return data;
    }

    _transact_pay(cid) {
        var order = this.pos.get_order();

        if (!this.pos.currency.transact_currency_code) {
            this._show_error(_t("Transact currency code not set"));
            return Promise.resolve();
        }

        var data = this._transact_pay_data();
        var line = this.pos.get_order().selected_paymentline //order.paymentlines.find((paymentLine) => paymentLine.cid === cid);
        line.setTerminalServiceId(this.most_recent_service_id);
        return this._call_transact(data, 'PostearTransaccion').then((data) => {
            console.log(data);
            return this._transact_handle_response(data);
        });
    }

    _transact_cancel(ignore_error) {
        var config = this.pos.config;
        var previous_service_id = this.most_recent_service_id;
        var line = this.pos.get_order().selected_paymentline;
        var data = line.transactTokenNro;
        if (!data) {
            var line = this.pending_transact_line();
            line.set_payment_status("waiting");
            this._show_error(_t("Token number not found"));
            return true; // Promise.resolve();
        }
        return this._call_transact(data, 'CancelarTransaccion').then((data) => {
            console.log(data);
            if (!ignore_error && (data?.Resp_CodigoRespuesta && data.Resp_CodigoRespuesta != 0)) {
                var error_message = data?.Resp_MensajeError || _t(
                        "Cancelling the payment failed. Please cancel it manually on the payment terminal."
                    );
                this._show_error(error_message);
            }
            return data;
        });
        var response = this._call_transact(data, 'CancelarTransaccion');
        return response;
    }

    /**
     * This method handles the response that comes from Transact
     * when we first make a request to pay.
     */
    _transact_handle_response(response) {
        var line = this.pending_transact_line();
        if (response?.Resp_CodigoRespuesta && response.Resp_CodigoRespuesta != 0) {
            if (response?.Resp_MensajeError) {
                this._show_error(sprintf(_t("%s"), response.Resp_MensajeError));
            }
            else {
                this._show_error(_t("Unknown error"));
            }
            line.set_payment_status("force_done");
            return false;
        }
        else {
            this.pos.get_order().selected_paymentline.transactTokenNro = response.TokenNro;
            line.set_payment_status("waitingCard");
            // return this.waitForPaymentConfirmation();

            const isPaymentSuccessful = this.isPaymentSuccessful(response);
            if (isPaymentSuccessful) {
                line.set_payment_status("done");
                // this.handleSuccessResponse(line, response);
                return true;
            } else {
                line.set_payment_status("force_done");
                this._show_error(
                    sprintf(_t("Message from Transact: %s"), response?.MsgRespuesta || "")
                );
                return false;
            }
        }
    }
    isPaymentSuccessful(response) {
        return (
            response.Aprobada
        );
    }
    // private methods
    _showMsg(msg, title) {
        this.env.services.dialog.add(AlertDialog, {
            title: "Transact " + title,
            body: msg,
        });
    }
    _show_error(msg, title) {
        if (!title) {
            title = _t("Transact Error");
        }
        this.env.services.dialog.add(AlertDialog, {
            title: title,
            body: msg,
        });
    }
}
