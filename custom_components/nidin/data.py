"""Common nidin Data class used by both sensor and entity."""

import logging
from datetime import datetime, timezone
import json
import base64
from http import HTTPStatus
import requests
from aiohttp.hdrs import (
    ACCEPT,
    AUTHORIZATION,
    CONTENT_TYPE,
    METH_GET,
    METH_POST,
    USER_AGENT 
)

from homeassistant.helpers.storage import Store
from homeassistant.const import (
    CONF_USERNAME,
    CONF_PASSWORD,
    CONF_TOKEN,
    CONTENT_TYPE_JSON,
    EVENT_HOMEASSISTANT_STOP
)
from .const import (
    ATTR_HTTPS_RESULT,
    BASE_URL,
    CONF_TOKEN_TIMEOUT,
    CONF_USER_ID,
    DEFAULT_ACCESS_TOKEN,
    DEFAULT_DEVICE_ID,
    DEFAULT_IDENTITY_1,
    DEFAULT_IDENTITY_2,
    DOMAIN,
    HA_USER_AGENT,
    REQUEST_TIMEOUT,
    NIDIN_ORDERS
)

_LOGGER = logging.getLogger(__name__)


class nidinData():
    """Class for handling the data retrieval."""

    def __init__(self, hass, session, login_info):
        """Initialize the data object."""
        self._hass = hass
        self._session = session
        self._username = login_info[CONF_USERNAME]
        self._password = login_info[CONF_PASSWORD]
        self._user_id = None
        self.orders = {}
        self.username = None
        self.expired = False
        self.ordered = False
        self.new_order = False
        self.uri = BASE_URL
        self.orders[login_info[CONF_USERNAME]] = {}
        self._last_check = datetime.now().timestamp()
        self._token = login_info[CONF_TOKEN]
        self._token_timeout = 0

    async def async_login(self):
        """ do login """

        now = datetime.now().timestamp()
        headers = {
            USER_AGENT: HA_USER_AGENT,
            CONTENT_TYPE: CONTENT_TYPE_JSON,
            ACCEPT: 'application/json, text/plain, */*'
        }
        if len(self._password) >= 1:
            payload = {
                "type": 1,
                "account": self._username,
                "password": self._password,
                "device_id": DEFAULT_DEVICE_ID,
                "identity": DEFAULT_IDENTITY_1
            }
        else:
            payload = {
                "type": 2,
                "device_id": DEFAULT_DEVICE_ID,
                "identity": DEFAULT_IDENTITY_2,
                "access_token": DEFAULT_ACCESS_TOKEN
            }
            params = {'_': int(now * 100)}

        try:
            if payload["type"] == 1:
                response = await self._session.request(
                    METH_POST,
                    url=f"{BASE_URL}/user/loginWeb",
                    data=json.dumps(payload).replace(" ", ""),
                    #json=payload,
                    headers=headers,
                    timeout=REQUEST_TIMEOUT
                )
            else:
                response = await self._session.request(
                    METH_POST,
                    url=f"{BASE_URL}/user/loginWeb",
                    data=json.dumps(payload),
                    headers=headers,
                    params=params,
                    timeout=REQUEST_TIMEOUT
                )

        except requests.exceptions.RequestException:
            _LOGGER.error("Failed fetching data for %s", self._username)
            return

        if response.status == HTTPStatus.OK:
            data = await response.json()
            token = data[CONF_TOKEN]
            user_id = str(data[CONF_USER_ID])
            raw_data = token.split(".")[1]
            if len(raw_data) >= 1:
                if raw_data[-1] != "=":
                    raw_data = raw_data + "="
                    try:
                        info = json.loads(base64.b64decode(raw_data).decode("utf8"))
                        self._token_timeout = info.get("exp", str(int(now + 60 * 60 * 24 * 30)))
                    except:
                        self._token_timeout = str(int(now + 60 * 60 * 24 * 30))
                    self._token = token
                    self._user_id = user_id

        else:
            info = ""
            self.orders[self._username][ATTR_HTTPS_RESULT] = response.status
            if response.status == HTTPStatus.FORBIDDEN:
                info = " Token is expired"
            _LOGGER.error(
                "Failed fetching data for %s (HTTP Status Code = %d).%s",
                self._username,
                response.status,
                info
            )

    async def async_refresh_token(self):
        """ do refresh token """


    async def async_load_tokens(self) -> dict:
        """
        Update tokens in .storage
        """
        if self._token is not None:
            return {
                CONF_TOKEN: self._token,
                CONF_TOKEN_TIMEOUT: self._token_timeout,
                CONF_USER_ID: self._user_id
            }

        default = {
                CONF_TOKEN: "",
                CONF_TOKEN_TIMEOUT: "1577836800",
                CONF_USER_ID: ""
            }
        store = Store(self._hass, 1, f"{DOMAIN}/tokens.json")
        data = await store.async_load() or None
        if not data:
            # force login
            return default
        tokens = data.get(self._username, default)

        # noinspection PyUnusedLocal
        async def stop(*args):
            # save devices data to .storage
            tokens = {
                CONF_TOKEN: self._token,
                CONF_TOKEN_TIMEOUT: self._token_timeout,
                CONF_USER_ID: self._user_id
            }
            data[self._username] = tokens

            await store.async_save(data)

        self._hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, stop)
        return tokens

    async def async_store_tokens(self, tokens: dict):
        """
        Update tokens in .storage
        """
        store = Store(self._hass, 1, f"{DOMAIN}/tokens.json")
        data = await store.async_load() or {}
        data[self._username] = tokens

        await store.async_save(data)

    async def async_check_tokens(self):
        """ check the tokens if valid """
        tokens = await self.async_load_tokens()

        self._token = tokens.get(CONF_TOKEN, "")
        token_timeout = str(tokens.get(CONF_TOKEN_TIMEOUT, 0))

        if not isinstance(token_timeout, str):
            token_timeout = "1577836800"

        now = datetime.now().timestamp()

        self._token_timeout = token_timeout = int(token_timeout)

        timeout = token_timeout

        if ((int(timeout - now) < 86400)):
            await self.async_login()
            if len(self._token) < 1:
                return False

            await self.async_store_tokens({
                CONF_TOKEN: self._token,
                CONF_TOKEN_TIMEOUT: self._token_timeout,
                CONF_USER_ID: self._user_id
            })

        self.username = self._username
        return True

    async def async_check_order_history(self):
        """ check the order history """

        headers = {
            USER_AGENT: HA_USER_AGENT,
            CONTENT_TYPE: CONTENT_TYPE_JSON,
            ACCEPT: 'application/json, text/plain, */*',
            'MC-API-Token': self._token,
            'MC-API-USER': self._user_id
        }

        try:
            response = await self._session.request(
                METH_GET,
                url=f"{BASE_URL}/order/list?status[]=100&status[]=110&status[]=99&status[]=120&status[]=121&status[]=122&status[]=130&status[]=140&status[]=31&status[]=35&status[]=39&status[]=38&sort[]=order_time%20DESC&page=1&count=20",
                headers=headers,
                timeout=REQUEST_TIMEOUT
            )

        except requests.exceptions.RequestException:
            _LOGGER.error("Failed fetching data for %s", self._username)
            return

        self.orders[self._username][NIDIN_ORDERS] = []
        if response.status == HTTPStatus.OK:
            try:
                res = await response.json()
            except:
                res = {"data": response.text}

            for order in res.get("order_list", []):
                if ((order['status'] == 130 and order['special_status'] == 13009) or
                        order['status'] == 99):
                    continue
                self.orders[self._username][NIDIN_ORDERS].append(order)
            self.orders[self._username][ATTR_HTTPS_RESULT] = response.status
        else:
            info = ""
            self.orders[self._username][ATTR_HTTPS_RESULT] = response.status
            if response.status == HTTPStatus.FORBIDDEN:
                info = " Token is expired"
            _LOGGER.error(
                "Failed fetching data for %s (HTTP Status Code = %d).%s",
                self._username,
                response.status,
                info
            )

        return self.orders[self._username][NIDIN_ORDERS]


    async def async_update_data(self):
        """Get the latest data for nidin from REST service."""

        force_update = False
        now = datetime.now().timestamp()

        if (int(now - self._last_check) > 300):
            force_update = True
            self._last_check = now

        if not self.expired and (self.ordered or force_update):

            ret = await self.async_check_tokens()
            if not ret:
                return self

            data = await self.async_check_order_history()
            if len(data) >= 1:
                self.new_order = True
                self.ordered = True
            else:
                self.new_order = False
                self.ordered = False

        return self