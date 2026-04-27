from eval.harness import score_fixture


def test_perfect_recall_when_all_keywords_matched():
    reported = ["inverted comparison in check_guess", "swapped higher lower labels"]
    expected = ["inverted", "swapped"]
    score = score_fixture(reported, expected)
    assert score["recall"] == 1.0


def test_zero_recall_when_nothing_matched():
    reported = ["some unrelated label"]
    expected = ["session_state", "secret resets"]
    score = score_fixture(reported, expected)
    assert score["recall"] == 0.0


def test_partial_recall():
    reported = ["secret resets on rerun"]
    expected = ["secret resets", "session_state"]
    score = score_fixture(reported, expected)
    assert score["recall"] == 0.5


def test_precision_penalizes_false_positives():
    # 3 reported, only 1 matches
    reported = ["inverted hints", "style issue", "missing docstring"]
    expected = ["inverted"]
    score = score_fixture(reported, expected)
    assert score["precision"] == round(1 / 3, 2)


def test_empty_reported_gives_zero_precision():
    score = score_fixture([], ["inverted"])
    assert score["precision"] == 0.0


def test_empty_expected_gives_full_recall():
    score = score_fixture(["anything"], [])
    assert score["recall"] == 1.0
