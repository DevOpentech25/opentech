# 📌 Modelo en Odoo para la Declaración de Ventas
from odoo import models, fields, api, _
import requests


class LPSPaymentMethod(models.Model):
    _name = "lps.payment.method"
    _description = "Payment Methods for LPS"

    code = fields.Char(string="Código", required=True)
    name = fields.Char(string="Descripción", required=True)


class LPSCFECode(models.Model):
    _name = "lps.cfe.code"
    _description = "CFE Codes for LPS"

    code = fields.Char(string="Código", required=True)
    name = fields.Char(string="Descripción", required=True)



class LPSSaleDeclaration(models.Model):
    _name = "lps.sale.declaration"
    _description = "Sales Declaration for LPS"

    vat_number = fields.Char(string="Número de RUT", required=True)
    shopping_code = fields.Char(string="Código Shopping", required=True)
    contract_number = fields.Char(string="Número de Contrato", required=True)
    channel_code = fields.Selection([
        ('1', 'Local'),
        ('2', 'Delivery'),
        ('3', 'Pick-Up'),
    ], string="Código de Canal", required=True)
    sequential = fields.Integer(string="Secuencial", required=True)
    cash_register = fields.Char(string="Caja")
    customer_name = fields.Char(string="Nombre Cliente")
    phone_number = fields.Char(string="Número de Teléfono")
    cfe_code = fields.Many2one("lps.cfe.code", string="Código CFE", required=True)
    cfe_number = fields.Char(string="Número CFE")
    cfe_series = fields.Char(string="Serie CFE")
    cfe_doc_id = fields.Char(string="DocId CFE (Opcional)")
    cfe_currency = fields.Selection([
        ('UYU', 'Pesos Uruguayos'),
        ('USD', 'Dólares'),
    ], string="Moneda CFE", required=True)
    cfe_issue_date = fields.Datetime(string="Fecha Emisión CFE", required=True)
    total_mociva = fields.Float(string="Total MOCIVA")
    total_msiva = fields.Float(string="Total MSIVA")
    payment_method_1 = fields.Many2one("lps.payment.method", string="Forma de Pago 1", required=True)
    total_1 = fields.Float(string="Total 1")
    payment_method_2 = fields.Many2one("lps.payment.method", string="Forma de Pago 2")
    total_2 = fields.Float(string="Total 2")
    payment_method_3 = fields.Many2one("lps.payment.method", string="Forma de Pago 3")
    total_3 = fields.Float(string="Total 3")
    promo_number = fields.Char(string="Número de Promoción")
    transfer_date = fields.Date(string="Fecha de Transferencia")
    transfer_hour = fields.Char(string="Hora de Transferencia")
    installment_count = fields.Integer(string="Cantidad de Cuotas")
    category_code = fields.Char(string="Código de Rubro")
    cash_payment = fields.Float(string="Contado MSIVA")
    credit_payment = fields.Float(string="Crédito MSIVA")
    debit_payment = fields.Float(string="Débito MSIVA")
    include_in_promo = fields.Boolean(string="Incluir en Promoción")

    status = fields.Selection([
        ('pending', 'Pendiente'),
        ('sent', 'Enviado'),
        ('error', 'Error'),
    ], string="Estado de Envío", default="pending")

    def send_sale_declaration(self):
        """
        Envía la declaración de ventas al WebService.
        """
        for sale in self:
            url = "https://ventas.laspiedrasshopping.com.uy/soap/NodumLocales/services/forms/v1.3/wsDeclaVtas2?wsdl"
            payload = {
                "NumeroRUT": sale.vat_number,
                "CodigoShopping": sale.shopping_code,
                "NumeroContrato": sale.contract_number,
                "CodigoCanal": sale.channel_code,
                "Secuencial": sale.sequential,
                "Caja": sale.cash_register,
                "NombreCliente": sale.customer_name,
                "NroTelefono": sale.phone_number,
                "CodigoCFE": sale.cfe_code,
                "NumeroCFE": sale.cfe_number,
                "SerieCFE": sale.cfe_series,
                "DocIdCFE": sale.cfe_doc_id or "",
                "MonedaCFE": sale.cfe_currency,
                "FechaEmisionCFE": sale.cfe_issue_date.strftime('%Y-%m-%d %H:%M'),
                "TotalMOCIVA": sale.total_mociva,
                "TotalMSIVA": sale.total_msiva,
                "CodigoFormaPago": sale.payment_method_1,
                "Total1": sale.total_1,
                "CodigoFormaPago2": sale.payment_method_2 or "",
                "Total2": sale.total_2 or 0,
                "CodigoFormaPago3": sale.payment_method_3 or "",
                "Total3": sale.total_3 or 0,
                "NumeroDePromo": sale.promo_number or "",
                "FechaTransferencia": sale.transfer_date.strftime('%Y-%m-%d') if sale.transfer_date else "",
                "HoraTransferencia": sale.transfer_hour or "",
                "CantidadCuotas": sale.installment_count or 0,
                "CodRubro": sale.category_code or "",
                "ContadoMNSIVA": sale.cash_payment or 0,
                "CreditoMNSIVA": sale.credit_payment or 0,
                "DebitoMNSIVA": sale.debit_payment or 0,
                "IncluirenPromo": "SI" if sale.include_in_promo else "NO"
            }

            try:
                response = requests.post(url, json=payload, timeout=10)
                if response.status_code == 200:
                    sale.status = "sent"
                else:
                    sale.status = "error"
            except requests.exceptions.RequestException:
                sale.status = "error"

# Datos Salida:
# - 0 - Grabado correctamente
# - 1 - Pre-grabado correctamente
# - 2 - Error al grabar
# - 3 - Error al procesar archivo