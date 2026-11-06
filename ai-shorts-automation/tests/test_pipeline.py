import pytest
from pipeline import validate_story


def test_valid_story():
    assert validate_story({"scenes": [{"text": "Hello", "duration": 5}]})["scenes"][0]["text"] == "Hello"


@pytest.mark.parametrize("story", [
    {}, {"scenes": []}, {"scenes": [{"text": ""}]},
    {"scenes": [{"text": "Hi", "duration": 0}]},
    {"scenes": [{"text": "Hi", "duration": 31}]},
    {"scenes": [{"text": "Hi", "duration": True}]},
    {"scenes": [{"text": "x" * 601}]},
])
def test_reject_invalid(story):
    with pytest.raises(ValueError):
        validate_story(story)
