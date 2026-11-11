from app.duration import duration_seconds_of


def test_duration_seconds_from_string():
    assert duration_seconds_of({"duration_string": "26:02"}) == 1562


def test_duration_seconds_from_hms():
    assert duration_seconds_of({"duration_string": "1:05:30"}) == 3930
