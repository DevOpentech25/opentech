# common / servidor.py
# servidores = {
#     "efactura": "Efactura",
#     "biller": "Biller",
#     "factura_express": "Factura Express",
#     "uruware": "Uruware",
# }

from odoo import models, fields
from odoo.exceptions import UserError


class TypeCFECode(models.Model):
    _name = "type.cfe.code"
    _description = "CFE Codes for LPS"

    code = fields.Char(string="Código", required=True)
    name = fields.Char(string="Descripción", required=True)


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
        "l10n_uy_cfe.server.type",
        string="Tipo de Servidor",
        required=True
    )
    url_api_cfe = fields.Char("URL Invoke CFE", required=False)
    url_query_cfe = fields.Char("URL Query CFE", required=False)
    token_api_cfe = fields.Char("Token API CFE", required=False)
    user_ws = fields.Char("Usuario WS", required=False)
    key_ws = fields.Char("Clave WS", required=False)
    active = fields.Boolean("Activo", default=False)

    def test_connection(self):
        return True

