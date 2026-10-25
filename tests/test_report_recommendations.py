"""Tests for report Recommendations sheet, recommendation_overrides, and Executive summary.

Includes encoding: Excel report must correctly contain Unicode in recommendation text
(multilingual compliance samples, base_legal, etc.) so we do not regress in production.
"""

from pathlib import Path

import pandas as pd

from core.database import LocalDBManager
from report.generator import generate_report


def test_recommendations_without_overrides_uses_builtin_logic(tmp_path):
    """Without config/recommendation_overrides, Recommendations sheet uses built-in CPF/EMAIL/etc. logic."""
    db_path = str(tmp_path / "audit.db")
    out_dir = str(tmp_path / "out")
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    mgr = LocalDBManager(db_path)
    try:
        mgr.set_current_session_id("s1")
        mgr.create_session_record("s1")
        mgr.save_finding(
            "database",
            target_name="T1",
            column_name="cpf",
            sensitivity_level="HIGH",
            pattern_detected="CPF",
            norm_tag="LGPD Art. 5",
            ml_confidence=90,
        )
        mgr.finish_session("s1")
        path = generate_report(mgr, "s1", output_dir=out_dir, config=None)
        assert path is not None
        import pandas as pd

        with pd.ExcelFile(path) as xl:
            assert "Recommendations" in xl.sheet_names
            df = pd.read_excel(xl, sheet_name="Recommendations")
        assert "Data / Pattern" in df.columns and "Base legal" in df.columns
        cpf_row = df[df["Data / Pattern"] == "CPF"].iloc[0]
        assert "CRÍTICA" in str(cpf_row["Prioridade"])
        assert (
            "LGPD" in str(cpf_row["Base legal"])
            or "identificação" in str(cpf_row["Base legal"]).lower()
        )
    finally:
        mgr.dispose()


def test_recommendations_with_overrides_uses_override_for_matching_norm_tag(tmp_path):
    """With report.recommendation_overrides, a matching norm_tag gets the override row in Recommendations."""
    db_path = str(tmp_path / "audit2.db")
    out_dir = str(tmp_path / "out2")
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    mgr = LocalDBManager(db_path)
    try:
        mgr.set_current_session_id("s2")
        mgr.create_session_record("s2")
        mgr.save_finding(
            "database",
            target_name="T1",
            column_name="national_id",
            sensitivity_level="HIGH",
            pattern_detected="UK_SSN",
            norm_tag="UK GDPR",
            ml_confidence=85,
        )
        mgr.finish_session("s2")
        config = {
            "report": {
                "output_dir": out_dir,
                "recommendation_overrides": [
                    {
                        "norm_tag_pattern": "UK GDPR",
                        "base_legal": "UK GDPR Art. 4(1)",
                        "risk": "Identification of data subject.",
                        "recommendation": "Apply UK GDPR safeguards and DPA registration if required.",
                        "priority": "ALTA",
                        "relevant_for": "DPO, UK Representative",
                    },
                ],
            },
        }
        path = generate_report(mgr, "s2", output_dir=out_dir, config=config)
        assert path is not None
        import pandas as pd

        with pd.ExcelFile(path) as xl:
            df = pd.read_excel(xl, sheet_name="Recommendations")
        uk_row = df[df["Data / Pattern"] == "UK_SSN"].iloc[0]
        assert "UK GDPR Art. 4(1)" in str(uk_row["Base legal"])
        assert "UK GDPR safeguards" in str(uk_row["Recomendação"]) or "DPA" in str(
            uk_row["Recomendação"]
        )
        assert str(uk_row["Prioridade"]) == "ALTA"
    finally:
        mgr.dispose()


def test_pii_ambiguous_recommendation_row_medium_and_confirm_manually(tmp_path):
    """PII_AMBIGUOUS (generic doc_id, document_id, etc.) gets MÉDIA priority and 'Confirmar manualmente' in Recommendations."""
    db_path = str(tmp_path / "audit_ambiguous.db")
    out_dir = str(tmp_path / "out_ambiguous")
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    mgr = LocalDBManager(db_path)
    try:
        mgr.set_current_session_id("s-amb")
        mgr.create_session_record("s-amb")
        mgr.save_finding(
            "database",
            target_name="T1",
            column_name="doc_id",
            sensitivity_level="MEDIUM",
            pattern_detected="PII_AMBIGUOUS",
            norm_tag="Generic identifier – confirm manually (doc_id, document_id, etc.)",
            ml_confidence=60,
        )
        mgr.finish_session("s-amb")
        path = generate_report(mgr, "s-amb", output_dir=out_dir, config=None)
        assert path is not None
        with pd.ExcelFile(path) as xl:
            df = pd.read_excel(xl, sheet_name="Recommendations")
        row = df[df["Data / Pattern"] == "PII_AMBIGUOUS"].iloc[0]
        assert "MÉDIA" in str(row["Prioridade"])
        assert (
            "Confirmar manualmente" in str(row["Recomendação"])
            or "confirmar" in str(row["Recomendação"]).lower()
        )
    finally:
        mgr.dispose()


