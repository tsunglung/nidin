"""Config flow to configure nidin component."""
import logging
from typing import Optional
import voluptuous as vol

from homeassistant import core, exceptions
from homeassistant.config_entries import (
    CONN_CLASS_CLOUD_POLL,
    ConfigFlow,
    OptionsFlow,
    ConfigEntry
    )
from homeassistant.const import CONF_USERNAME, CONF_PASSWORD, CONF_TOKEN
from homeassistant.core import callback
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    DOMAIN
)
from .data import nidinData

ACTIONS = {"cloud": "Add Nidin Account", "token": "Add Nidin by Tokens"}

_LOGGER = logging.getLogger(__name__)

async def validate_input(hass: core.HomeAssistant, data):
    """Validate that the user input allows us to connect to DataPoint.

    Data has the keys from DATA_SCHEMA with values provided by the user.
    """

    session = async_get_clientsession(hass)
    login_info = {
        CONF_USERNAME: data[CONF_USERNAME],
        CONF_PASSWORD: data.get(CONF_PASSWORD, ""),
        CONF_TOKEN: data.get(CONF_TOKEN, "")
    }

    nidin_data = nidinData(hass, session, login_info)
    nidin_data.expired = False
    nidin_data.ordered = True
    await nidin_data.async_update_data()
    if nidin_data.username is None:
        raise CannotConnect()

    return {CONF_USERNAME: nidin_data.username}

class nidinFlowHandler(ConfigFlow, domain=DOMAIN):
    """Handle a nidin config flow."""

    VERSION = 1
    CONNECTION_CLASS = CONN_CLASS_CLOUD_POLL

    def __init__(self):
        """Initialize flow."""
        self._username: Optional[str] = None
        self._password: Optional[str] = None

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry):
        """ get option flow """
        return OptionsFlowHandler(config_entry)

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            if user_input["action"] == CONF_TOKEN:
                return await self.async_step_token()
            return await self.async_step_cloud()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {vol.Required("action", default="cloud"): vol.In(ACTIONS)}
            ),
        )

    async def async_step_cloud(
        self,
        user_input: Optional[ConfigType] = None
    ):
        """Handle a flow initialized by the user."""
        errors = {}
        if user_input is not None:
            await self.async_set_unique_id(
                f"{user_input[CONF_USERNAME]}"
            )
            self._abort_if_unique_id_configured()

            try:
                info = await validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                user_input[CONF_USERNAME] = info[CONF_USERNAME]
                return self.async_create_entry(
                    title=user_input[CONF_USERNAME], data=user_input
                )

        data_schema = vol.Schema(
            {
                vol.Required(CONF_USERNAME): str,
                vol.Required(CONF_PASSWORD): str
            }
        )

        return self.async_show_form(
            step_id="cloud", data_schema=data_schema, errors=errors
        )

    async def async_step_token(self, user_input: dict = None, error=None):

        errors = {}
        if user_input is not None:
            await self.async_set_unique_id(
                f"{user_input[CONF_USERNAME]}"
            )
            self._abort_if_unique_id_configured()

            try:
                info = await validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                user_input[CONF_USERNAME] = info[CONF_USERNAME]
                return self.async_create_entry(
                    title=user_input[CONF_USERNAME], data=user_input
                )

        data_schema = vol.Schema(
            {
                vol.Required(CONF_USERNAME): str,
                vol.Required(CONF_TOKEN): str
            }
        )

        return self.async_show_form(
            step_id=CONF_TOKEN, data_schema=data_schema, errors=errors
        )

    @property
    def _name(self):
        # pylint: disable=no-member
        # https://github.com/PyCQA/pylint/issues/3167
        return self.context.get(CONF_USERNAME)

    @_name.setter
    def _name(self, value):
        # pylint: disable=no-member
        # https://github.com/PyCQA/pylint/issues/3167
        self.context[CONF_USERNAME] = value
        self.context["title_placeholders"] = {"name": self._username}


class OptionsFlowHandler(OptionsFlow):
    # pylint: disable=too-few-public-methods
    """Handle options flow changes."""
    _username = None
    _password = None
    _token = None

    def __init__(self, config_entry):
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        if CONF_TOKEN in self.config_entry.options:
            return await self.async_step_token()
        return await self.async_step_cloud()

    async def async_step_cloud(self, user_input=None):
        """Manage the options."""
        errors = {}
        if user_input is not None:
            user_input[CONF_USERNAME] = self._username
            try:
                info = await validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                user_input[CONF_USERNAME] = info[CONF_USERNAME]
                return self.async_create_entry(
                    title=user_input[CONF_USERNAME], data=user_input
                )

        self._username = self.config_entry.options.get(CONF_USERNAME, '')
        self._password = self.config_entry.options.get(CONF_PASSWORD, '')

        return self.async_show_form(
            step_id="cloud",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_PASSWORD, default=self._password): str
                }
            ),
            errors=errors
        )

    async def async_step_token(self, user_input=None):
        """Manage the options."""
        errors = {}
        if user_input is not None:
            user_input[CONF_USERNAME] = self._username
            try:
                info = await validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                user_input[CONF_USERNAME] = info[CONF_USERNAME]
                return self.async_create_entry(
                    title=user_input[CONF_USERNAME], data=user_input
                )

        self._username = self.config_entry.options.get(CONF_USERNAME, '')
        self._token = self.config_entry.options.get(CONF_TOKEN, '')

        return self.async_show_form(
            step_id=CONF_TOKEN,
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_TOKEN, default=self._token): str
                }
            ),
            errors=errors
        )

class CannotConnect(exceptions.HomeAssistantError):
    """Error to indicate we cannot connect."""
