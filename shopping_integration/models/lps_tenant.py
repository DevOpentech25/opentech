# 📌 Modelo en Odoo para la Consulta por RUT o Contrato
from odoo import models, fields, api
import requests

class LPSTenant(models.Model):
    _name = "lps.tenant"
    _description = "Tenant Information for LPS"

    vat_number = fields.Char(string="Número de RUT", required=True)
    shopping_code = fields.Char(string="Código Shopping")
    contract_number = fields.Char(string="Número de Contrato")
    contract_description = fields.Text(string="Descripción del Contrato")
    stores = fields.Text(string="Locales")
    publication_stage = fields.Char(string="Etapa de Publicaciones")

    def get_tenant_data(self):
        """
        Consulta la información del locatario por su número de RUT.
        """
        for tenant in self:
            url = "https://ventas.laspiedrasshopping.com.uy/soap/NodumLocales/services/sim/v1.3/wsConsxRUT?wsdl"
            payload = {
                "NumeroRUT": tenant.vat_number
            }

            try:
                response = requests.post(url, json=payload, timeout=10)
                if response.status_code == 200:
                    data = response.json()  # Convertimos la respuesta en JSON
                    tenant.shopping_code = data.get("CodigoShopping")
                    tenant.contract_number = data.get("NumeroContrato")
                    tenant.contract_description = data.get("DescripcionContrato")
                    tenant.stores = ", ".join(data.get("Locales", []))
                    tenant.publication_stage = data.get("EtapaPublicaciones")
                else:
                    raise ValueError(f"Error en la respuesta del servidor: {response.status_code}")

            except requests.exceptions.RequestException as e:
                raise ValueError(f"Error en la conexión con el WebService: {str(e)}")

