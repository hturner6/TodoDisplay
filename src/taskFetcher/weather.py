from dataclasses import dataclass
from datetime import datetime, timedelta
import requests

FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
# The forecast is asked for at most this often, whether or not the last ask worked.
REFRESH_AFTER = timedelta(hours=1)
# A failing request keeps showing the last good weather this long, then hides it.
SHOW_FOR = timedelta(hours=3)
TIMEOUT_SECONDS = 10


CONDITIONS = ["clear", "partly", "cloud", "fog", "rain", "snow", "storm"]


@dataclass(frozen=True)
class Weather:
    temperature: int  # whole degrees Celsius
    condition: str  # one of CONDITIONS


def condition_for(code: int) -> str:
    """One of a few conditions for a WMO weather code, which is as much as a small glyph can say."""
    if code == 0:
        return "clear"
    if code in (1, 2):
        return "partly"
    if code == 3:
        return "cloud"
    if code in (45, 48):
        return "fog"
    if code in (51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82):
        return "rain"
    if code in (71, 73, 75, 77, 85, 86):
        return "snow"
    if code in (95, 96, 99):
        return "storm"
    raise ValueError("unknown weather code")


class WeatherService:
    """The current weather from Open-Meteo, which needs no key.

    Only the coordinates, rounded to one decimal (about 11 km), are sent. current(now) returns a
    Weather, or None when there is none to show: weather is a nicety, so a failure hides it
    rather than raising.
    """

    def __init__(self, latitude: float, longitude: float, get=requests.get):
        self._params = {
            "latitude": round(latitude, 1),
            "longitude": round(longitude, 1),
            "current": "temperature_2m,weather_code",
            "timezone": "auto",
        }
        self._get = get
        self._asked_at = None
        self._weather = None
        self._fetched_at = None

    @classmethod
    def from_env(cls, env) -> "WeatherService | None":
        """Set up from WEATHER_LATITUDE and WEATHER_LONGITUDE, or None when they are not both set."""
        latitude, longitude = env.get("WEATHER_LATITUDE"), env.get("WEATHER_LONGITUDE")
        if not latitude or not longitude:
            return None
        try:
            return cls(float(latitude), float(longitude))
        except ValueError:
            raise ValueError("WEATHER_LATITUDE and WEATHER_LONGITUDE must be numbers") from None

    def current(self, now: datetime):
        if self._asked_at is None or now - self._asked_at >= REFRESH_AFTER:
            self._asked_at = now
            try:
                self._weather = self._fetch()
                self._fetched_at = now
            except Exception as error:
                print(f"Could not fetch the weather: {type(error).__name__}")
        if self._weather is None or now - self._fetched_at >= SHOW_FOR:
            return None
        return self._weather

    def _fetch(self) -> Weather:
        response = self._get(FORECAST_URL, params=self._params, timeout=TIMEOUT_SECONDS)
        response.raise_for_status()
        current = response.json()["current"]
        return Weather(int(round(current["temperature_2m"])), condition_for(int(current["weather_code"])))

    def __repr__(self):
        # No coordinates: a repr ends up in logs and tracebacks.
        return "<weather service>"