def test_executive_summary_sheet_when_enabled(tmp_path):
    """With report.include_executive_summary true, report contains 'Executive summary' sheet with Metric, Category, Count."""
    db_path = str(tmp_path / "audit_exec.db")
    out_dir = str(tmp_path / "out_exec")
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    mgr = LocalDBManager(db_path)
    try:
        mgr.set_current_session_id("s-exec")
        mgr.create_session_record("s-exec")
        mgr.save_finding(
            "database",
            target_name="DB1",
            column_name="email",
            sensitivity_level="HIGH",
            pattern_detected="EMAIL",
            norm_tag="GDPR Art. 4(1)",
            ml_confidence=90,
        )
        mgr.save_finding(
            "filesystem",
            target_name="FS1",
            file_name="data.csv",
            sensitivity_level="MEDIUM",
            pattern_detected="DATE",
            norm_tag="",
            ml_confidence=70,
        )
        mgr.finish_session("s-exec")
        config = {"report": {"output_dir": out_dir, "include_executive_summary": True}}
        path = generate_report(mgr, "s-exec", output_dir=out_dir, config=config)
        assert path is not None
        import pandas as pd

        with pd.ExcelFile(path) as xl:
            assert "Executive summary" in xl.sheet_names
            df = pd.read_excel(xl, sheet_name="Executive summary")
        assert (
            "Metric" in df.columns
            and "Category" in df.columns
            and "Count" in df.columns
        )
        by_sens = df[df["Metric"] == "Findings by sensitivity"]
        assert len(by_sens) >= 3  # HIGH, MEDIUM, LOW
        high_row = by_sens[by_sens["Category"] == "HIGH"].iloc[0]
        assert high_row["Count"] == 1
        by_norm = df[df["Metric"] == "Findings by Framework / Norm"]
        assert len(by_norm) >= 1
        top_targets = df[df["Metric"] == "Top targets by finding count"]
        assert len(top_targets) >= 1
    finally:
        mgr.dispose()


def test_min_sensitivity_filters_low_from_findings_sheets(tmp_path):
    """With report.min_sensitivity HIGH, LOW findings do not appear in Database/Filesystem findings sheets."""
    db_path = str(tmp_path / "audit_min.db")
    out_dir = str(tmp_path / "out_min")
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    mgr = LocalDBManager(db_path)
    try:
        mgr.set_current_session_id("s-min")
        mgr.create_session_record("s-min")
        mgr.save_finding(
            "database",
            target_name="T1",
            column_name="cpf",
            sensitivity_level="HIGH",
            pattern_detected="CPF",
            norm_tag="LGPD",
            ml_confidence=90,
        )
        mgr.save_finding(
            "database",
            target_name="T1",
            column_name="note",
            sensitivity_level="LOW",
            pattern_detected="GENERIC",
            norm_tag="",
            ml_confidence=30,
        )
        mgr.finish_session("s-min")
        config = {"report": {"output_dir": out_dir, "min_sensitivity": "HIGH"}}
        path = generate_report(mgr, "s-min", output_dir=out_dir, config=config)
        assert path is not None
        import pandas as pd

        with pd.ExcelFile(path) as xl:
            assert "Database findings" in xl.sheet_names
            df = pd.read_excel(xl, sheet_name="Database findings")
        # Only HIGH (CPF) should appear; LOW (note/GENERIC) excluded
        assert len(df) == 1
        assert df.iloc[0]["sensitivity_level"] == "HIGH"
        assert "CPF" in str(df.iloc[0]["pattern_detected"])
    finally:
        mgr.dispose()


