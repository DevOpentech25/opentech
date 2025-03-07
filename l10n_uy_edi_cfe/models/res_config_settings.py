# -*- coding: utf-8 -*-

from odoo import fields, models, _, api


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    server_cfe_id = fields.Many2one(
        "l10n_uy_cfe.server",
        string="Servidor CFE",
        config_parameter="l10n_uy_edi_cfe.server_cfe_id",
    )

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env["ir.config_parameter"].set_param(
            "l10n_uy_edi_cfe.server_cfe_id", self.server_cfe_id.id
        )

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        server_cfe_id = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("l10n_uy_edi_cfe.server_cfe_id")
        )
        res.update(server_cfe_id=int(server_cfe_id) if server_cfe_id else False)
        return res
