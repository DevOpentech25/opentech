#📌 Modelo en Odoo para la Consulta por Número de Contrato
from odoo import models, fields, api
import requests

class LPSContract(models.Model):
    _name = "lps.contract"
    _description = "Contract Information for LPS"

    vat_number = fields.Char(string="Número de RUT", required=True)
    shopping_code = fields.Char(string="Código Shopping", required=True)
    contract_number = fields.Char(string="Número de Contrato", required=True)
    company_name = fields.Char(string="Nombre de la Empresa")
    contract_description = fields.Text(string="Descripción del Contrato")
    stores = fields.Text(string="Locales")
    credit_limit = fields.Float(string="Tope de Crédito")
    debit_limit = fields.Float(string="Tope de Débito")
    stage = fields.Char(string="Etapa")
    category_code = fields.Char(string="Código de Rubro")
    category_name = fields.Char(string="Nombre del Rubro")
    channel_code = fields.Char(string="Código de Canal")
    channel_name = fields.Char(string="Nombre del Canal")

    def get_contract_data(self):
        """
        Consulta la información del contrato por RUT, código de shopping y número de contrato.
        """
        for contract in self:
            url = "https://ventas.laspiedrasshopping.com.uy/soap/NodumLocales/services/sim/v1.3/wsConsxCont?wsdl"
            payload = {
                "NumeroRUT": contract.vat_number,
                "CodigoShopping": contract.shopping_code,
                "NumeroContrato": contract.contract_number
            }

            try:
                response = requests.post(url, json=payload, timeout=10)
                if response.status_code == 200:
                    data = response.json()  # Convertimos la respuesta en JSON
                    contract.company_name = data.get("NombreEmpresa")
                    contract.contract_description = data.get("DescripcionContrato")
                    contract.stores = ", ".join(data.get("Locales", []))
                    contract.credit_limit = data.get("TopeCredito", 0.0)
                    contract.debit_limit = data.get("TopeDebito", 0.0)
                    contract.stage = data.get("Etapa")
                    contract.category_code = data.get("CodigoRubro")
                    contract.category_name = data.get("NombreRubro")
                    contract.channel_code = data.get("CodigoCanal")
                    contract.channel_name = data.get("NombreCanal")
                else:
                    raise ValueError(f"Error en la respuesta del servidor: {response.status_code}")

            except requests.exceptions.RequestException as e:
                raise ValueError(f"Error en la conexión con el WebService: {str(e)}")
