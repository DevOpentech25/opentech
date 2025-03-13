===========
Module Name
===========

Servicios Web Disponibles
Se proporcionan tres WebServices SOAP:

Consulta por RUT (wsConsxRUT):

📍 URL:
plaintext
Copiar
Editar
https://ventas.laspiedrasshopping.com.uy/soap/NodumLocales/services/sim/v1.3/wsConsxRUT?wsdl
🔽 Entrada: Numero RUT
🔼 Salida: RUT, Código Shopping, Contrato, Locales, EtapaPublicaciones
📌 Uso: Obtener datos básicos del locatario.
Consulta por Número de Contrato (wsConsxCont):

📍 URL:
plaintext
Copiar
Editar
https://ventas.laspiedrasshopping.com.uy/soap/NodumLocales/services/sim/v1.3/wsConsxCont?wsdl
🔽 Entrada: NumeroRUT, CodigoShopping, NumeroContrato
🔼 Salida:
Nombre Empresa, Tope Crédito/Débito, Código Rubro, Código Canal
📌 Uso: Obtener detalles del contrato para realizar la declaración de ventas.
Declaración de Ventas (wsDeclaVtas2):

📍 URL:
plaintext
Copiar
Editar
https://ventas.laspiedrasshopping.com.uy/soap/NodumLocales/services/forms/v1.3/wsDeclaVtas2?wsdl
🔽 Entrada:
plaintext
Copiar
Editar
Numero RUT, CodigoShopping, NumeroContrato, CodigoCanal,
Secuencial, Caja, Cliente, Fecha, Monto, Forma de Pago...
🔼 Salida:
plaintext
Copiar
Editar
0 - Grabado correctamente
1 - Pre-grabado correctamente
2 - Error al grabar
3 - Error al procesar archivo
📌 Uso: Enviar ventas de manera interactiva. Máximo 10 registros por vez.
🔹 Autenticación
Es necesaria autenticación con usuario y contraseña proporcionados por Las Piedras Shopping.
🔹 Manejo de Errores y Envío Diferido
Se recomienda implementar un sistema de reintento en caso de fallos en el envío en línea.
Se debe programar un envío diferido automático que intente reenviar datos sin respuesta.
🔹 Códigos Importantes
Medios de Pago: 00 (Contado), 20 (OCA), 45 (VISA), 53 (MasterCard), 91 (Débito), etc.
Códigos CFE (Documentos Electrónicos): 101 (e-Ticket), 111 (e-Factura), 131 (e-Ticket Cuenta Ajena), etc.
Canales de Venta: 1 (Local), 2 (Delivery), 3 (Pick-Up).
Monedas: UYU (Pesos Uruguayos), USD (Dólares).

