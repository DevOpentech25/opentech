import requests
import logging
from odoo import models, api
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

class APIConnector(models.AbstractModel):
    _name = 'api.connector'
    _description = 'Abstract API Connector'

    def _get_api_credentials(self):
        """ Obtiene la URL base y el Token desde res.config.settings """
        config = self.env['ir.config_parameter'].sudo()
        endpoint_url = config.get_param('mundo_shop_integration.endpoint_url', '')
        auth_token = config.get_param('mundo_shop_integration.authorization_token', '')

        if not endpoint_url or not auth_token:
            _logger.error("Falta la configuración de la API en Odoo Settings.")
            raise ValidationError("Falta la configuración de la API en Odoo Settings. Verifica la URL y el Token.")

        return {'endpoint_url': endpoint_url, 'auth_token': auth_token}

    def _send_request(self, method, endpoint, payload=None):
        """ Envía una solicitud HTTP (GET o POST) a la API """
        credentials = self._get_api_credentials()  # Ahora lanza ValidationError si falta configuración

        url = f"{credentials['endpoint_url']}{endpoint}"
        headers = {
            "GeneXus-Agent": "SmartDevice Application",
            "Content-Type": "application/json",
            "Authorization": credentials['auth_token']
        }

        if method == "POST":
            headers["Accept"] = "application/json"

        try:
            response = requests.request(method, url, headers=headers, json=payload)
            response.raise_for_status()
            _logger.info(f"Respuesta de la API: {response.text}")
            return response.json()

        except requests.exceptions.RequestException as e:
            _logger.error(f"Error en {method} {url}: {e}")
            raise ValidationError(f"Error en la solicitud a la API: {e}")

    def _send_get_request(self, endpoint):
        """ Envía una solicitud GET a la API """
        return self._send_request("GET", endpoint)

    def _send_post_request(self, endpoint, payload):
        """ Envía una solicitud POST a la API con un payload """
        return self._send_request("POST", endpoint, payload)
