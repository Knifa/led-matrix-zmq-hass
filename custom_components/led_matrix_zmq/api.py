import aiohttp


class LmzApi:
    def __init__(self, url: str):
        self._session: aiohttp.ClientSession = aiohttp.ClientSession(base_url=url)

    async def get_brightness(self) -> int:
        async with self._session.get("/brightness") as res:
            res.raise_for_status()
            data = await res.json()
            return data["brightness"]

    async def set_brightness(self, brightness: int, transition: int = 0) -> None:
        async with self._session.post(
            "/brightness", json={"brightness": brightness, "transition": transition}
        ) as res:
            res.raise_for_status()

    async def get_temperature(self) -> int:
        async with self._session.get("/temperature") as res:
            res.raise_for_status()
            data = await res.json()
            return data["temperature"]

    async def set_temperature(self, temperature: int, transition: int = 0) -> None:
        async with self._session.post(
            "/temperature", json={"temperature": temperature, "transition": transition}
        ) as res:
            res.raise_for_status()

    async def assert_health(self) -> bool:
        try:
            async with self._session.get("/healthcheck") as res:
                res.raise_for_status()
                return True
        except aiohttp.ClientError:
            return False
