from odoo import models, fields, api
import logging
import requests
from odoo.exceptions import ValidationError
log = logging.getLogger(__name__)


class BillerClient(models.AbstractModel):
    _name = "l10n_uy_cfe.biller.client"
    _description = "CFE Biller Client"
    """Clase abstracta para manejar la comunicación con la API de CFE usando request"""

    url_api_cfe = fields.Char("URL API CFE")
    token_api_cfe = fields.Char("Token API CFE")
    version_api_cfe = fields.Char("Version API CFE", default="v2")

    def _get_api_method(self, operation_type):
        """Genera la URL del endpoint basado en la operación."""
        return f"{self.version_api_cfe}/comprobantes/{operation_type}"

    @staticmethod
    def _get_response(response):
        """Maneja la respuesta de la API y la convierte en un diccionario manejable."""
        try:
            log.debug(f"Response URL: {response.url}")
            log.debug(f"Response Status: {response.status_code}")

            if response.status_code == 200 and "comprobantes/pdf" in response.url:
                return {"estado": True, "respuesta": {"pdf": response.text}}

            res = response.json()
            if response.status_code not in [200, 201]:
                return {
                    "estado": False,
                    "respuesta": {"error": res, "codigo": response.status_code},
                }

            return {"estado": True, "respuesta": res}
        except Exception as e:
            log.error(f"Error procesando respuesta: {str(e)}")
            return {
                "estado": False,
                "respuesta": {"error": str(e), "codigo": response.status_code},
            }

    @staticmethod
    def _get_headers(token):
        """Retorna los headers para la API con autenticación."""
        return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    def _make_request(
            self, method, operation_type, token, params=None, json_data=None, timeout=30
    ):
        """Realiza peticiones HTTP genéricas a la API."""
        headers = self._get_headers(token)

        if not self.env.company.uy_server:
            raise ValidationError("No se ha configurado un servidor CFE para Biller")

        self.url_api_cfe = self.env.company.url_api_cfe
        self.token_api_cfe = self.env.company.token_api_cfe

        url = f"{self.url_api_cfe}/{self._get_api_method(operation_type)}"

        try:
            response = requests.request(
                method,
                url,
                headers=headers,
                params=params,
                json=json_data,
                timeout=timeout,
            )
            return self._get_response(response)
        except requests.RequestException as e:
            log.error(f"Error en la solicitud API: {str(e)}")
            return {"estado": False, "respuesta": {"error": str(e), "codigo": None}}

    def send_invoice(self, token, data):
        """Envía una factura a la API."""
        return self._make_request("POST", "crear", token, json_data=data)

    def get_pdf(self, token, invoice_id):
        """Obtiene el PDF de una factura."""
        return self._make_request(
            "GET", "pdf", token, params={"id": invoice_id}, timeout=300
        )

    def get_invoice(self, token, invoice_id):
        """Obtiene los datos de una factura."""
        return self._make_request("GET", "obtener", token, params={"id": invoice_id})

    def check_invoice(
            self,
            token,
            numero_interno=None,
            desde=None,
            tipo_comprobante=None,
            serie=None,
            numero=None,
    ):
        """Verifica una factura basada en diferentes criterios."""
        params = {}
        if numero_interno:
            params["numero_interno"] = numero_interno
        elif serie and numero and tipo_comprobante:
            params.update(
                {
                    "desde": desde,
                    "tipo_comprobante": tipo_comprobante,
                    "serie": serie,
                    "numero": numero,
                }
            )

        if params:
            return self._make_request("GET", "obtener", token, params=params)
        return {}
