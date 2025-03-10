from odoo import fields, models, api
from lxml import etree
from odoo.exceptions import UserError


class CfeUruwareDocument(models.Model):
    _name = 'cfe.uruware.document'
    _description = 'Tipo de documento CFE para enviar por Uruware'

    name = fields.Char()
    account_id = fields.Many2one('account.move', string='Documento de venta')


