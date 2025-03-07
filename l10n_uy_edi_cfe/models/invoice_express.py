from lxml import etree
from datetime import datetime
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class EInvoiceExpress(models.Model):
    _name = "einvoice.express"
    _description = "Factura Express"

    name = fields.Char(string="Nombre")
    tipo_cfe = fields.Selection(
        [("121", "e-Ticket"), ("122", "e-Factura"), ("123", "e-Remito")],
        string="Tipo CFE",
    )
    fecha_emision = fields.Date(string="Fecha de Emisión", default=fields.Date.today)
    fecha_vencimiento = fields.Date(string="Fecha de Vencimiento")
    monto_bruto = fields.Float(string="Monto Bruto")
    adquirente_id = fields.Many2one("res.partner", string="Adquirente")
    # item_ids = fields.One2many("einvoice.express.item", "invoice_id", string="Items")
    moneda = fields.Char(string="Moneda", default="UYU")
    tasa_cambio = fields.Float(string="Tasa de Cambio", default=1.0)
    mnt_total = fields.Float(string="Monto Total")
    cant_lin_det = fields.Integer(string="Cantidad Líneas Detalle")
    mnt_pagar = fields.Float(string="Monto a Pagar")
    # referencia_ids = fields.One2many("einvoice.express.referencia", "invoice_id", string="Referencias")
    # descuento_ids = fields.One2many("einvoice.express.descuento", "invoice_id", string="Descuentos")
    adenda = fields.Text(string="Adenda")

    def _format_date(self, date):
        """Convierte una fecha de formato Odoo a formato YYYYMMDD"""
        return date.strftime("%Y%m%d") if date else ""

    def _create_xml_element(self, parent, tag, text=None):
        """Crea un elemento XML con texto opcional"""
        element = etree.SubElement(parent, tag)
        if text:
            element.text = str(text)
        return element

    def _generate_datos_generales(self, root):
        general = self._create_xml_element(root, "DatosGenerales")
        self._create_xml_element(general, "MntBruto", self.monto_bruto)
        if self.fecha_vencimiento:
            self._create_xml_element(
                general, "FchVenc", self._format_date(self.fecha_vencimiento)
            )

    def _generate_receptor(self, root):
        if not self.adquirente_id:
            raise ValidationError("El adquirente es obligatorio.")

        receptor = self._create_xml_element(root, "Receptor")
        self._create_xml_element(
            receptor, "TipoDocRecep", self.adquirente_id.tipo_documento or "3"
        )
        self._create_xml_element(
            receptor, "CodPaisRecep", self.adquirente_id.cod_pais or "UY"
        )
        self._create_xml_element(receptor, "DocRecep", self.adquirente_id.vat or "0")
        self._create_xml_element(receptor, "RznSocRecep", self.adquirente_id.name or "")
        self._create_xml_element(receptor, "DirRecep", self.adquirente_id.street or "")
        self._create_xml_element(receptor, "CiudadRecep", self.adquirente_id.city or "")
        self._create_xml_element(
            receptor, "DeptoRecep", self.adquirente_id.state_id.name or ""
        )
        if self.tipo_cfe in ["121", "122", "123"]:
            self._create_xml_element(
                receptor, "PaisRecep", self.adquirente_id.country_id.name
            )

    def _generate_items(self, root):
        if not self.item_ids:
            raise ValidationError("Debe haber al menos un item en la factura.")

        detalle = self._create_xml_element(root, "Detalle")
        for index, line in enumerate(self.item_ids, start=1):
            item = self._create_xml_element(detalle, "Item")
            self._create_xml_element(item, "NroLinDet", index)
            self._create_xml_element(item, "IndFact", line.indicador_facturacion)
            self._create_xml_element(item, "NomItem", line.descripcion)
            self._create_xml_element(item, "Cantidad", round(line.cantidad, 3))
            self._create_xml_element(item, "UniMed", line.unidad_medida or "N/A")
            self._create_xml_element(
                item, "PrecioUnitario", round(line.precio_unitario, 2)
            )
            if line.descuento:
                self._create_xml_element(item, "DescuentoPct", round(line.descuento, 3))
            if line.descuento_monto:
                self._create_xml_element(
                    item, "DescuentoMonto", round(line.descuento_monto, 2)
                )
            self._create_xml_element(item, "MontoItem", line.monto_item)

    def _generate_totales(self, root):
        totales = self._create_xml_element(root, "Totales")
        self._create_xml_element(totales, "TpoMoneda", self.moneda)
        self._create_xml_element(totales, "TpoCambio", self.tasa_cambio)
        self._create_xml_element(totales, "MntTotal", self.mnt_total)
        self._create_xml_element(totales, "CantLinDet", self.cant_lin_det)
        self._create_xml_element(totales, "MntPagar", self.mnt_pagar)

    def _generate_referencias(self, root):
        if self.referencia_ids:
            referencia_group = self._create_xml_element(root, "Referencia")
            for ref in self.referencia_ids:
                ref_node = self._create_xml_element(referencia_group, "Referencia")
                self._create_xml_element(ref_node, "TpoDocRef", ref.tipo_doc_ref)
                self._create_xml_element(ref_node, "Serie", ref.serie)
                self._create_xml_element(ref_node, "NroCFERef", ref.numero)
                self._create_xml_element(
                    ref_node, "FechaCFEref", self._format_date(ref.fecha_cfe_ref)
                )

    def _generate_descuentos(self, root):
        if self.descuento_ids:
            descuento_group = self._create_xml_element(root, "DscRcgGlobal")
            for index, descuento in enumerate(self.descuento_ids, start=1):
                desc_node = self._create_xml_element(descuento_group, "DRG_Item")
                self._create_xml_element(desc_node, "NroLinDR", index)
                self._create_xml_element(desc_node, "TpoMovDR", "D")
                self._create_xml_element(
                    desc_node, "GlosaDR", descuento.descripcion[:50]
                )
                self._create_xml_element(desc_node, "ValorDR", descuento.monto)
                self._create_xml_element(
                    desc_node, "IndFactDR", descuento.indicador_facturacion
                )

    def generate_xml(self):
        root = etree.Element("CFE")
        self._generate_datos_generales(root)
        self._generate_receptor(root)
        self._generate_items(root)
        self._generate_totales(root)
        self._generate_descuentos(root)
        self._create_xml_element(root, "Adenda", self.adenda or "")
        if self.tipo_cfe in ["102", "103", "112", "113", "122", "123"]:
            self._generate_referencias(root)
        return etree.tostring(root, pretty_print=True, encoding="utf-8")
