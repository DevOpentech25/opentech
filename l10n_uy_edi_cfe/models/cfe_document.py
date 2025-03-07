# common / /documento.py
from odoo import models, fields, api


class CfeDocument(models.Model):  # class Documento
    _name = "cfe.document"
    _description = "Documento Base"

    servidor = fields.Char(string="Servidor")
    emisor_id = fields.Many2one("res.partner", string="Emisor")
    adquirente_id = fields.Many2one("res.partner", string="Adquirente")

    moneda = fields.Char(string="Moneda")
    tasa_cambio = fields.Float(string="Tasa de Cambio")

    montos_brutos = fields.Float(string="Montos Brutos")

    forma_pago = fields.Selection(
        [("contado", "Contado"), ("credito", "Crédito")], string="Forma de Pago"
    )

    tipo_cfe = fields.Char(string="Tipo CFE")
    serie = fields.Char(string="Serie")
    numero = fields.Char(string="Número")

    clausula_venta = fields.Char(string="Cláusula Venta")
    via_transporte = fields.Char(string="Vía Transporte")
    modalidad_venta = fields.Char(string="Modalidad Venta")

    fec_emision = fields.Date(string="Fecha Emisión")
    fec_vencimiento = fields.Date(string="Fecha Vencimiento")

    adenda = fields.Text(string="Adenda")

    items_ids = fields.One2many("document.items", "documento_id", string="Ítems")
    retenciones_percepciones_ids = fields.One2many(
        "document.retenciones.percepciones",
        "documento_id",
        string="Retenciones/Percepciones",
    )
    descuentos_ids = fields.One2many(
        "document.discount", "documento_id", string="Descuentos"
    )

    mnt_no_grv = fields.Float(string="Monto No Gravado", digits=(12, 2))
    mnt_neto_iva_tasa_min = fields.Float(
        string="Monto Neto IVA Tasa Mínima", digits=(12, 2)
    )
    mnt_neto_iva_tasa_basica = fields.Float(
        string="Monto Neto IVA Tasa Básica", digits=(12, 2)
    )

    iva_tasa_min = fields.Float(string="IVA Tasa Mínima", digits=(12, 2))
    iva_tasa_basica = fields.Float(string="IVA Tasa Básica", digits=(12, 2))

    mnt_iva_tasa_min = fields.Float(string="Monto IVA Tasa Mínima", digits=(12, 2))
    mnt_iva_tasa_basica = fields.Float(string="Monto IVA Tasa Básica", digits=(12, 2))

    mnt_total = fields.Float(string="Monto Total", digits=(12, 2))
    cant_lin_det = fields.Integer(string="Cantidad Líneas Detalle")

    monto_nf = fields.Float(string="Monto NF", digits=(12, 2))
    mnt_pagar = fields.Float(string="Monto a Pagar", digits=(12, 2))

    referencia_global = fields.Char(string="Referencia Global")
    referencias_ids = fields.One2many(
        "document.referencia", "documento_id", string="Referencias"
    )

    tipo_traslado = fields.Char(string="Tipo Traslado")
    numero_interno = fields.Char(string="Número Interno")
    numero_orden = fields.Char(string="Número Orden")


class DocumentReferencia(models.Model):
    _name = "document.referencia"
    _description = "Referencias del Documento"

    documento_id = fields.Many2one("cfe.document", string="Documento")
    motivo = fields.Char(string="Motivo")
    tipo_doc_ref = fields.Char(string="Tipo Documento Referenciado")
    serie = fields.Char(string="Serie")
    numero = fields.Char(string="Número")
    fecha_cfe_ref = fields.Date(string="Fecha CFE Referenciado")


class DocumentItems(models.Model):
    _name = "document.items"
    _description = "Ítems del Documento"

    documento_id = fields.Many2one("cfe.document", string="Documento")

    indicador_facturacion = fields.Char(string="Indicador Facturación")
    descripcion = fields.Char(string="Descripción")
    cantidad = fields.Float(string="Cantidad", digits=(12, 3))
    unidad_medida = fields.Char(string="Unidad de Medida", default="N/A")
    precio_unitario = fields.Float(string="Precio Unitario", digits=(12, 10))
    monto_item = fields.Float(string="Monto Item", digits=(12, 8))

    codigo = fields.Char(string="Código")
    cod_producto = fields.Char(string="Código Producto")

    descuento = fields.Float(string="Descuento %", digits=(12, 2))
    descuento_monto = fields.Float(string="Descuento Monto", digits=(12, 2))
    recargo_monto = fields.Float(string="Recargo Monto", digits=(12, 2))
    recargo = fields.Float(string="Recargo %", digits=(12, 2))


class DocumentRetencionesPercepciones(models.Model):
    _name = "document.retenciones.percepciones"
    _description = "Retenciones y Percepciones del Documento"

    documento_id = fields.Many2one("cfe.document", string="Documento")
    codigo = fields.Char(string="Código")
    tasa = fields.Float(string="Tasa", digits=(12, 2))
    base = fields.Float(string="Base", digits=(12, 2))
    monto = fields.Float(string="Monto", digits=(12, 2))
    indicador_facturacion = fields.Char(string="Indicador Facturación")


class DocumentDiscount(models.Model):
    _name = "document.discount"
    _description = "Descuento del Documento"

    documento_id = fields.Many2one("cfe.document", string="Documento")
    descripcion = fields.Char(string="Descripción")
    monto = fields.Float(string="Monto", digits=(12, 2))
    indicador_facturacion = fields.Char(string="Indicador Facturación")


class DocumentType(models.Model):
    _name = "document.type"
    _description = "Tipos de Documento"

    name = fields.Char(string="Nombre")
    code = fields.Char(string="Código")
    description = fields.Char(string="Descripción")
    active = fields.Boolean(string="Activo", default=True)
    # E-ticket, E-factura, E-remisión, E-liquidación,
    # E-ticket-contingencia, E-factura-contingencia,
    # E-remisión-contingencia, E-liquidación-contingencia
