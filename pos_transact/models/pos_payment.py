from odoo import api, fields, models, _



class PosPayment(models.Model):

    _inherit = "pos.payment"

    transact_token = fields.Char(string='Transact Token Nro', readonly=True)