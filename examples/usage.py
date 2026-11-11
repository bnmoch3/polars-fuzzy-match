import polars as pl

from polars_fuzzy_match import fuzzy_match_score

df = pl.DataFrame(
    {
        "strs": ["foo", "foo quz BAR", "baaarfoo", "quz"],
    }
)
pattern = "bar"
out = (
    df.with_columns(
        score=fuzzy_match_score(
            pl.col("strs"),
            pl.lit(pattern),
        )
    )
    .filter(pl.col("score").is_not_null())
    .sort(by="score", descending=True)
)
print(out)

df = pl.DataFrame(
    {
        "text": ["music.mp3", "file.mp3", "file.txt"],
        "pattern": ["^music", ".mp3$", ".mp3$"],
    }
)
print(df.with_columns(score=fuzzy_match_score("text", "pattern")))
