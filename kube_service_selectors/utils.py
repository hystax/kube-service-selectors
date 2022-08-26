import re

from typing import Optional, Dict, Tuple, List

INVALID_LABEL_CHAR = re.compile("[^a-zA-Z0-9_]")
MATCH_ALL_CAP = re.compile("([a-z0-9])([A-Z])")
LABEL_PREFIX = "label"
CONFLICT_SUFFIX = "conflict"


def to_snake_case(value: str) -> str:
    return re.sub(MATCH_ALL_CAP, r"\1_\2", value).lower()


def sanitize_label_name(value: str) -> str:
    return re.sub(INVALID_LABEL_CHAR, "_", value)


def label_conflict_suffix(label: str, count: int) -> str:
    return f"{label}_{CONFLICT_SUFFIX}{count}"


def get_label_name(label_key: str, prefix: Optional[str] = None) -> str:
    res = sanitize_label_name(label_key)
    res = to_snake_case(res)
    if prefix:
        res = f"{prefix}_{res}"
    return res


class Conflict:
    def __init__(self, initial):
        self.initial = initial
        self.count = 1


def map_to_prometheus_labels(
    labels: Dict[str, str]
) -> Tuple[List[str], List[str]]:
    label_keys = []
    label_values = []
    conflicts = {}
    for k in sorted(labels.keys()):
        label_key = get_label_name(k, prefix=LABEL_PREFIX)
        conflict = conflicts.get(label_key)
        if conflict:
            if conflict.count == 1:
                label_keys[conflict.initial] = label_conflict_suffix(
                    label_keys[conflict.initial], conflict.count
                )
            conflicts[label_key].count += 1
            label_key = label_conflict_suffix(label_key, conflict.count)
        else:
            conflicts[label_key] = Conflict(len(label_keys))

        label_keys.append(label_key)
        label_values.append(labels[k])
    return label_keys, label_values
