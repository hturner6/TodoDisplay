import os
import stat
import sys
from datetime import date, timedelta
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from taskFetcher.tickTick import apiTokenVerifier

SECRET = "tok-SECRET-123"


@pytest.fixture
def token_response(monkeypatch):
    monkeypatch.setenv("CLIENT_ID", "id")
    monkeypatch.setenv("CLIENT_SECRET", "secret")
    response = SimpleNamespace(ok=True, text="",
                               json=lambda: {"access_token": SECRET, "token_type": "bearer", "expires_in": 15552000})
    monkeypatch.setattr(apiTokenVerifier.requests, "post", lambda *args, **kwargs: response)
    return response


def test_verify_saves_the_token_and_keeps_the_other_keys(token_response, tmp_path):
    env = tmp_path / ".env"
    env.write_text("CLIENT_ID=id\nACCESS_TOKEN=old\nTASK_SOURCE=ticktick\n")

    apiTokenVerifier.verify_api_key("code", env_file=env)

    assert env.read_text() == f"CLIENT_ID=id\nACCESS_TOKEN={SECRET}\nTASK_SOURCE=ticktick\n"


def test_verify_adds_the_token_when_the_file_has_none(token_response, tmp_path):
    env = tmp_path / ".env"
    env.write_text("CLIENT_ID=id")

    apiTokenVerifier.verify_api_key("code", env_file=env)

    assert env.read_text() == f"CLIENT_ID=id\nACCESS_TOKEN={SECRET}\n"


def test_verify_creates_the_file_private(token_response, tmp_path):
    env = tmp_path / ".env"

    apiTokenVerifier.verify_api_key("code", env_file=env)

    assert stat.S_IMODE(os.stat(env).st_mode) == 0o600


def test_verify_makes_a_loose_file_private(token_response, tmp_path):
    env = tmp_path / ".env"
    env.write_text("CLIENT_ID=id\n")
    env.chmod(0o644)

    apiTokenVerifier.verify_api_key("code", env_file=env)

    assert stat.S_IMODE(os.stat(env).st_mode) == 0o600


def test_verify_does_not_print_the_token_but_shows_the_expiry(token_response, tmp_path, capsys):
    apiTokenVerifier.verify_api_key("code", env_file=tmp_path / ".env")

    out = capsys.readouterr().out
    assert SECRET not in out
    assert str(date.today() + timedelta(days=180)) in out


def test_a_failed_exchange_leaves_the_file_alone(token_response, tmp_path):
    token_response.ok = False
    token_response.text = "bad code"
    env = tmp_path / ".env"
    env.write_text("ACCESS_TOKEN=old\n")

    apiTokenVerifier.verify_api_key("code", env_file=env)

    assert env.read_text() == "ACCESS_TOKEN=old\n"


def test_a_response_without_a_token_leaves_the_file_alone(token_response, tmp_path, capsys):
    token_response.json = lambda: {"token_type": "bearer", "expires_in": 15552000}
    env = tmp_path / ".env"
    env.write_text("ACCESS_TOKEN=old\n")

    apiTokenVerifier.verify_api_key("code", env_file=env)

    assert env.read_text() == "ACCESS_TOKEN=old\n"
    assert "no access token" in capsys.readouterr().out.lower()


def test_a_response_without_an_expiry_does_not_invent_one(token_response, tmp_path, capsys):
    token_response.json = lambda: {"access_token": SECRET}
    env = tmp_path / ".env"

    apiTokenVerifier.verify_api_key("code", env_file=env)

    assert env.read_text() == f"ACCESS_TOKEN={SECRET}\n"
    assert str(date.today()) not in capsys.readouterr().out


def test_a_stale_loose_temp_file_does_not_loosen_the_env_file(token_response, tmp_path):
    env = tmp_path / ".env"
    stale = tmp_path / ".env.tmp"
    stale.write_text("")
    stale.chmod(0o644)

    apiTokenVerifier.verify_api_key("code", env_file=env)

    assert stat.S_IMODE(os.stat(env).st_mode) == 0o600


def test_authorize_url_uses_the_default_redirect_and_client():
    url = apiTokenVerifier.authorize_url(env={"CLIENT_ID": "id"})

    assert url == ("https://ticktick.com/oauth/authorize?client_id=id&scope=tasks:read&state=test"
                   "&redirect_uri=https://localhost:3000&response_type=code")


def test_the_redirect_can_be_set_in_env_and_is_sent_when_verifying(token_response, tmp_path, monkeypatch):
    monkeypatch.setenv("TICKTICK_REDIRECT_URI", "https://example.test/cb")
    sent = {}
    monkeypatch.setattr(apiTokenVerifier.requests, "post",
                        lambda *args, **kwargs: sent.update(kwargs["data"]) or token_response)

    apiTokenVerifier.verify_api_key("code", env_file=tmp_path / ".env")

    assert sent["redirect_uri"] == "https://example.test/cb"
    assert "redirect_uri=https://example.test/cb" in apiTokenVerifier.authorize_url(env=os.environ)
