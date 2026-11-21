"""Pure helpers for Donetick label todo lists (no HA import)."""

from __future__ import annotations

from typing import Any

HA_LABEL_MARKER_PREFIX = "ha-label:"


def normalize_label_name(name: str | None) -> str | None:
    if not name:
        return None
    normalized = name.strip().lower()
    return normalized or None


def label_key(label_id: int | None, normalized_name: str | None) -> str | None:
    if label_id is not None:
        return f"id_{label_id}"
    if normalized_name:
        return f"name_{normalized_name}"
    return None


def collect_label_descriptors(tasks: list[Any]) -> list[dict[str, Any]]:
    """Collect unique labels from task-like objects with labels_v2 / label_names."""
    label_map: dict[str, dict[str, Any]] = {}
    for task in tasks:
        if not task or not getattr(task, "is_active", True):
            continue
        labels_v2 = getattr(task, "labels_v2", None) or []
        if labels_v2:
            for label in labels_v2:
                name = getattr(label, "name", None)
                lid = getattr(label, "id", None)
                color = getattr(label, "color", None)
                normalized = normalize_label_name(name)
                key = label_key(lid, normalized)
                if not key or key in label_map:
                    continue
                label_map[key] = {
                    "label_id": lid,
                    "label_name": name or f"Label {lid}",
                    "normalized_name": normalized,
                    "color": color,
                }
            continue
        for name in getattr(task, "label_names", None) or []:
            normalized = normalize_label_name(name)
            key = label_key(None, normalized)
            if not key or key in label_map:
                continue
            label_map[key] = {
                "label_id": None,
                "label_name": name,
                "normalized_name": normalized,
                "color": None,
            }
    return sorted(label_map.values(), key=lambda item: item["label_name"].lower())


def description_label_names(description: str | None) -> list[str]:
    """Return HA-managed label markers from a Donetick description."""
    if not description:
        return []
    labels = []
    for raw_line in str(description).replace("<!--", "\n").replace("-->", "\n").splitlines():
        line = raw_line.strip()
        if not line.lower().startswith(HA_LABEL_MARKER_PREFIX):
            continue
        normalized = normalize_label_name(line[len(HA_LABEL_MARKER_PREFIX) :])
        if normalized and normalized not in labels:
            labels.append(normalized)
    return labels


def ensure_description_label_marker(
    description: str | None,
    normalized_name: str | None,
) -> str | None:
    """Append an HA label marker so eAPI-created chores stay in label lists."""
    if not normalized_name:
        return description
    existing = description or ""
    marker = f"<!-- {HA_LABEL_MARKER_PREFIX}{normalized_name} -->"
    if normalized_name in description_label_names(existing):
        return existing
    return f"{existing}\n{marker}".strip()


def task_matches_label(
    task: Any,
    *,
    label_id: int | None,
    normalized_name: str | None,
) -> bool:
    if label_id is not None:
        for label in getattr(task, "labels_v2", None) or []:
            if getattr(label, "id", None) == label_id:
                return True
    if normalized_name:
        names = getattr(task, "label_names_normalized", None) or []
        if normalized_name in names:
            return True
        if normalized_name in description_label_names(getattr(task, "description", None)):
            return True
    return False
