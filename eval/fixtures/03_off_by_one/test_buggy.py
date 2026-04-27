from buggy import check_attempts, get_range_for_difficulty


def test_hard_range_is_hardest():
    _, hard_max = get_range_for_difficulty("Hard")
    _, normal_max = get_range_for_difficulty("Normal")
    assert hard_max > normal_max, (
        f"Hard difficulty ({hard_max}) should be a wider range than Normal ({normal_max})"
    )


def test_out_of_attempts_at_limit():
    assert check_attempts(5, 5) is True, (
        "Player at exactly the attempt limit should be out of attempts"
    )
