import logging

from typing import Final

from homeassistant.const import Platform


LOGGER: Final = logging.getLogger(__package__)

DOMAIN: Final = "led_matrix_zmq"
PLATFORMS: Final = [Platform.LIGHT]

CONF_NAME: Final = "name"
CONF_URL: Final = "url"
