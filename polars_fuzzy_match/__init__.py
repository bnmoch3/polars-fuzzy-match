from __future__ import annotations

from enum import StrEnum
from pathlib import Path
from typing import TYPE_CHECKING

import polars as pl
from polars.plugins import register_plugin_function

if TYPE_CHECKING:
    from polars._typing import IntoExpr


__all__ = ["CaseMatching", "Normalization", "fuzzy_match_score"]


class Normalization(StrEnum):
    """Configure unicode normalization when matching patterns.

    Attributes:
        NEVER: Characters do not match their normalized form (a ≠ ä).
        SMART: Search strings are normalized; pattern is not. Asymmetric.
    """

    NEVER = "Never"
    SMART = "Smart"


class CaseMatching(StrEnum):
    """Configure case sensitivity when matching patterns.

    Attributes:
        RESPECT: Pattern matches case exactly.
        IGNORE: Both pattern and search strings are lowercased.
        SMART: Case-insensitive if pattern is lowercase; case-sensitive if mixed.
    """

    RESPECT = "Respect"
    IGNORE = "Ignore"
    SMART = "Smart"


def fuzzy_match_score(
    expr: IntoExpr,
    pattern: IntoExpr,
    normalization: Normalization = Normalization.SMART,
    case_matching: CaseMatching = CaseMatching.SMART,
) -> pl.Expr:
    """Fuzzy match strings using fzf-style pattern syntax.

    Parameters
    ----------
    expr
        Column or expression to match against.
    pattern
        Column or expression containing the search pattern for each row.
        Strings name columns; use pl.lit("bar") for a literal pattern.
        Supports fzf syntax: fuzzy (bar), exact ('foo), prefix (^music),
        suffix (.mp3$), and negation (!fire).
    normalization
        How to handle unicode normalization.
    case_matching
        How to treat case differences.

    Returns
    -------
    polars.Expr
        Unsigned 32-bit integer scores, or null for non-matches.
        Higher scores indicate closer matches.
    """
    if not isinstance(expr, pl.Expr):
        expr = pl.col(expr) if isinstance(expr, str) else pl.lit(expr)
    if not isinstance(pattern, pl.Expr):
        pattern = pl.col(pattern) if isinstance(pattern, str) else pl.lit(pattern)

    return register_plugin_function(
        plugin_path=Path(__file__).parent,
        function_name="fuzzy_match_score",
        is_elementwise=True,
        args=[expr, pattern],
        kwargs={
            "normalization": str(normalization),
            "case_matching": str(case_matching),
        },
    )
