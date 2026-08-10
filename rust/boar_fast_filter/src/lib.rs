use pyo3::exceptions::PyRuntimeError;
use pyo3::prelude::*;
use regex::Regex;

#[pyclass]
pub struct FastFilter {
    cpf_pattern: Regex,
    email_pattern: Regex,
    credit_card_pattern: Regex,
}

#[pymethods]
impl FastFilter {
    #[new]
    fn py_new() -> PyResult<Self> {
        Self::try_new().map_err(|e| PyRuntimeError::new_err(format!("regex compile error: {e}")))
    }

    /// Return only suspect indexes from the input batch.
    /// Panic-free by design: regex matching does not unwrap dynamic state.
    fn filter_batch(&self, batch: Vec<String>) -> PyResult<Vec<usize>> {
        Ok(self.filter_batch_pure(&batch))
    }
}

impl FastFilter {
    /// Pure-Rust constructor (no Python dependency). Returns the underlying
    /// regex error directly so it can be unit-tested without a Python interpreter.
    pub fn try_new() -> Result<Self, regex::Error> {
        let cpf_pattern = Regex::new(r"\d{3}\.?\d{3}\.?\d{3}-?\d{2}")?;
        let email_pattern = Regex::new(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")?;
        let credit_card_pattern = Regex::new(r"\b(?:\d[ -]*?){13,19}\b")?;
        Ok(FastFilter {
            cpf_pattern,
            email_pattern,
            credit_card_pattern,
        })
    }

    /// Pure-Rust filter that returns suspect indexes for a borrowed slice.
    /// `filter_batch` (the PyO3-exposed method) delegates here so behavior is
    /// identical between the Python binding and Rust unit tests.
    pub fn filter_batch_pure(&self, batch: &[String]) -> Vec<usize> {
        let mut suspects = Vec::new();
        for (idx, content) in batch.iter().enumerate() {
            if self.cpf_pattern.is_match(content) || self.email_pattern.is_match(content) {
                suspects.push(idx);
                continue;
            }
            if self.has_valid_luhn_card(content) {
                suspects.push(idx);
            }
        }
        suspects
    }

    fn has_valid_luhn_card(&self, content: &str) -> bool {
        self.credit_card_pattern
            .find_iter(content)
            .any(|m| Self::check_luhn(m.as_str()))
    }

    /// Standard Luhn check on the digits found in `card_number`. Non-digit
    /// characters (spaces, dashes) are ignored. Returns false for sequences
    /// outside the 13..=19 digit range used by real card numbers.
    pub fn check_luhn(card_number: &str) -> bool {
        let digits: Vec<u32> = card_number
            .chars()
            .filter(|c| c.is_ascii_digit())
            .filter_map(|c| c.to_digit(10))
            .collect();

        if digits.len() < 13 || digits.len() > 19 {
            return false;
        }

        let sum: u32 = digits
            .iter()
            .rev()
            .enumerate()
            .map(|(i, &digit)| {
                if i % 2 == 1 {
                    let d = digit * 2;
                    if d > 9 {
                        d - 9
                    } else {
                        d
                    }
                } else {
                    digit
                }
            })
            .sum();

        sum.is_multiple_of(10)
    }
}

/// Guest-side trust gate for SDK mesh dogfood (#1116 / GAP-010).
///
/// ``boar_fast_filter`` refuses a tinted/adulterated host before filter work.
/// Pure function — no network; complements Ed25519 mutual attestation in Python.
#[pyfunction]
fn guest_accepts_host_trust(trust_level: &str) -> bool {
    matches!(trust_level, "trusted" | "degraded" | "unknown")
}

#[pymodule]
fn boar_fast_filter(_py: Python<'_>, m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<FastFilter>()?;
    m.add_function(wrap_pyfunction!(guest_accepts_host_trust, m)?)?;
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    fn ff() -> FastFilter {
        FastFilter::try_new().expect("baseline regexes must compile")
    }

    fn s(items: &[&str]) -> Vec<String> {
        items.iter().map(|x| (*x).to_string()).collect()
    }

    #[test]
    fn guest_accepts_trusted_and_rejects_adulterated() {
        assert!(guest_accepts_host_trust("trusted"));
        assert!(guest_accepts_host_trust("degraded"));
        assert!(!guest_accepts_host_trust("adulterated"));
        assert!(!guest_accepts_host_trust("untrusted"));
    }

    // ----- Luhn ---------------------------------------------------------

    #[test]
    fn luhn_accepts_known_valid_visa_test_number() {
        // Standard PAN test vector (Visa), passes Luhn.
        assert!(FastFilter::check_luhn("4539578763621486"));
    }

    #[test]
    fn luhn_accepts_known_valid_mastercard_test_number() {
        assert!(FastFilter::check_luhn("5555555555554444"));
    }

    #[test]
    fn luhn_accepts_known_valid_amex_test_number() {
        // 15 digits — Amex.
        assert!(FastFilter::check_luhn("378282246310005"));
    }

    #[test]
    fn luhn_rejects_invalid_check_digit() {
        // Same as the valid Visa above with last digit perturbed.
        assert!(!FastFilter::check_luhn("4539578763621487"));
    }

    #[test]
    fn luhn_rejects_too_short() {
        // 12 digits is below the 13-digit minimum.
        assert!(!FastFilter::check_luhn("123456789012"));
    }

    #[test]
    fn luhn_rejects_too_long() {
        // 20 digits is above the 19-digit maximum.
        assert!(!FastFilter::check_luhn("12345678901234567890"));
    }

    #[test]
    fn luhn_ignores_separators() {
        // Spaces and dashes must not change the result.
        assert!(FastFilter::check_luhn("4539-5787-6362-1486"));
        assert!(FastFilter::check_luhn("4539 5787 6362 1486"));
    }

    #[test]
    fn luhn_rejects_empty_and_non_numeric() {
        assert!(!FastFilter::check_luhn(""));
        assert!(!FastFilter::check_luhn("not-a-card"));
    }

    // ----- Constructor --------------------------------------------------

    #[test]
    fn try_new_compiles_all_patterns() {
        let _ = ff();
    }

    // ----- filter_batch_pure: positive matches --------------------------

    #[test]
    fn detects_cpf_with_punctuation() {
        let f = ff();
        let batch = s(&["clean line", "cpf 390.533.447-05", "another clean line"]);
        assert_eq!(f.filter_batch_pure(&batch), vec![1]);
    }

    #[test]
    fn detects_cpf_without_punctuation() {
        let f = ff();
        let batch = s(&["nope", "39053344705"]);
        assert_eq!(f.filter_batch_pure(&batch), vec![1]);
    }

    #[test]
    fn detects_email() {
        let f = ff();
        let batch = s(&["please contact a@example.test about it"]);
        assert_eq!(f.filter_batch_pure(&batch), vec![0]);
    }

    #[test]
    fn detects_credit_card_with_valid_luhn() {
        let f = ff();
        let batch = s(&["card on file: 4539 5787 6362 1486 ok"]);
        assert_eq!(f.filter_batch_pure(&batch), vec![0]);
    }

    // ----- filter_batch_pure: negative cases ----------------------------

    #[test]
    fn skips_clean_content() {
        let f = ff();
        let batch = s(&["totally clean", "still fine", "no PII here"]);
        assert!(f.filter_batch_pure(&batch).is_empty());
    }

    #[test]
    fn skips_card_like_groups_failing_luhn() {
        // 16 digits in card-style groups, invalid Luhn check digit. Spaces also
        // prevent the CPF regex from matching, so the line is exercising the
        // credit-card path specifically and must NOT be flagged.
        let f = ff();
        let batch = s(&["order id 1234 5678 9012 3456 here"]);
        assert!(f.filter_batch_pure(&batch).is_empty());
    }

    #[test]
    fn handles_empty_batch() {
        let f = ff();
        let batch: Vec<String> = Vec::new();
        assert!(f.filter_batch_pure(&batch).is_empty());
    }

    // ----- filter_batch_pure: behavior ----------------------------------

    #[test]
    fn each_item_reported_at_most_once() {
        // CPF + email in same line: should still produce exactly one index.
        let f = ff();
        let batch = s(&["cpf 390.533.447-05 mail a@example.test"]);
        assert_eq!(f.filter_batch_pure(&batch), vec![0]);
    }

    #[test]
    fn preserves_input_order_in_output_indexes() {
        let f = ff();
        let batch = s(&[
            "a@example.test",
            "clean",
            "cpf 390.533.447-05",
            "clean",
            "4539578763621486",
        ]);
        assert_eq!(f.filter_batch_pure(&batch), vec![0, 2, 4]);
    }

    #[test]
    fn detects_mixed_signal_batch() {
        let f = ff();
        let batch = s(&[
            "no signal here",
            "cpf 390.533.447-05",
            "totally clean",
            "x@y.io",
        ]);
        assert_eq!(f.filter_batch_pure(&batch), vec![1, 3]);
    }
}
