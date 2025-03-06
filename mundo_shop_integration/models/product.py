from odoo import fields, models, api
import logging
_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def _sync_price_with_api(self):
        """ Encapsula la lógica para sincronizar el precio con la API """
        for product in self:
            if not product.default_code:
                _logger.warning(f"Skipping price update for {product.name}: Missing SKU")
                continue  # Evitar enviar datos inválidos a la API

            _logger.info(f"Updating price for product {product.default_code}")

            try:
                self.env['api.inventory.update'].update_external_price_by_sku(
                    product.default_code, product.currency_id.name, product.list_price
                )
            except Exception as e:
                _logger.error(f"Error updating external price: {e}")

    def _sync_stock_with_api(self):
        """ Encapsula la lógica para sincronizar el stock con la API """
        for product in self:
            if not product.default_code:
                _logger.warning(f"Skipping stock update for {product.name}: Missing SKU")
                continue

            _logger.info(f"Updating stock for product {product.default_code}")

            try:
                self.env['api.inventory.update'].update_product_stock_by_sku(
                    product.default_code, product.qty_available
                )
            except Exception as e:
                _logger.error(f"Error updating product stock: {e}")

    @api.model
    def create(self, vals):
        """ Llama a la API después de crear un nuevo producto """
        new_product = super().create(vals)  # Crear el producto en Odoo
        new_product._sync_price_with_api()  # Sincronizar precio
        new_product._sync_stock_with_api()  # Sincronizar stock
        return new_product

    def write(self, vals):
        """ Llama a la API solo si cambia el precio o stock """
        res = super().write(vals)  # Primero actualizar en Odoo

        if 'list_price' in vals:
            self._sync_price_with_api()  # Sincronizar solo si cambia el precio

        if 'qty_available' in vals:
            self._sync_stock_with_api()  # Sincronizar solo si cambia el stock

        return res

