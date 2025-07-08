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


def test_check_and_send_campaigns_with_mocked_dependencies(monkeypatch):
    sys.modules.pop('advertising_system.auto_sender', None)
    auto_sender = importlib.import_module('advertising_system.auto_sender')

    class DummyScheduler:
        def __init__(self, db_path):
            pass

        def get_pending_sends(self):
            return [(1, 2, None, None, None, None, 'telegram,whatsapp')]

        def update_next_send(self, *a):
            pass

    class DummyRateLimiter:
        def __init__(self, db_path):
            pass

    class DummyStats:
        def __init__(self, db_path):
            pass

    monkeypatch.setattr(auto_sender, 'CampaignScheduler', DummyScheduler)
    monkeypatch.setattr(auto_sender, 'IntelligentRateLimiter', DummyRateLimiter)
    monkeypatch.setattr(auto_sender, 'StatisticsManager', DummyStats)
    monkeypatch.setattr(auto_sender, 'TelegramMultiBot', lambda *a, **k: object())
    monkeypatch.setattr(auto_sender, 'WHATicketAPI', lambda *a, **k: object())

    AutoSender = auto_sender.AutoSender

    config = {
        'db_path': 'db',
        'telegram_tokens': ['t'],
        'whaticket_url': 'http://w',
        'whaticket_token': 'tok'
    }
    sender = AutoSender(config)

    monkeypatch.setattr(auto_sender.time, 'sleep', lambda x: None)
    calls = []
    monkeypatch.setattr(sender, '_send_telegram_campaign', lambda *a, **k: calls.append('tg'))
    monkeypatch.setattr(sender, '_send_whatsapp_campaign', lambda *a, **k: calls.append('wa'))

    assert sender._check_and_send_campaigns() is True
    assert calls == ['tg', 'wa']

    calls.clear()
    sender.scheduler.get_pending_sends = lambda: []
    assert sender._check_and_send_campaigns() is False
    assert calls == []
