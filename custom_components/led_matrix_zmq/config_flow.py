from typing import Any

import voluptuous as vol
from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult, OptionsFlowWithReload

from .api import LmzApi
from .const import CONF_DEFAULT_TRANSITION, CONF_NAME, CONF_URL, DEFAULT_TRANSITION, DOMAIN


class LmzConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self) -> None:
        self._name: str | None = None
        self._url: str | None = None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors = {}

        if user_input is not None:
            name = user_input[CONF_NAME].strip()
            url = user_input[CONF_URL].strip().removesuffix("/")

            for entry in self._async_current_entries():
                if entry.data[CONF_NAME] == name or entry.data[CONF_URL] == url:
                    return self.async_abort(reason="already_configured")

            if await self._assert_health(url):
                return self.async_create_entry(
                    title=name,
                    data=user_input,
                )
            else:
                errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="user",
            data_schema=self._get_data_schema(
                user_input.get(CONF_NAME) if user_input is not None else None,
                user_input.get(CONF_URL) if user_input is not None else None,
            ),
            errors=errors,
            last_step=True,
        )

    async def async_step_zeroconf(
        self, discovery_info: ZeroconfServiceInfo
    ) -> ConfigFlowResult:
        self._name = discovery_info.name.removesuffix(f".{discovery_info.type}")
        self._url = f"http://{discovery_info.ip_address}:{discovery_info.port}"

        await self.async_set_unique_id(self._url)
        self._abort_if_unique_id_configured()

        self.context["title_placeholders"] = {"name": self._name}

        return await self.async_step_zeroconf_confirm()

    async def async_step_zeroconf_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        assert self._name
        assert self._url

        errors = {}

        if user_input is not None:
            if await self._assert_health(self._url):
                return self.async_create_entry(
                    title=self._name,
                    data={CONF_NAME: self._name, CONF_URL: self._url},
                )
            else:
                errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="zeroconf_confirm",
            description_placeholders={"name": self._name, "url": self._url},
            errors=errors,
            last_step=True,
        )

    @staticmethod
    def async_get_options_flow(config_entry):
        return LmzOptionsFlowHandler()

    @staticmethod
    async def _assert_health(url: str) -> bool:
        return await LmzApi(url).assert_health()

    @staticmethod
    def _get_data_schema(name: str | None = None, url: str | None = None) -> vol.Schema:
        return vol.Schema(
            {
                vol.Required(CONF_NAME, default=name): str,
                vol.Required(CONF_URL, default=url): str,
            }
        )


class LmzOptionsFlowHandler(OptionsFlowWithReload):
    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=self._get_options_schema()
        )

    def _get_options_schema(self) -> vol.Schema:
        return vol.Schema({
            vol.Optional(
                CONF_DEFAULT_TRANSITION,
                default=self.config_entry.options.get(CONF_DEFAULT_TRANSITION, DEFAULT_TRANSITION)
            ): vol.All(vol.Coerce(float), vol.Range(min=0, max=30))
        })
