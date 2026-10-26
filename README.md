# Polars Fuzzy Matching

## Installation

```bash
pip install polars-fuzzy-match
```

Or with [uv](https://github.com/astral-sh/uv):

```bash
uv add polars-fuzzy-match
```

## Requirements

- CPython 3.11-3.15
- Polars >= 2.0, < 3

Python 3.15 is the default for local development. Install the development
dependencies with `uv sync` and run the tests with `uv run pytest tests/`.
The supported Python versions and both ends of the Polars 2.x range are
checked in CI. Rust and Python package versions are locked for development
in `Cargo.lock` and `uv.lock`; published dependencies use compatibility
ranges instead. Building from source requires Rust 1.95 or newer; the
development toolchain is pinned to 1.99.1.

## Migrating from 0.1.x to 0.2.0

The `pattern` argument to `fuzzy_match_score` now accepts a Polars expression.
Plain strings name **columns**, rather than representing literal patterns.
If you previously wrote `fuzzy_match_score("text", "bar")`, use
`fuzzy_match_score("text", pl.lit("bar"))` instead. To use a different pattern
for each row, pass a column name or expression, for example
`fuzzy_match_score("text", "pattern")`.

Version 0.2.0 requires CPython 3.11 or newer and Polars 2.x. Python 3.8-3.10,
PyPy, and Polars releases outside the 2.x series are no longer supported.

## Usage

With both the plugin and polars installed, usage is as follows:

```python
import polars as pl
from polars_fuzzy_match import fuzzy_match_score


df = pl.DataFrame(
    {
        "strs": ["foo", "foo quz BAR", "baaarfoo", "quz"],
    }
)
pattern = "bar"
out = df.with_columns(
    score=fuzzy_match_score(
        pl.col("strs"),
        pl.lit(pattern),
    )
)
print(out)
```

This outputs:

```
shape: (4, 2)
┌─────────────┬───────┐
│ strs        ┆ score │
│ ---         ┆ ---   │
│ str         ┆ u32   │
╞═════════════╪═══════╡
│ foo         ┆ null  │
│ foo quz BAR ┆ 88    │
│ baaarfoo    ┆ 74    │
│ quz         ┆ null  │
└─────────────┴───────┘
```

When there is no match, score is `null`. When the pattern matches the value in
the given column, score is non-null. The higher the score, the closer the value
is to the pattern. Therefore, we can filter out values that do not match and
order by score:

```python
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
```

This outputs:

```
shape: (2, 2)
┌─────────────┬───────┐
│ strs        ┆ score │
│ ---         ┆ ---   │
│ str         ┆ u32   │
╞═════════════╪═══════╡
│ foo quz BAR ┆ 88    │
│ baaarfoo    ┆ 74    │
└─────────────┴───────┘
```

To compare two columns, pass the pattern column as an expression (or its name):

```python
df = pl.DataFrame({"text": ["music.mp3", "file.mp3"], "pattern": ["^music", ".mp3$"]})
out = df.with_columns(score=fuzzy_match_score("text", "pattern"))
```

Each row uses its own pattern. A string argument names a column; wrap literal
patterns with `pl.lit("bar")`. Null values in either column produce null scores.

### Fzf-style search syntax

This plugin supports Fzf-style search syntax for the pattern. It's worth noting
that this section is taken almost verbatim from the Fzf README:

| Pattern   | Match type                 | Description                                 |
| --------- | -------------------------- | ------------------------------------------- |
| `bar`     | fuzzy                      | items that fuzzy match `bar` e.g. 'bXXaXXr' |
| `'foo`    | substring exact match      | items that include `foo` e.g. 'is foo ok'  |
| `^music`  | prefix exact match         | items that start with `music`               |
| `.mp3$`   | suffix exact match         | items that end with `.mp3`                  |
| `!fire`   | inverse exact match        | items that do not include `fire`            |
| `!^music` | inverse prefix exact match | items that do not start with `music`        |
| `!.mp3$`  | inverse suffix exact match | items that do not end with `.mp3`           |

## Credits

1. Marco Gorelli's Tutorial on writing Polars Plugin. See
   [here](https://marcogorelli.github.io/polars-plugins-tutorial/).
2. The Helix Editor team for the
   [Nucleo fuzzy matching library](https://github.com/helix-editor/nucleo).
