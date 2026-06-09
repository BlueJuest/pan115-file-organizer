from app.core.security import clean_path_part, mask_secret


def test_mask_secret_hides_middle():
    assert mask_secret("UID=abc;CID=def;SEID=secret", visible=4) == "UID=*******************cret"


def test_mask_secret_keeps_original_length_for_boundary_values():
    for value in ["123456789", "1234567890", "123456789012"]:
        masked = mask_secret(value, visible=4)
        assert len(masked) == len(value)
        assert "*" in masked
        assert masked != value


def test_mask_secret_handles_empty_value():
    assert mask_secret(None) == ""
    assert mask_secret("") == ""


def test_mask_secret_masks_short_values_without_exposing_complete_secret():
    short_masked = mask_secret("abcde", visible=4)
    assert "*" in short_masked
    assert short_masked != "abcde"
    assert not (short_masked.startswith("abcd") and short_masked.endswith("bcde"))

    exact_boundary_masked = mask_secret("abcdefgh", visible=4)
    assert "*" in exact_boundary_masked
    assert exact_boundary_masked != "abcdefgh"
    assert not (exact_boundary_masked.startswith("abcd") and exact_boundary_masked.endswith("efgh"))


def test_clean_path_part_replaces_illegal_characters():
    assert clean_path_part('电影:名/第*一?集<>|"') == "电影_名_第_一_集____"
