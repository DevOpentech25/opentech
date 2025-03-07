# common / servidor.py
# servidores = {
#     "efactura": "Efactura",
#     "biller": "Biller",
#     "factura_express": "Factura Express",
#     "uruware": "Uruware",
# }

from odoo import models, fields
from odoo.exceptions import UserError


class CfeServerType(models.Model):
    _name = "l10n_uy_cfe.server.type"
    _description = "Tipos de Servidores CFE"
    _rec_name = "name"

    name = fields.Char("Nombre", required=True, translate=True)


class CfeServer(models.Model):
    _name = "l10n_uy_cfe.server"
    _description = "Diferentes Servidores CFE"

    name = fields.Char("Nombre", required=True)
    server_type_id = fields.Many2one(
        "l10n_uy_cfe.server.type", string="Tipo de Servidor", required=True
    )
    company_id = fields.Many2one(
        "res.company",
        string="Compañía",
        required=True,
        default=lambda self: self.env.company,
    )
    url_api_cfe = fields.Char("URL Invoke CFE", required=False)
    url_query_cfe = fields.Char("URL Query CFE", required=False)
    token_api_cfe = fields.Char("Token API CFE", required=False)
    user_ws = fields.Char("Usuario WS", required=False)
    key_ws = fields.Char("Clave WS", required=False)
    active = fields.Boolean("Activo", default=True)

    def test_connection(self):
        return True
