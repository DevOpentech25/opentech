from odoo import models, fields, api
import logging

log = logging.getLogger(__name__)
# l10n_uy_cfe.biller.client
# biller.document.item


class BillerDocument(models.Model):
    _name = "biller.document"
    _description = "Electronic Invoice Document"

    tipo_comprobante = fields.Selection(
        [
            ("181", "Traslado"),
            ("182", "Otro"),
            ("151", "Tipo 151"),
            ("152", "Tipo 152"),
            ("153", "Tipo 153"),
        ],
        string="Tipo de Comprobante",
    )

    tipo_traslado = fields.Char(string="Tipo de Traslado")
    fecha_vencimiento = fields.Date(string="Fecha de Vencimiento")
    forma_pago = fields.Char(string="Forma de Pago")
    fecha_emision = fields.Date(string="Fecha de Emisión")
    moneda = fields.Char(string="Moneda")
    tasa_cambio = fields.Float(string="Tasa de Cambio")
    montos_brutos = fields.Boolean(string="Montos Brutos")
    sucursal = fields.Char(string="Sucursal", default="1")
    numero_interno = fields.Char(string="Número Interno")
    numero_orden = fields.Char(string="Número de Orden")

    cliente_id = fields.Many2one("res.partner", string="Cliente")
    direccion = fields.Char(related="cliente_id.street", string="Dirección")
    ciudad = fields.Char(related="cliente_id.city", string="Ciudad")
    departamento = fields.Char(
        related="cliente_id.state_id.name", string="Departamento"
    )
    pais = fields.Char(related="cliente_id.country_id.code", string="País")

    items = fields.One2many("biller.document.item", "document_id", string="Items")
    server_id = fields.Many2one(
        "l10n_uy_cfe.biller.client", string="Servidor"
    )  # obtiene la información del servidor
    servidor_url = fields.Char(
        string="URL del Servidor", related="server_id.url_api_cfe"
    )
    servidor_token = fields.Char(
        string="Token del Servidor", related="server_id.token_api_cfe"
    )

    def get_document(self):
        """Genera la estructura del documento para la facturación electrónica."""
        self.ensure_one()
        return {
            "tipo_comprobante": self.tipo_comprobante,
            "fecha_emision": self.fecha_emision,
            "moneda": self.moneda,
            "tasa_cambio": self.tasa_cambio if self.moneda != "UYU" else None,
            "cliente": {
                "tipo_documento": self.cliente_id.vat,
                "documento": self.cliente_id.vat,
                "razon_social": self.cliente_id.name,
                "direccion": self.direccion,
                "ciudad": self.ciudad,
                "departamento": self.departamento,
                "pais": self.pais,
            },
            "items": [
                {
                    "cantidad": item.cantidad,
                    "concepto": item.descripcion[:80],
                    "precio": item.precio_unitario,
                }
                for item in self.items
            ],
        }

    def send_einvoice(self):
        """Envía una factura electrónica utilizando la clase Cliente."""
        self.ensure_one()
        client = self.env["l10n_uy_cfe.client"]
        return client.send_invoice(self.servidor_token, self.get_document())

    def get_biller_pdf(self, biller_id):
        """Obtiene el PDF de la factura electrónica utilizando la clase Cliente."""
        client = self.env["l10n_uy_cfe.client"]
        return client.get_pdf(self.servidor_token, biller_id)

    def get_biller_invoice(self, biller_id):
        """Obtiene la información de una factura electrónica utilizando la clase Cliente."""
        client = self.env["l10n_uy_cfe.client"]
        return client.get_invoice(self.servidor_token, biller_id)

    def check_biller_invoice(
        self, numero_interno, desde=None, tipo_comprobante=None, serie=None, numero=None
    ):
        """Verifica una factura en el sistema biller utilizando la clase Cliente."""
        client = self.env["l10n_uy_cfe.client"]
        return client.check_invoice(
            self.servidor_token, numero_interno, desde, tipo_comprobante, serie, numero
        )


class BillerDocumentItem(models.Model):
    _name = "biller.document.item"
    _description = "Biller Document Items"

    document_id = fields.Many2one("biller.document", string="Documento")
    cantidad = fields.Float(string="Cantidad")
    codigo = fields.Char(string="Código")
    descripcion = fields.Char(string="Descripción")
    precio_unitario = fields.Float(string="Precio Unitario")
