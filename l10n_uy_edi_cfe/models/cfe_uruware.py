from odoo import fields, models, api


class CfeUruwareDocument(models.Model):
    _name = 'cfe.uruware.document'
    _description = 'Tipo de documento CFE para enviar por Uruware'

    name = fields.Char()
    
    def get_document(self):
        return self.name
