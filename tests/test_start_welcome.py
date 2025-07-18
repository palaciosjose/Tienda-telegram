import types
from tests.test_shop_info import setup_main


def test_start_existing_user_main_menu(monkeypatch, tmp_path):
    dop, main, calls, _ = setup_main(monkeypatch, tmp_path)
    dop.ensure_database_schema()

    sid = dop.create_shop("S1", admin_id=1)
    dop.set_user_shop(5, sid)

    monkeypatch.setattr(dop, "it_first", lambda uid: False)
    monkeypatch.setattr(dop, "get_adminlist", lambda: [1])
    monkeypatch.setattr(dop, "get_sost", lambda cid: False)
    monkeypatch.setattr(dop, "user_loger", lambda chat_id=0: None)

    called = {}

    def fake_menu(cid, username, name):
        called["menu"] = (cid, username, name)

    def fake_select(cid, message=None):
        called["select"] = (cid, message)

    monkeypatch.setattr(main, "send_main_menu", fake_menu)
    monkeypatch.setattr(main, "show_shop_selection", fake_select)

    class Msg:
        def __init__(self):
            self.text = "/start"
            self.chat = types.SimpleNamespace(id=5, username="u")
            self.from_user = types.SimpleNamespace(first_name="N")
            self.content_type = "text"

    main.message_send(Msg())

    assert called.get("menu") == (5, "u", "N")
    assert "select" not in called


def test_start_new_user_shows_shop_list(monkeypatch, tmp_path):
    dop, main, calls, _ = setup_main(monkeypatch, tmp_path)
    dop.ensure_database_schema()

    dop.create_shop("S1", admin_id=1)

    monkeypatch.setattr(dop, "it_first", lambda uid: False)
    monkeypatch.setattr(dop, "get_adminlist", lambda: [1])
    monkeypatch.setattr(dop, "get_sost", lambda cid: False)
    monkeypatch.setattr(dop, "user_loger", lambda chat_id=0: None)

    called = {}

    def fake_menu(cid, username, name):
        called["menu"] = (cid, username, name)

    def fake_select(cid, message=None):
        called["select"] = (cid, message)

    monkeypatch.setattr(main, "send_main_menu", fake_menu)
    monkeypatch.setattr(main, "show_shop_selection", fake_select)

    class Msg:
        def __init__(self):
            self.text = "/start"
            self.chat = types.SimpleNamespace(id=5, username="u")
            self.from_user = types.SimpleNamespace(first_name="N")
            self.content_type = "text"

    main.message_send(Msg())

    assert called.get("select") == (5, None)
    assert "menu" not in called


def test_start_new_user_keeps_showing_list(monkeypatch, tmp_path):
    dop, main, calls, _ = setup_main(monkeypatch, tmp_path)
    dop.ensure_database_schema()

    dop.create_shop("S1", admin_id=1)

    monkeypatch.setattr(dop, "it_first", lambda uid: False)
    monkeypatch.setattr(dop, "get_adminlist", lambda: [1])
    monkeypatch.setattr(dop, "get_sost", lambda cid: False)
    users_file = tmp_path / "users.txt"
    monkeypatch.setattr(dop.files, "users_list", str(users_file))

    called = []

    def fake_menu(cid, username, name):
        called.append(("menu", cid))

    def fake_select(cid, message=None):
        called.append(("select", cid))

    monkeypatch.setattr(main, "send_main_menu", fake_menu)
    monkeypatch.setattr(main, "show_shop_selection", fake_select)

    class Msg:
        def __init__(self):
            self.text = "/start"
            self.chat = types.SimpleNamespace(id=5, username="u")
            self.from_user = types.SimpleNamespace(first_name="N")
            self.content_type = "text"

    main.message_send(Msg())
    assert called == [("select", 5)]
    assert not dop.user_has_shop(5)

    called.clear()
    main.message_send(Msg())

    assert called == [("select", 5)]
    assert not dop.user_has_shop(5)

