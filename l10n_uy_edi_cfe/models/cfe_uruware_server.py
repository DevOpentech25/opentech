import requests
import json
from odoo import models, fields

CREDENCIALES_BASE64 = "219507810019:ItSTSB5id4KYHPFYp82ruw=="


class UCFEService(models.Model):
    _name = "cfe.uruware.service"
    _description = "Integración con UCFE"

    def send_cfe(self, cfe_data):
        url = "https://test.ucfe.com.uy/inbox115_2/CfeService.svc/rest/Invoke"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Basic {CREDENCIALES_BASE64}",
        }
        payload = {
            "CodComercio": "XXXX",
            "CodTerminal": "YYYY",
            "Req": cfe_data,
            "RequestDate": fields.Datetime.now(),
            "Tout": 30000,
        }

        response = requests.post(url, data=json.dumps(payload), headers=headers)

        if response.status_code == 200:
            return response.json()
        else:
            return {"error": response.text}

    def get_cfe_received(self, numero_cfe, serie):
        url = f"https://[SERVIDOR_UCFE]/CfeService.svc/rest/Invoke"
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Basic [CREDENCIALES_BASE64]",
        }
        payload = {
            "CodComercio": "XXXX",
            "CodTerminal": "YYYY",
            "Req": {"TipoMensaje": "650", "NumeroCfe": numero_cfe, "Serie": serie},
            "RequestDate": fields.Datetime.now(),
            "Tout": 30000,
        }

        response = requests.post(url, data=json.dumps(payload), headers=headers)
        return (
            response.json() if response.status_code == 200 else {"error": response.text}
        )
