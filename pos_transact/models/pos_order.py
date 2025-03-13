# -*- coding: utf-8 -*-
from odoo import fields, models, api, _

class PosOrder(models.Model):
    _inherit = "pos.order"

    @api.model
    def _payment_fields(self, order, ui_paymentline):
        fields = super(PosOrder, self)._payment_fields(order, ui_paymentline)
        if ui_paymentline.get('transact_token'):
            fields.update({
                'transact_token': ui_paymentline['transact_token'],
            })
        return fields