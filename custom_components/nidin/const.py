"""Constants of the nidin component."""
from datetime import timedelta

DEFAULT_NAME = "nidin"
DOMAIN = "nidin"
PLATFORMS = [ "binary_sensor", "button", "image", "sensor" ]
DATA_KEY = "data_nidin"

ATTR_ETA = "eta"
ATTR_RESTAURANT_NAME = "restaurant_name"
ATTR_COURIER_NAME = "courier_name"
ATTR_COURIER_PHONE = "courier_phone"
ATTR_COURIER_DESCRIPTION = "courier_description"
ATTR_TITLE_SUMMARY = "title_summary"
ATTR_SUBTITLE_SUMMARY = "subtitle_summary"
ATTR_LATITUDE = "latitude"
ATTR_LONGITUDE = "longitude"
ATTR_HTTPS_RESULT = "https_result"
ATTR_LIST = [
    ATTR_ETA,
    ATTR_RESTAURANT_NAME,
    ATTR_SUBTITLE_SUMMARY,
    ATTR_TITLE_SUMMARY,
    ATTR_HTTPS_RESULT
]

DEFAULT_SCAN_INTERVAL = timedelta(minutes=1)

CONF_TOKEN_TIMEOUT = "token_timeout"
CONF_DEVICE_ID = "device_id"
CONF_USER_ID = "user_id"
DEFAULT_ACCESS_TOKEN = "EAAIAALwuPZAYBO5OMDKkKD3UvMg5rmHSRy3kHDLkMAU9SSJ9hGKxj1ziMrVSoGqZAZCgJ7yMuiFC442Gvc1vMcFoNNKgiZAddJb61VZCg6SxetEs9Q1jQpgudlPWHuX1OGjy1YIBbhxZAeBZBQ3kiEhzWeYOZAfBt9zBheKzZBScGTbgy7LoFhELCIr5sEwZDZD"
DEFAULT_DEVICE_ID = "NIDINShopperWeb_OWfnzrTUvQ"
DEFAULT_IDENTITY_1 = "nidinphone"
DEFAULT_IDENTITY_2 = "562953110568342"
ATTRIBUTION = "Powered by nidin Data"
MANUFACTURER = "nidin"
DEFAULT_LOCALCODE = "tw"
NIDIN_COORDINATOR = "nidin_coordinator"
NIDIN_DATA = "nidin_data"
NIDIN_NAME = "fnidin_name"
NIDIN_ORDERS = "orders"
UPDATE_LISTENER = "update_listener"

HA_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.72 Safari/537.36"
BASE_URL = 'https://loctw-service-api.nidin.shop/shopper/v2'

REQUEST_TIMEOUT = 10  # seconds

LANGUAGE_TRANSLATIONS = {
    "en": {
        "shop.order.status.message_awaiting_vendor_confirmation": "Awaiting vendor confirmation",
        "shop.order.status.message_order_accepted_by_vendor": "Order accepted by vendor",
        "shop.order.status.message_order_picked_by_rider": "Order picked by rider",
        "shop.order.status.message_order_rider_arrived": "Order rider arrvied"
    },
    "tw": {
        "shop.order.status.message_awaiting_vendor_confirmation": "\u8a02\u55ae\u6b63\u5728\u6e96\u5099\u4e2d\u3002",
        "shop.order.status.message_order_accepted_by_vendor": "\u9910\u5ef3\u5df2\u63a5\u53d7\u8a02\u55ae",
        "shop.order.status.message_order_picked_by_rider": "\u6b63\u524d\u5f80\u9818\u53d6\u8a02\u55ae\u3002",
        "shop.order.status.message_order_rider_arrived": "\u5373\u5c07\u62b5\u9054\u3002"
    }
}