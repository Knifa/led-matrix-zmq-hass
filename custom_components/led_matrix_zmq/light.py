from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.components.light import LightEntity
from homeassistant.helpers.entity_platform import AddEntitiesCallback


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    async_add_entities([LmzLight(entry.data["name"], entry.data["host"])])


class LmzLight(LightEntity):
    _attr_has_entity_name = True

    def __init__(self, name: str, host: str):
        self._name = name
        self._host = host

        self._attr_unique_id = host
        self._attr_name = name
