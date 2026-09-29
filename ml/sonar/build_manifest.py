from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image


VALID_IMAGE_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".tif",
    ".tiff",
}


def sha256_file(path: Path) -> str:
    """Return SHA-256 hash for duplicate/leakage checking."""

    digest = hashlib.sha256()

    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)

    return digest.hexdigest()


def find_files(directory: Path) -> list[Path]:
    """Return supported image files from a directory."""

    if not directory.exists():
        raise FileNotFoundError(
            f"Required directory does not exist: {directory}"
        )

    return sorted(
        path
        for path in directory.iterdir()
        if path.is_file()
        and path.suffix.lower() in VALID_IMAGE_EXTENSIONS
    )


def inspect_mask(mask_path: Path) -> dict:
    """Inspect a segmentation mask."""

    with Image.open(mask_path) as mask_image:
        mask_array = np.asarray(mask_image)

        if mask_array.ndim == 3:
            mask_array = mask_array[..., 0]

        unique_values = np.unique(mask_array)

        foreground_pixels = int(np.count_nonzero(mask_array))
        total_pixels = int(mask_array.size)

        foreground_fraction = (
            foreground_pixels / total_pixels
            if total_pixels > 0
            else 0.0
        )

        width, height = mask_image.size

    return {
        "label_width": width,
        "label_height": height,
        "label_values": "|".join(
            str(int(value))
            for value in unique_values.tolist()
        ),
        "foreground_pixels": foreground_pixels,
        "foreground_fraction": round(
            foreground_fraction,
            8,
        ),
    }


def collect_split(
    dataset_root: Path,
    split: str,
) -> list[dict]:
    """
    Collect image/label metadata for one split.

    Expected local normalized structure:

    datasets/AI4Shipwrecks/
        train/
            images/
            labels/
        test/
            images/
            labels/
    """

    images_directory = dataset_root / split / "images"
    labels_directory = dataset_root / split / "labels"

    image_files = find_files(images_directory)
    label_files = find_files(labels_directory)

    labels_by_stem = {
        path.stem: path
        for path in label_files
    }

    rows: list[dict] = []

    for image_path in image_files:
        label_path = labels_by_stem.get(image_path.stem)

        with Image.open(image_path) as image:
            image_width, image_height = image.size
            image_mode = image.mode

        row = {
            "sample_id": f"{split}:{image_path.stem}",
            "split": split,
            "image_name": image_path.name,
            "image_path": image_path.as_posix(),
            "image_width": image_width,
            "image_height": image_height,
            "image_mode": image_mode,
            "image_sha256": sha256_file(image_path),
            "label_name": "",
            "label_path": "",
            "label_exists": False,
            "label_width": "",
            "label_height": "",
            "label_values": "",
            "foreground_pixels": "",
            "foreground_fraction": "",
            "dimensions_match": False,
            "quality_status": "MISSING_LABEL",
        }

        if label_path is not None:
            label_info = inspect_mask(label_path)

            dimensions_match = (
                image_width == label_info["label_width"]
                and image_height == label_info["label_height"]
            )

            row.update(
                {
                    "label_name": label_path.name,
                    "label_path": label_path.as_posix(),
                    "label_exists": True,
                    "label_sha256": sha256_file(label_path),
                    **label_info,
                    "dimensions_match": dimensions_match,
                    "quality_status": (
                        "OK"
                        if dimensions_match
                        else "DIMENSION_MISMATCH"
                    ),
                }
            )
        else:
            row["label_sha256"] = ""

        rows.append(row)

    image_stems = {
        path.stem
        for path in image_files
    }

    orphan_labels = [
        path
        for path in label_files
        if path.stem not in image_stems
    ]

    for label_path in orphan_labels:
        rows.append(
            {
                "sample_id": f"{split}:ORPHAN:{label_path.stem}",
                "split": split,
                "image_name": "",
                "image_path": "",
                "image_width": "",
                "image_height": "",
                "image_mode": "",
                "image_sha256": "",
                "label_name": label_path.name,
                "label_path": label_path.as_posix(),
                "label_exists": True,
                "label_sha256": sha256_file(label_path),
                "label_width": "",
                "label_height": "",
                "label_values": "",
                "foreground_pixels": "",
                "foreground_fraction": "",
                "dimensions_match": False,
                "quality_status": "ORPHAN_LABEL",
            }
        )

    return rows


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build BLUE-RESCUE sonar dataset manifest."
    )

    parser.add_argument(
        "--dataset-root",
        type=Path,
        default=Path("datasets/AI4Shipwrecks"),
        help="Dataset root directory.",
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=Path(
            "ml/manifests/ai4shipwrecks_manifest.csv"
        ),
        help="Output manifest CSV.",
    )

    args = parser.parse_args()

    all_rows: list[dict] = []

    for split in ("train", "test"):
        all_rows.extend(
            collect_split(
                args.dataset_root,
                split,
            )
        )

    dataframe = pd.DataFrame(all_rows)

    args.output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    dataframe.to_csv(
        args.output,
        index=False,
    )

    print()
    print("BLUE-RESCUE Sonar Manifest")
    print("=" * 40)

    print(f"Total records : {len(dataframe)}")

    if not dataframe.empty:
        print()
        print("Split counts:")
        print(
            dataframe["split"]
            .value_counts()
            .to_string()
        )

        print()
        print("Quality status:")
        print(
            dataframe["quality_status"]
            .value_counts()
            .to_string()
        )

    print()
    print(f"Manifest saved to: {args.output}")


if __name__ == "__main__":
    main()