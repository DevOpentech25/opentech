import requests
import json
from odoo import models, fields, api
import base64
from odoo.exceptions import UserError


class UCFEService(models.Model):
    _name = "cfe.uruware.service"
    _description = "Integración con UCFE"

    server_settings = fields.Many2one(
        "l10n_uy_cfe.server",
        compute="_compute_server_settings",
        store=False,  # Ahora se guarda en la BD
    )

    user_ws = fields.Char("Usuario WS", related="server_settings.user_ws", readonly=True)
    key_ws = fields.Char("Clave WS", related="server_settings.key_ws", readonly=True)

    @api.depends("server_settings")
    def _compute_server_settings(self):
        """Calcula la configuración del servidor UCFE."""
        for record in self:
            server = self.env.company.uy_server

            if not server:
                setting = self.env["ir.config_parameter"].sudo().get_param("l10n_uy_edi_cfe.server_cfe_id")
                if setting:
                    server = self.env["l10n_uy_cfe.server"].browse(int(setting))

            record.server_settings = server or False  # Evita asignar None

    def get_headers(self):
        credentials = f"{self.user_ws}:{self.key_ws}"
        auth_header = base64.b64encode(credentials.encode()).decode()
        return {
            "Authorization": f"Basic {auth_header}",
            "Content-Type": "application/json",
        }

    def get_url_server(self):
        setting = self.env["ir.config_parameter"].sudo().get_param("l10n_uy_edi_cfe.server_cfe_id")
        if not setting:
            raise UserError("No se ha configurado el servidor CFE")

        server = self.env["l10n_uy_cfe.server"].browse(int(setting)) if setting else False
        return server.url_api_cfe if server else False

    def send_cfe_document(self, cfe_data):
        url = self.get_url_server()+"/Invoke"
        headers = self.get_headers()
        cod_shop = self.env.company.cfe_code_shop
        cod_terminal = self.env.company.cfe_code_terminal
        payload = {
            "CodComercio":cod_shop,
            "CodTerminal": cod_terminal,
            "Req": cfe_data,
            "RequestDate": fields.Datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            "TipoMensaje": 300,
        }

        response = requests.post(url, data=json.dumps(payload), headers=headers)

        if response.status_code == 200:
            raise UserError(response.text)
        else:
            return {"error": response.text}

    def get_cfe_received(self, cfe_number, serie):
        url = self.get_url_server()
        headers = self.get_headers()
        cod_shop = self.env.company.cfe_code_shop
        cod_terminal = self.env.company.cfe_code_terminal

        payload = {
            "CodComercio": cod_shop,
            "CodTerminal": cod_terminal,
            "Req": {"TipoMensaje": "650", "NumeroCfe": cfe_number, "Serie": serie},
            "RequestDate": fields.Datetime.now(),
            "Tout": 30000,
        }

        response = requests.post(url, data=json.dumps(payload), headers=headers)
        return (
            response.text if response.status_code == 200 else {"error": response.text}
        )


    # WEB Service QUERY
    def invoke_cfe_service(self):
        #"https://test.ucfe.com.uy/Query116_2/WebServicesFE.svc/rest/ConsultaHtmlPorNumero"
        url = get_url_server()+"/ConsultaHtmlPorNumero"
        headers = get_headers()
        FECHA_COMPROBANTE = "2025-03-06"  # Fecha en formato correcto

        # Estructura del payload según los parámetros esperados por el servicio
        payload = {
            "rut": self.env.company.vat,
            "tipoCfe": 101,  # e-Ticket
            "serieCfe": "A",
            "numeroCfe": "12",
        }

        response = requests.post(url, json=payload, headers=headers)

        if response.status_code == 200:
            return response.text
        else:
            return {
                "error": f"Request failed with status code {response.status_code}",
                "details": response.text,
            }
