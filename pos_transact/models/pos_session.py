# -*- coding: utf-8 -*-

from odoo import models


class PosSession(models.Model):
    _inherit = 'pos.session'

    def _loader_params_pos_payment_method(self):
        result = super()._loader_params_pos_payment_method()
        result['search_params']['fields'].append('transact_terminal_identifier')
        return result

    def _loader_params_res_currency(self):
        res = super()._loader_params_res_currency()
        fields = res.get('search_params', {}).get('fields', [])
        fields += ["transact_currency_code"]
        res['search_params']['fields'] = fields
        return res