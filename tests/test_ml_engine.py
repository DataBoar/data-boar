"""Tests for core.ml_engine MLSensitivityScanner.

Includes tests that encode SonarQube rules so regressions are caught:
- S6709: random_state must have a seed for reproducibility
- S6973: Scikit-learn estimator must have min_samples_leaf and max_features
- S117: local variable names must match ^[_a-z][a-z0-9_]*$ (lowercase + underscores)
"""

import ast
import re
from pathlib import Path

import pytest

from core.ml_engine import MLSensitivityScanner

# S117 default pattern: local names must be lowercase with optional leading underscore
_S117_LOCAL_NAME_PATTERN = re.compile(r"^[_a-z][a-z0-9_]*$")


def test_ml_scanner_has_random_state_seed():
    """S6709: RandomForestClassifier must have random_state set for reproducibility."""
    scanner = MLSensitivityScanner()
    assert hasattr(scanner.model, "random_state")
    assert scanner.model.random_state is not None
    assert isinstance(scanner.model.random_state, int)


def test_ml_scanner_has_required_hyperparameters():
    """S6973: RandomForestClassifier must explicitly set min_samples_leaf and max_features."""
    scanner = MLSensitivityScanner()
    assert getattr(scanner.model, "min_samples_leaf", None) is not None
    assert getattr(scanner.model, "max_features", None) is not None
    assert scanner.model.min_samples_leaf >= 1
    assert scanner.model.max_features in ("sqrt", "log2", None) or isinstance(
        scanner.model.max_features, (int, float)
    )


def _names_from_assign(node: ast.Assign) -> list[str]:
    return [t.id for t in node.targets if isinstance(t, ast.Name)]


def _names_from_for(node: ast.For) -> list[str]:
    return [node.target.id] if isinstance(node.target, ast.Name) else []


def _names_from_with(node: ast.With) -> list[str]:
    return [
        item.optional_vars.id
        for item in node.items
        if item.optional_vars and isinstance(item.optional_vars, ast.Name)
    ]


def _collect_assigned_names(tree: ast.AST) -> list[str]:
    """Collect all variable names that are assigned (Assign, For target, WithItem)."""
    names = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            names.extend(_names_from_assign(node))
        elif isinstance(node, ast.For):
            names.extend(_names_from_for(node))
        elif isinstance(node, ast.With):
            names.extend(_names_from_with(node))
    return names


def test_ml_engine_local_variables_comply_with_s117():
    """S117: All local variable names in ml_engine must match ^[_a-z][a-z0-9_]*$."""
    ml_engine_path = Path(__file__).resolve().parent.parent / "core" / "ml_engine.py"
    source = ml_engine_path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    assigned = _collect_assigned_names(tree)
    violations = [n for n in assigned if not _S117_LOCAL_NAME_PATTERN.match(n)]
    assert not violations, (
        f"Local variable(s) {violations} do not match S117 pattern ^[_a-z][a-z0-9_]*$. "
        "Use lowercase and underscores only."
    )


def test_predict_sensitivity_returns_float_in_range():
    """predict_sensitivity returns a probability in [0.0, 1.0]."""
    scanner = MLSensitivityScanner()
    prob = scanner.predict_sensitivity("cpf")
    assert isinstance(prob, (float, int))
    assert 0.0 <= float(prob) <= 1.0


def test_predict_sensitivity_empty_returns_zero():
    """Empty or falsy input returns 0.0."""
    scanner = MLSensitivityScanner()
    assert scanner.predict_sensitivity("") == pytest.approx(0.0)
    assert scanner.predict_sensitivity(None) == pytest.approx(0.0)


def test_predict_sensitivity_reproducible():
    """Same input yields same probability (random_state seed ensures reproducibility)."""
    scanner = MLSensitivityScanner()
    text = "email address"
    p1 = scanner.predict_sensitivity(text)
    p2 = scanner.predict_sensitivity(text)
    assert p1 == p2


def test_predict_sensitivity_sensitive_likely_high():
    """Training terms for sensitive data should tend to get higher probability."""
    scanner = MLSensitivityScanner()
    sensitive_prob = scanner.predict_sensitivity("cpf")
    non_sensitive_prob = scanner.predict_sensitivity("log_sistema")
    assert sensitive_prob >= non_sensitive_prob
