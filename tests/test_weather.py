import sys
from datetime import datetime, timedelta
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from taskFetcher.weather import Weather, WeatherService

NOW = datetime(2026, 10, 27, 9, 0)


class FakeResponse:
    def __init__(self, body, status=200):
        self._body = body
        self.status_code = status

    def raise_for_status(self):
        if self.status_code >= 400:
            raise OSError(f"HTTP {self.status_code}")

    def json(self):
        return self._body


class FakeGet:
    """Stands in for requests.get: records each call, answers with whatever is set."""

    def __init__(self, temperature=11.8, code=0):
        self.calls = []
        self.temperature, self.code = temperature, code
        self.fail = False

    def __call__(self, url, params=None, timeout=None):
        self.calls.append((url, params, timeout))
        if self.fail:
            raise ConnectionError("no network")
        return FakeResponse({"current": {"temperature_2m": self.temperature, "weather_code": self.code}})


def service(get, **kwargs):
    return WeatherService(51.4928, -0.1029, get=get, **kwargs)


def test_the_weather_is_the_current_temperature_rounded_and_a_condition():
    assert service(FakeGet(temperature=11.8, code=0)).current(NOW) == Weather(12, "clear")


@pytest.mark.parametrize("code, condition", [
    (0, "clear"), (1, "partly"), (2, "partly"), (3, "cloud"), (45, "fog"), (48, "fog"), (53, "rain"),
    (65, "rain"), (81, "rain"), (73, "snow"), (86, "snow"), (96, "storm"), (99, "storm"),
])
def test_wmo_codes_become_a_few_conditions(code, condition):
    assert service(FakeGet(code=code)).current(NOW).condition == condition


def test_a_temperature_below_zero_keeps_its_sign_and_zero_is_never_negative():
    assert service(FakeGet(temperature=-3.4)).current(NOW).temperature == -3
    assert service(FakeGet(temperature=-0.2)).current(NOW).temperature == 0


def test_only_coordinates_rounded_to_one_decimal_leave_the_device():
    get = FakeGet()
    service(get).current(NOW)

    (_, params, _), = get.calls
    assert (params["latitude"], params["longitude"]) == (51.5, -0.1)


def test_the_forecast_is_fetched_at_most_once_an_hour():
    get = FakeGet()
    weather = service(get)

    weather.current(NOW)
    weather.current(NOW + timedelta(minutes=59))
    assert len(get.calls) == 1

    weather.current(NOW + timedelta(hours=1))
    assert len(get.calls) == 2


def test_a_failing_request_has_a_timeout_and_hides_the_weather():
    get = FakeGet()
    get.fail = True

    assert service(get).current(NOW) is None
    assert get.calls[0][2] is not None


def test_a_failure_after_a_good_fetch_keeps_the_last_weather_for_a_while_then_hides_it():
    get = FakeGet(temperature=9.0, code=3)
    weather = service(get)
    weather.current(NOW)
    get.fail = True

    assert weather.current(NOW + timedelta(hours=1)) == Weather(9, "cloud")
    assert weather.current(NOW + timedelta(hours=4)) is None


def test_a_failing_fetch_is_not_retried_on_every_refresh():
    get = FakeGet()
    get.fail = True
    weather = service(get)

    weather.current(NOW)
    weather.current(NOW + timedelta(minutes=30))

    assert len(get.calls) == 1


def test_an_unreadable_reply_hides_the_weather():
    def odd(url, params=None, timeout=None):
        return FakeResponse({"error": True})

    assert service(odd).current(NOW) is None


def test_the_service_is_off_without_coordinates():
    assert WeatherService.from_env({}) is None
    assert WeatherService.from_env({"WEATHER_LATITUDE": "51.5"}) is None
    assert WeatherService.from_env({"WEATHER_LATITUDE": "51.5", "WEATHER_LONGITUDE": "-0.1"}) is not None


def test_unreadable_coordinates_are_an_error_not_a_silent_default():
    with pytest.raises(ValueError):
        WeatherService.from_env({"WEATHER_LATITUDE": "north", "WEATHER_LONGITUDE": "-0.1"})


def test_a_repr_never_shows_the_coordinates():
    assert "51" not in repr(service(FakeGet()))
