/** @odoo-module */
import { patch } from "@web/core/utils/patch";
import { PosStore } from "@point_of_sale/app/store/pos_store";

patch(PosStore.prototype, {
    // Override
    async setup() {
        await super.setup(...arguments);
        this.data.connectWebSocket("TRANSACT_LATEST_RESPONSE", (payload) => {
            if (payload.config_id === this.config.id) {
                const pendingLine = this.getPendingPaymentLine("transact");

                if (pendingLine) {
                    pendingLine.payment_method_id.payment_terminal.handleTransactStatusResponse();
                }
            }
        });
    },
});
