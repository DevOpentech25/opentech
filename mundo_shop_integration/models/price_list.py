from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)

class ProductPricelistItem(models.Model):
    _inherit = "product.pricelist.item"

    def _sync_price_with_api(self):
        """ Encapsula la lógica para sincronizar precios con la API """
        for record in self:
            sku = record.product_id.default_code if record.product_id.default_code else record.product_tmpl_id.default_code
            name = record.product_id.name if record.product_id.name else record.product_tmpl_id.name
            if not sku:
                _logger.warning(f"Skipping API sync for {name}: Missing SKU")
                continue  # Evitar enviar datos inválidos a la API

            price_list_dict = [{
                "Id": record.id,
                "CurrencyCode": record.currency_id.name,
                "Price": float(record.fixed_price) if record.fixed_price else 0.0
            }]
            _logger.info(f"Syncing price-list for product {price_list_dict}")

            try:
                record.env['api.inventory.update'].update_product_pricelist_by_sku(
                    sku, price_list_dict
                )
            except Exception as e:
                _logger.error(f"Error updating price in API: {e}")

    @api.model_create_multi
    def create(self, vals_list):
        """ Optimiza la creación en lote y sincroniza con la API """
        records = super().create(vals_list)  # Crear los registros en Odoo

        # Llamar a la API para cada registro creado
        for record in records:
            record._sync_price_with_api()

        return records  # Retornar los registros creados

    def write(self, vals):
        """ Llama a la API solo si cambia el precio """
        res = super().write(vals)  # Primero actualizar en Odoo

        if 'fixed_price' in vals:
            self._sync_price_with_api()  # Sincronizar con API solo si se modificó el precio

        return res
