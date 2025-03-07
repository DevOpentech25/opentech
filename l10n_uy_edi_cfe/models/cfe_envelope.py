# common / /documento.py + empresa.py
from datetime import datetime
from xml.dom.minidom import CDATASection
from odoo import models, fields, api


class CfeEnvelope(models.Model):  # class Sobre
    _name = "l10n_uy_edi_cfe.envelope.cfe"
    _description = "Sobre CFE"

    rut_emisor = fields.Char(string="RUT Emisor")
    numero = fields.Char(string="Número")
    fecha = fields.Date(string="Fecha")
    documento_id = fields.Many2one(
        "empresa.documento", string="Documento"
    )  # self.cfe = Documento(vals.get('documento', {}))
    adenda = fields.Text(string="Adenda")
    impresion = fields.Text(string="Impresión")
    servidor_id = fields.Many2one("l10n_uy_cfe.server", string="Servidor")

    def enviarCFE(self):
        SoapClient = self.env["l10n_uy_cfe.soap.client"]
        SobreFactura = self.env["l10n_uy_cfe.sobre_factura"]
        if self.servidor.codigo == "efactura":
            cliente = SoapClient()  # Client(self.servidor.url)
            sobre = SobreFactura().getDocument(self)
            vals = {
                "usuario": self.servidor.usuario,
                "clave": self.servidor.clave,
                "rutEmisor": self.rutEmisor,
                "sobre": sobre,
                "impresion": self.impresion,
            }
            estado, respuesta = cliente.recibo_venta(vals)
            return {"estado": estado, "respuesta": respuesta}
        elif self.servidor.codigo == "factura_express":
            cliente = self.env[
                "einvoice.express.client.soap"
            ]._connect()  # FEClient(self.servidor.url) Invoice Express
            FacturaExpress = self.env["einvoice.express"]
            xml_data = FacturaExpress().generate_xml(
                self.cfe
            )  # invoice_express.py FacturaExpress().xmlData(self.cfe)
            vals = {}
            vals["idEmisor"] = self.cfe.emisor.id
            documento = self.cfe
            for sucursal in self.cfe.emisor.sucursal:
                vals["codSucursal"] = str(sucursal.codigo)
                break
            vals["tipoComprobante"] = documento.tipoCFE
            vals["serie"] = documento.serie
            vals["numero"] = documento.numero
            vals["fechaEmision"] = datetime.strptime(
                documento.fecEmision, "%Y-%m-%d"
            ).strftime("%Y%m%d")
            if documento.fecVencimiento:
                vals["FchVenc"] = datetime.strptime(
                    documento.fecVencimiento, "%Y-%m-%d"
                ).strftime("%Y%m%d")
            vals["formaPago"] = documento.formaPago
            # FchVenc Falta
            vals["usuario"] = self.servidor.usuario
            vals["password"] = self.servidor.clave
            cdata = CDATASection()
            cdata.data = str(xml_data, "utf-8")
            vals["xmlData"] = cdata
            estado, respuesta = cliente.envioCfe(vals)
            return {"estado": estado, "respuesta": respuesta}
        elif self.servidor.codigo == "biller":
            biller = self.env["biller.document"]  # Biller(self.cfe)
            return biller.send_einvoice()
        else:
            return {}

    def obtenerPdfCFE(self, ducument_url_id):
        if self.servidor.codigo == "biller":
            biller = self.env["biller.document"]  # Biller(self.cfe)
            return biller.get_biller_pdf(ducument_url_id)
        elif self.servidor.codigo == "factura_express":
            cliente = cliente = self.env[
                "einvoice.express.client.soap"
            ]._connect()  # FEClient(self.servidor.url) Invoice Express
            return cliente.get_pdf(ducument_url_id)
        else:
            return {}

    def obtenerEstadoCFE(self, biller_id):
        if self.servidor.codigo == "biller":
            biller = self.env["biller.document"]  # Biller(self.cfe)
            return biller.get_biller_invoice(biller_id)
        else:
            return {}

    def verificarEstadoCFE(
        self, numero_interno, desde=None, tipo_comprobante=None, serie=None, numero=None
    ):
        if self.servidor.codigo == "biller":
            biller = self.env["biller.document"]  # Biller(self.cfe)
            return biller.check_biller_invoice(
                numero_interno, desde, tipo_comprobante, serie, numero
            )
        else:
            return {}
