from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


ALLOWED_MASK_VALUES = {
    0,
    1,
    255,
}


def parse_mask_values(value: object) -> set[int]:
    if pd.isna(value):
        return set()

    text = str(value).strip()

    if not text:
        return set()

    values = set()

    for part in text.split("|"):
        try:
            values.add(int(part))
        except ValueError:
            pass

    return values


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate BLUE-RESCUE sonar dataset manifest."
    )

    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path(
            "ml/manifests/ai4shipwrecks_manifest.csv"
        ),
    )

    parser.add_argument(
        "--report",
        type=Path,
        default=Path(
            "ml/manifests/ai4shipwrecks_validation.json"
        ),
    )

    args = parser.parse_args()

    if not args.manifest.exists():
        raise FileNotFoundError(
            f"Manifest not found: {args.manifest}"
        )

    dataframe = pd.read_csv(args.manifest)

    total_records = len(dataframe)

    missing_labels = int(
        (dataframe["label_exists"] != True).sum()
    )

    dimension_mismatches = int(
        (
            (dataframe["label_exists"] == True)
            & (dataframe["dimensions_match"] != True)
        ).sum()
    )

    invalid_mask_samples: list[str] = []

    for _, row in dataframe.iterrows():
        if row.get("label_exists") != True:
            continue

        mask_values = parse_mask_values(
            row.get("label_values")
        )

        if not mask_values:
            continue

        if not mask_values.issubset(
            ALLOWED_MASK_VALUES
        ):
            invalid_mask_samples.append(
                str(row["sample_id"])
            )

    valid_image_rows = dataframe[
        dataframe["image_sha256"]
        .fillna("")
        .astype(str)
        .str.len()
        > 0
    ]

    duplicate_groups = (
        valid_image_rows
        .groupby("image_sha256")["sample_id"]
        .apply(list)
    )

    duplicate_groups = {
        hash_value: samples
        for hash_value, samples
        in duplicate_groups.items()
        if len(samples) > 1
    }

    leakage_groups: dict[str, list[str]] = {}

    for hash_value, samples in duplicate_groups.items():
        rows = valid_image_rows[
            valid_image_rows["image_sha256"]
            == hash_value
        ]

        splits = set(
            rows["split"]
            .astype(str)
            .tolist()
        )

        if len(splits) > 1:
            leakage_groups[hash_value] = samples

    valid_samples = int(
        (
            dataframe["quality_status"]
            == "OK"
        ).sum()
    )

    report = {
        "dataset": "AI4Shipwrecks",
        "task": "shipwreck_segmentation",
        "total_records": total_records,
        "valid_samples": valid_samples,
        "missing_labels": missing_labels,
        "dimension_mismatches": (
            dimension_mismatches
        ),
        "invalid_mask_samples": (
            invalid_mask_samples
        ),
        "duplicate_image_groups": (
            duplicate_groups
        ),
        "cross_split_leakage_groups": (
            leakage_groups
        ),
        "validation_passed": (
            missing_labels == 0
            and dimension_mismatches == 0
            and len(invalid_mask_samples) == 0
            and len(leakage_groups) == 0
        ),
    }

    args.report.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    args.report.write_text(
        json.dumps(
            report,
            indent=2,
        ),
        encoding="utf-8",
    )

    print()
    print("BLUE-RESCUE Dataset Validation")
    print("=" * 40)

    print(f"Records             : {total_records}")
    print(f"Valid samples       : {valid_samples}")
    print(f"Missing labels      : {missing_labels}")
    print(
        f"Dimension mismatch  : "
        f"{dimension_mismatches}"
    )
    print(
        f"Invalid masks       : "
        f"{len(invalid_mask_samples)}"
    )
    print(
        f"Duplicate groups    : "
        f"{len(duplicate_groups)}"
    )
    print(
        f"Cross-split leakage : "
        f"{len(leakage_groups)}"
    )

    print()

    if report["validation_passed"]:
        print("RESULT: PASS")
    else:
        print("RESULT: REVIEW REQUIRED")

    print()
    print(
        f"Validation report saved to: "
        f"{args.report}"
    )


if __name__ == "__main__":
    main()