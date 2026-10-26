use polars::prelude::*;
use pyo3_polars::derive::polars_expr;
use nucleo::Utf32Str;
use nucleo_matcher::pattern::{CaseMatching, Normalization};
use serde::Deserialize;

#[derive(Deserialize, Debug)]
struct FuzzyMatchKwargs {
    normalization: Option<PatternNormalization>,
    case_matching: Option<PatternCaseMatching>,
}

impl FuzzyMatchKwargs {
    fn to_pattern(&self, pattern: &str) -> nucleo_matcher::pattern::Pattern {
        let n = match self.normalization {
            Some(PatternNormalization::Never) => Normalization::Never,
            _ => Normalization::Smart,
        };
        let c = match self.case_matching {
            Some(PatternCaseMatching::Respect) => CaseMatching::Respect,
            Some(PatternCaseMatching::Ignore) => CaseMatching::Ignore,
            _ => CaseMatching::Smart,
        };
        nucleo_matcher::pattern::Pattern::parse(pattern, c, n)
    }
}

#[derive(Deserialize, Debug)]
pub enum PatternNormalization {
    Never,
    Smart,
}

#[derive(Deserialize, Debug)]
pub enum PatternCaseMatching {
    Respect,
    Ignore,
    Smart,
}

#[polars_expr(output_type=UInt32)]
fn fuzzy_match_score(inputs: &[Series], kwargs: FuzzyMatchKwargs) -> PolarsResult<Series> {
    let ca = inputs[0].str()?;
    let patterns = inputs[1].str()?;
    let config = nucleo::Config::DEFAULT;
    let mut matcher = nucleo::Matcher::new(config);
    let mut buf = Vec::new();

    let mut score = |s: &str, pattern: &nucleo_matcher::pattern::Pattern| {
        let haystack_utf32 = Utf32Str::new(s, &mut buf);
        pattern.score(haystack_utf32, &mut matcher)
    };
    let out: UInt32Chunked = if patterns.len() == 1 {
        let pattern = patterns.get(0).map(|p| kwargs.to_pattern(p));
        ca.into_iter()
            .map(|s| s.and_then(|s| pattern.as_ref().and_then(|p| score(s, p))))
            .collect()
    } else if patterns.len() == ca.len() {
        ca.into_iter()
            .zip(patterns)
            .map(|(s, p)| s.zip(p).and_then(|(s, p)| score(s, &kwargs.to_pattern(p))))
            .collect()
    } else {
        polars_bail!(ShapeMismatch: "pattern length {} does not match haystack length {}", patterns.len(), ca.len());
    };

    Ok(out.into_series())
}
