from datetime import datetime

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


def _convert_date_datetime(date_str):
    """Convierte el formato de fecha de MercadoLibre al formato de Odoo"""
    try:
        return datetime.strptime(date_str[:19], "%Y-%m-%dT%H:%M:%S").strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    except ValueError:
        return False  # Retorna False si hay un error en la conversión


class APISalesOrders(models.AbstractModel):
    _name = "api.sale.order"
    _description = "API Sales Orders"
    _inherit = "api.connector"  # Hereda de APIConnector

    # Métodos para obtener órdenes de venta de MercadoLibre
    def fetch_meli_orders(self, last_days=1000):
        """Obtiene órdenes de MeLi desde la API y crea registros en sale.order"""
        endpoint = f"/rest/GetSalesOrderWebMeliWebhookDP?Lastdays={last_days}"
        orders_response = self._send_get_request(endpoint)

        if (
            not orders_response
            or isinstance(orders_response, dict)
            and "error" in orders_response
        ):
            raise ValidationError(
                f"Error al obtener órdenes de MeLi: {orders_response.get('error', 'Sin respuesta válida')}"
            )

        for order_data in orders_response:
            meli_order = order_data.get("MeliOrderNewRawData", {}).get("Orders", [])[0]
            if not meli_order:
                continue

            # buscar si existe esa orden de meli en odoo
            existing_order = self.env["sale.order"].search(
                [("external_meli_id", "=", meli_order.get("id"))]
            )
            if existing_order:
                _logger.info(f"Order {meli_order.get('id')} already exists in Odoo")
                continue

            buyer_data = meli_order.get("buyer", {})
            order_items = meli_order.get("order_items", [])
            payments = meli_order.get("payments", [])
            shipping_data = meli_order.get("shipping", {})  # todo implementar

            # Buscar o crear el cliente (partner)
            partner = self._get_or_create_partner(buyer_data)

            # Convertir la fecha correctamente
            order_date = _convert_date_datetime(meli_order.get("date_created"))

            # Crear la orden de venta en Odoo
            sale_order = self.env["sale.order"].create(
                {
                    "partner_id": partner.id,
                    "date_order": order_date,
                    "amount_total": float(meli_order.get("total_amount", 0.0)),
                    "currency_id": self._get_currency_id(meli_order.get("currency_id")),
                    "origin": f"Meli Order {meli_order.get('id')}",
                    "order_line": self._prepare_order_lines(order_items),
                    "external_meli_id": meli_order.get("id"),
                    "created_by_meli": True,
                }
            )

            # Crear pagos si existen
            if payments:
                # crear la factura account.move y relacionarla con la orden de venta
                account_move = self._create_invoice(sale_order)
                self._create_payments(account_move, payments)

            _logger.info(
                f"Orden de venta creada en Odoo: {sale_order.name} (ID: {sale_order.id})"
            )

        return True

    def _get_or_create_partner(self, buyer_data):
        """Busca o crea un cliente basado en los datos de MercadoLibre"""
        partner_model = self.env["res.partner"]
        email = buyer_data.get("email")

        partner = partner_model.search([("email", "=", email)], limit=1)
        if not partner:
            partner = partner_model.create(
                {
                    "name": f"{buyer_data.get('first_name', '')} {buyer_data.get('last_name', '')}".strip(),
                    "email": email,
                    "vat": buyer_data.get("billing_info", {}).get("doc_number", ""),
                    "customer_rank": 1,
                }
            )
        return partner

    def _prepare_order_lines(self, order_items):
        """Prepara las líneas de la orden de venta"""
        order_lines = []
        for item in order_items:
            product = self._get_or_create_product(item["item"])
            order_lines.append(
                (
                    0,
                    0,
                    {
                        "product_id": product.id,
                        "name": item["item"]["title"],
                        "product_uom_qty": int(item["quantity"]),
                        "price_unit": float(item["unit_price"]),
                    },
                )
            )
        return order_lines

    def _get_or_create_product(self, item_data):
        """Busca o crea un producto basado en la información de MercadoLibre"""
        product_model = self.env["product.product"]
        sku = item_data.get("seller_custom_field", "{}")
        product_id = None

        try:
            product_id = eval(sku).get("PrId")  # Extraer ID del campo JSON
        except:
            _logger.error(f"Error al extraer ID de producto de MercadoLibre: {sku}")
            pass

        product = product_model.search([("default_code", "=", product_id)], limit=1)
        if not product:
            product = product_model.create(
                {
                    "name": item_data.get("title"),
                    "default_code": product_id,
                    "list_price": float(item_data.get("price", 0.0)),
                    "type": "consu",
                    "categ_id": self.env.ref("product.product_category_all").id,
                }
            )
        return product

    def _create_invoice(self, sale_order):
        """Crea una factura a partir de una orden de venta"""
        invoice_model = self.env["account.move"]
        invoice = invoice_model.create(
            {
                "move_type": "out_invoice",  # Factura de cliente
                "partner_id": sale_order.partner_id.id,
                "invoice_date": sale_order.date_order,
                "invoice_origin": sale_order.origin,
                "invoice_payment_term_id": sale_order.payment_term_id.id,
                "invoice_user_id": sale_order.user_id.id,
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": line.product_id.id,
                            "name": line.product_id.name,
                            "account_id": line.product_id.categ_id.property_account_income_categ_id.id,  # Cuenta contable de ingresos
                            "quantity": line.product_uom_qty,
                            "price_unit": line.price_unit,
                            #'tax_ids': [(6, 0, line.product_id.taxes_id.ids)],  # Asignar impuestos si aplica
                        },
                    )
                    for line in sale_order.order_line
                ],
            }
        )
        sale_order.write({"invoice_ids": [(4, invoice.id)]})
        return invoice

    def _create_payments(self, account_move, payments):
        """Crea registros de pagos asociados a la orden"""
        payment_model = self.env["account.payment"]
        for payment in payments:
            payment_model.create(
                {
                    "partner_id": account_move.partner_id.id,
                    "amount": float(payment["transaction_amount"]),
                    "currency_id": self._get_currency_id(payment["currency_id"]),
                    "payment_type": "inbound",
                    "partner_type": "customer",
                    "move_id": account_move.id,
                    "payment_method_id": self._get_payment_method_id(
                        payment["payment_method_id"]
                    ),
                    "memo": f"Pago ML: {payment['id']}",
                }
            )

    def _get_currency_id(self, currency_code):
        """Devuelve el ID de la moneda en Odoo basado en el código (ARS, USD, etc.)"""
        currency = self.env["res.currency"].search(
            [("name", "=", currency_code)], limit=1
        )
        return currency.id if currency else self.env.company.currency_id.id

    def _get_payment_method_id(self, payment_method):
        """Devuelve el ID del método de pago en Odoo basado en el método de MercadoLibre"""
        payment_method_map = {
            "credit_card": "Manual",
            "account_money": "Bank",
        }
        method_name = payment_method_map.get(payment_method, "Manual")
        payment_method = self.env["account.payment.method"].search(
            [("name", "=", method_name)], limit=1
        )
        return payment_method.id if payment_method else False

    # Métodos para obtener órdenes de Fenicio
    def fetch_fenicio_orders(self, last_days=1000):
        """Obtiene órdenes de Fenicio desde la API y crea registros en sale.order"""
        endpoint = f"/rest/GetSalesOrderWebFenicioWebhookDP?Lastdays={last_days}"
        orders_response = self._send_get_request(endpoint)

        if (
            not orders_response
            or isinstance(orders_response, dict)
            and "error" in orders_response
        ):
            raise ValidationError(
                f"Error al obtener órdenes de Fenicio: {orders_response.get('error', 'Sin respuesta válida')}"
            )

        for order_data in orders_response:
            order_raw = order_data.get("OrderRawData", {})
            order_external_id = order_data.get("OrderExternalId")
            order_status = order_data.get("OrderStatus")

            if not order_raw:
                _logger.error(f"Orden de Fenicio sin datos: {order_external_id}")
                continue

            # buscar si la orden ya existe en Odoo
            existing_order = self.env["sale.order"].search(
                [("external_fenicio_id", "=", order_external_id)], limit=1
            )
            if existing_order:
                _logger.info(f"Orden de Fenicio ya existe en Odoo: {order_external_id}")
                continue

            # Extraer información del comprador y productos
            buyer_data = order_raw.get("comprador", {})
            order_items = order_raw.get("lineas", [])
            payment_data = order_raw.get("pago", {})

            # Buscar o crear el cliente
            partner = self._get_or_create_partner_fenicio(buyer_data)

            # Convertir la fecha correctamente
            order_date = _convert_date_datetime(order_raw.get("fechaInicioD"))

            # Crear la orden de venta en Odoo
            sale_order = self.env["sale.order"].create(
                {
                    "partner_id": partner.id,
                    "date_order": order_date,
                    "amount_total": float(order_raw.get("importeTotal", 0.0)),
                    "currency_id": self._get_currency_id(order_raw.get("moneda")),
                    "origin": f"Fenicio Order {order_external_id}",
                    "state": "sale" if order_status == "APROBADA" else "draft",
                    "order_line": self._prepare_order_lines_fenicio(order_items),
                    "created_by_fenicio": True,
                    "external_fenicio_id": order_external_id,
                }
            )

            # Crear pagos si existen
            if payment_data:
                account_move = self._create_invoice_fenicio(sale_order)
                self._create_payments_fenicio(account_move, payment_data)

            _logger.info(
                f"Orden de venta creada en Odoo: {sale_order.name} (ID: {sale_order.id})"
            )

        return True

    def _get_or_create_partner_fenicio(self, buyer_data):
        """Busca o crea un cliente basado en los datos de Fenicio"""
        partner_model = self.env["res.partner"]
        email = buyer_data.get("email")

        partner = partner_model.search([("email", "=", email)], limit=1)
        if not partner:
            partner = partner_model.create(
                {
                    "name": f"{buyer_data.get('nombre', '')} {buyer_data.get('apellido', '')}".strip(),
                    "email": email,
                    "phone": buyer_data.get("telefono", ""),
                    "vat": buyer_data.get("documento", {}).get("numero", ""),
                    "customer_rank": 1,
                }
            )
        return partner

    def _prepare_order_lines_fenicio(self, order_items):
        """Prepara las líneas de la orden de venta"""
        order_lines = []
        for item in order_items:
            product = self._get_or_create_product_fenicio(item)
            order_lines.append(
                (
                    0,
                    0,
                    {
                        "product_id": product.id,
                        "name": item.get("nombre", ""),
                        "product_uom_qty": int(item.get("cantidad", 1)),
                        "price_unit": float(item.get("precio", 0.0)),
                    },
                )
            )
        return order_lines

    def _get_or_create_product_fenicio(self, item_data):
        """Busca o crea un producto basado en la información de Fenicio"""
        product_model = self.env["product.product"]
        sku = item_data.get("sku", "")

        product = product_model.search([("default_code", "=", sku)], limit=1)
        if not product:
            product = product_model.create(
                {
                    "name": item_data.get("nombre", "Producto sin nombre"),
                    "default_code": sku,
                    "list_price": float(item_data.get("precio", 0.0)),
                    "type": "consu",
                }
            )
        return product

    def _create_invoice_fenicio(self, sale_order):
        """Crea una factura asociada a la orden de Fenicio"""
        invoice = sale_order._create_invoices()

        if invoice:
            return invoice
        return False

    def _create_payments_fenicio(self, account_move, payment_data):
        """Crea registros de pagos asociados a la orden de Fenicio"""
        payment_model = self.env["account.payment"]

        if payment_data.get("estado") == "APROBADO":
            payment_model.create(
                {
                    "partner_id": account_move.partner_id.id,
                    "amount": float(payment_data.get("importe", 0.0)),
                    "currency_id": self._get_currency_id(payment_data.get("moneda")),
                    "payment_type": "inbound",
                    "partner_type": "customer",
                    "move_id": account_move.id,
                    "memo": f"Pago Fenicio: {payment_data.get('idExterno', '')}",
                }
            )
