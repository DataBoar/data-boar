"""Column-name normalization for ML/DL (FN reduction slice 2)."""

from core.column_name_normalize import fold_accents, normalize_column_name_for_ml
from core.scanner import DataScanner


def test_fold_accents_strips_marks() -> None:
    assert fold_accents("téléphone") == "telephone"
    assert fold_accents("São Paulo") == "Sao Paulo"


def test_normalize_column_name_separators() -> None:
    assert normalize_column_name_for_ml("User_Email") == "user email"
    assert normalize_column_name_for_ml("data.nascimento") == "data nascimento"


def test_normalize_for_ml_off_by_default_no_regression() -> None:
    s = DataScanner()
    r1 = s.scan_column("telefone", "")
    s2 = DataScanner(
        detection_config={"column_name_normalize_for_ml": True},
    )
    r2 = s2.scan_column("téléfone", "")
    assert r1["sensitivity_level"] in ("HIGH", "MEDIUM", "LOW")
    # Accented column should align better with training term "telefone" when normalize on.
    assert r2["ml_confidence"] >= r1["ml_confidence"]
