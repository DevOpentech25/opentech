/** @odoo-module */
import { register_payment_method } from "@point_of_sale/app/store/pos_store";
import { PosPayment } from "@point_of_sale/app/models/pos_payment";
import { PaymentTransact } from "@pos_transact/app/payment_transact";
import { registry } from "@web/core/registry";

export class CustomPayment extends PosPayment {
    setup(vals) {
        super.setup(vals);
        this.terminalServiceId = vals.terminalServiceId || null;
        this.transactTokenNro = vals.transactTokenNro || '';
    }

    //@override
    export_as_JSON() {
        const json = super.export_as_JSON();
        json.terminal_service_id = this.terminalServiceId;
        json.transact_token = this.transactTokenNro;
        return json;
    }

    //@override
    init_from_JSON(json) {
        super.init_from_JSON(json);
        this.terminalServiceId = json.terminal_service_id || null;
        this.transactTokenNro = json.transact_token || '';
    }

    setTerminalServiceId(id) {
        this.terminalServiceId = id;
    }
}

// Registrar el nuevo método de pago en `pos_available_models`
registry.category("pos_available_models").add("custom_payment", CustomPayment);

// Registrar el nuevo método de pago en `pos_store`
register_payment_method("transact", PaymentTransact);
