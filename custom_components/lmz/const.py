import logging

from typing import Final

from homeassistant.const import Platform


LOGGER: Final = logging.getLogger(__package__)

DOMAIN: Final = "lmz"
PLATFORMS: Final = [Platform.LIGHT]

CONF_NAME: Final = "name"
CONF_URL: Final = "url"
