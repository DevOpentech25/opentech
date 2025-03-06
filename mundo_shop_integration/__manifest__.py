{
    "name": "MundoShop Integration",
    "version": "1.2",
    "summary": "Integración con MundoShop",
    "sequence": 10,
    "description": """
Permite la integración con MundoShop para obtener las órdenes de venta, informacion de productos y actualizarlas en Odoo.
    """,
    "author": "Yadier Abel / Opentech",
    "depends": [
        "base",
        "sale_management",
        "stock",
    ],
    "category": "Extra Tools",
    "auto_install": False,
    "data": [
        "data/ir_cron_sales_orders.xml",
        #"security/ir.model.access.csv",
        "views/res_config_setting.xml",
        "views/sale_order_views.xml",
    ],
    "license": "LGPL-3",
}
