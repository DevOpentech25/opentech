#     efactura /cliente.py
# Se conecta a un servicio SOAP utilizando la librería pysimplesoap y zeep.

from odoo import models, fields, api
from pysimplesoap.client import SoapClient, SoapFault, SimpleXMLElement
from lxml import etree
from zeep import Client as ZeepClient, Settings
from zeep.transports import Transport
import logging
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class InvoiceSoapClient(models.TransientModel):
    _name = "l10n_uy_cfe.soap.client"
    _description = "Cliente SOAP para Facturación"

    url = fields.Char(string="URL del Servicio")
    usuario = fields.Char(string="Usuario")
    clave = fields.Char(string="Clave")
    rut_emisor = fields.Char(string="RUT Emisor")
    impresion = fields.Integer(string="Impresión")

    _soap_namespaces = {
        "soap11": "http://schemas.xmlsoap.org/soap/envelope/",
        "soap": "http://schemas.xmlsoap.org/soap/envelope/",
        "soapenv": "http://schemas.xmlsoap.org/soap/envelope/",
        "soap12": "http://www.w3.org/2003/05/soap-env",
        "soap12env": "http://www.w3.org/2003/05/soap-envelope",
    }

    _soap_template = """<soapenv:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:ws="http://turobot.com/ws/ws_efacturainfo_ventas.php">
       <soapenv:Header/>
       <soapenv:Body>
          <ws:RECIBESOBREVENTA soapenv:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
             <usuario xsi:type="xsd:string">%s</usuario>
             <clave xsi:type="xsd:string">%s</clave>
             <rutEmisor xsi:type="xsd:string">%s</rutEmisor>
             <sobre xsi:type="ws:Sobre">
                <contenido_sobre xsi:type="xsd:string"><![CDATA[%s]]></contenido_sobre>
             </sobre>
             <impresion xsi:type="xsd:int">%s</impresion>
          </ws:RECIBESOBREVENTA>
       </soapenv:Body>
    </soapenv:Envelope>"""

    def _get_client(self):
        """Inicializa la conexión SOAP con el servicio"""
        if not self.env.company.uy_server:
            raise ValidationError("No se ha configurado un servidor CFE para Biller")

        self.url = self.env.company.uy_server.url_api_cfe
        self.usuario = self.env.company.uy_server.usuario
        self.clave = self.env.company.uy_server.clave

        return SoapClient(
            location=self.url, action=f"{self.url}/RECIBESOBREVENTA", namespace=self.url
        )

    def _call_ws(self, xml):
        """Envía una solicitud SOAP y procesa la respuesta"""
        cliente = self._get_client()
        try:
            xml_response = cliente.send("RECIBESOBREVENTA", xml)
            _logger.info(f"Respuesta SOAP: {xml_response}")

            response = SimpleXMLElement(xml_response, namespace=self.url)

            if response("Fault", ns=list(self._soap_namespaces.values()), error=False):
                detailXml = response(
                    "detail", ns=list(self._soap_namespaces.values()), error=False
                )
                detail = repr(detailXml.children()) if detailXml else None
                raise SoapFault(
                    str(response.faultcode), str(response.faultstring), detail
                )

            return response

        except SoapFault as e:
            _logger.error(f"Error SOAP: {e.faultcode} - {e.faultstring}")
            return {"faultcode": e.faultcode, "faultstring": e.faultstring}
        except Exception as e:
            _logger.error(f"Error inesperado en SOAP: {str(e)}")
            return {"error": str(e)}

    def _call_service(self, params):
        """Prepara el XML y llama a _call_ws"""
        try:
            xml = self._soap_template % (
                params.get("usuario"),
                params.get("clave"),
                params.get("rutEmisor"),
                params.get("sobre"),
                params.get("impresion"),
            )
            parser = etree.XMLParser(strip_cdata=False)
            root = etree.fromstring(xml, parser)
            xml = etree.tostring(
                root, pretty_print=True, xml_declaration=True, encoding="utf-8"
            )

            _logger.info(f"Enviando SOAP: {xml}")
            response = self._call_ws(xml)

            return {
                "estado": str(response.estado or ""),
                "codigosError": str(response.codigosError or ""),
                "serie": str(response.serie or ""),
                "numero": str(response.numero or ""),
                "PDFcode": str(response.PDFcode or ""),
                "QRcode": str(response.QRcode or ""),
                "codigoSeg": str(response.codigoSeg or ""),
                "CAE": str(response.CAE or ""),
                "CAEserie": str(response.CAEserie or ""),
                "CAEdesde": str(response.CAEdesde or ""),
                "CAEhasta": str(response.CAEhasta or ""),
                "CAEvto": str(response.CAEvto or ""),
                "URLcode": str(response.URLcode or ""),
            }

        except Exception as e:
            _logger.error(f"Error en _call_service: {str(e)}")
            return {"error": str(e)}

    def recibo_venta(self, params):
        """Envía una venta al servicio SOAP"""
        return self._call_service(params)

    def compras_cfes(self, params, servidor):
        """Obtiene información de compras de CFEs"""

        def process_xml(str_xml):
            xml = etree.fromstring(
                str_xml.encode("utf-8"), parser=etree.XMLParser(strip_cdata=False)
            )
            res = []
            for invoice in xml.findall("cabezal"):
                res.append(
                    {
                        "tipo": invoice.find("tipo").text,
                        "serie": invoice.find("serie").text,
                        "num": invoice.find("num").text,
                        "pago": invoice.find("pago").text,
                        "fecha": invoice.find("fecha").text,
                        "vto": invoice.find("vto").text,
                        "rutEmisor": invoice.find("rutEmisor").text,
                        "moneda": invoice.find("moneda").text,
                        "TC": invoice.find("TC").text,
                        "bruto": invoice.find("bruto").text,
                        "iva": invoice.find("iva").text,
                    }
                )
            return res

        settings = Settings(strict=False)
        transport = Transport()
        client = ZeepClient(servidor.url, transport=transport, settings=settings)
        params["usuario"] = servidor.usuario
        params["clave"] = servidor.clave

        try:
            response = client.service.compras_CFEs(**params)
            return process_xml(response.informeXML)
        except Exception as e:
            _logger.error(f"Error en compras_cfes: {str(e)}")
            return []
