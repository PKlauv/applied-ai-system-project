from logic_utils import check_guess, parse_guess, update_score, get_range_for_difficulty


# --- check_guess tests ---

def test_winning_guess():
    outcome, msg = check_guess(50, 50)
    assert outcome == "Win"

def test_guess_too_high():
    outcome, msg = check_guess(60, 50)
    assert outcome == "Too High"

def test_guess_too_low():
    outcome, msg = check_guess(40, 50)
    assert outcome == "Too Low"

def test_check_guess_messages():
    _, msg = check_guess(50, 50)
    assert "Correct" in msg

    _, msg = check_guess(60, 50)
    assert "LOWER" in msg

    _, msg = check_guess(40, 50)
    assert "HIGHER" in msg


# --- parse_guess tests ---

def test_parse_guess_valid():
    ok, value, err = parse_guess("42")
    assert ok is True
    assert value == 42
    assert err is None

def test_parse_guess_empty():
    ok, value, err = parse_guess("")
    assert ok is False
    assert value is None

def test_parse_guess_none():
    ok, value, err = parse_guess(None)
    assert ok is False
    assert value is None

def test_parse_guess_non_numeric():
    ok, value, err = parse_guess("abc")
    assert ok is False
    assert "not a number" in err

def test_parse_guess_decimal():
    ok, value, err = parse_guess("3.7")
    assert ok is True
    assert value == 3

def test_parse_guess_negative():
    ok, value, err = parse_guess("-5")
    assert ok is True
    assert value == -5


# --- update_score tests ---

def test_update_score_win():
    score = update_score(0, "Win", 1)
    assert score == 80  # 100 - 10*(1+1) = 80

def test_update_score_too_high():
    score = update_score(50, "Too High", 1)
    assert score == 45

def test_update_score_too_low():
    score = update_score(50, "Too Low", 1)
    assert score == 45

def test_update_score_symmetry():
    high_score = update_score(100, "Too High", 2)
    low_score = update_score(100, "Too Low", 2)
    assert high_score == low_score  # both should deduct equally


# --- get_range_for_difficulty tests ---

def test_easy_range():
    low, high = get_range_for_difficulty("Easy")
    assert low == 1
    assert high == 20

def test_normal_range():
    low, high = get_range_for_difficulty("Normal")
    assert low == 1
    assert high == 100

def test_hard_range():
    low, high = get_range_for_difficulty("Hard")
    assert low == 1
    assert high == 200

def test_unknown_difficulty_defaults():
    low, high = get_range_for_difficulty("Unknown")
    assert low == 1
    assert high == 100
