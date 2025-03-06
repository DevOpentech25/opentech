import logging
import requests
import re
from base64 import encodebytes
from lxml import etree
from pysimplesoap.client import SoapClient, SoapFault

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

log = logging.getLogger(__name__)


class EInvoiceExpressSoap(models.AbstractModel):
    _name = "einvoice.express.client.soap"
    _description = "Cliente SOAP para Facturación Electrónica"

    url = fields.Char(string="URL del Servicio SOAP")

    def _connect(self):
        """Inicializa el cliente SOAP."""
        if not self.env.company.uy_server:
            raise ValidationError("No se ha configurado un servidor CFE para Biller")

        self.url = self.env.company.url_api_cfe

        wsdl_url = f"{self.url}?wsdl" if "?wsdl" not in self.url else self.url
        self._client = SoapClient(
            wsdl=wsdl_url,
            cache=None,
            ns="econ",
            namespace="http://eConectorWS/",
            soap_ns="soapenv",
            soap_server="jbossas6",
            trace=True,
        )

    @staticmethod
    def _get_response(response):
        """Procesa la respuesta de una solicitud HTTP."""
        try:
            log.debug(response)
            log.debug(str(response.url))
            if response.status_code in [200, 201]:
                log.debug(response.text)
                pdf = response.content
                return {
                    "estado": True,
                    "respuesta": {"pdf": str(encodebytes(pdf), "utf-8")},
                }
            return {
                "estado": False,
                "respuesta": {
                    "error": str(response.text),
                    "codigo": response.status_code,
                },
            }
        except Exception as e:
            log.error(f"Error en la respuesta: {e}")
            return {
                "estado": False,
                "respuesta": {"error": response.text, "codigo": response.status_code},
            }

    def get_pdf(self, pdf_url):
        """Obtiene un archivo PDF desde una URL."""
        url = self.get_pdf_url(pdf_url)
        if url:
            try:
                response = requests.get(url)
                return self._get_response(response)
            except Exception as e:
                log.error(f"Error al obtener PDF: {e}")
                return {
                    "estado": False,
                    "respuesta": {"error": "Error al obtener el PDF"},
                }
        else:
            return {
                "estado": False,
                "respuesta": {"error": "No se encontró la URL del PDF"},
            }

    @staticmethod
    def get_pdf_url(pdf_url):
        """Extrae la URL del PDF desde una respuesta HTML."""
        try:
            response = requests.get(pdf_url)
            pattern = r".*<script>.*location.href.*(http.+pdf).+</script>.*"
            url_pattern = re.findall(pattern, response.text.replace("\n", ""))
            return url_pattern[0] if url_pattern else False
        except Exception as e:
            log.error(f"Error obteniendo URL del PDF: {e}")
            return False

    def _call_service(self, name, params):
        """Llama al servicio SOAP."""
        try:
            self._connect()
            service = getattr(self._client, name)
            response = service(**params)

            res = {}
            if response.get("return"):
                data = response.get("return")
                response_xml = etree.fromstring(data)

                fields_map = {
                    "tipoComprobante": "tipoComprobante",
                    "codigo_retorno": "codigo_retorno",
                    "nro_transaccion": "nro_transaccion",
                    "mensaje_retorno": "mensaje_retorno",
                    "serie": "serie",
                    "numero": "numero",
                    "qrText": "qrText",
                    "qrFile": "qrFile",
                    "id": "id",
                    "dNro": "dNro",
                    "hNro": "hNro",
                    "fecVenc": "fecVenc",
                    "codigoResolucion": "codigoResolucion",
                    "codigoSeguridad": "codigoSeguridad",
                    "fechaFirma": "fechaFirma",
                    "linkDocumento": "linkDocumento",
                }

                for key, xpath in fields_map.items():
                    element = response_xml.find(f".//{xpath}")
                    if element is not None:
                        res[key] = element.text

                if "linkDocumento" in res:
                    pdf_data = self.get_pdf(res["linkDocumento"])
                    res["pdf_document"] = (
                        pdf_data.get("estado")
                        and pdf_data.get("respuesta").get("pdf")
                        or ""
                    )

                res["return"] = data
            else:
                return False, {"faultstring": "No se pudo obtener la respuesta"}

            return True, res
        except SoapFault as e:
            log.error(f"SOAP Fault: {e}")
            return False, {"faultcode": e.faultcode, "faultstring": e.faultstring}
        except Exception as e:
            log.error(f"Error general en _call_service: {e}")
            return False, {}

    def envio_cfe(self, params):
        """Envia una factura electrónica CFE mediante el servicio SOAP."""
        return self._call_service("envioCfe", params)
