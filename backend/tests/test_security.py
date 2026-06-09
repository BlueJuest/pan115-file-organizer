from app.core.security import clean_path_part, mask_secret


def test_mask_secret_hides_middle():
    assert mask_secret("UID=abc;CID=def;SEID=secret", visible=4) == "UID=**********************cret"


def test_mask_secret_handles_empty_value():
    assert mask_secret(None) == ""
    assert mask_secret("") == ""


def test_clean_path_part_replaces_illegal_characters():
    assert clean_path_part('电影:名/第*一?集<>|"') == "电影_名_第_一_集____"
