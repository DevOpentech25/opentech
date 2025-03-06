from odoo import fields, models, api


class CfeApiClient(models.Model):
    _name = "cfe.api.client"
    _description = "Api Client for CFE"

    name = fields.Char(string="Name", required=True)
    server_type_id = fields.Many2one(
        "l10n_uy_cfe.server.type", string="Server Type", required=True
    )
    api_type = fields.Selection(
        [
            ("json", "JSON"),
            ("xml", "XML"),
            ("soap", "SOAP"),
            ("rest", "REST"),
            ("web_service", "Web Service"),
            ("ftp", "FTP"),
            ("sftp", "SFTP"),
            ("other", "Other"),
        ],
        string="API Type",
        required=True,
        default="json",
    )

    def test_connection(self):
        return True # TODO: Implement this method
