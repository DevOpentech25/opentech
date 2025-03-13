# coding: utf-8
import logging
import pprint
import time

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError, UserError, AccessDenied
import json

from zeep import Client, Settings, helpers
from zeep.exceptions import Fault

_logger = logging.getLogger(__name__)

# UNPREDICTABLE_TRANSACT_DATA = object() # sentinel

class PosPaymentMethod(models.Model):
    _inherit = 'pos.payment.method'

    def _get_payment_terminal_selection(self):
        return super(PosPaymentMethod, self)._get_payment_terminal_selection() + [('transact', 'Transact')]

    # Transact
    transact_hash = fields.Char(string="Transact Hash", help='Used when connecting to Transact', copy=False, groups='base.group_erp_manager')
    transact_company_code = fields.Char(string="Transact Company Code", help='Used when connecting to Transact', copy=False, groups='base.group_erp_manager')
    transact_terminal_identifier = fields.Char(help='', copy=False)
    transact_test_mode = fields.Boolean(help='Run transactions in the test environment.', groups='base.group_erp_manager')

    transact_latest_response = fields.Char(copy=False, groups='base.group_erp_manager') # used to buffer the latest asynchronous notification from Transact.
    # transact_latest_diagnosis = fields.Char(copy=False, groups='base.group_erp_manager') # used to determine if the terminal is still connected.

    @api.constrains('transact_terminal_identifier')
    def _check_transact_terminal_identifier(self):
        for payment_method in self:
            if not payment_method.transact_terminal_identifier:
                continue
            # sudo() to search all companies
            existing_payment_method = self.sudo().search([('id', '!=', payment_method.id),
                                                   ('transact_terminal_identifier', '=', payment_method.transact_terminal_identifier)],
                                                  limit=1)
            if existing_payment_method:
                if existing_payment_method.company_id == payment_method.company_id:
                    raise ValidationError(_('Terminal %s is already used on payment method %s.',
                                      payment_method.transact_terminal_identifier, existing_payment_method.display_name))
                else:
                    raise ValidationError(_('Terminal %s is already used in company %s on payment method %s.',
                                             payment_method.transact_terminal_identifier,
                                             existing_payment_method.company_id.name,
                                             existing_payment_method.display_name))

    def _get_transact_endpoints(self):
        return 'https://wwwi.transact.com.uy/Concentrador/TarjetasTransaccion_401.svc?wsdl'

    def _is_write_forbidden(self, fields):
        return super(PosPaymentMethod, self)._is_write_forbidden(fields - {'transact_latest_response'})

    def get_latest_transact_status(self):
        self.ensure_one()
        if not self.env.su and not self.user_has_groups('point_of_sale.group_pos_user'):
            raise AccessDenied()

        latest_response = self.sudo().transact_latest_response
        return latest_response

    def proxy_transact_request(self, data, operation=False):
        ''' Necessary because Transact's endpoints don't have CORS enabled '''
        self.ensure_one()
        res = self._proxy_transact_request_direct(data, operation)
        if operation == 'PostearTransaccion' and res.get('TokenNro'):
            now = fields.Datetime.now()
            time.sleep(10)
            token = res.get('TokenNro')
            timeout = res.get('TokenSegundosConsultar', 10)
            for transact_range in range(120):
                if res.get('Resp_TransaccionFinalizada', False):
                    break
                if (fields.Datetime.now() - now).total_seconds() > 120.0:
                    raise UserError('Timeout waiting for transaction to complete.')
                res = self._proxy_transact_request_direct(token, 'ConsultarTransaccion', timeout)
                timeout = res.get('Resp_TokenSegundosReConsultar', 10)
        return res

    def _proxy_transact_request_direct(self, data, operation, timeout=0):
        self.ensure_one()
        # TIMEOUT = 10
        if timeout>0:
            time.sleep(timeout)
        _logger.info('Request to Transact by user #%d:\n%s', self.env.uid, pprint.pformat(data))
        if not operation:
            operation = 'PostearTransaccion'

        # environment = 'test' if self.sudo().transact_test_mode else 'live'
        endpoint = self._get_transact_endpoints() # % environment

        settings = Settings(strict=False, xml_huge_tree=True, raw_response=False)
        client = Client(wsdl=endpoint, settings=settings)
        service = client.service
        if operation == 'PostearTransaccion':
            transaccion = {
                'EmpHASH': self.transact_hash,
                'EmpCod': self.transact_company_code,
                'TermCod': self.transact_terminal_identifier,
                # 'Operacion': 'VTA',  # Tipo de operación, VTA para venta
                # 'MonedaISO': '858',  # Código ISO de moneda (pesos uruguayos en este ejemplo)
                # 'Monto': monto * 100,  # Monto de la transacción
                # 'FacturaNro': factura_nro,
                # 'FacturaMonto': factura_monto * 100,
                # 'FacturaMontoIVA': factura_iva * 100,
                # 'FacturaConsumidorFinal': consumidor_final
            }
            if self.transact_test_mode:
                transaccion['ModoEmulacion'] = True
            transaccion.update(data)
        elif operation == 'CancelarTransaccion':
            transaccion = data #[{'TokenNro': data.get('TokenNro', '')}]
        elif operation == 'ConsultarTransaccion':
            transaccion = data
        try:
            op = getattr(service, operation)
            response = op(transaccion) # client.service.PostearTransaccion(transaccion)
        except Fault as e:
            raise ValueError(f"Error en la transacción: {e.message}")
        except Exception as e:
            raise ValueError(f"Error en la transacción: {e}")
        _logger.info('Response from Transact:\n%s', pprint.pformat(response))
        res = helpers.serialize_object(response)
        # self.sudo().transact_latest_response = json.dumps(res)
        return  dict(res) #json.loads(json.dumps(res))
        # res = {}
        # try:
        #     res['Resp_CodigoRespuesta'] = response.Resp_CodigoRespuesta or False,
        # except Exception as e:
        #     res['Resp_CodigoRespuesta'] = False
        # try:
        #     res['Resp_MensajeError'] = response.Resp_MensajeError or False
        # except Exception as e:
        #     res['Resp_MensajeError'] = False
        # try:
        #     res['Resp_EstadoAvance'] = response.Resp_EstadoAvance or False
        # except Exception as e:
        #     res['Resp_EstadoAvance'] = False
        # try:
        #     res['TokenNro'] = response.TokenNro or False
        # except Exception as e:
        #     res['TokenNro'] = False
        # try:
        #     res['TokenSegundosConsultar'] = response.TokenSegundosConsultar or False
        # except Exception as e:
        #     res['TokenSegundosConsultar'] = False
        # try:
        #     res['Resp_Finalizado'] = response.Resp_Finalizado or False
        # except Exception as e:
        #     res['Resp_Finalizado'] = False
        # self.sudo().transact_latest_response = json.dumps(res)
        return res
