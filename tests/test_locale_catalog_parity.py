"""M-LOCALE-V1: shipped locale JSON files must have identical key sets (see PLAN_DASHBOARD_I18N.md)."""

from __future__ import annotations

from api.locale_i18n import locale_catalog_keys


def test_locale_json_key_parity_en_pt_br():
    en_keys = locale_catalog_keys("en")
    pt_keys = locale_catalog_keys("pt-BR")
    assert en_keys == pt_keys, (
        "Locale key mismatch — sync api/locales/en.json and api/locales/pt-BR.json "
        f"(or run scripts/build_locale_catalogs.py).\n"
        f"Only in EN: {sorted(en_keys - pt_keys)!r}\n"
        f"Only in pt-BR: {sorted(pt_keys - en_keys)!r}"
    )
