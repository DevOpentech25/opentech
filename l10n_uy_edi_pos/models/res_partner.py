# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.ondelete(at_uninstall=False)
    def _pe_unlink_except_master_data(self):
        consumidor_final_anonimo = self.env.ref("l10n_uy.partner_cfu")
        if consumidor_final_anonimo & self:
            raise UserError(
                _(
                    "Deleting the partner %s is not allowed because it is required by the Peruvian point of sale.",
                    consumidor_final_anonimo.display_name,
                )
            )

    @api.model
    def _load_pos_data_fields(self, config_id):
        fields = super()._load_pos_data_fields(config_id)
        if self.env.company.country_id.code == "UY":
            fields += ["city_id", "l10n_latam_identification_type_id", "uy_doc_type"]
        return fields