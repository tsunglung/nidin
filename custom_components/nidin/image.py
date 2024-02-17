"""This component provides basic support for Nidin Store Image."""

import logging
from datetime import datetime

from homeassistant.components.image import ImageEntity
from homeassistant.helpers.typing import UndefinedType
from homeassistant.const import (
    CONF_USERNAME
)

from .const import (
    DEFAULT_NAME,
    DOMAIN,
    NIDIN_DATA,
    NIDIN_COORDINATOR,
    NIDIN_ORDERS,
    MANUFACTURER
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config, async_add_devices):
    """Add a Image from a config entry."""

    if config.data.get(CONF_USERNAME, None):
        username = config.data[CONF_USERNAME]
    else:
        username = config.options[CONF_USERNAME]

    data = hass.data[DOMAIN][config.entry_id][NIDIN_DATA]
    data.expired = False
    data.ordered = False
    coordinator = hass.data[DOMAIN][config.entry_id][NIDIN_COORDINATOR]
    device = NidinImage(hass, data, username)

    async_add_devices([device], update_before_add=True)

class NidinImage(ImageEntity):
    """An implementation of a Nidin Store Image."""

    def __init__(self, hass, data, username):
        """Set initializing values."""
        super().__init__(hass)
        self._name = "{} {}".format(DEFAULT_NAME, username)
        self._attributes = {}
        self._username = username
        self._data = data
        self._attr_should_poll = True
        self.hass = hass

    @property
    def unique_id(self):
        """Return an unique ID."""
        uid = self._name.replace(" ", "_")
        return f"{uid}_store_image"

    @property
    def name(self):
        """Return the name of the sensor."""
        return f"{self._name} Store"

    @property
    def device_info(self):
        """Return Device Info."""
        return {
            'identifiers': {(DOMAIN, self._username)},
            'manufacturer': MANUFACTURER,
            'name': self._name
        }

    @property
    def state(self) -> str | None:
        """Return the state."""
        try:
            if self._username in self._data.orders:
                orders = self._data.orders[self._username].get(NIDIN_ORDERS, [])
                if len(orders) >= 1:
                    return orders[0]['brand_name'] + orders[0]['store_name']
        except:
            return None

    @property
    def image_url(self) -> str | None | UndefinedType:
        """Return URL of image."""
        try:
            if self._username in self._data.orders:
                orders = self._data.orders[self._username].get(NIDIN_ORDERS, [])
                if len(orders) >= 1:
                    return orders[0]['store_images']
        except:
            pass
        return "https://upload.wikimedia.org/wikipedia/commons/thumb/b/bc/Unknown_person.jpg/217px-Unknown_person.jpg"