def test_possible_minor_recommendation_row_and_priority(tmp_path):
    """When a finding has DOB_POSSIBLE_MINOR, Recommendations sheet has a dedicated CRÍTICA row with differential treatment (LGPD 14, GDPR 8, consent, storage/usage/share). Minor rec is surfaced first."""
    db_path = str(tmp_path / "audit_minor.db")
    out_dir = str(tmp_path / "out_minor")
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    mgr = LocalDBManager(db_path)
    try:
        mgr.set_current_session_id("s-minor")
        mgr.create_session_record("s-minor")
        mgr.save_finding(
            "database",
            target_name="T1",
            column_name="idade",
            sensitivity_level="HIGH",
            pattern_detected="DOB_POSSIBLE_MINOR",
            norm_tag="LGPD Art. 14 – possible minor data; GDPR Art. 8",
            ml_confidence=85,
        )
        mgr.save_finding(
            "database",
            target_name="T1",
            column_name="cpf",
            sensitivity_level="HIGH",
            pattern_detected="LGPD_CPF",
            norm_tag="LGPD Art. 5",
            ml_confidence=90,
        )
        mgr.finish_session("s-minor")
        path = generate_report(mgr, "s-minor", output_dir=out_dir, config=None)
        assert path is not None
        import pandas as pd

        with pd.ExcelFile(path) as xl:
            df = pd.read_excel(xl, sheet_name="Recommendations")
        minor_rows = df[
            df["Data / Pattern"]
            .astype(str)
            .str.contains("DOB_POSSIBLE_MINOR", na=False)
        ]
        assert len(minor_rows) >= 1
        row = minor_rows.iloc[0]
        assert "CRÍTICA" in str(row["Prioridade"])
        assert "LGPD Art. 14" in str(row["Base legal"]) or "Art. 14" in str(
            row["Base legal"]
        )
        rec_text = str(row["Recomendação"])
        assert "consentimento" in rec_text.lower() or "consent" in rec_text.lower()
        assert (
            "armazenamento" in rec_text.lower()
            or "storage" in rec_text.lower()
            or "retenção" in rec_text.lower()
        )
        assert (
            "menor" in rec_text.lower()
            or "minor" in rec_text.lower()
            or "criança" in rec_text.lower()
        )
        # Possible-minor recommendation should appear first (we sort minor recs to top)
        first_row = df.iloc[0]
        assert "DOB_POSSIBLE_MINOR" in str(first_row["Data / Pattern"])
    finally:
        mgr.dispose()


def test_config_scope_hash_stored_and_in_report_info(tmp_path):
    """Session can store config_scope_hash; report Report info sheet includes it when present."""
    db_path = str(tmp_path / "audit_hash.db")
    out_dir = str(tmp_path / "out_hash")
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    mgr = LocalDBManager(db_path)
    try:
        mgr.set_current_session_id("s-hash")
        mgr.create_session_record(
            "s-hash",
            config_scope_hash="a1b2c3d4e5f6",
        )
        mgr.save_finding(
            "database",
            target_name="T1",
            column_name="email",
            sensitivity_level="HIGH",
            pattern_detected="EMAIL",
            norm_tag="GDPR",
            ml_confidence=85,
        )
        mgr.finish_session("s-hash")
        sessions = mgr.list_sessions()
        assert len(sessions) == 1
        assert sessions[0].get("config_scope_hash") == "a1b2c3d4e5f6"
        path = generate_report(mgr, "s-hash", output_dir=out_dir, config={})
        assert path is not None
        import pandas as pd

        with pd.ExcelFile(path) as xl:
            df = pd.read_excel(xl, sheet_name="Report info")
        scope_row = df[df["Field"] == "Config scope hash"]
        assert len(scope_row) == 1
        assert scope_row.iloc[0]["Value"] == "a1b2c3d4e5f6"
    finally:
        mgr.dispose()


