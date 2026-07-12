from __future__ import annotations

import time
from typing import Any

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_COLOR_TEMP_KELVIN,
    ATTR_TRANSITION,
    ColorMode,
    LightEntity,
    LightEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api import LmzApi, LmzApiError
from .const import CONF_DEFAULT_TRANSITION, DEFAULT_TRANSITION, DOMAIN

DEFAULT_BRIGHTNESS = 255
DEFAULT_COLOR_TEMP_KELVIN = 6500

# Slack added to the transition window during which polled values are ignored.
POLL_SUPPRESS_MARGIN = 0.5


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    url = entry.data["url"]
    api = LmzApi(async_get_clientsession(hass), url)

    async_add_entities(
        [
            LmzLight(
                api=api,
                name=entry.data["name"],
                url=url,
                default_transition=entry.options.get(
                    CONF_DEFAULT_TRANSITION, DEFAULT_TRANSITION
                ),
            )
        ],
        update_before_add=True,
    )


class LmzLight(LightEntity):
    _attr_has_entity_name = True
    _attr_name = None

    _attr_color_mode = ColorMode.COLOR_TEMP
    _attr_supported_color_modes = {ColorMode.COLOR_TEMP}
    _attr_supported_features = LightEntityFeature.TRANSITION
    _attr_min_color_temp_kelvin = 2000
    _attr_max_color_temp_kelvin = 6500

    def __init__(
        self, api: LmzApi, name: str, url: str, default_transition: float
    ) -> None:
        self._api = api
        self._default_transition = default_transition

        self._attr_unique_id = url
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, url)},
            name=name,
            manufacturer="led-matrix-zmq",
        )

        self._is_on: bool | None = None
        # Last known values, retained while off so turn_on can restore them.
        self._level: int | None = None
        self._kelvin: int | None = None
        self._ignore_polls_until = 0.0

    @property
    def is_on(self) -> bool | None:
        return self._is_on

    @property
    def brightness(self) -> int | None:
        return self._level if self._is_on else None

    @property
    def color_temp_kelvin(self) -> int | None:
        return self._kelvin if self._is_on else None

    def _transition(self, kwargs: dict[str, Any]) -> tuple[float, int]:
        """Return the transition in seconds and milliseconds."""
        seconds = float(kwargs.get(ATTR_TRANSITION, self._default_transition))
        return seconds, int(seconds * 1000)

    def _suppress_polls(self, seconds: float) -> None:
        self._ignore_polls_until = time.monotonic() + seconds + POLL_SUPPRESS_MARGIN

    async def async_update(self) -> None:
        try:
            level = await self._api.get_brightness()
            kelvin = await self._api.get_temperature()
        except LmzApiError:
            self._attr_available = False
            return

        self._attr_available = True

        # A poll landing mid-fade would report a value we're transitioning
        # away from, so keep the optimistic state until the fade has finished.
        if time.monotonic() < self._ignore_polls_until:
            return

        self._is_on = level > 0
        if level > 0:
            self._level = level
        if kelvin > 0:
            self._kelvin = kelvin

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the light on, restoring the last level unless one is given."""
        level = kwargs.get(ATTR_BRIGHTNESS)
        if level == 0:
            await self.async_turn_off(**kwargs)
            return
        if level is None:
            level = self._level if self._level is not None else DEFAULT_BRIGHTNESS

        kelvin = kwargs.get(ATTR_COLOR_TEMP_KELVIN)
        if kelvin is None:
            kelvin = self._kelvin if self._kelvin is not None else DEFAULT_COLOR_TEMP_KELVIN

        seconds, transition = self._transition(kwargs)

        try:
            # Temperature first, so the panel doesn't fade up in the old colour.
            if kelvin != self._kelvin or not self._is_on:
                await self._api.set_temperature(kelvin, transition)
                self._kelvin = kelvin

            await self._api.set_brightness(level, transition)
        except LmzApiError as err:
            raise HomeAssistantError(f"Failed to turn on {self.entity_id}") from err

        self._suppress_polls(seconds)
        self._level = level
        self._is_on = True

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the light off, keeping the current level for later restore."""
        if self._is_on is False:
            return

        seconds, transition = self._transition(kwargs)

        try:
            await self._api.set_brightness(0, transition)
        except LmzApiError as err:
            raise HomeAssistantError(f"Failed to turn off {self.entity_id}") from err

        self._suppress_polls(seconds)
        self._is_on = False
