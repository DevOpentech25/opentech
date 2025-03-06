from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class StockQuant(models.Model):
    _inherit = "stock.quant"

    def write(self, vals):
        """ Llama a la API cuando cambia la cantidad en stock """
        res = super().write(vals)  # Primero actualizar en Odoo

        if "quantity" in vals or "available_quantity" in vals:
            for record in self:
                record._trigger_inventory_update_quant()

        return res

    def _trigger_inventory_update_quant(self):
        """ Llama a la API cuando se modifica el stock en `stock.quant` """
        for record in self:
            product_sku = record.product_id.default_code
            stock_qty = record.available_quantity  # Stock actualizado
            available_qty = record.product_id.qty_available  # Stock actualizado

            if product_sku:
                warehouse_id = 1  # TODO: Pedir los id de almacen a la API
                wshelf_code = "1"  # TODO: Pedir los códigos de shelf a la API
                wlevel_code = "1"  # TODO: Pedir los códigos de level a la API
                wpile_code = "1"  # TODO: Pedir los códigos de pile a la API
                type_move_code = 5  # TODO: Pedir los códigos de movimiento de stock a la API

                products = [{
                    "SKU": product_sku,
                    "Stock": str(stock_qty),
                    "ProductStateCode": "OK",
                }]

                _logger.info(f"Updating inventory for product {product_sku} due to stock adjustment")
                self.env["api.inventory.update"].update_inventory(
                    warehouse_id, wshelf_code, wlevel_code, wpile_code, type_move_code, products
                )

                # También actualizar el stock del producto en la API
                self.env["api.inventory.update"].update_product_stock_by_sku(product_sku, available_qty)
