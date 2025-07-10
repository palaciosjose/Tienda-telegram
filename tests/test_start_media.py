from tests.test_categories import setup_dop
from tests.test_shop_info import setup_main
import os


def test_start_media_helpers(monkeypatch, tmp_path):
    dop = setup_dop(monkeypatch, tmp_path)
    dop.ensure_database_schema()
    os.makedirs('data/bd', exist_ok=True)

    dop.save_message('start', 'hola', file_id='fid', media_type='photo')
    assert dop.get_start_media() == {'file_id': 'fid', 'type': 'photo'}

    dop.remove_start_media()
    assert dop.get_start_media() is None


def test_send_main_menu_uses_media(monkeypatch, tmp_path):
    dop, main, calls, _ = setup_main(monkeypatch, tmp_path)
    dop.ensure_database_schema()
    os.makedirs('data/bd', exist_ok=True)

    dop.save_message('start', 'hola', file_id='fid', media_type='photo')

    main.send_main_menu(5, 'u', 'N')
    assert any(c[0] == 'send_photo' for c in calls)
    assert any(c[2].get('caption') == 'hola' for c in calls if c[0] == 'send_photo')

