from lxml import etree
from collections import OrderedDict

from odoo import models, fields

# self._ns = "http://efactura.info"
# self._xsi = "http://www.w3.org/2001/XMLSchema-instance"
# self._schemaLocation = "SobreFactura.xsd"
# self._root = None


class SobreFactura(models.Model): # clase SobreFactura
    _name = "l10n_uy_cfe.sobre_factura"

    ns = fields.Char(string="ns", default="http://efactura.info")
    xsi = fields.Char(string="xsi", default="http://www.w3.org/2001/XMLSchema-instance")
    schemaLocation = fields.Char(string="schemaLocation", default="SobreFactura.xsd")
    root = fields.Char(string="root")

    def getDocument(self, sobre):
        tag = etree.QName(self.ns, 'SobreFactura')
        nsmap1 = OrderedDict([('xsi', self.xsi), ('ns', self.ns)])
        schemaLocation = '{%s}%s' % (self.xsi, 'schemaLocation')
        self.root = etree.Element(tag.text, attrib={schemaLocation: self.schemaLocation}, nsmap=nsmap1)
        # self._root.set('schemaLocation', schemaLocation)
        cabezal = etree.SubElement(self.root, "Cabezal")

        etree.SubElement(cabezal, "RUTEmisor").text = sobre.rutEmisor
        etree.SubElement(cabezal, "NumSobre").text = str(sobre.numero)
        etree.SubElement(cabezal,
                         "Fecha").text = sobre.fecha  # datetime.strptime(sobre.send_date, "%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%dT%H:%M:%S")

        cfe = etree.SubElement(self.root, "CFESimple")
        # parser = etree.XMLParser(remove_blank_text=True, ns_clean=False)
        xml = CFESimple().getInvoice(sobre.cfe)  # etree.fromstring(sobre.cfe, parser=parser, base_url=None)
        # xml = etree.tostring(xml, pretty_print=True, xml_declaration = True, encoding='utf-8')
        cfe.append(xml)
        etree.SubElement(cfe, "Anulado").text = "0"
        etree.SubElement(cfe, "Addenda").text = sobre.adenda or ""

        sobre = etree.tostring(self.root, pretty_print=True, xml_declaration=True, encoding='utf-8')
        return str(sobre, 'utf-8').replace('<CFE version="1.0">',
                                           '<CFE version="1.0" xmlns:ns="http://efactura.info" >')


