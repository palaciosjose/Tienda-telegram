import json
from tests.test_shop_info import setup_main
import webhook_server


def setup_app(monkeypatch, tmp_path):
    dop, main, calls, bot = setup_main(monkeypatch, tmp_path)
    monkeypatch.setattr(main.config, "WEBHOOK_SECRET_TOKEN", "secret")
    # Reset metrics for each test
    monkeypatch.setattr(webhook_server, "metrics", {"requests_total": 0, "updates_total": 0}, raising=False)
    app = webhook_server.create_app()
    return app, webhook_server, calls, bot, main


def test_valid_update(monkeypatch, tmp_path):
    app, server, calls, bot, main = setup_app(monkeypatch, tmp_path)
    monkeypatch.setattr(bot, "process_new_updates", lambda updates: calls.append(("process_new_updates", updates)))
    client = app.test_client()
    update = {"update_id": 1}
    before = server.metrics.copy()
    resp = client.post(main.config.WEBHOOK_PATH, json=update, headers={"X-Telegram-Bot-Api-Secret-Token": "secret"})
    assert resp.status_code == 200
    assert any(c[0] == "process_new_updates" for c in calls)
    assert server.metrics["updates_total"] == before["updates_total"] + 1
    assert server.metrics["requests_total"] == before["requests_total"] + 1


def test_invalid_secret(monkeypatch, tmp_path):
    app, server, calls, bot, main = setup_app(monkeypatch, tmp_path)
    monkeypatch.setattr(bot, "process_new_updates", lambda updates: calls.append(("process_new_updates", updates)))
    client = app.test_client()
    update = {"update_id": 1}
    before = server.metrics.copy()
    resp = client.post(main.config.WEBHOOK_PATH, json=update, headers={"X-Telegram-Bot-Api-Secret-Token": "bad"})
    assert resp.status_code == 403
    assert not any(c[0] == "process_new_updates" for c in calls)
    assert server.metrics["updates_total"] == before["updates_total"]
    assert server.metrics["requests_total"] == before["requests_total"] + 1


def test_invalid_content_type(monkeypatch, tmp_path):
    app, server, calls, bot, main = setup_app(monkeypatch, tmp_path)
    monkeypatch.setattr(bot, "process_new_updates", lambda updates: calls.append(("process_new_updates", updates)))
    client = app.test_client()
    before = server.metrics.copy()
    resp = client.post(main.config.WEBHOOK_PATH, data="notjson", headers={"X-Telegram-Bot-Api-Secret-Token": "secret"})
    assert resp.status_code == 415
    assert not any(c[0] == "process_new_updates" for c in calls)
    assert server.metrics["updates_total"] == before["updates_total"]
    assert server.metrics["requests_total"] == before["requests_total"] + 1
