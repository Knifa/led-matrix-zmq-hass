import voluptuous as vol

from typing import Any

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.components.zeroconf import ZeroconfServiceInfo

from .const import DOMAIN, CONF_NAME, CONF_HOST, CONF_PORT


DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NAME): str,
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_PORT, default=4200): int,
    }
)


class LmzConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self) -> None:
        self._name: str | None = None
        self._hostname: str | None = None
        self._port: int | None = None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            for entry in self._async_current_entries():
                if (
                    (
                        entry.data[CONF_HOST] == user_input[CONF_HOST]
                        and entry.data[CONF_PORT] == user_input[CONF_PORT]
                    )
                    or entry.data[CONF_NAME] == user_input[CONF_NAME]
                ):
                    return self.async_abort(reason="already_configured")

            return self.async_create_entry(
                title=user_input[CONF_NAME],
                data=user_input,
            )

        return self.async_show_form(step_id="user", data_schema=DATA_SCHEMA)

    async def async_step_zeroconf(
        self, discovery_info: ZeroconfServiceInfo
    ) -> ConfigFlowResult:
        self._hostname = discovery_info.hostname
        self._name = discovery_info.name
        self._port = discovery_info.port

        await self.async_set_unique_id(f"{self._hostname}:{self._port}")
        self._abort_if_unique_id_configured()

        self.context["title_placeholders"] = {"name": self._name}

        return await self.async_step_zeroconf_confirm()

    async def async_step_zeroconf_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        assert self._name
        assert self._hostname
        assert self._port

        if user_input is None:
            return self.async_show_form(
                step_id="zeroconf_confirm",
                description_placeholders={"name": self._name},

            )

        return self.async_create_entry(
            title=self._name,
            data={
                CONF_NAME: self._name,
                CONF_HOST: self._hostname,
                CONF_PORT: self._port,
            },
        )
