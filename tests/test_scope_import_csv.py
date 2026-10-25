"""Tests for canonical scope-import CSV to YAML config fragments."""

import pytest
import yaml

from config.loader import normalize_config
from config.scope_import_csv import (
    csv_to_fragment_yaml,
    parse_scope_import_csv,
    rows_to_targets,
)


def test_filesystem_target_roundtrip() -> None:
    csv = "type,name,path,recursive\nfilesystem,docs,/data/docs,false\n"
    yml = csv_to_fragment_yaml(csv, merge_hint=False)
    data = yaml.safe_load(yml)
    cfg = normalize_config({"targets": data["targets"]})
    assert len(cfg["targets"]) == 1
    t = cfg["targets"][0]
    assert t["type"] == "filesystem"
    assert t["path"] == "/data/docs"
    assert t["recursive"] is False


def test_postgresql_alias() -> None:
    csv = (
        "type,host,port,database,user,pass_from_env\n"
        "postgresql,db.internal,5432,appdb,auditor,DB_PASS\n"
    )
    yml = csv_to_fragment_yaml(csv, merge_hint=False)
    data = yaml.safe_load(yml)
    t = data["targets"][0]
    assert t["type"] == "database"
    assert t["driver"] == "postgresql"
    assert t["host"] == "db.internal"
    assert t["port"] == 5432
    assert t["database"] == "appdb"
    assert t["pass_from_env"] == "DB_PASS"


def test_smb_target() -> None:
    csv = "type,name,host,share,path,user,pass_from_env\nsmb,files,srv,c$/share,,,SMB_PASS\n"
    yml = csv_to_fragment_yaml(csv, merge_hint=False)
    data = yaml.safe_load(yml)
    t = data["targets"][0]
    assert t["type"] == "smb"
    assert t["host"] == "srv"
    assert t["share"] == "c$/share"
    assert t["pass_from_env"] == "SMB_PASS"


def test_nfs_and_scope_import_meta() -> None:
    csv = (
        "type,name,path,host,export_path,tags,source_system\n"
        "nfs,nfs1,/mnt/nfs1,fs.example.com,/exports/data,prod|eu,manual\n"
    )
    yml = csv_to_fragment_yaml(csv, merge_hint=False)
    data = yaml.safe_load(yml)
    t = data["targets"][0]
    assert t["type"] == "nfs"
    assert t["path"] == "/mnt/nfs1"
    assert t["host"] == "fs.example.com"
    assert t["export_path"] == "/exports/data"
    assert t["scope_import"]["tags"] == ["prod", "eu"]
    assert t["scope_import"]["source_system"] == "manual"


def test_leading_hash_comments() -> None:
    csv = "# inventory\n\ntype,path\nfilesystem,/tmp\n"
    rows = parse_scope_import_csv(csv)
    assert len(rows) == 1
    assert rows[0]["path"] == "/tmp"


def test_missing_type_column_raises() -> None:
    csv = "kind,path\nfilesystem,/tmp\n"
    with pytest.raises(ValueError, match="type"):
        parse_scope_import_csv(csv)


def test_filesystem_missing_path_raises() -> None:
    csv = "type,name\nfilesystem,bad\n"
    with pytest.raises(ValueError, match="path"):
        rows_to_targets(parse_scope_import_csv(csv))


def test_merge_hint_in_default_output() -> None:
    csv = "type,path\nfilesystem,/x\n"
    yml = csv_to_fragment_yaml(csv)
    assert "Merge:" in yml
    assert "targets:" in yml
