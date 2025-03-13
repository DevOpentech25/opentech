# -*- coding: utf-8 -*-


from odoo import models, fields

class ResCurrency(models.Model):
    _inherit = 'res.currency'

    transact_currency_code = fields.Char(string='Transact Currency Code', help='Transact Currency Code')