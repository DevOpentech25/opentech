# common / /documento.py + empresa.py
from datetime import datetime
from xml.dom.minidom import CDATASection
from odoo import models, fields, api
from odoo.exceptions import UserError


class CfeEnvelope(models.Model):  # class Sobre
    _name = "l10n_uy_edi_cfe.envelope.cfe"
    _description = "Sobre CFE"

    rut_emisor = fields.Char(string="RUT Emisor")
    numero = fields.Char(string="Número")
    fecha = fields.Date(string="Fecha")
    adenda = fields.Text(string="Adenda")
    impresion = fields.Text(string="Impresión")
    servidor_id = fields.Many2one(
        "l10n_uy_cfe.server", string="Servidor", compute="_compute_server_id"
    )
    documento = fields.Json(string="Documento")
    server_code = fields.Char(
        related="servidor_id.server_type_id.name", string="Server Code"
    )
    uuid_sobre = fields.Char(string="UUID Sobre")
    invoice_id = fields.Many2one("account.move", string="Factura")

    def _compute_server_id(self):
        for record in self:
            record.servidor_id = self.env["l10n_uy_cfe.server"].search(
                [("company_id", "=", self.env.company.id)], limit=1
            )

    def enviarCFE(self):
        server_code = self.server_code

        if not server_code:
            raise UserError("No se ha configurado el servidor CFE")

        SobreFactura = self.env["l10n_uy_cfe.sobre_factura"]

        if self.server_code == "efactura":
            cliente = SoapClient()  # Client(self.servidor.url)
            sobre = SobreFactura().getDocument(self)
            vals = {
                "usuario": self.servidor_id.user_ws,
                "clave": self.servidor_id.key_ws,
                "rutEmisor": self.rut_emisor,
                "sobre": sobre,
                "impresion": self.impresion,
            }
            estado, respuesta = cliente.recibo_venta(vals)
            return {"estado": estado, "respuesta": respuesta}

        elif self.server_code == "factura_express":
            cliente = self.env["einvoice.express.client.soap"]._connect()  # FEClient(self.servidor_id.url) Invoice Express
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
            vals["usuario"] = self.servidor_id.user_ws
            vals["password"] = self.servidor_id.key_ws

            cdata = CDATASection()
            cdata.data = str(xml_data, "utf-8")

            vals["xmlData"] = cdata
            estado, respuesta = cliente.envioCfe(vals)

            return {"estado": estado, "respuesta": respuesta}

        elif self.server_code == "biller":
            biller = self.env["biller.document"]  # Biller(self.cfe)
            return biller.send_einvoice()

        elif self.server_code == "uruware":
            invoice = self.invoice_id
            api = self.env["cfe.uruware.service"].send_cfe_document(
                cfe_xml=self.documento,
                invoice_id=invoice.id,
            )
            raise UserError(f"Server Response Uruware {api}")

        else:
            return {}

    def obtenerPdfCFE(self, ducument_url_id):
        if self.server_code == "biller":
            biller = self.env["biller.document"]  # Biller(self.cfe)
            return biller.get_biller_pdf(ducument_url_id)
        elif self.server_code == "factura_express":
            cliente = self.env["einvoice.express.client.soap"]._connect()  # FEClient(self.servidor_id.url) Invoice Express
            return cliente.get_pdf(ducument_url_id)
        else:
            return {}

    def obtenerEstadoCFE(self, biller_id):
        if self.server_code == "biller":
            biller = self.env["biller.document"]  # Biller(self.cfe)
            return biller.get_biller_invoice(biller_id)
        else:
            return {}

    def verificarEstadoCFE(
        self, numero_interno, desde=None, tipo_comprobante=None, serie=None, numero=None
    ):
        if self.server_code == "biller":
            biller = self.env["biller.document"]  # Biller(self.cfe)
            return biller.check_biller_invoice(
                numero_interno, desde, tipo_comprobante, serie, numero
            )
        else:
            return {}
