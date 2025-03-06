from odoo import models, fields

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    api_endpoint_url = fields.Char(
        string="API Endpoint URL",
        config_parameter="mundo_shop_integration.endpoint_url",
        help="URL del endpoint de la API Fenicio"
    )

    api_authorization_token = fields.Char(
        string="API Authorization Token",
        config_parameter="mundo_shop_integration.authorization_token",
        help="Token de autorización para la API Fenicio"
    )

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].set_param('mundo_shop_integration.endpoint_url', self.api_endpoint_url)
        self.env['ir.config_parameter'].set_param('mundo_shop_integration.authorization_token', self.api_authorization_token)
        
        
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        res.update(
            api_endpoint_url=self.env['ir.config_parameter'].get_param('mundo_shop_integration.endpoint_url'),
            api_authorization_token=self.env['ir.config_parameter'].get_param('mundo_shop_integration.authorization_token')
        )
        return res

