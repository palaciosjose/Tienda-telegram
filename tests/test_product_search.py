import types, shelve, os
from tests.test_shop_info import setup_main


def test_direct_search_shows_buttons(monkeypatch, tmp_path):
    dop, main, calls, _ = setup_main(monkeypatch, tmp_path)
    dop.ensure_database_schema()
    sid = dop.create_shop('S1', admin_id=1)
    dop.create_product('Apple', 'd', 'txt', 1, 2, 'x', shop_id=sid)
    dop.create_product('Banana', 'd', 'txt', 1, 2, 'x', shop_id=sid)
    dop.set_user_shop(5, sid)

    class Msg:
        def __init__(self, text):
            self.text = text
            self.chat = types.SimpleNamespace(id=5, username='u')
            self.from_user = types.SimpleNamespace(first_name='N')
            self.content_type = 'text'

    main.message_send(Msg('/buscar App'))

    send_calls = [c for c in calls if c[0] == 'send_message']
    assert send_calls
    buttons = send_calls[-1][2]['reply_markup'].buttons
    assert any(b.text.endswith('Apple') for b in buttons)


def test_search_waits_for_query(monkeypatch, tmp_path):
    dop, main, calls, _ = setup_main(monkeypatch, tmp_path)
    dop.ensure_database_schema()
    sid = dop.create_shop('S1', admin_id=1)
    dop.create_product('Apple', 'd', 'txt', 1, 2, 'x', shop_id=sid)
    dop.set_user_shop(5, sid)
    monkeypatch.setattr(main.files, 'sost_bd', str(tmp_path / 'sost.bd'))

    class Msg:
        def __init__(self, text):
            self.text = text
            self.chat = types.SimpleNamespace(id=5, username='u')
            self.from_user = types.SimpleNamespace(first_name='N')
            self.content_type = 'text'

    main.message_send(Msg('/buscar'))
    with shelve.open(main.files.sost_bd) as bd:
        assert bd['5'] == 24

    main.message_send(Msg('App'))
    with shelve.open(main.files.sost_bd) as bd:
        assert '5' not in bd

    send_calls = [c for c in calls if c[0] == 'send_message']
    buttons = send_calls[-1][2]['reply_markup'].buttons
    assert any(b.text.endswith('Apple') for b in buttons)
