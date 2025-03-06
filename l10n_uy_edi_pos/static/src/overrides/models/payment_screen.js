/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { AlertDialog, ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { formatDate, formatDateTime, serializeDateTime } from "@web/core/l10n/dates";
import { _t } from "@web/core/l10n/translation";

patch(PaymentScreen.prototype, {
    //@override
    async validateOrder(isForceValidate) {
        if (this.currentOrder.is_uruguayan_company()) {
            this.currentOrder.set_to_invoice(true);
            if (!this.currentOrder.get_partner() && this.currentOrder.session._uy_anonymous_id){
                this.currentOrder.update({ partner_id: this.currentOrder.session._uy_anonymous_id });
            }
            if (!this.currentOrder.get_partner()){
                this.dialog.add(AlertDialog, {
                    title: _t("Missing Customer"),
                    body: _t("You must have a client assigned"),
                });
                return;
            }
            var client = this.currentOrder.get_partner();

            if (client.uy_doc_type){
                if (!client.vat){
                    this.dialog.add(AlertDialog, {
                        title: _t("Client rut number"),
                        body: _t("You must enter number rut"),
                    });
                    return false;
                }
                if (!client.street){
                    this.dialog.add(AlertDialog, {
                        title: _t("Client Address"),
                        body: _t("You must enter an address"),
                    });
                    return;
                }
                if (!client.city){
                    this.dialog.add(AlertDialog, {
                        title: _t("Client City"),
                        body: _t("You must enter an city"),
                    });
                    return;
                }
                if (!client.state_id){
                    this.dialog.add(AlertDialog, {
                        title: _t("Client State"),
                        body: _t("You must enter an state"),
                    });
                    return;
                }

            }
            var qty_error = "";
            var price_error = "";
            for (var i = 0; i < this.currentOrder.lines.length; i++) {
                if (this.currentOrder.lines[i].quantity==0.0){
                    qty_error+=this.currentOrder.lines.models[i].get_product().display_name + "\n";
                }
                if (this.currentOrder.lines[i].price==0.0){
                    price_error+=this.currentOrder.lines[i].get_product().display_name + "\n";
                }
            }
            /*this.currentOrder.orderlines.each(_.bind( function(item) {
                if (item.qty==0.0){
                    qty_error+=item.get_product().name + "<br />";
                }
            }, this));  */

            if (qty_error!=""){
                this.dialog.add(AlertDialog, {
                    title: _t("Error"),
                    body: _t("The product quantity must be greater than zero"),
                });
                return;
            }
            if (price_error!=""){
                this.dialog.add(AlertDialog, {
                    title: _t("Error"),
                    body: _t("The product price must be greater than zero"),
                });
                return;
            }
        }
        return await super.validateOrder(isForceValidate);

    },
    async _finalizeValidation() {
        if (!this.currentOrder.is_uruguayan_company()) {
            return await super._finalizeValidation();
        }
        if (this.currentOrder.is_paid_with_cash() || this.currentOrder.get_change()) {
            this.hardwareProxy.openCashbox();
        }
        this.currentOrder.date_order = serializeDateTime(luxon.DateTime.now());
        for (const line of this.paymentLines) {
            if (!line.amount === 0) {
                this.currentOrder.remove_paymentline(line);
            }
        }

        this.pos.addPendingOrder([this.currentOrder.id]);
        this.currentOrder.state = "paid";

        this.env.services.ui.block();
        let syncOrderResult;
        try {
            // 1. Save order to server.
            syncOrderResult = await this.pos.syncAllOrders({ throw: true });
            if (!syncOrderResult) {
                return;
            }
            this.pos.showScreen(this.nextScreen);

            this.currentOrder.account_move;
            // 2. Invoice.
            if (this.shouldDownloadInvoice() && this.currentOrder.is_to_invoice()) {
                if (this.currentOrder.account_move) {
                    this.currentOrder.uy_order_server_id = syncOrderResult[0].id
                } else {
                    throw {
                        code: 401,
                        message: "Backend Invoice",
                        data: { order: this.currentOrder },
                    };
                }
            }
        } catch (error) {
            if (error instanceof ConnectionLostError) {
                this.pos.showScreen(this.nextScreen);
                Promise.reject(error);
            } else if (error instanceof RPCError) {
                this.currentOrder.state = "draft";
                handleRPCError(error, this.dialog);
            } else {
                throw error;
            }
            return error;
        } finally {
            this.env.services.ui.unblock();
        }

        // 3. Post process.
        const postPushOrders = syncOrderResult.filter((order) => order.wait_for_push_order());
        if (postPushOrders.length > 0) {
            await this.postPushOrderResolve(postPushOrders.map((order) => order.id));
        }

        await this.afterOrderValidation(!!syncOrderResult && syncOrderResult.length > 0);
    }
});
