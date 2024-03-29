"""Support for the nidin."""
import logging
from typing import Callable
from http import HTTPStatus
from datetime import datetime 
import json

from homeassistant.core import HomeAssistant, callback
from homeassistant.config_entries import ConfigEntry
from homeassistant.components.sensor import SensorEntity
from homeassistant.const import (
    ATTR_ATTRIBUTION,
    CONF_USERNAME
)

from .const import (
    ATTRIBUTION,
    ATTR_ETA,
    ATTR_RESTAURANT_NAME,
    ATTR_COURIER_NAME,
    ATTR_COURIER_PHONE,
    ATTR_COURIER_DESCRIPTION,
    ATTR_TITLE_SUMMARY,
    ATTR_SUBTITLE_SUMMARY,
    ATTR_LATITUDE,
    ATTR_LONGITUDE,
    ATTR_HTTPS_RESULT,
    ATTR_LIST,
    DEFAULT_NAME,
    DOMAIN,
    NIDIN_DATA,
    NIDIN_COORDINATOR,
    NIDIN_ORDERS,
    LANGUAGE_TRANSLATIONS,
    MANUFACTURER
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, config: ConfigEntry, async_add_devices: Callable
) -> None:
    """Set up the Nidin Sensor from config."""

    if config.data.get(CONF_USERNAME, None):
        username = config.data[CONF_USERNAME]
    else:
        username = config.options[CONF_USERNAME]

    data = hass.data[DOMAIN][config.entry_id][NIDIN_DATA]
    data.expired = False
    data.ordered = False
    coordinator = hass.data[DOMAIN][config.entry_id][NIDIN_COORDINATOR]
    device = NidinSensor(username, data, coordinator)

    async_add_devices([device], update_before_add=True)


class NidinSensor(SensorEntity):
    """Implementation of a Nidin sensor."""

    def __init__(self, username, data, coordinator):
        """Initialize the sensor."""
        self._state = None
        self._data = data
        self._coordinator = coordinator
        self._attributes = {}
        self._attr_value = {}
        self._name = "{} {}".format(DEFAULT_NAME, username)
        self._username = username

    @property
    def unique_id(self):
        """Return an unique ID."""
        uid = self._name.replace(" ", "_")
        return f"{uid}_orders"

    @property
    def name(self):
        """Return the name of the sensor."""
        return f"{self._name} Orders"

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def icon(self):
        """Icon to use in the frontend, if any."""
        return "mdi:food-variant"

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return None

    @property
    def extra_state_attributes(self):
        """Return extra attributes."""
        self._attributes = {}
        self._attributes[ATTR_ATTRIBUTION] = ATTRIBUTION
        for k, _ in self._attr_value.items():
            self._attributes[k] = self._attr_value[k]
        return self._attributes

    @property
    def device_info(self):
        return {
            'identifiers': {(DOMAIN, self._username)},
            'manufacturer': MANUFACTURER,
            'name': self._name
        }

    async def async_added_to_hass(self) -> None:
        """Set up a listener and load data."""
        self.async_on_remove(
            self._coordinator.async_add_listener(self._update_callback)
        )
        self._update_callback()

    @callback
    def _update_callback(self) -> None:
        """Load data from integration."""
        self.async_write_ha_state()

    def _get_eta(self, target_time: str) -> str:
        """ get eta time to target time """
        try:
            now = datetime.now()
            target = datetime.strptime(target_time, "%Y-%m-%d %H:%M:%S")
            eta = str(target - now) if (target - now) > datetime.timedelta(seconds=1) else "00:00:00.000"
        except:
            _LOGGER.error("Convert eta filed")
            eta = "00:00:00.000"
        return eta

    async def async_update(self):
        """Schedule a custom update via the common entity update service."""
        await self._coordinator.async_request_refresh()

        self._attr_value = {}
        for i in ATTR_LIST:
            self._attr_value[i] = ''
        try:
            if self._username in self._data.orders:
                orders = self._data.orders[self._username].get(NIDIN_ORDERS, [])
                self._state = len(orders)
                index = 0
                if len(orders) >= 1:
                    translations = LANGUAGE_TRANSLATIONS["tw"]

                    for order in orders:

                        if index == 0:
                            if "delivery_reserv_time" in order:
                                self._attr_value[ATTR_ETA] = self._get_eta(
                                    order['delivery_reserv_date'] + " " + order['delivery_reserv_time'])
                            if "status_msg" in order:
                                self._attr_value[ATTR_TITLE_SUMMARY] = order['status_msg']
                            if "process_msg" in order:
                                self._attr_value[ATTR_SUBTITLE_SUMMARY] = order['process_msg'] if order['process_msg'] != 'None' else "Unkown"
                            if "brand_name" in order:
                                self._attr_value[ATTR_RESTAURANT_NAME] = order['brand_name'] + order['store_name']
                        if index >= 1:
                            if "delivery_reserv_time" in order:
                                self._attr_value[f"{ATTR_ETA}_{index + 1}"] = self._get_eta(
                                    order['delivery_reserv_date'] + " " + order['delivery_reserv_time'])
                            if "status_msg" in order:
                                self._attr_value[f"{ATTR_TITLE_SUMMARY}_{index + 1}"] = order['status_msg']
                            if "process_msg" in order:
                                self._attr_value[f"{ATTR_SUBTITLE_SUMMARY}_{index + 1}"] = order['process_msg']
                            if "brand_name" in order:
                                self._attr_value[f"{ATTR_RESTAURANT_NAME}_{index + 1}"] = order['brand_name'] + order['store_name']

                        index = index + 1

        except Exception as e:
            _LOGGER.error(f"paring orders occured exception {e}")
            self._state = 0

        self._attr_value[ATTR_HTTPS_RESULT] = self._data.orders[self._username].get(
            ATTR_HTTPS_RESULT, 'Unknown')
        if self._attr_value[ATTR_HTTPS_RESULT] == HTTPStatus.FORBIDDEN:
            self._state = None

        return