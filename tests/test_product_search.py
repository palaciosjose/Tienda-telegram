import types, shelve
from tests.test_shop_info import setup_main
from tests.test_categories import setup_dop
import os


def test_search_button_in_menu(monkeypatch, tmp_path):
    dop, main, calls, _ = setup_main(monkeypatch, tmp_path)
    dop.ensure_database_schema()
    main.send_main_menu(5, 'u', 'N')
    buttons = calls[-1][2]['reply_markup'].buttons
    assert any('Buscar productos' in b.text for b in buttons)


def test_search_products_query(monkeypatch, tmp_path):
    dop = setup_dop(monkeypatch, tmp_path)
    dop.ensure_database_schema()
    sid1 = dop.create_shop('S1', admin_id=1)
    sid2 = dop.create_shop('S2', admin_id=1)
    dop.create_product('Widget', 'great tool', 'txt', 1, 10, 'x', shop_id=sid1)
    dop.create_product('Gadget', 'useful item', 'txt', 1, 20, 'y', shop_id=sid2)

    res1 = dop.search_products('wid')
    assert any(r[2] == 'Widget' for r in res1)
    res2 = dop.search_products('useful')
    assert any(r[2] == 'Gadget' for r in res2)


def test_inline_sets_search_state(monkeypatch, tmp_path):
    dop, main, calls, _ = setup_main(monkeypatch, tmp_path)
    dop.ensure_database_schema()
    os.makedirs('data/bd', exist_ok=True)
    monkeypatch.setattr(main.files, 'sost_bd', str(tmp_path / 'sost.bd'))

    captured = {}

    def fake_edit(bot, msg, text, reply_markup=None, parse_mode=None):
        captured['text'] = text
        return True

    monkeypatch.setattr(dop, 'safe_edit_message', fake_edit)
    monkeypatch.setattr(main.bot, 'answer_callback_query', lambda *a, **k: None, raising=False)

    class Msg:
        def __init__(self):
            self.chat = types.SimpleNamespace(id=5, username='u')
            self.message_id = 1
            self.content_type = 'text'
            self.from_user = types.SimpleNamespace(first_name='N')

    cb = types.SimpleNamespace(data='Buscar productos', message=Msg(), id='1', from_user=types.SimpleNamespace(username='u'))
    main.inline(cb)

    with shelve.open(main.files.sost_bd) as bd:
        assert bd[str(cb.message.chat.id)] == 24
    assert 'buscar productos' in captured['text'].lower()


def test_message_search_results(monkeypatch, tmp_path):
    dop, main, calls, _ = setup_main(monkeypatch, tmp_path)
    dop.ensure_database_schema()
    monkeypatch.setattr(main.files, 'sost_bd', str(tmp_path / 'sost.bd'))
    with shelve.open(main.files.sost_bd) as bd:
        bd['5'] = 24

    def fake_search(term, limit=10):
        return [(1, 'S1', 'Widget', 10)]

    monkeypatch.setattr(dop, 'search_products', fake_search)

    class Msg:
        def __init__(self, text):
            self.text = text
            self.chat = types.SimpleNamespace(id=5, username='u')
            self.from_user = types.SimpleNamespace(first_name='N')
            self.content_type = 'text'

    main.message_send(Msg('wid'))

    with shelve.open(main.files.sost_bd) as bd:
        assert '5' not in bd
    assert any('Widget' in c[1][1] for c in calls if c[0] == 'send_message')
