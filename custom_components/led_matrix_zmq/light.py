from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.components.light import LightEntity, ColorMode
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api import LmzApi


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    name = entry.data["name"]
    url = entry.data["url"]

    async_add_entities(
        [
            LmzLight(
                api=LmzApi(url),
                name=name,
                url=url,
            ),
        ]
    )


class LmzLight(LightEntity):
    _attr_has_entity_name = True

    _attr_color_mode = ColorMode.COLOR_TEMP
    _attr_supported_color_modes = {ColorMode.COLOR_TEMP}
    _attr_min_color_temp_kelvin = 2000
    _attr_max_color_temp_kelvin = 6500

    def __init__(self, name: str, url: str, api: LmzApi):
        self._api = api

        self._attr_unique_id = url
        self._attr_name = name

        self._available = True
        self._brightness: int | None = None
        self._brightness_before_off: int | None = None
        self._color_temp_kelvin: int | None = None

    async def async_update(self) -> None:
        self._available = await self._api.assert_health()
        if not self._available:
            return

        self._brightness = await self._api.get_brightness()
        self._color_temp_kelvin = await self._api.get_temperature()

    async def async_turn_on(self, **kwargs) -> None:
        brightness: int | None = kwargs.get("brightness")
        if not self.is_on:
            brightness = brightness or self._brightness_before_off or 255
            self._brightness_before_off = None

        color_temp_kelvin = kwargs.get("color_temp_kelvin") or self._color_temp_kelvin

        if brightness is not None:
            await self._api.set_brightness(brightness)
            self._brightness = brightness

        if color_temp_kelvin is not None:
            await self._api.set_temperature(color_temp_kelvin)
            self._color_temp_kelvin = color_temp_kelvin

    async def async_turn_off(self, **kwargs) -> None:
        self._brightness_before_off = self._brightness
        await self._api.set_brightness(0)

    @property
    def available(self) -> bool:
        return self._available

    @property
    def brightness(self) -> int | None:
        return self._brightness

    @property
    def color_temp_kelvin(self) -> int | None:
        return self._color_temp_kelvin

    @property
    def is_on(self) -> bool | None:
        return self._brightness is not None and self._brightness > 0
