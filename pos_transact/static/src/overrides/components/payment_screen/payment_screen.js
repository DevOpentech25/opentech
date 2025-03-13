/** @odoo-module */

import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen"; // changed
import { onMounted, useComponent } from "@odoo/owl"; // changed

export class CustomPaymentScreen extends PaymentScreen {
    setup() {
        super.setup();
        onMounted(() => {
            const order = this.env.pos.get_order();  // Obtener la orden activa
            if (!order || !order.paymentlines) {
                console.warn("currentOrder or paymentlines is not available yet");
                return;
            }

            const pendingPaymentLine = order.paymentlines.find(
                (paymentLine) =>
                    paymentLine.payment_method.use_payment_terminal === "transact" &&
                    !paymentLine.is_done() &&
                    paymentLine.get_payment_status() !== "pending"
            );

            if (!pendingPaymentLine) {
                return;
            }

            pendingPaymentLine.payment_method.payment_terminal.set_most_recent_service_id(
                pendingPaymentLine.terminalServiceId
            );
        });
    }
}
