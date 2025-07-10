from tests.test_categories import setup_dop


def test_toggle_discount_features(monkeypatch, tmp_path):
    dop = setup_dop(monkeypatch, tmp_path)
    dop.ensure_database_schema()

    conf = dop.get_discount_config()
    assert conf['enabled']

    dop.update_discount_config(enabled=False, shop_id=1)
    assert not dop.get_discount_config()['enabled']

    dop.update_discount_config(show_fake_price=False, shop_id=1)
    assert not dop.get_discount_config()['show_fake_price']

    dop.update_discount_config(text='X', multiplier=2.0, shop_id=1)
    conf = dop.get_discount_config()
    assert conf['text'] == 'X'
    assert conf['multiplier'] == 2.0