class CFESimple():
    _ns0 = "http://efactura.info"
    _root = None

    def _getVoucher(self, id_doc, documento):
        tag = etree.QName(self._ns0, 'TipoCFE')
        etree.SubElement(id_doc, tag.text, nsmap={'ns0': tag.namespace}).text = documento.tipoCFE
        tag = etree.QName(self._ns0, 'Serie')
        etree.SubElement(id_doc, tag.text, nsmap={'ns0': tag.namespace})
        tag = etree.QName(self._ns0, 'Nro')
        etree.SubElement(id_doc, tag.text, nsmap={'ns0': tag.namespace})
        tag = etree.QName(self._ns0, 'FchEmis')
        etree.SubElement(id_doc, tag.text, nsmap={'ns0': tag.namespace}).text = documento.fecEmision
        # Ojo
        if documento.montosBrutos == '1':
            tag = etree.QName(self._ns0, 'MntBruto')
            etree.SubElement(id_doc, tag.text, nsmap={'ns0': tag.namespace}).text = documento.montosBrutos  # '1'
        # Ojo preguntar
        if documento.tipoCFE not in ['182']:
            tag = etree.QName(self._ns0, 'FmaPago')
            etree.SubElement(id_doc, tag.text, nsmap={'ns0': tag.namespace}).text = documento.formaPago  # "1"

        if documento.fecVencimiento:
            tag = etree.QName(self._ns0, 'FchVenc')
            etree.SubElement(id_doc, tag.text, nsmap={'ns0': tag.namespace}).text = documento.fecVencimiento
        if documento.tipoCFE in ['121', '122', '123', '124']:
            tag = etree.QName(self._ns0, 'ClauVenta')
            etree.SubElement(id_doc, tag.text, nsmap={'ns0': tag.namespace}).text = documento.clauVenta
            tag = etree.QName(self._ns0, 'ModVenta')
            etree.SubElement(id_doc, tag.text, nsmap={'ns0': tag.namespace}).text = documento.modVenta
            tag = etree.QName(self._ns0, 'ViaTransp')
            etree.SubElement(id_doc, tag.text, nsmap={'ns0': tag.namespace}).text = documento.viaTransp

    def _getCompany(self, emisor, documento):
        empresa = documento.emisor
        tag = etree.QName(self._ns0, 'RUCEmisor')
        etree.SubElement(emisor, tag.text, nsmap={'ns0': tag.namespace}).text = empresa.numDocumento
        tag = etree.QName(self._ns0, 'RznSoc')
        etree.SubElement(emisor, tag.text, nsmap={'ns0': tag.namespace}).text = empresa.nombre
        if empresa.sucursal:
            for sucursal in empresa.sucursal:
                tag = etree.QName(self._ns0, 'CdgDGISucur')
                etree.SubElement(emisor, tag.text, nsmap={'ns0': tag.namespace}).text = str(sucursal.codigo)
                tag = etree.QName(self._ns0, 'DomFiscal')
                etree.SubElement(emisor, tag.text, nsmap={'ns0': tag.namespace}).text = ""  # sucursal.direccion
                tag = etree.QName(self._ns0, 'Ciudad')
                etree.SubElement(emisor, tag.text, nsmap={'ns0': tag.namespace}).text = ""  # sucursal.ciudad
                tag = etree.QName(self._ns0, 'Departamento')
                etree.SubElement(emisor, tag.text, nsmap={'ns0': tag.namespace}).text = ""  # sucursal.departamento
                break
        else:
            tag = etree.QName(self._ns0, 'DomFiscal')
            etree.SubElement(emisor, tag.text, nsmap={'ns0': tag.namespace}).text = empresa.direccion
            tag = etree.QName(self._ns0, 'Ciudad')
            etree.SubElement(emisor, tag.text, nsmap={'ns0': tag.namespace}).text = empresa.ciudad
            tag = etree.QName(self._ns0, 'Departamento')
            etree.SubElement(emisor, tag.text, nsmap={'ns0': tag.namespace}).text = empresa.departamento

    def _getPartner(self, receptor, documento):
        adquirente = documento.adquirente
        tag = etree.QName(self._ns0, 'TipoDocRecep')
        etree.SubElement(receptor, tag.text, nsmap={'ns0': tag.namespace}).text = adquirente.tipoDocumento or "3"
        tag = etree.QName(self._ns0, 'CodPaisRecep')
        etree.SubElement(receptor, tag.text, nsmap={'ns0': tag.namespace}).text = adquirente.codPais or "UY"
        tag = etree.QName(self._ns0, 'DocRecep')
        etree.SubElement(receptor, tag.text, nsmap={'ns0': tag.namespace}).text = adquirente.numDocumento or "0"
        tag = etree.QName(self._ns0, 'RznSocRecep')
        etree.SubElement(receptor, tag.text, nsmap={'ns0': tag.namespace}).text = adquirente.nombre or ''
        tag = etree.QName(self._ns0, 'DirRecep')
        etree.SubElement(receptor, tag.text, nsmap={'ns0': tag.namespace}).text = adquirente.direccion or ''
        tag = etree.QName(self._ns0, 'CiudadRecep')
        etree.SubElement(receptor, tag.text, nsmap={'ns0': tag.namespace}).text = adquirente.ciudad or ''
        tag = etree.QName(self._ns0, 'DeptoRecep')
        etree.SubElement(receptor, tag.text, nsmap={'ns0': tag.namespace}).text = adquirente.departamento or ''
        if documento.tipoCFE in ['121', '122', '123']:
            tag = etree.QName(self._ns0, 'PaisRecep')
            etree.SubElement(receptor, tag.text, nsmap={'ns0': tag.namespace}).text = adquirente.nomPais

    def _getTotal(self, totales, documento):
        tag = etree.QName(self._ns0, 'TpoMoneda')
        etree.SubElement(totales, tag.text, nsmap={'ns0': tag.namespace}).text = documento.moneda
        if documento.tipoCFE in ['121', '122', '123']:
            tag = etree.QName(self._ns0, 'TpoCambio')
            etree.SubElement(totales, tag.text, nsmap={'ns0': tag.namespace}).text = str(documento.tasaCambio)
            tag = etree.QName(self._ns0, 'MntExpoyAsim')
            etree.SubElement(totales, tag.text, nsmap={'ns0': tag.namespace}).text = str(documento.mntTotal)
            tag = etree.QName(self._ns0, 'MntTotal')
            etree.SubElement(totales, tag.text, nsmap={'ns0': tag.namespace}).text = str(documento.mntTotal)
            tag = etree.QName(self._ns0, 'CantLinDet')
            etree.SubElement(totales, tag.text, nsmap={'ns0': tag.namespace}).text = str(documento.cantLinDet)
            tag = etree.QName(self._ns0, 'MontoNF')
            etree.SubElement(totales, tag.text, nsmap={'ns0': tag.namespace}).text = '0.0'
            tag = etree.QName(self._ns0, 'MntPagar')
            etree.SubElement(totales, tag.text, nsmap={'ns0': tag.namespace}).text = str(documento.mntPagar)
        elif documento.tipoCFE in ['182']:
            if documento.moneda != 'UYU':
                tag = etree.QName(self._ns0, 'TpoCambio')
                etree.SubElement(totales, tag.text, nsmap={'ns0': tag.namespace}).text = str(documento.tasaCambio)
            ret_perc_vals = {}
            cred_fisc = 0.0
            mnt_retenido = 0.0
            for retencionesPercepcion in documento.retencionesPercepciones:
                sign = retencionesPercepcion.indicadorFacturacion == '9' and -1 or 1
                monto = sign * retencionesPercepcion.monto
                ret_perc_vals[retencionesPercepcion.codigo] = monto
                if retencionesPercepcion.codigo[:4] in '2181':
                    cred_fisc += monto
                mnt_retenido += monto

            tag = etree.QName(self._ns0, 'MntTotRetenido')
            etree.SubElement(totales, tag.text, nsmap={'ns0': tag.namespace}).text = str(mnt_retenido - cred_fisc)
            tag = etree.QName(self._ns0, 'MntTotCredFisc')
            etree.SubElement(totales, tag.text, nsmap={'ns0': tag.namespace}).text = str(cred_fisc)
            tag = etree.QName(self._ns0, 'CantLinDet')
            etree.SubElement(totales, tag.text, nsmap={'ns0': tag.namespace}).text = str(
                len(documento.retencionesPercepciones))
            for codigo, monto in ret_perc_vals.items():
                tag = etree.QName(self._ns0, 'RetencPercep')
                ret_perc = etree.SubElement(totales, tag.text, nsmap={'ns0': tag.namespace})
                tag = etree.QName(self._ns0, 'CodRet')
                etree.SubElement(ret_perc, tag.text, nsmap={'ns0': tag.namespace}).text = codigo
                tag = etree.QName(self._ns0, 'ValRetPerc')
                etree.SubElement(ret_perc, tag.text, nsmap={'ns0': tag.namespace}).text = str(monto)
        else:
            tag = etree.QName(self._ns0, 'MntNoGrv')
            etree.SubElement(totales, tag.text, nsmap={'ns0': tag.namespace}).text = str(documento.mntNoGrv)
            tag = etree.QName(self._ns0, 'MntNetoIVATasaMin')
            etree.SubElement(totales, tag.text, nsmap={'ns0': tag.namespace}).text = str(documento.mntNetoIVATasaMin)
            tag = etree.QName(self._ns0, 'MntNetoIVATasaBasica')
            etree.SubElement(totales, tag.text, nsmap={'ns0': tag.namespace}).text = str(documento.mntNetoIVATasaBasica)
            tag = etree.QName(self._ns0, 'IVATasaMin')
            etree.SubElement(totales, tag.text, nsmap={'ns0': tag.namespace}).text = str(documento.ivaTasaMin)
            tag = etree.QName(self._ns0, 'IVATasaBasica')
            etree.SubElement(totales, tag.text, nsmap={'ns0': tag.namespace}).text = str(documento.ivaTasaBasica)
            tag = etree.QName(self._ns0, 'MntIVATasaMin')
            etree.SubElement(totales, tag.text, nsmap={'ns0': tag.namespace}).text = str(documento.mntIVATasaMin)
            tag = etree.QName(self._ns0, 'MntIVATasaBasica')
            etree.SubElement(totales, tag.text, nsmap={'ns0': tag.namespace}).text = str(documento.mntIVATasaBasica)
            tag = etree.QName(self._ns0, 'MntTotal')
            etree.SubElement(totales, tag.text, nsmap={'ns0': tag.namespace}).text = str(documento.mntTotal)
            tag = etree.QName(self._ns0, 'CantLinDet')
            etree.SubElement(totales, tag.text, nsmap={'ns0': tag.namespace}).text = str(documento.cantLinDet)
            tag = etree.QName(self._ns0, 'MontoNF')
            etree.SubElement(totales, tag.text, nsmap={'ns0': tag.namespace}).text = str(documento.montoNF)
            tag = etree.QName(self._ns0, 'MntPagar')
            etree.SubElement(totales, tag.text, nsmap={'ns0': tag.namespace}).text = str(documento.mntPagar)

    def _getLines(self, detalle, line, line_number):
        tag = etree.QName(self._ns0, 'Item')
        item = etree.SubElement(detalle, tag.text, nsmap={'ns0': tag.namespace})

        tag = etree.QName(self._ns0, 'NroLinDet')
        etree.SubElement(item, tag.text, nsmap={'ns0': tag.namespace}).text = str(line_number)

        tag = etree.QName(self._ns0, 'IndFact')
        etree.SubElement(item, tag.text, nsmap={'ns0': tag.namespace}).text = line.indicadorFacturacion

        tag = etree.QName(self._ns0, 'NomItem')
        etree.SubElement(item, tag.text, nsmap={'ns0': tag.namespace}).text = line.descripcion

        tag = etree.QName(self._ns0, 'Cantidad')
        etree.SubElement(item, tag.text, nsmap={'ns0': tag.namespace}).text = str(round(line.cantidad, 3))

        tag = etree.QName(self._ns0, 'UniMed')
        etree.SubElement(item, tag.text, nsmap={'ns0': tag.namespace}).text = line.unidadMedida or 'N/A'

        tag = etree.QName(self._ns0, 'PrecioUnitario')
        etree.SubElement(item, tag.text, nsmap={'ns0': tag.namespace}).text = str(round(line.precioUnitario, 2))

        if line.descuento:
            tag = etree.QName(self._ns0, 'DescuentoPct')
            etree.SubElement(item, tag.text, nsmap={'ns0': tag.namespace}).text = str(round(line.descuento, 3))
        if line.descuentoMonto:
            tag = etree.QName(self._ns0, 'DescuentoMonto')
            etree.SubElement(item, tag.text, nsmap={'ns0': tag.namespace}).text = str(round(line.descuentoMonto, 2))

        tag = etree.QName(self._ns0, 'MontoItem')
        etree.SubElement(item, tag.text, nsmap={'ns0': tag.namespace}).text = str(line.montoItem)

    def _getRetencPercepLines(self, detalle, line, line_number):
        tag = etree.QName(self._ns0, 'Item')
        item = etree.SubElement(detalle, tag.text, nsmap={'ns0': tag.namespace})

        tag = etree.QName(self._ns0, 'NroLinDet')
        etree.SubElement(item, tag.text, nsmap={'ns0': tag.namespace}).text = str(line_number)
        if line.indicadorFacturacion:
            tag = etree.QName(self._ns0, 'IndFact')
            etree.SubElement(item, tag.text, nsmap={'ns0': tag.namespace}).text = str(line.indicadorFacturacion)
        tag = etree.QName(self._ns0, 'RetencPercep')
        retenc_precep = etree.SubElement(item, tag.text, nsmap={'ns0': tag.namespace})
        tag = etree.QName(self._ns0, 'CodRet')
        etree.SubElement(retenc_precep, tag.text, nsmap={'ns0': tag.namespace}).text = str(line.codigo)

        tag = etree.QName(self._ns0, 'Tasa')
        etree.SubElement(retenc_precep, tag.text, nsmap={'ns0': tag.namespace}).text = str(line.tasa)

        tag = etree.QName(self._ns0, 'MntSujetoaRet')
        etree.SubElement(retenc_precep, tag.text, nsmap={'ns0': tag.namespace}).text = str(line.base)

        tag = etree.QName(self._ns0, 'ValRetPerc')
        etree.SubElement(retenc_precep, tag.text, nsmap={'ns0': tag.namespace}).text = str(line.monto)

    def _getRef(self, documento, etck):
        tag = etree.QName(self._ns0, 'Referencia')
        referenciam = etree.SubElement(etck, tag.text, nsmap={'ns0': tag.namespace})

        tag = etree.QName(self._ns0, 'Referencia')
        referencia = etree.SubElement(referenciam, tag.text, nsmap={'ns0': tag.namespace})

        tag = etree.QName(self._ns0, 'NroLinRef')
        etree.SubElement(referencia, tag.text, nsmap={'ns0': tag.namespace}).text = str(len(documento.referencias))

        # tag = etree.QName(self._ns0, 'RazonRef')
        # etree.SubElement(referencia, tag.text, nsmap={'ns0':tag.namespace}).text=documento.name

        for ref in documento.referencias:
            tag = etree.QName(self._ns0, 'TpoDocRef')
            etree.SubElement(referencia, tag.text, nsmap={'ns0': tag.namespace}).text = ref.tipoDocRef
            tag = etree.QName(self._ns0, 'Serie')
            etree.SubElement(referencia, tag.text, nsmap={'ns0': tag.namespace}).text = ref.serie
            tag = etree.QName(self._ns0, 'NroCFERef')
            etree.SubElement(referencia, tag.text, nsmap={'ns0': tag.namespace}).text = ref.numero
            tag = etree.QName(self._ns0, 'FechaCFEref')
            etree.SubElement(referencia, tag.text, nsmap={'ns0': tag.namespace}).text = ref.fechaCFEref

    def _getDescuento(self, documento, etck):
        if documento.descuentos:
            tag = etree.QName(self._ns0, 'DscRcgGlobal')
            desc_global = etree.SubElement(etck, tag.text, nsmap={'ns0': tag.namespace})
            line_number = 1
            for descuento in documento.descuentos:
                tag = etree.QName(self._ns0, 'DRG_Item')
                item = etree.SubElement(desc_global, tag.text, nsmap={'ns0': tag.namespace})
                tag = etree.QName(self._ns0, 'NroLinDR')
                etree.SubElement(item, tag.text, nsmap={'ns0': tag.namespace}).text = str(line_number)
                tag = etree.QName(self._ns0, 'TpoMovDR')
                etree.SubElement(item, tag.text, nsmap={'ns0': tag.namespace}).text = 'D'
                tag = etree.QName(self._ns0, 'GlosaDR')
                etree.SubElement(item, tag.text, nsmap={'ns0': tag.namespace}).text = descuento.descripcion[:50]
                tag = etree.QName(self._ns0, 'ValorDR')
                etree.SubElement(item, tag.text, nsmap={'ns0': tag.namespace}).text = str(descuento.monto)
                tag = etree.QName(self._ns0, 'IndFactDR')
                etree.SubElement(item, tag.text, nsmap={'ns0': tag.namespace}).text = descuento.indicadorFacturacion
                line_number += 1

    def getInvoice(self, documento):
        xmlns = etree.QName(None, 'CFE')
        nsmap1 = OrderedDict([('ns0', self._ns0)])
        self._root = etree.Element("CFE", version="1.0", nsmap=nsmap1)
        if documento.tipoCFE in ['101', '102', '103', '201', '202', '203']:
            tag = etree.QName(self._ns0, 'eTck')
            etck = etree.SubElement(self._root, tag.text, nsmap={'ns0': tag.namespace})
        elif documento.tipoCFE in ['121', '122', '123']:
            tag = etree.QName(self._ns0, 'eFact_Exp')
            etck = etree.SubElement(self._root, tag.text, nsmap={'ns0': tag.namespace})
        elif documento.tipoCFE in ['182']:
            tag = etree.QName(self._ns0, 'eResg')
            etck = etree.SubElement(self._root, tag.text, nsmap={'ns0': tag.namespace})
        else:
            tag = etree.QName(self._ns0, 'eFact')
            etck = etree.SubElement(self._root, tag.text, nsmap={'ns0': tag.namespace})
        tag = etree.QName(self._ns0, 'Encabezado')
        encabezado = etree.SubElement(etck, tag.text, nsmap={'ns0': tag.namespace})
        tag = etree.QName(self._ns0, 'IdDoc')
        id_doc = etree.SubElement(encabezado, tag.text, nsmap={'ns0': tag.namespace})

        self._getVoucher(id_doc, documento)

        tag = etree.QName(self._ns0, 'Emisor')
        emisor = etree.SubElement(encabezado, tag.text, nsmap={'ns0': tag.namespace})

        self._getCompany(emisor, documento)

        tag = etree.QName(self._ns0, 'Receptor')
        receptor = etree.SubElement(encabezado, tag.text, nsmap={'ns0': tag.namespace})

        self._getPartner(receptor, documento)

        tag = etree.QName(self._ns0, 'Totales')
        totales = etree.SubElement(encabezado, tag.text, nsmap={'ns0': tag.namespace})

        self._getTotal(totales, documento)

        tag = etree.QName(self._ns0, 'Detalle')
        detalle = etree.SubElement(etck, tag.text, nsmap={'ns0': tag.namespace})
        i = 0
        if documento.tipoCFE in ['182']:
            for line in documento.retencionesPercepciones:
                i += 1
                self._getRetencPercepLines(detalle, line, i)
        else:
            for line in documento.items:
                i += 1
                self._getLines(detalle, line, i)

        self._getDescuento(documento, etck)
        if documento.tipoCFE in ['102', '103', '112', '113', '122', '123']:
            self._getRef(documento, etck)
        elif documento.tipoCFE in ['182'] and documento.referencias:
            self._getRef(documento, etck)
        tag = etree.QName(self._ns0, 'DigestValue')
        etree.SubElement(self._root, tag.text, nsmap={'ns0': tag.namespace})

        return self._root
