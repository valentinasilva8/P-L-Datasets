#!/usr/bin/env python3
"""
Validate dataset CSVs against schema: columns, dtypes, nullability, ranges, PKs, referential integrity.
Output: validation_report.md and validation_report.json in artifacts/validation/<dataset>/<version>/
Exit: 0 if pass, 1 if fail.
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path

import pandas as pd
import yaml

# Map schema dtypes to pandas
DTYPE_MAP = {
    "int": ["int64", "int32"],
    "float": ["float64", "float32"],
    "string": ["object"],
    "bool": ["bool"],
    "date": ["object"],  # stored as object/string in CSV
    "datetime": ["object"],
}

ORPHAN_RATE_THRESHOLD = 0.005  # 0.5%


def load_schema(repo_root: Path, dataset: str, version: str) -> dict:
    schema_path = repo_root / "schemas" / dataset / version / "schema.yaml"
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema not found: {schema_path}")
    with open(schema_path) as f:
        return yaml.safe_load(f)


def load_catalog(repo_root: Path) -> dict:
    catalog_path = repo_root / "catalog" / "datasets.yaml"
    if not catalog_path.exists():
        return {}
    with open(catalog_path) as f:
        return yaml.safe_load(f)


def infer_repo_root() -> Path:
    """Find repo root (directory containing catalog/, schemas/, datasets/)."""
    p = Path(__file__).resolve().parent
    for _ in range(5):
        if (p / "catalog").exists() and (p / "schemas").exists() and (p / "datasets").exists():
            return p
        p = p.parent
    return Path.cwd()


def check_dtype(col_series: pd.Series, expected: str) -> bool:
    actual = str(col_series.dtype)
    allowed = DTYPE_MAP.get(expected, [expected])
    return actual in allowed


def coerce_and_compare_dtype(col_series: pd.Series, expected: str) -> tuple[bool, str | None]:
    """Try to coerce to expected dtype and compare. Returns (ok, error_msg)."""
    if expected == "string":
        return True, None
    if expected == "int":
        try:
            pd.to_numeric(col_series, errors="coerce")
            return True, None
        except Exception as e:
            return False, str(e)
    if expected == "float":
        try:
            pd.to_numeric(col_series, errors="coerce")
            return True, None
        except Exception as e:
            return False, str(e)
    if expected == "bool":
        vals = col_series.dropna().unique()
        if all(v in (True, False, "True", "False", "true", "false", 1, 0) for v in vals):
            return True, None
        return False, f"Non-boolean values: {vals[:5]}"
    if expected in ("date", "datetime"):
        return True, None
    return True, None


def validate_file(
    repo_root: Path,
    dataset: str,
    version: str,
    filename: str,
    file_spec: dict,
    catalog_files: dict,
) -> dict:
    """Validate a single CSV file. Returns result dict with errors, warnings."""
    data_path = repo_root / "datasets" / dataset / version / filename
    result = {
        "file": filename,
        "errors": [],
        "warnings": [],
        "checks": {},
    }

    # 1. File exists
    if not data_path.exists():
        result["errors"].append(f"File not found: {data_path}")
        return result
    result["checks"]["file_exists"] = True

    df = pd.read_csv(data_path)
    columns = set(df.columns)
    schema_cols = file_spec.get("columns", {})

    # 2. Required columns exist
    for col_name, col_spec in schema_cols.items():
        if col_spec.get("required", True) and col_name not in columns:
            result["errors"].append(f"Missing required column: {col_name}")
    result["checks"]["required_columns"] = len([e for e in result["errors"] if "Missing required" in e]) == 0

    # 3. Unexpected columns (warn)
    schema_col_names = set(schema_cols.keys())
    unexpected = columns - schema_col_names
    if unexpected:
        result["warnings"].append(f"Unexpected columns: {sorted(unexpected)}")

    # 4. Dtype checks (warn)
    for col_name in columns:
        if col_name not in schema_cols:
            continue
        col_spec = schema_cols[col_name]
        expected_dtype = col_spec.get("dtype", "string")
        series = df[col_name]
        ok, err = coerce_and_compare_dtype(series, expected_dtype)
        if not ok:
            result["warnings"].append(f"Column {col_name}: dtype mismatch (expected {expected_dtype}): {err}")
        if not check_dtype(series, expected_dtype):
            result["warnings"].append(
                f"Column {col_name}: stored as {series.dtype}, schema expects {expected_dtype}"
            )

    # 5. Nullability checks (fail if non-nullable has nulls)
    for col_name, col_spec in schema_cols.items():
        if col_name not in columns:
            continue
        nullable = col_spec.get("nullable", False)
        if not nullable:
            null_count = df[col_name].isna().sum()
            if null_count > 0:
                result["errors"].append(
                    f"Column {col_name}: non-nullable but has {null_count} null(s)"
                )

    # 6. Range checks for numeric columns (warn)
    for col_name, col_spec in schema_cols.items():
        if col_name not in columns:
            continue
        for bound in ("min", "max"):
            val = col_spec.get(bound)
            if val is None:
                continue
            series = pd.to_numeric(df[col_name], errors="coerce")
            valid = series.dropna()
            if bound == "min" and len(valid) > 0 and valid.min() < val:
                result["warnings"].append(
                    f"Column {col_name}: values below min {val} (actual min: {valid.min()})"
                )
            if bound == "max" and len(valid) > 0 and valid.max() > val:
                result["warnings"].append(
                    f"Column {col_name}: values above max {val} (actual max: {valid.max()})"
                )

    # 7. PK uniqueness
    pk = file_spec.get("primary_key")
    if pk and pk in columns:
        dupes = df[pk].duplicated().sum()
        if dupes > 0:
            result["errors"].append(f"Primary key {pk}: {dupes} duplicate(s)")
        result["checks"]["pk_unique"] = dupes == 0
    elif file_spec.get("composite_key"):
        comp = file_spec["composite_key"]
        if all(c in columns for c in comp):
            dupes = df[comp].duplicated().sum()
            if dupes > 0:
                result["errors"].append(f"Composite key {comp}: {dupes} duplicate(s)")
            result["checks"]["composite_key_unique"] = dupes == 0

    # 8. Referential integrity
    join_keys = file_spec.get("join_keys", [])
    for jk in join_keys:
        col = jk.get("column")
        ref = jk.get("references")
        if not col or not ref or col not in columns:
            continue
        # ref is like "customers.customer_id" or "wallet_scores.wallet_address"
        ref_table, ref_col = ref.split(".")
        ref_path = repo_root / "datasets" / dataset / version / f"{ref_table}.csv"
        if not ref_path.exists():
            result["warnings"].append(f"Reference table not found: {ref_table}.csv")
            continue
        ref_df = pd.read_csv(ref_path)
        if ref_col not in ref_df.columns:
            result["warnings"].append(f"Reference column {ref_col} not in {ref_table}")
            continue
        parent_values = set(ref_df[ref_col].astype(str))
        child_values = set(df[col].dropna().astype(str))
        orphans = child_values - parent_values
        total_child = len(child_values)
        if total_child == 0:
            continue
        orphan_count = df[col].isin([x for x in orphans]).sum()
        orphan_rate = orphan_count / len(df)
        if orphan_rate > ORPHAN_RATE_THRESHOLD:
            result["errors"].append(
                f"Referential integrity {col} -> {ref}: {orphan_rate:.2%} orphan rate "
                f"({orphan_count} rows) exceeds {ORPHAN_RATE_THRESHOLD:.1%} threshold"
            )
        elif orphan_count > 0:
            result["warnings"].append(
                f"Referential integrity {col} -> {ref}: {orphan_count} orphan(s) ({orphan_rate:.2%})"
            )

    # Catalog checksums (optional)
    if catalog_files:
        rel_path = f"datasets/{dataset}/{version}/{filename}"
        for cf in catalog_files.get("files", []):
            if cf.get("path") == rel_path:
                actual_size = data_path.stat().st_size
                expected_size = cf.get("file_size_bytes")
                if expected_size is not None and actual_size != expected_size:
                    result["warnings"].append(
                        f"File size mismatch: expected {expected_size}, got {actual_size}"
                    )
                with open(data_path, "rb") as fp:
                    actual_sha = hashlib.sha256(fp.read()).hexdigest()
                expected_sha = cf.get("sha256")
                if expected_sha and actual_sha != expected_sha:
                    result["warnings"].append(f"SHA256 mismatch for {filename}")
                break

    return result


def main():
    parser = argparse.ArgumentParser(
        description="Validate dataset CSVs against schema"
    )
    parser.add_argument(
        "--dataset",
        default="covenant_pl",
        help="Dataset ID (default: covenant_pl)",
    )
    parser.add_argument(
        "--version",
        default="v1.0.0",
        help="Version (default: v1.0.0)",
    )
    parser.add_argument(
        "--repo",
        type=Path,
        default=None,
        help="Repo root (default: auto-detect)",
    )
    args = parser.parse_args()

    repo_root = args.repo or infer_repo_root()
    dataset = args.dataset
    version = args.version

    catalog = load_catalog(repo_root)
    ds_catalog = catalog.get("datasets", {}).get(dataset, {})
    catalog_files = {f["path"].split("/")[-1]: f for f in ds_catalog.get("files", [])}

    schema = load_schema(repo_root, dataset, version)
    file_specs = schema.get("files", {})

    all_results = []
    for filename, file_spec in file_specs.items():
        cf = catalog_files.get(filename)
        res = validate_file(repo_root, dataset, version, filename, file_spec, ds_catalog)
        all_results.append(res)

    # Build report
    total_errors = sum(len(r["errors"]) for r in all_results)
    total_warnings = sum(len(r["warnings"]) for r in all_results)
    passed = total_errors == 0

    out_dir = repo_root / "artifacts" / "validation" / dataset / version
    out_dir.mkdir(parents=True, exist_ok=True)

    # JSON report (ensure native Python types for serialization)
    def to_serializable(obj):
        if isinstance(obj, dict):
            return {k: to_serializable(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [to_serializable(v) for v in obj]
        if isinstance(obj, (bool, type(None))):
            return obj
        if hasattr(obj, "item"):  # numpy scalar
            return obj.item()
        return obj

    report_json = {
        "dataset": dataset,
        "version": version,
        "passed": passed,
        "total_errors": total_errors,
        "total_warnings": total_warnings,
        "results": to_serializable(all_results),
    }
    json_path = out_dir / "validation_report.json"
    with open(json_path, "w") as f:
        json.dump(report_json, f, indent=2)

    # Markdown report
    lines = [
        f"# Validation Report: {dataset} {version}",
        "",
        f"**Status:** {'PASS' if passed else 'FAIL'}",
        f"**Errors:** {total_errors}",
        f"**Warnings:** {total_warnings}",
        "",
        "## Summary by File",
        "",
    ]
    for r in all_results:
        status = "OK" if not r["errors"] else "FAIL"
        lines.append(f"### {r['file']} — {status}")
        if r["errors"]:
            lines.append("**Errors:**")
            for e in r["errors"]:
                lines.append(f"- {e}")
        if r["warnings"]:
            lines.append("**Warnings:**")
            for w in r["warnings"]:
                lines.append(f"- {w}")
        if not r["errors"] and not r["warnings"]:
            lines.append("No issues.")
        lines.append("")

    md_path = out_dir / "validation_report.md"
    with open(md_path, "w") as f:
        f.write("\n".join(lines))

    # Terminal summary
    print(f"Validation: {dataset} {version}")
    print(f"  Status: {'PASS' if passed else 'FAIL'}")
    print(f"  Errors: {total_errors}, Warnings: {total_warnings}")
    print(f"  Report: {md_path}")
    if not passed:
        for r in all_results:
            if r["errors"]:
                print(f"  [{r['file']}] {r['errors']}")

    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