def test_recommendation_overrides_first_match_wins_put_specific_before_generic(
    tmp_path,
):
    """norm_tag_pattern uses substring matching; first list entry wins — order specific before generic."""
    db_path = str(tmp_path / "audit_order.db")
    out_dir = str(tmp_path / "out_order")
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    mgr = LocalDBManager(db_path)
    try:
        mgr.set_current_session_id("s-order")
        mgr.create_session_record("s-order")
        mgr.save_finding(
            "database",
            target_name="T1",
            column_name="id",
            sensitivity_level="HIGH",
            pattern_detected="ID_DOC",
            norm_tag="UK GDPR",
            ml_confidence=80,
        )
        mgr.finish_session("s-order")
        # Wrong order: generic "GDPR" matches "UK GDPR" first and steals the row.
        config_wrong = {
            "report": {
                "output_dir": out_dir,
                "recommendation_overrides": [
                    {
                        "norm_tag_pattern": "GDPR",
                        "base_legal": "Generic GDPR row",
                        "risk": "generic",
                        "recommendation": "generic GDPR text",
                        "priority": "MÉDIA",
                        "relevant_for": "DPO",
                    },
                    {
                        "norm_tag_pattern": "UK GDPR",
                        "base_legal": "UK GDPR Art. X",
                        "risk": "uk-specific",
                        "recommendation": "UK ICO guidance",
                        "priority": "ALTA",
                        "relevant_for": "DPO",
                    },
                ],
            },
        }
        path_wrong = generate_report(
            mgr, "s-order", output_dir=out_dir, config=config_wrong
        )
        assert path_wrong is not None
        with pd.ExcelFile(path_wrong) as xl:
            df_wrong = pd.read_excel(xl, sheet_name="Recommendations")
        row_w = df_wrong[df_wrong["Data / Pattern"] == "ID_DOC"].iloc[0]
        assert "Generic GDPR row" in str(row_w["Base legal"])

        # Right order: UK-specific before generic substring.
        config_right = {
            "report": {
                "output_dir": out_dir,
                "recommendation_overrides": [
                    {
                        "norm_tag_pattern": "UK GDPR",
                        "base_legal": "UK GDPR Art. X",
                        "risk": "uk-specific",
                        "recommendation": "UK ICO guidance",
                        "priority": "ALTA",
                        "relevant_for": "DPO",
                    },
                    {
                        "norm_tag_pattern": "GDPR",
                        "base_legal": "Generic GDPR row",
                        "risk": "generic",
                        "recommendation": "generic GDPR text",
                        "priority": "MÉDIA",
                        "relevant_for": "DPO",
                    },
                ],
            },
        }
        path_right = generate_report(
            mgr, "s-order", output_dir=out_dir, config=config_right
        )
        assert path_right is not None
        with pd.ExcelFile(path_right) as xl:
            df_right = pd.read_excel(xl, sheet_name="Recommendations")
        row_r = df_right[df_right["Data / Pattern"] == "ID_DOC"].iloc[0]
        assert "UK GDPR Art. X" in str(row_r["Base legal"])
        assert "ALTA" in str(row_r["Prioridade"])
    finally:
        mgr.dispose()


def test_report_recommendations_unicode_in_override(tmp_path):
    """Excel Recommendations sheet contains Unicode from recommendation_overrides (multilingual support)."""
    db_path = str(tmp_path / "audit_unicode.db")
    out_dir = str(tmp_path / "out_unicode")
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    mgr = LocalDBManager(db_path)
    try:
        mgr.set_current_session_id("s-unicode")
        mgr.create_session_record("s-unicode")
        mgr.save_finding(
            "database",
            target_name="T1",
            column_name="personal_data",
            sensitivity_level="HIGH",
            pattern_detected="APPI",
            norm_tag="APPI",
            ml_confidence=88,
        )
        mgr.finish_session("s-unicode")
        # Unicode in base_legal and recommendation (e.g. Japanese, Arabic, or accented)
        config = {
            "report": {
                "output_dir": out_dir,
                "recommendation_overrides": [
                    {
                        "norm_tag_pattern": "APPI",
                        "base_legal": "APPI 個人情報の保護 (Japan)",
                        "risk": "Identification of data subject.",
                        "recommendation": "Apply safeguards. Dados pessoais / données personnelles.",
                        "priority": "ALTA",
                        "relevant_for": "DPO",
                    },
                ],
            },
        }
        path = generate_report(mgr, "s-unicode", output_dir=out_dir, config=config)
        assert path is not None
        with pd.ExcelFile(path) as xl:
            df = pd.read_excel(xl, sheet_name="Recommendations")
        appi_row = df[df["Data / Pattern"] == "APPI"].iloc[0]
        assert "APPI" in str(appi_row["Base legal"])
        assert "個人" in str(appi_row["Base legal"]) or "Japan" in str(
            appi_row["Base legal"]
        )
        assert "safeguards" in str(appi_row["Recomendação"]) or "données" in str(
            appi_row["Recomendação"]
        )
    finally:
        mgr.dispose()
