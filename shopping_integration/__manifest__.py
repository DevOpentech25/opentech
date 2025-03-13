{
    "name": "Shopping Integration",
    "version": "1.2",
    "summary": "Conectar con el WebService de la empresa Shopping.",
    "sequence": 10,
    "description": """Conectar con el WebService de la empresa Shopping.
    Consultar datos del locatario (por RUT o contrato).
    Enviar ventas al WebService de manera automática y manual.
    Gestionar reintentos en caso de fallos en el envío.
    """,
    "website": "https://www.opentech.uy",
    "author": "Ing. Yadier A. De Quesada / Opentech",
    "depends": [
        "base",
        "sale",
        "account",
    ],
    "category": "Extra Tools",
    "auto_install": False,
    "data": [
        "data/data_lps_cfe_code.xml",
        "data/data_payment_method.xml",
        # "views/view.xml",
        # "security/ir.model.access.csv",
    ],
    "license": "LGPL-3",
}
