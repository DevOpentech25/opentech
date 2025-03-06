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
        "l10n_uy_cfe.server.type",
        string="Tipo de Servidor",
        required=True
    )
    url_api_cfe = fields.Char("URL API CFE", required=True)
    token_api_cfe = fields.Char("Token API CFE", required=True)
    usuario = fields.Char("Usuario", required=True)
    clave = fields.Char("Clave", required=True)
    codigo = fields.Char("Código", required=True)
    active = fields.Boolean("Activo", default=True)
    type_client_id = fields.Many2one('cfe.api.client', string='Tipo de Cliente', required=True)

    def test_connection(self):
        if self.type_client_id:
            return self.type_client_id.test_connection()
        raise UserError("No se ha configurado el tipo de cliente")

