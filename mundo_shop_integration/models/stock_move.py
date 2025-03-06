from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)

class StockMove(models.Model):
    _inherit = "stock.move"

    def write(self, vals):
        """ Llama a la API solo cuando un movimiento se confirma (state = 'done') """
        res = super().write(vals)  # Primero actualizar en Odoo

        if "state" in vals and vals["state"] == "done":
            for record in self:
                record._trigger_inventory_update_move()

        return res

    def _trigger_inventory_update_move(self):
        """ Llama a la API cuando un movimiento de stock se confirma """
        for record in self:
            if record.state != "done":
                return  # Evita ejecutar si no está finalizado

            for move_line in record.move_line_ids:
                product_sku = move_line.product_id.default_code
                stock_qty = move_line.quantity  # Cantidad movida
                available_qty = move_line.product_id.qty_available  # Stock actualizado

                if product_sku:
                    warehouse_id = 1 # TODO: Pedir los id de almacen a la API
                    wshelf_code = "1" # TODO: Pedir los códigos de shelf a la API
                    wlevel_code = "1" # TODO: Pedir los códigos de level a la API
                    wpile_code = "1" # TODO: Pedir los códigos de pile a la API
                    type_move_code = 5  # TODO: Pedir los códigos de movimiento de stock a la API

                    products = [{
                        "SKU": product_sku,
                        "Stock": str(stock_qty),
                        "ProductStateCode": "OK",
                    }]

                    _logger.info(f"Updating inventory for product {product_sku} due to stock move")
                    self.env["api.inventory.update"].update_inventory(
                        warehouse_id, wshelf_code, wlevel_code, wpile_code, type_move_code, products
                    )

                    # También actualizar el stock del producto en la API
                    self.env["api.inventory.update"].update_product_stock_by_sku(product_sku, available_qty)
