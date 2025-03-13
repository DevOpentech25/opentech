# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'POS Transact',
    'version': '1.0',
    'category': 'Sales/Point of Sale',
    'sequence': 6,
    'summary': 'Integrate your POS with an Transact payment terminal',
    'data': [
        'data/res_currency_data.xml',
        'views/res_config_settings_views.xml',
        'views/pos_payment_method_views.xml',
        'views/res_currency_views.xml',
    ],
    'depends': ['point_of_sale'],
    'installable': True,
    'assets': {
        'point_of_sale._assets_pos': [
            'pos_transact/static/src/app/payment_transact.js',
            'pos_transact/static/src/app/pos_bus.js',
            'pos_transact/static/src/overrides/components/payment_screen/payment_screen.js',
            'pos_transact/static/src/overrides/models/models.js',
        ],
    },
    'license': 'LGPL-3',
}
