from odoo import models


class APIInventoryUpdate(models.AbstractModel):
    _name = "api.inventory.update"
    _description = "API Inventory Update"
    _inherit = "api.connector"  # Hereda de API Connector

    def update_product_pricelist_by_sku(self, sku, price_list):
        """Modifica el precio de un producto por SKU en la API"""
        endpoint = f"/servlet/awsproductweb?{sku},2"
        payload = {"PriceList": price_list}
        return self._send_post_request(endpoint, payload)

    def update_external_price_by_sku(self, sku, currency_code, price):
        """Modifica el precio externo de un producto por SKU en la API"""
        endpoint = f"/servlet/awsproductweb?{sku},2"
        payload = {"CurrencyCode": currency_code, "Price": price}
        return self._send_post_request(endpoint, payload)

    def update_product_stock_by_sku(self, sku, quantity):
        """Modifica el stock de un producto por SKU en la API"""
        endpoint = f"/servlet/awsproductweb?{sku},2"
        payload = {"Quantity": quantity}
        return self._send_post_request(endpoint, payload)

    def update_inventory(
        self,
        warehouse_id,
        wshelf_code,
        wlevel_code,
        wpile_code,
        type_move_code,
        products,
    ):
        """Modifica el inventario en la API"""
        endpoint = "/servlet/awsinventory"
        payload = {
            "WarehouseId": warehouse_id,
            "WShelfCode": wshelf_code,
            "WLevelCode": wlevel_code,
            "WPileCode": wpile_code,
            "TypeMoveCode": type_move_code,
            "Product": products,
        }
        return self._send_post_request(endpoint, payload)


    def query_product(self, product_title=None, product_sku=None, only_ids=0):
        """Consulta productos en la API por título o SKU"""
        endpoint = "/servlet/awsproductsweb?"
        payload = {
            "OnlyIds": only_ids,  # 0 para obtener todos los detalles, 1 solo los IDs
            "ProductTitle": product_title or "",
            "ProductSKU": product_sku or "",
        }
        return self._send_post_request(endpoint, payload)
