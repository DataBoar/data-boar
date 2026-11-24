"""Loader wiring for detection.image_blob (#2362 D2362-13)."""

from config.loader import normalize_config


def _minimal_config(**detection_extra: object) -> dict:
    return {
        "targets": [
            {
                "name": "t1",
                "type": "database",
                "driver": "sqlite",
                "path": ":memory:",
            }
        ],
        "detection": {
            "cnpj_alphanumeric": True,
            "minor_age_threshold": 21,
            **detection_extra,
        },
    }


def test_D2362_13_image_blob_defaults_when_missing():
    out = normalize_config(_minimal_config())
    assert out["detection"]["image_blob"] == {
        "enabled": False,
        "sampling_rows": 5,
        "base64_min_chars": 100,
    }
    assert out["detection"]["cnpj_alphanumeric"] is True
    assert out["detection"]["minor_age_threshold"] == 21


def test_D2362_13_image_blob_normalizes_enabled_block():
    out = normalize_config(
        _minimal_config(
            image_blob={"enabled": True, "sampling_rows": 3},
        )
    )
    assert out["detection"]["image_blob"] == {
        "enabled": True,
        "sampling_rows": 3,
        "base64_min_chars": 100,
    }
    assert out["detection"]["cnpj_alphanumeric"] is True
    assert out["detection"]["minor_age_threshold"] == 21
