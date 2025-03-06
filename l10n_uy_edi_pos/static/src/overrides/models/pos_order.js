import { PosOrder } from "@point_of_sale/app/models/pos_order";
import { patch } from "@web/core/utils/patch";

patch(PosOrder.prototype, {
    //@override
    setup() {
        super.setup(...arguments);
        if (this.is_uruguayan_company()) {
            this.uy_order_server_id = false;
            this.uy_invoice = false;
            this.uy_height = false;
            this.uy_width = false;
            /*if (window.isSecureContext) {
                this.uy_uuid = crypto.randomUUID();
            }
            else {
                this.uy_uuid = this.generate_uy_uuid();
            }*/
        }
    },
    is_uruguayan_company() {
        return this.company.country_id?.code == "UY";
    },

    /*generate_uy_uuid(){
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
            var r = Math.random()*16|0, v = c == 'x' ? r : (r&0x3|0x8);
            return v.toString(16);
        });
    },*/
    //@override
    /*export_as_JSON() {
        const json = super.export_as_JSON(...arguments);
        json.uy_order_server_id = this.uy_order_server_id;
        json.uy_uuid = this.uy_uuid;
        return json;
    },*/
    //@override
    /*init_from_JSON(json) {
        super.init_from_JSON(...arguments);
        if (json.uy_order_server_id) {
            this.uy_order_server_id = json.uy_order_server_id;
        }
        if (json.uy_uuid) {
            this.uy_uuid = json.uy_uuid;
        }
    },*/
    //@override
    export_for_printing(){
        const json = super.export_for_printing(...arguments);
        json.uy_invoice = this.uy_invoice;
        json.uy_height = this.uy_height;
        json.uy_height = this.uy_height;
        json.uy_company = this.is_uruguayan_company();
        return json
    },
});
