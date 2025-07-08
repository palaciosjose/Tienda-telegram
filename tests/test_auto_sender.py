import importlib
import sys


def test_check_and_send_campaigns_returns_bool(tmp_path, monkeypatch):
    # Reload the real module in case previous tests inserted a stub
    sys.modules.pop('advertising_system.auto_sender', None)
    auto_sender = importlib.import_module('advertising_system.auto_sender')
    AutoSender = auto_sender.AutoSender

    config = {
        'db_path': str(tmp_path / 'db.db'),
        'telegram_tokens': ['t'],
        'whaticket_url': 'http://w',
        'whaticket_token': 'tok'
    }
    sender = AutoSender(config)

    # Avoid actual delays
    monkeypatch.setattr(auto_sender.time, 'sleep', lambda x: None)

    calls = []
    monkeypatch.setattr(sender, '_send_telegram_campaign', lambda *a, **k: calls.append('tg'))
    monkeypatch.setattr(sender, '_send_whatsapp_campaign', lambda *a, **k: calls.append('wa'))

    sender.scheduler.get_pending_sends = lambda: [(1, 2, None, None, None, None, 'telegram')]
    assert sender._check_and_send_campaigns() is True
    assert calls == ['tg']

    calls.clear()
    sender.scheduler.get_pending_sends = lambda: []
    assert sender._check_and_send_campaigns() is False
    assert calls == []
