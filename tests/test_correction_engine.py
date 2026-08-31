from correction_engine import (
    apply_corrections,
    extract_context,
    load_corrections,
    new_correction,
    save_corrections,
    suggest_corrections,
    validate_correction,
)


def test_new_correction_defaults():
    corr = new_correction("  teh  ", "the")
    assert corr["pattern"] == "teh"
    assert corr["replacement"] == "the"
    assert corr["case_sensitive"] is False
    assert corr["whole_word"] is True
    assert corr["enabled"] is True
    assert corr["hits"] == 0
    assert corr["id"]


def test_validate_correction():
    assert validate_correction("", "the")
    assert validate_correction("te", "the")  # too short
    assert validate_correction("teh", "")
    assert validate_correction("the", "the")
    assert not validate_correction("teh", "the")


def test_apply_corrections_basic_replacement():
    corr = new_correction("teh", "the")
    text, applied = apply_corrections("I love teh world", [corr])
    assert text == "I love the world"
    assert len(applied) == 1
    assert applied[0]["count"] == 1
    assert corr["hits"] == 1
    assert corr["last_hit"] is not None


def test_apply_corrections_multiple_hits():
    corr = new_correction("teh", "the")
    text, applied = apply_corrections("teh teh teh", [corr])
    assert text == "the the the"
    assert applied[0]["count"] == 3


def test_apply_corrections_case_insensitive_by_default():
    corr = new_correction("teh", "the")
    text, _ = apply_corrections("TEH and Teh", [corr])
    assert text == "the and the"


def test_apply_corrections_case_sensitive():
    corr = new_correction("teh", "the", context_left="", context_right="")
    corr["case_sensitive"] = True
    text, _ = apply_corrections("TEH and teh", [corr])
    assert text == "TEH and the"


def test_apply_corrections_whole_word_boundary():
    corr = new_correction("cat", "dog")
    text, _ = apply_corrections("concatenate a cat", [corr])
    assert text == "concatenate a dog"


def test_apply_corrections_not_whole_word():
    corr = new_correction("cat", "dog")
    corr["whole_word"] = False
    text, _ = apply_corrections("concatenate a cat", [corr])
    assert text == "condogenate a dog"


def test_apply_corrections_disabled():
    corr = new_correction("teh", "the")
    corr["enabled"] = False
    text, applied = apply_corrections("teh", [corr])
    assert text == "teh"
    assert applied == []


def test_apply_corrections_context_left():
    corr = new_correction("teh", "the", context_left="say")
    text, applied = apply_corrections("please say teh thing", [corr])
    assert text == "please say the thing"
    assert len(applied) == 1


def test_apply_corrections_context_left_variable_whitespace():
    corr = new_correction("teh", "the", context_left="say")
    text, applied = apply_corrections("please say  teh thing", [corr])
    assert text == "please say  the thing"
    assert len(applied) == 1


def test_apply_corrections_context_left_missing_does_not_replace():
    corr = new_correction("teh", "the", context_left="say")
    text, applied = apply_corrections("please type teh thing", [corr])
    assert text == "please type teh thing"
    assert applied == []


def test_apply_corrections_context_right():
    corr = new_correction("teh", "the", context_left="", context_right="thing")
    text, applied = apply_corrections("the teh thing stays", [corr])
    assert text == "the the thing stays"
    assert len(applied) == 1


def test_apply_corrections_context_left_and_right():
    corr = new_correction("teh", "the", context_left="say", context_right="thing")
    text, applied = apply_corrections("say teh thing", [corr])
    assert text == "say the thing"
    assert len(applied) == 1


def test_apply_corrections_exception():
    corr = new_correction("teh", "the")
    corr["exceptions"] = [{"left": "some", "right": ""}]
    text, applied = apply_corrections("some teh thing other teh thing", [corr])
    assert text == "some teh thing other the thing"
    assert applied[0]["count"] == 1


def test_apply_corrections_invalid_pattern_is_skipped():
    corr = {"id": "x", "pattern": "", "replacement": "the", "enabled": True}
    text, applied = apply_corrections("teh", [corr])
    assert text == "teh"
    assert applied == []


def test_apply_corrections_empty_input():
    text, applied = apply_corrections("", [new_correction("teh", "the")])
    assert text == ""
    assert applied == []
    text, applied = apply_corrections("teh", [])
    assert text == "teh"
    assert applied == []


def test_suggest_corrections():
    suggestions = suggest_corrections("hello teh world", "hello good world")
    assert suggestions
    assert suggestions[0]["pattern"] == "teh"
    assert suggestions[0]["replacement"] == "good"


def test_suggest_corrections_no_change():
    assert suggest_corrections("same text", "same text") == []


def test_suggest_corrections_limit():
    old = "one two three four"
    new = "1 2 3 4"
    suggestions = suggest_corrections(old, new, max_suggestions=2)
    assert len(suggestions) <= 2


def test_extract_context():
    left, right = extract_context("please say teh thing", "teh")
    assert left == "say"
    assert right == "thing"


def test_extract_context_missing():
    assert extract_context("no match here", "zzz") == ("", "")


def test_save_and_load_corrections(tmp_path, monkeypatch):
    monkeypatch.setattr("correction_engine.CORRECTIONS_FILE", str(tmp_path / "corr.json"))
    assert load_corrections() == []
    corr = new_correction("teh", "the")
    save_corrections([corr])
    loaded = load_corrections()
    assert len(loaded) == 1
    assert loaded[0]["pattern"] == "teh"


def test_load_corrections_corrupt_file(tmp_path, monkeypatch):
    bad = tmp_path / "corr.json"
    bad.write_text("{not valid json")
    monkeypatch.setattr("correction_engine.CORRECTIONS_FILE", str(bad))
    assert load_corrections() == []