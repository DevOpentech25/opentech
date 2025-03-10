# -*- encoding: utf-8 -*-
from odoo import api, fields, models, _
from lxml import etree


class UySendCFE(models.AbstractModel):
    _name = "uy.edi.send.cfe"
    _description = "No description"

    def get_server(self, company_id):
        vals = {}
        vals["url"] = company_id.uy_server_url
        vals["usuario"] = company_id.uy_username
        vals["clave"] = company_id.uy_password
        vals["codigo"] = company_id.uy_server
        if company_id.uy_server in ["biller"]:
            vals["token"] = company_id.uy_password
        return vals

    def get_sobre(self, batch_id):
        vals = {}
        # if not batch_id.uy_number:
        if batch_id._name == "account.edi.document":
            batch_id.get_uy_number()
            if not batch_id.uy_send_date:
                to = self.with_context(tz="America/Montevideo")
                batch_id.uy_send_date = fields.Datetime.to_string(
                    fields.Datetime.context_timestamp(to, fields.Datetime.now())
                )
            vals["rutEmisor"] = batch_id.move_id.company_id.vat
            vals["numero"] = str(batch_id.uy_send_number)
            vals["fecha"] = batch_id.uy_send_date.strftime("%Y-%m-%dT%H:%M:%S")

            vals["adenda"] = (
                batch_id.move_id.narration
                and str(batch_id.move_id.narration)
                .replace("<br>", "\n")
                .replace("<br />", "\n")
                .replace("<p>", "")
                .replace("</p>", "\n")
                or ""
            )
            if (
                batch_id.move_id.uy_document_code == "182"
                and batch_id.move_id.reversed_entry_id
            ):
                vals["adenda"] = (
                    batch_id.move_id.ref or batch_id.move_id.reversed_entry_id.name
                )
            vals["impresion"] = (
                batch_id.move_id.journal_id.uy_efactura_print_mode
                or batch_id.move_id.company_id.uy_efactura_print_mode
                or "1"
            )
        elif batch_id._name == "uy.stock.edi.document":
            batch_id.get_uy_number()
            if not batch_id.uy_send_date:
                to = self.with_context(tz="America/Montevideo")
                batch_id.uy_send_date = fields.Datetime.to_string(
                    fields.Datetime.context_timestamp(to, fields.Datetime.now())
                )
            vals["rutEmisor"] = batch_id.picking_id.company_id.vat
            vals["numero"] = str(batch_id.uy_send_number)
            vals["fecha"] = batch_id.uy_send_date.strftime("%Y-%m-%dT%H:%M:%S")

            vals["adenda"] = (
                batch_id.picking_id.note
                and str(batch_id.move_id.note)
                .replace("<br>", "\n")
                .replace("<br />", "\n")
                .replace("<p>", "")
                .replace("</p>", "\n")
                or ""
            )
            vals["impresion"] = (
                batch_id.picking_id.company_id.uy_efactura_print_mode or "1"
            )
        return vals

    def _get_voucher(self, invoice_id):
        vals = {}
        vals["tipoCFE"] = invoice_id.uy_document_code
        if invoice_id.move_type == "entry":
            vals["fecEmision"] = invoice_id.date.strftime("%Y-%m-%d")
        else:
            vals["fecEmision"] = invoice_id.invoice_date.strftime("%Y-%m-%d")
        if (
            invoice_id.invoice_date
            and invoice_id.invoice_date_due
            and invoice_id.invoice_date < invoice_id.invoice_date_due
        ):
            vals["fecVencimiento"] = invoice_id.invoice_date_due.strftime("%Y-%m-%d")
            vals["formaPago"] = "2"
        else:
            vals["formaPago"] = "1"
        currency_name = (
            invoice_id.currency_id.uy_currency_code or invoice_id.currency_id.name
        )
        vals["moneda"] = currency_name

        vals["clauVenta"] = invoice_id.uy_clause
        vals["viaTransp"] = invoice_id.uy_transport
        vals["modVenta"] = invoice_id.uy_sales_mode
        vals["numero_interno"] = invoice_id.uy_uuid
        if invoice_id.uy_document_code not in ["182"]:
            vals["numero_orden"] = invoice_id.ref
        return vals

    def _get_branch(self, partner_id, code=""):
        # uy_branch_id = self.env.context.get('uy_branch_id')
        # uy_branch_code = self.env.context.get('uy_branch_code')
        # if uy_branch_id and uy_branch_code:
        #     partner_id = self.env['res.partner'].browse(uy_branch_id)
        #     code = uy_branch_code
        vals = {}
        vals["codigo"] = code
        vals["direccion"] = partner_id.street
        vals["ciudad"] = partner_id.city_id.name
        vals["departamento"] = partner_id.city_id.name
        vals["codPais"] = partner_id.country_id.code or "UY"
        return [vals]

    def _get_company(self, company_id):
        vals = {}
        vals["numDocumento"] = company_id.vat
        vals["nombre"] = company_id.name
        vals["id"] = company_id.uy_company_id
        partner_id = company_id.partner_id
        if company_id.uy_branch_code:
            vals["sucursal"] = self._get_branch(partner_id, company_id.uy_branch_code)
        else:
            vals["direccion"] = partner_id.street
            vals["ciudad"] = partner_id.city_id.name
            vals["departamento"] = partner_id.state_id.name
            vals["codPais"] = partner_id.country_id.code
        return vals

    def _get_partner(self, partner_id):
        partner_id = partner_id.parent_id or partner_id
        vals = {}
        vals["tipoDocumento"] = partner_id.uy_doc_type
        vals["numDocumento"] = partner_id.vat
        vals["direccion"] = partner_id.street
        vals["ciudad"] = partner_id.city_id.name
        vals["departamento"] = partner_id.state_id.name
        vals["codPais"] = partner_id.country_id.code or "UY"
        vals["nomPais"] = partner_id.country_id.name
        vals["nombre"] = partner_id.name
        vals["nombreFantasia"] = partner_id.uy_tradename or partner_id.name
        return vals

    def _get_total(self, invoice_id):
        vals = {}
        vals["tasaCambio"] = invoice_id.uy_currency_rate
        vals["mntNoGrv"] = invoice_id.uy_amount_unafected
        vals["mntNetoIVATasaMin"] = invoice_id.uy_tax_min_base
        vals["mntNetoIVATasaBasica"] = invoice_id.uy_tax_basic_base
        vals["ivaTasaMin"] = invoice_id.uy_tax_min_rate
        vals["ivaTasaBasica"] = invoice_id.uy_tax_basic_rate
        vals["mntIVATasaMin"] = invoice_id.uy_tax_min
        vals["mntIVATasaBasica"] = invoice_id.uy_tax_basic
        vals["mntTotal"] = invoice_id.amount_total
        vals["montoNF"] = (
            invoice_id.uy_amount_untaxed
        )  # Revisar este campo en exportacion
        vals["mntPagar"] = invoice_id.amount_total
        return vals

    def _get_lines(self, invoice_line_ids):
        lines = []
        for line in invoice_line_ids:
            vals = {}
            vals["indicadorFacturacion"] = line.uy_invoice_indicator
            vals["descripcion"] = line.name[:80]
            vals["cantidad"] = line.quantity
            vals["unidadMedida"] = (
                line.product_uom_id and line.product_uom_id.uy_unit_code or "N/A"
            )
            vals["precioUnitario"] = (
                line.price_unit
            )  # line._get_price_total_and_subtotal(quantity=1)['price_total']
            vals["descuento"] = line.discount
            vals["codigo"] = line.product_id.default_code
            if line.discount > 0.0:
                vals["descuentoMonto"] = line.uy_amount_discount
            if line.move_id.uy_gross_amount == "1":
                vals["montoItem"] = line.price_total
            else:
                vals["montoItem"] = line.price_subtotal
            # vals['montoItem'] =  line._get_price_total_and_subtotal()['price_total']
            lines.append(vals)
        return lines

    def _get_retention_perception_lines(self, uy_retention_perception_ids):
        lines = []
        for line_id in uy_retention_perception_ids:
            vals = {
                "codigo": line_id.code_id.code,
                "tasa": line_id.rate,
                "base": line_id.base,
                "monto": line_id.amount,
            }
            if line_id.payment_id.move_id.reversed_entry_id:
                vals["indicadorFacturacion"] = "9"
            lines.append(vals)
        return lines

    def _get_descuentos(self, invoice_line_ids):
        lines = []
        for line in invoice_line_ids:
            vals = {}
            vals["indicadorFacturacion"] = line.uy_invoice_indicator
            vals["descripcion"] = line.name[:80]
            if line.move_id.uy_gross_amount == "1":
                vals["monto"] = abs(line.price_total)
            else:
                vals["monto"] = abs(line.price_subtotal)
            lines.append(vals)
        return lines

    def _get_ref(self, invoice_id):
        vals = {}
        vals["referenciaGlobal"] = (
            (invoice_id.reversed_entry_id or invoice_id.debit_origin_id) and 0 or 1
        )
        vals["referencia"] = invoice_id.ref
        if invoice_id.uy_document_code in ["102", "112", "122", "152", "182"]:
            if invoice_id.uy_document_code == "182":
                vals["descripcion"] = (
                    invoice_id.ref or invoice_id.invoice_line_ids[0].name[:80] or ""
                )
            else:
                vals["descripcion"] = (
                    invoice_id.ref or invoice_id.invoice_line_ids[0].name[:80] or ""
                )
            vals["tipoDocRef"] = invoice_id.reversed_entry_id.uy_document_code or ""
            if invoice_id.reversed_entry_id.uy_cfe_serie:
                vals["serie"] = invoice_id.reversed_entry_id.uy_cfe_serie or ""
            else:
                vals["serie"] = invoice_id.name.split("-")[0]
            if invoice_id.reversed_entry_id.uy_cfe_number:
                vals["numero"] = invoice_id.reversed_entry_id.uy_cfe_number or ""
            else:
                vals["numero"] = invoice_id.name.split("-")[-1]
            vals["fechaCFEref"] = (
                invoice_id.reversed_entry_id.invoice_date
                or invoice_id.reversed_entry_id.date
            ).strftime("%Y-%m-%d")
        else:
            vals["descripcion"] = (
                invoice_id.ref or invoice_id.invoice_line_ids[0].name[:80] or ""
            )
            vals["tipoDocRef"] = invoice_id.debit_origin_id.uy_document_code or ""
            vals["serie"] = invoice_id.debit_origin_id.uy_cfe_serie or ""
            vals["numero"] = invoice_id.debit_origin_id.uy_cfe_number or ""
            vals["fechaCFEref"] = invoice_id.debit_origin_id.invoice_date.strftime(
                "%Y-%m-%d"
            )
        return [vals]

    def send_einvoice(self, batch_id):
        vals = {}
        vals.update(self.get_sobre(batch_id))
        vals["servidor"] = self.get_server(batch_id.move_id.company_id)
        documento = {}

        documento.update(self._get_voucher(batch_id.move_id))
        documento["emisor"] = self._get_company(batch_id.move_id.company_id)
        if batch_id.move_id.company_id.uy_server == "factura_express":
            documento["serie"] = batch_id.move_id.name.replace("ANNUL/", "").split("-")[
                0
            ]
            documento["numero"] = batch_id.move_id.name.replace("ANNUL/", "").split(
                "-"
            )[-1]
        documento["adquirente"] = self._get_partner(batch_id.move_id.partner_id)
        documento.update(self._get_total(batch_id.move_id))

        if batch_id.move_id.origin_payment_id:
            documento["retencionesPercepciones"] = self._get_retention_perception_lines(
                batch_id.move_id.origin_payment_id.uy_retention_perception_ids
            )
        else:
            documento["items"] = self._get_lines(
                batch_id.move_id.invoice_line_ids.filtered(
                    lambda s: s.price_subtotal > 0.0
                )
            )
        if batch_id.move_id.uy_document_code in [
            "102",
            "103",
            "112",
            "113",
            "122",
            "123",
            "152",
            "153",
        ]:
            documento["descuentos"] = self._get_descuentos(
                batch_id.move_id.invoice_line_ids.filtered(
                    lambda s: s.price_subtotal < 0.0
                )
            )
        documento["montosBrutos"] = batch_id.move_id.uy_gross_amount
        documento["adenda"] = (
            batch_id.move_id.narration
            and str(batch_id.move_id.narration)
            .replace("<br>", "\n")
            .replace("<br />", "\n")
            .replace("<p>", "")
            .replace("</p>", "\n")
            or ""
        )
        if (
            batch_id.move_id.uy_document_code == "182"
            and batch_id.move_id.reversed_entry_id
        ):
            vals["adenda"] = (
                batch_id.move_id.ref or batch_id.move_id.reversed_entry_id.name
            )
        vals["documento"] = documento
        if batch_id.move_id.uy_document_code in [
            "102",
            "103",
            "112",
            "113",
            "122",
            "123",
            "152",
            "153",
            "182",
        ]:
            if (
                batch_id.move_id.uy_document_code == "182"
                and batch_id.move_id.reversed_entry_id
            ):
                documento["referencias"] = self._get_ref(batch_id.move_id)
            elif batch_id.move_id.uy_document_code != "182":
                documento["referencias"] = self._get_ref(batch_id.move_id)
        # cambiar los valores por los de la factura
        if batch_id.move_id.company_id.uy_server.server_type_id.name.lower() == "uruware":
            if "rutEmisor" in vals:
                vals["rut_emisor"] = vals.pop("rutEmisor")
            if "servidor" in vals:
                vals.pop("servidor", None)
            vals["documento"] = self.get_uruware_cfe_xml(batch_id.move_id.id)
            vals["uuid_sobre"] = batch_id.move_id.uy_uuid # UUID de la factura
            vals["invoice_id"] = batch_id.move_id.id

        # model cfe_envelope.py -> l10n_uy_edi_cfe.envelope.cfe
        Sobre = self.env["l10n_uy_edi_cfe.envelope.cfe"].create(vals)
        res = Sobre.enviarCFE() # llama a la funcion de enviarCFE enviando la factura
        return res

    def get_uruware_cfe_xml(self, account_id):
        # Buscar la factura en Odoo
        invoice = self.env['account.move'].browse(account_id)
        company = self.env.company

        if not invoice:
            raise UserError("No se encontró documento para ese ID")

        # Datos generales de la factura
        tipo_cfe = invoice.uy_document_code,   # "111"  Tipo de CFE (puedes mapear según el tipo de factura)
        serie = invoice.uy_cfe_serie  # Serie de la factura (puedes definirlo según la configuración)
        nro = invoice.uy_cfe_number
        fecha_emision = invoice.invoice_date.strftime("%Y-%m-%d") if invoice.invoice_date else fields.Date.today()
        fma_pago = "1"  # Puedes mapear según los términos de pago

        # Datos del Emisor (Tienda)
        ruc_emisor = company.vat if company.vat else False  # RUC de la tienda
        rzn_soc = company.name if company.name else "Razon Social"  # Razón social de la tienda
        cdg_dgi_sucur = company.dgi_code  # Código DGI de la sucursal
        dom_fiscal = company.street  # Domicilio fiscal de la tienda
        ciudad = company.city  # Ciudad de la tienda
        departamento = company.state_id.name  # Departamento de la tienda

        # Datos del Cliente (Receptor)
        cliente = invoice.partner_id
        tipo_doc_recep = "2"  # 2 = RUT (puedes mapearlo según el tipo de cliente)
        cod_pais_recep = cliente.country_id.code  # Código del país del cliente
        doc_recep = cliente.vat  # RUT del cliente
        rzn_soc_recep = cliente.name # razon social del cliente
        dir_recep = cliente.street
        ciudad_recep = cliente.city
        pais_recep = cliente.country_id.name

        # Totales
        tpo_moneda = invoice.currency_id.name # Moneda de la factura
        mnt_neto_iva_tasa_basica = invoice.amount_untaxed
        iva_tasa_min = invoice.uy_tax_min
        iva_tasa_basica = invoice.uy_tax_basic_base
        mnt_iva_tasa_basica = invoice.uy_tax_min_base
        mnt_total = invoice.amount_total
        cant_lin_det = len(invoice.invoice_line_ids)
        mnt_pagar = invoice.amount_total

        # Detalles de los productos
        detalles_xml = ""
        for idx, line in enumerate(invoice.invoice_line_ids, start=1):
            detalles_xml += f"""
            <Item>
                <NroLinDet>{idx}</NroLinDet>
                <CodItem><TpoCod>INT2</TpoCod><Cod>{line.product_id.default_code or '000'}</Cod></CodItem>
                <IndFact>3</IndFact>
                <NomItem>{line.name}</NomItem>
                <Cantidad>{line.quantity}</Cantidad>
                <UniMed>{line.product_uom_id.name if line.product_uom_id else 'Unidad'}</UniMed>
                <PrecioUnitario>{line.price_unit}</PrecioUnitario>
                <MontoItem>{line.price_subtotal}</MontoItem>
            </Item>
            """

        # Construcción del XML
        cfe_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
        <CFE xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" version="1.0" xmlns="http://cfe.dgi.gub.uy">
            <eFact>
                <Encabezado>
                    <IdDoc>
                        <TipoCFE>{tipo_cfe}</TipoCFE>
                        <Serie>{serie}</Serie>
                        <Nro>{nro}</Nro>
                        <NroInterno>{invoice.id}</NroInterno>
                        <FchEmis>{fecha_emision}</FchEmis>
                        <FmaPago>{fma_pago}</FmaPago>
                    </IdDoc>
                    <Emisor>
                        <RUCEmisor>{ruc_emisor}</RUCEmisor>
                        <RznSoc>{rzn_soc}</RznSoc>
                        <CdgDGISucur>{cdg_dgi_sucur}</CdgDGISucur>
                        <DomFiscal>{dom_fiscal}</DomFiscal>
                        <Ciudad>{ciudad}</Ciudad>
                        <Departamento>{departamento}</Departamento>
                    </Emisor>
                    <Receptor>
                        <TipoDocRecep>{tipo_doc_recep}</TipoDocRecep>
                        <CodPaisRecep>{cod_pais_recep}</CodPaisRecep>
                        <DocRecep>{doc_recep}</DocRecep>
                        <RznSocRecep>{rzn_soc_recep}</RznSocRecep>
                        <DirRecep>{dir_recep}</DirRecep>
                        <CiudadRecep>{ciudad_recep}</CiudadRecep>
                        <PaisRecep>{pais_recep}</PaisRecep>
                    </Receptor>
                    <Totales>
                        <TpoMoneda>{tpo_moneda}</TpoMoneda>
                        <MntNetoIVATasaBasica>{mnt_neto_iva_tasa_basica:.2f}</MntNetoIVATasaBasica>
                        <IVATasaMin>{iva_tasa_min}</IVATasaMin>
                        <IVATasaBasica>{iva_tasa_basica}</IVATasaBasica>
                        <MntIVATasaBasica>{mnt_iva_tasa_basica:.2f}</MntIVATasaBasica>
                        <MntTotal>{mnt_total:.2f}</MntTotal>
                        <CantLinDet>{cant_lin_det}</CantLinDet>
                        <MntPagar>{mnt_pagar:.2f}</MntPagar>
                    </Totales>
                </Encabezado>
                <Detalle>
                    {detalles_xml}
                </Detalle>
                <CAEData>
                    <CAE_ID>90250001110</CAE_ID>
                    <DNro>1</DNro>
                    <HNro>9999999</HNro>
                    <FecVenc>2026-12-31</FecVenc>
                </CAEData>
            </eFact>
        </CFE>
        """

        # Validar formato XML
        try:
            etree.fromstring(cfe_xml.encode("utf-8"))  # Verifica si el XML es válido
        except etree.XMLSyntaxError as e:
            raise ValueError(f"Error en la generación del XML: {e}")

        return cfe_xml

    def get_cfe_pdf(self, move, batch_id=False):
        if not batch_id:
            batch_ids = move.edi_document_ids.filtered(
                lambda s: s.edi_format_id.code == "edi_uy_cfe"
                and s.uy_biller_id != False
            )
            batch_id = len(batch_ids) > 1 and batch_ids[0] or batch_ids
        if batch_id:
            if move.company_id.uy_server == "biller":
                try:
                    vals = {}
                    vals["servidor"] = self.get_server(batch_id.move_id.company_id)
                    if batch_id.uy_cfe_id:
                        Sobre = self.env["l10n_uy_edi_cfe.envelope.cfe"].create(vals)
                        pdf_data = Sobre.obtenerPdfCFE(batch_id.uy_cfe_id)
                        return pdf_data
                    else:
                        return {}
                except Exception:
                    return {
                        "estado": False,
                        "respuesta": {"error": "Error en la consulta a biller"},
                    }
            elif move.company_id.uy_server == "factura_express":
                try:
                    vals = {}
                    vals["servidor"] = self.get_server(batch_id.move_id.company_id)
                    if batch_id.uy_invoice_url:
                        Sobre = self.env["l10n_uy_edi_cfe.envelope.cfe"].create(vals)
                        pdf_data = Sobre.obtenerPdfCFE(batch_id.uy_invoice_url)
                        return pdf_data
                    else:
                        return {}
                except Exception:
                    return {
                        "estado": False,
                        "respuesta": {
                            "error": "Error en la consulta a Factura Express"
                        },
                    }
        else:
            return {
                "estado": False,
                "respuesta": {"error": "No existe hash de consulta"},
            }

    def get_cfe_invoice_status(self, move_id, batch_id=None):
        if not batch_id:
            batch_ids = move_id.edi_document_ids.filtered(
                lambda s: s.edi_format_id.code == "edi_uy_cfe"
                and s.uy_biller_id != False
            )
            batch_id = len(batch_ids) > 1 and batch_ids[0] or batch_ids
        if batch_id:
            try:
                vals = {}
                vals["servidor"] = self.get_server(batch_id.move_id.company_id)
                if batch_id.uy_cfe_id:
                    Sobre = self.env["l10n_uy_edi_cfe.envelope.cfe"].create(vals)
                    invoice_data = Sobre.obtenerEstadoCFE(batch_id.uy_cfe_id)
                    return len(invoice_data) and invoice_data[0] or {}
                else:
                    return {}
            except Exception:
                return {
                    "estado": False,
                    "respuesta": {"error": "Error en la consulta a biller"},
                }
        else:
            return {
                "estado": False,
                "respuesta": {"error": "No existe hash de consulta"},
            }

    def check_cfe_invoice_status(self, move_id, batch_id=None):
        if not batch_id:
            batch_ids = move_id.edi_document_ids.filtered(
                lambda s: s.edi_format_id.code == "edi_uy_cfe"
                and s.uy_biller_id != False
            )
            batch_id = len(batch_ids) > 1 and batch_ids[0] or batch_ids
        if batch_id:
            try:
                vals = {}
                vals["servidor"] = self.get_server(batch_id.move_id.company_id)
                Sobre = self.env["l10n_uy_edi_cfe.envelope.cfe"].create(vals)
                invoice_data = Sobre.verificarEstadoCFE(
                    batch_id.move_id.uy_uuid,
                    batch_id.move_id.invoice_date.strftime("%Y-%m-%d 00:00:00"),
                    batch_id.move_id.uy_document_code,
                    batch_id.move_id.name.split("-")[0],
                    batch_id.move_id.name.split("-")[-1],
                )
                return invoice_data or {}
            except Exception:
                return {
                    "estado": False,
                    "respuesta": {"error": "Error en la consulta a biller"},
                }
        else:
            return {
                "estado": False,
                "respuesta": {"error": "No existe hash de consulta"},
            }

    def check_cfe_eresuardo_status(self, picking_id, edi_document_id):
        if not picking_id:
            batch_ids = picking_id.uy_edi_cfe_ids.filtered(
                lambda s: s.edi_format_id.code == "edi_uy_cfe"
                and s.uy_biller_id != False
            )
            edi_document_id = len(batch_ids) > 1 and batch_ids[0] or batch_ids
        if edi_document_id:
            try:
                vals = {}
                vals["servidor"] = self.get_server(
                    edi_document_id.picking_id.company_id
                )
                Sobre = self.env["l10n_uy_edi_cfe.envelope.cfe"].create(vals)
                invoice_data = Sobre.verificarEstadoCFE(
                    edi_document_id.picking_id.uy_uuid,
                    edi_document_id.picking_id.uy_eremito_date.strftime(
                        "%Y-%m-%d 00:00:00"
                    ),
                    "181",
                    edi_document_id.picking_id.uy_cfe_serie,
                    edi_document_id.picking_id.uy_cfe_number,
                )
                return invoice_data or {}
            except Exception:
                return {
                    "estado": False,
                    "respuesta": {"error": "Error en la consulta a biller"},
                }
        else:
            return {
                "estado": False,
                "respuesta": {"error": "No existe hash de consulta"},
            }

    def _get_eresuardo(self, picking_id):
        vals = {}
        vals["tipoCFE"] = "181"
        vals["fecEmision"] = picking_id.uy_eremito_date.strftime("%Y-%m-%d")
        vals["numero_interno"] = picking_id.uy_uuid
        vals["tipo_traslado"] = picking_id.uy_edi_cfe_type
        return vals

    def _get_eresuardo_lines(self, move_line_ids):
        lines = []
        for line in move_line_ids:
            vals = {}
            vals["descripcion"] = line.name[:80]
            vals["cantidad"] = line.product_uom_qty
            vals["unidadMedida"] = (
                line.product_uom and line.product_uom.uy_unit_code or "N/A"
            )
            vals["codigo"] = line.product_id.default_code
            lines.append(vals)
        return lines

    def send_eresuardo(self, batch_id):
        vals = {}
        vals.update(self.get_sobre(batch_id))
        vals["servidor"] = self.get_server(batch_id.picking_id.company_id)
        documento = {}
        documento.update(self._get_eresuardo(batch_id.picking_id))
        documento["emisor"] = self._get_company(batch_id.picking_id.company_id)
        documento["adquirente"] = self._get_partner(batch_id.picking_id.partner_id)
        documento["items"] = self._get_eresuardo_lines(
            batch_id.picking_id.move_ids_without_package
        )
        documento["adenda"] = (
            batch_id.picking_id.note
            and str(batch_id.picking_id.note)
            .replace("<br>", "\n")
            .replace("<br />", "\n")
            .replace("<p>", "")
            .replace("</p>", "\n")
            or ""
        )
        vals["documento"] = documento
        Sobre = self.env["l10n_uy_edi_cfe.envelope.cfe"].create(vals)
        res = Sobre.enviarCFE()
        return res
