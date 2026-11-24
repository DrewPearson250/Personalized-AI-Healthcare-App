"""Load config/reason_groups.yaml and map NHAMCS RFV codes / symptom-set labels to groups."""
from pathlib import Path

import yaml

CONFIG = Path("config/reason_groups.yaml")


def load(path=CONFIG):
    return yaml.safe_load(Path(path).read_text())


def rfv_mapper(cfg=None):
    """Return f(file_value) -> group id or None. File values are codes x 10 (10501 = 1050.1)."""
    cfg = cfg or load()
    ranges = [(g["id"], lo, hi) for g in cfg["groups"] for lo, hi in g.get("rfv", [])]

    def f(value):
        if value is None or value <= 0:
            return None
        code = value / 10
        return next((gid for gid, lo, hi in ranges if lo <= code <= hi + 1e-9), None)
    return f


def symptom_set_map(cfg=None):
    cfg = cfg or load()
    return {lab: g["id"] for g in cfg["groups"] for lab in g.get("symptom_set", [])}
