"""led-matrix-zmq integration."""

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import PLATFORMS


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    if entry.unique_id is None:
        # Entries created before unique IDs were introduced (pre-1.2.0) have
        # none set, so the config flow's duplicate-URL check silently misses
        # them. Backfill it here so dedup applies to every existing entry too.
        url = entry.data["url"].strip().removesuffix("/")
        hass.config_entries.async_update_entry(entry, unique_id=url)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    return True
