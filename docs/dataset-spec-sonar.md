# BLUE-RESCUE AI — Sonar Dataset Specification V1

## Owner

Om Srivastav

---

# Task

Supervised side-scan-sonar underwater-target analysis.

The final V1 task may be segmentation or object detection depending on the approved dataset annotations.

---

# Required Data

Side-scan sonar imagery.

Preferred formats:

- PNG
- JPEG
- TIFF

---

# Labels

Only genuine dataset labels may be used.

Example:

If the original dataset class is:

`pipeline`

it must not be renamed:

`wreckage`

without genuine ground truth.

---

# Metadata

Preserve where available:

- dataset name
- dataset source
- original image ID
- survey/site
- sensor information
- annotation type
- image dimensions
- licence
- quality status

---

# Annotation Types

Segmentation:

- binary mask
- class mask

Detection:

- YOLO
- COCO
- bounding boxes

---

# Dataset Split

Required:

- train
- validation
- test

Prefer survey/site-based splitting where metadata permits.

Nearly identical neighbouring sonar frames should not be distributed across both training and test sets.

---

# Quality Checks

Flag or reject:

- corrupted images
- missing labels
- image/mask dimension mismatch
- duplicate samples
- invalid masks
- invalid bounding boxes
- undocumented files

---

# Evaluation

For segmentation:

- IoU
- Dice/F1
- Precision
- Recall

For detection:

- Precision
- Recall
- mAP@50
- mAP@50-95

False negatives must be reported explicitly.

---

# Repository Rules

Raw datasets must not be committed to the normal Git repository.

Track:

- manifests
- metadata
- preprocessing scripts
- configuration
- documentation

Synthetic/demo data must not be presented as real field data.