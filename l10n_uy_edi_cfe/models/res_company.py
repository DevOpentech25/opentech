# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class ResCompany(models.Model):
    _inherit = "res.company"

    uy_server = fields.Many2one(
        "l10n_uy_cfe.server",
        string="Server",
        compute="_compute_server_cfe",
        inverse="_set_server_cfe",  # Guarda el valor en ir.config_parameter
        store=False,  # No se almacena en la base de datos directamente
    )

    uy_username = fields.Char(
        related="uy_server.user_ws", string="Username", readonly=True
    )
    uy_password = fields.Char(
        related="uy_server.key_ws", string="Password", readonly=True
    )
    uy_server_url = fields.Char(
        related="uy_server.url_api_cfe", string="Server URL", readonly=True
    )
    uy_efactura_print_mode = fields.Selection(
        selection="get_uy_efactura_print_mode", string="Print Mode"
    )
    uy_branch_code = fields.Char("Branch Code")
    uy_sync_mode = fields.Boolean("Sync Mode", default=True)
    uy_resolution = fields.Char("Resolution")
    uy_verification_url = fields.Char("Verification Url")
    uy_amount = fields.Float(string="Amount", digits=(16, 2), default=36300.00)
    uy_company_id = fields.Char("Company Id")
    emission_id_code = fields.Char(string="UUID del Emisor") # UUID del emisor
    cfe_code_terminal = fields.Char(string="Código de Terminal")
    cfe_code_shop = fields.Char(string="Código de Comercio")
    dgi_code = fields.Char(string="Código de casa DGI")

    @api.depends_context("uid")
    def _compute_server_cfe(self):
        """Obtiene el servidor CFE desde ir.config_parameter cuando se accede a uy_server"""
        for record in self:
            server_cfe_id = (
                self.env["ir.config_parameter"]
                .sudo()
                .get_param("l10n_uy_edi_cfe.server_cfe_id")
            )
            record.uy_server = int(server_cfe_id) if server_cfe_id else False

    def _set_server_cfe(self):
        """Guarda el servidor seleccionado en ir.config_parameter"""
        for record in self:
            self.env["ir.config_parameter"].sudo().set_param(
                "l10n_uy_edi_cfe.server_cfe_id",
                record.uy_server.id if record.uy_server else "",
            )

    @api.model
    def get_uy_efactura_print_mode(self):
        return self.env["uy.datas"].get_by_code("UY.EFACTURA.PRINT.MODE")
