from odoo import models, fields, api
import requests


class LPSConfig(models.Model):
    _name = "lps.config"
    _description = "Configuración de WebService LPS"

    user = fields.Char(string="Usuario WebService", required=True)
    password = fields.Char(string="Contraseña WebService", required=True)
    url = fields.Char(string="URL WebService", required=True)


class LpsWebSales(models.Model):
    _name = "lps.point.sale"
    _description = "Ventas enviadas a Las Piedras Shopping"

    rut_number = fields.Char(string="RUT", required=True)
    shopping_code = fields.Char(string="Código Shopping")
    contract_number = fields.Char(string="Número Contrato")
    channel_code = fields.Selection(
        [
            ("1", "Local"),
            ("2", "Delivery"),
            ("3", "Pick-Up"),
        ],
        string="Canal de Venta",
        required=True,
    )
    int_sequence = fields.Integer(string="Secuencial", required=True)
    point_box = fields.Char(string="Caja")
    emission_date = fields.Datetime(string="Fecha Emisión") 
    total_mociva = fields.Float(string="Total MOCIVA")
    total_msiva = fields.Float(string="Total MSIVA")
    send_state = fields.Selection(
        [
            ("pending", "Pendiente"),
            ("send", "Enviado"),
            ("error", "Error"),
        ],
        string="Estado de Envío",
        default="pendiente",
    )

    def send_sale_info_ws(self):
        """
        Envía la venta al WebService.
        """
        for sale in self:
            url = "https://ventas.laspiedrasshopping.com.uy/soap/NodumLocales/services/forms/v1.3/wsDeclaVtas2?wsdl"
            data = {
                "NumeroRUT": sale.rut_number,
                "CodigoShopping": sale.shopping_code,
                "NumeroContrato": sale.contract_number,
                "CodigoCanal": sale.channel_code,
                "Secuencial": sale.int_sequence,
                "Caja": sale.point_box,
                "FechaEmisionCFE": sale.emission_date.strftime("%Y-%m-%d %H:%M"),
                "TotalMOCIVA": sale.total_mociva,
                "TotalMSIVA": sale.total_msiva,
            }

            try:
                response = requests.post(url, json=data, timeout=10)
                if response.status_code == 200:
                    sale.send_state = "send"
                else:
                    sale.send_state = "error"
            except requests.exceptions.RequestException:
                sale.send_state = "error"
                continue

    @api.model
    def cron_send_pending_sales(self):
        """
        Tarea automática que envía ventas pendientes cada día.
        """
        pending_sales = self.search([("send_state", "=", "pending")])
        pending_sales.send_sale_info_ws()
