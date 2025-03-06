from odoo import fields, models, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    # Campos personalizados y llamadas a métodos del api_connector
    external_meli_id = fields.Char(string="ID Externo Meli", readonly=True)
    external_fenicio_id = fields.Char(string="ID Externo Fenicio", readonly=True)
    created_by_fenicio = fields.Boolean(string="Creado por API Fenicio", default=False)
    created_by_meli = fields.Boolean(string="Creado por API Meli", default=False)
    send_invoice_meli = fields.Boolean(string="Enviar factura a Meli", default=False)
