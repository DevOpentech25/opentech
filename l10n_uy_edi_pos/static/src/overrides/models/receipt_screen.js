/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import { ReceiptScreen } from "@point_of_sale/app/screens/receipt_screen/receipt_screen";

patch(ReceiptScreen.prototype, {
    //@override
    setup() {
        super.setup();
        this._printUyReceipt()
    },
    //@override
    async _printUyReceipt() {
        if (this.currentOrder.uy_order_server_id){
            const data = await this.pos.data.call("pos.order", "get_uy_pdf_invoice", [this.currentOrder.uy_order_server_id]);
            if (data.error){
                alert(data.error);
            }
            if (data.invoice) {
                this.currentOrder.uy_invoice = "data:image/png;base64,"+ data.invoice.image;
                this.currentOrder.uy_height = data.invoice.height;
                this.currentOrder.uy_width = data.invoice.width;
            }
        }
    },

});
