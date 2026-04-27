from buggy import check_guess


def test_higher_hint_when_guess_too_low():
    _, hint = check_guess(30, 80)  # 30 < 80, player should go higher
    assert "higher" in hint.lower(), f"Expected 'higher' in hint, got: {hint!r}"


def test_lower_hint_when_guess_too_high():
    _, hint = check_guess(90, 40)  # 90 > 40, player should go lower
    assert "lower" in hint.lower(), f"Expected 'lower' in hint, got: {hint!r}"
