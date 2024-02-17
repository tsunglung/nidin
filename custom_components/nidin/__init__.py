"""The nidin integration."""
import asyncio
import logging
from datetime import datetime

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.storage import Store
from homeassistant.const import CONF_USERNAME, CONF_PASSWORD, CONF_TOKEN

from .const import (
    CONF_TOKEN_TIMEOUT,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    NIDIN_COORDINATOR,
    NIDIN_DATA,
    NIDIN_NAME,
    PLATFORMS,
    UPDATE_LISTENER
)
from .data import nidinData

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry):
    """Set up a nidin entry."""

    username = _get_config_value(config_entry, CONF_USERNAME, "")
    login_info = {
        CONF_USERNAME: username,
        CONF_PASSWORD: _get_config_value(config_entry, CONF_PASSWORD, ""),
        CONF_TOKEN: _get_config_value(config_entry, CONF_TOKEN, "")
    }

    # migrate data (also after first setup) to options
    if config_entry.data:
        hass.config_entries.async_update_entry(
            config_entry, data={}, options=config_entry.data)

    session = async_get_clientsession(hass)

    store = Store(hass, 1, f"{DOMAIN}/tokens.json")
    data = await store.async_load() or None
    if data:
        tokens = data.get(username, {})
    token_timeout = int(tokens.get(CONF_TOKEN_TIMEOUT, 0))
    now = datetime.now().timestamp()
    _LOGGER.error(f"__init__ {int(token_timeout - now)} {tokens}")
    if (0 < int(token_timeout - now) < 3600):
        tokens[CONF_USERNAME] = username
        tokens[CONF_PASSWORD] = _get_config_value(config_entry, CONF_PASSWORD, "")
        nidin_data = nidinData(hass, session, tokens)
    else:
        nidin_data = nidinData(hass, session, login_info)

    nidin_coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=f"nidin for {username}",
        update_method=nidin_data.async_update_data,
        update_interval=DEFAULT_SCAN_INTERVAL,
    )

    nidin_hass_data = hass.data.setdefault(DOMAIN, {})
    nidin_hass_data[config_entry.entry_id] = {
        NIDIN_DATA: nidin_data,
        NIDIN_COORDINATOR: nidin_coordinator,
        NIDIN_NAME: username,
    }
    nidin_data.expired = False
    nidin_data.ordered = True

    # Fetch initial data so we have data when entities subscribe
    await nidin_coordinator.async_refresh()
    if nidin_data.username is None:
        raise ConfigEntryNotReady()

    for platform in PLATFORMS:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(config_entry, platform)
        )

    update_listener = config_entry.add_update_listener(async_update_options)
    hass.data[DOMAIN][config_entry.entry_id][UPDATE_LISTENER] = update_listener

    return True


async def async_update_options(hass: HomeAssistant, config_entry: ConfigEntry):
    """Update options."""
    await hass.config_entries.async_reload(config_entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry):
    """Unload a config entry."""
    unload_ok = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(config_entry, platform)
                for platform in PLATFORMS
            ]
        )
    )
    if unload_ok:
        update_listener = hass.data[DOMAIN][config_entry.entry_id][UPDATE_LISTENER]
        update_listener()
        hass.data[DOMAIN].pop(config_entry.entry_id)
        if not hass.data[DOMAIN]:
            hass.data.pop(DOMAIN)
    return unload_ok


def _get_config_value(config_entry, key, default):
    if config_entry.options:
        return config_entry.options.get(key, default)
    return config_entry.data.get(key, default)
