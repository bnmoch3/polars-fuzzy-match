"""Tests for fuzzy_match_score expression."""

import polars as pl
import pytest

from polars_fuzzy_match import CaseMatching, fuzzy_match_score


def test_basic_fuzzy_match():
    """Test basic fuzzy matching with simple pattern."""
    df = pl.DataFrame({"text": ["foo", "foobar", "barfoo", "xyz"]})
    result = df.select(score=fuzzy_match_score(pl.col("text"), pl.lit("foo")))
    # "foo" and "foobar" should match, "xyz" should not
    assert result["score"][0] is not None  # "foo" matches
    assert result["score"][1] is not None  # "foobar" matches
    assert result["score"][2] is not None  # "barfoo" matches
    assert result["score"][3] is None  # "xyz" does not match


def test_case_matching_smart():
    """Test SMART case matching (default)."""
    df = pl.DataFrame({"text": ["foo", "FOO", "Foo"]})
    result = df.select(
        score=fuzzy_match_score(
            pl.col("text"), pl.lit("foo"), case_matching=CaseMatching.SMART
        )
    )
    # All should match since pattern is lowercase
    assert all(s is not None for s in result["score"])


def test_case_matching_respect():
    """Test RESPECT case matching."""
    df = pl.DataFrame({"text": ["foo", "FOO", "Foo"]})
    result = df.select(
        score=fuzzy_match_score(
            pl.col("text"), pl.lit("foo"), case_matching=CaseMatching.RESPECT
        )
    )
    assert result["score"][0] is not None  # "foo" matches exactly
    assert result["score"][1] is None  # "FOO" does not match
    assert result["score"][2] is None  # "Foo" does not match


def test_null_handling():
    """Test that None values in column are handled correctly."""
    df = pl.DataFrame({"text": ["foo", None, "foobar"]})
    result = df.select(score=fuzzy_match_score(pl.col("text"), pl.lit("foo")))
    assert result["score"][0] is not None
    assert result["score"][1] is None
    assert result["score"][2] is not None


def test_no_match_returns_null():
    """Test that non-matching strings return null."""
    df = pl.DataFrame({"text": ["xyz", "abc"]})
    result = df.select(score=fuzzy_match_score(pl.col("text"), pl.lit("foo")))
    assert all(s is None for s in result["score"])


def test_pattern_prefix_exact():
    """Test fzf-style prefix exact match with ^."""
    df = pl.DataFrame({"text": ["music.mp3", "xmusic.mp3", "musicbox"]})
    result = df.select(score=fuzzy_match_score(pl.col("text"), pl.lit("^music")))
    assert result["score"][0] is not None  # starts with "music"
    assert result["score"][1] is None  # does not start with "music"
    assert result["score"][2] is not None  # starts with "music"


def test_pattern_suffix_exact():
    """Test fzf-style suffix exact match with $."""
    df = pl.DataFrame({"text": ["file.mp3", "file.txt", "mp3file"]})
    result = df.select(score=fuzzy_match_score(pl.col("text"), pl.lit(".mp3$")))
    assert result["score"][0] is not None  # ends with ".mp3"
    assert result["score"][1] is None  # ends with ".txt"
    assert result["score"][2] is None  # does not end with ".mp3"


def test_pattern_column():
    df = pl.DataFrame(
        {
            "text": ["music.mp3", "file.mp3", "xmusic.mp3", "file.txt"],
            "pattern": ["^music", ".mp3$", "^music", ".mp3$"],
        }
    )
    result = df.select(score=fuzzy_match_score("text", "pattern"))
    assert [score is not None for score in result["score"]] == [
        True,
        True,
        False,
        False,
    ]


def test_null_pattern_and_haystack():
    df = pl.DataFrame({"text": ["foo", "foo", None], "pattern": ["foo", None, "foo"]})
    result = df.select(score=fuzzy_match_score(pl.col("text"), pl.col("pattern")))
    assert result["score"][0] is not None
    assert result["score"][1:].to_list() == [None, None]


def test_literal_pattern_broadcast():
    df = pl.DataFrame({"text": ["foo", "foobar", "bar"]})
    result = df.select(score=fuzzy_match_score("text", pl.lit("foo")))
    assert [score is not None for score in result["score"]] == [True, True, False]


def test_null_literal_pattern():
    df = pl.DataFrame({"text": ["foo", "bar"]})
    result = df.select(score=fuzzy_match_score("text", pl.lit(None, dtype=pl.String)))
    assert result["score"].to_list() == [None, None]


def test_pattern_length_mismatch():
    df = pl.DataFrame({"text": ["foo", "bar", "baz"]})
    with pytest.raises(
        pl.exceptions.ComputeError,
        match="pattern length 2 does not match haystack length 3",
    ):
        df.select(fuzzy_match_score("text", pl.lit(pl.Series(["foo", "bar"]))))
