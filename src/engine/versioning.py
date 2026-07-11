"""Rules version management — create, modify, diff, and share rule versions.

Storage model:
- v1.0/ — Read-only baseline (full data copies)
- v2.0+/ — Diff-only versions (diff.json + meta.json)
- index.json — Version registry
"""
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

_DATA = Path(__file__).resolve().parent.parent.parent / "data"
_VERSIONS = _DATA / "versions"
_BASELINE = _VERSIONS / "v1.0"

CATEGORIES = ("weapons", "monsters", "spells", "skills", "rules")
MATCH_FIELDS = {
    "weapons": "名称",
    "monsters": "名称",
    "spells": "名称",
    "skills": "名称",
    "rules": "id",
}

_set_default_version: Optional[str] = None


# ---------------------------------------------------------------------------
# Version registry
# ---------------------------------------------------------------------------

def _load_index() -> list[dict]:
    """Load the version index (read-only by callers)."""
    path = _VERSIONS / "index.json"
    if path.exists():
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return []


def _save_index(versions: list[dict]):
    """Persist the version index."""
    _VERSIONS.mkdir(parents=True, exist_ok=True)
    with open(_VERSIONS / "index.json", "w", encoding="utf-8") as f:
        json.dump(versions, f, ensure_ascii=False, indent=2)


def get_version_list() -> list[dict]:
    """Return all registered versions."""
    return _load_index()


def get_version_meta(version_id: str) -> dict:
    """Get metadata for a specific version."""
    meta_path = _VERSIONS / version_id / "meta.json"
    if not meta_path.exists():
        raise ValueError(f"版本 '{version_id}' 不存在")
    with open(meta_path, encoding="utf-8") as f:
        return json.load(f)


def _find_in_index(version_id: str) -> Optional[dict]:
    """Find a version entry in the index, or None."""
    for v in _load_index():
        if v["id"] == version_id:
            return v
    return None


# ---------------------------------------------------------------------------
# Baseline initialization
# ---------------------------------------------------------------------------

def _copy_data_files(src_dir: Path, dst_dir: Path):
    """Copy JSON data files from src to dst (used for v1.0 baseline)."""
    dst_dir.mkdir(parents=True, exist_ok=True)
    for name in ("weapons.json", "monsters.json", "spells.json", "skills.json", "rules.json"):
        src = src_dir / name
        if src.exists():
            shutil.copy2(src, dst_dir / name)

    rule_src = src_dir / "rules"
    rule_dst = dst_dir / "rules"
    if rule_src.is_dir():
        rule_dst.mkdir(parents=True, exist_ok=True)
        for f in rule_src.glob("*.json"):
            shutil.copy2(f, rule_dst / f.name)


def _ensure_baseline():
    """Create v1.0 baseline from data/ if it doesn't exist."""
    if _BASELINE.exists():
        return
    _copy_data_files(_DATA, _BASELINE)

    # Add to index if not already there
    index = _load_index()
    if not any(v["id"] == "v1.0" for v in index):
        index.insert(0, {
            "id": "v1.0",
            "name": "七版标准规则",
            "based_on": None,
            "readonly": True,
            "created_at": datetime.now().strftime("%Y-%m-%d"),
        })
        _save_index(index)


# ---------------------------------------------------------------------------
# Version creation
# ---------------------------------------------------------------------------

def create_version(
    version_id: str,
    name: str,
    based_on: str = "v1.0",
    description: str = "",
) -> dict:
    """Create a new house-rule version."""
    # Validate
    if _find_in_index(version_id):
        raise ValueError(f"版本 '{version_id}' 已存在")
    if based_on != "v1.0" and not _find_in_index(based_on):
        raise ValueError(f"基础版本 '{based_on}' 不存在")

    # Ensure baseline exists
    _ensure_baseline()

    # Create version directory
    ver_dir = _VERSIONS / version_id
    ver_dir.mkdir(parents=True, exist_ok=True)

    meta = {
        "name": name,
        "based_on": based_on,
        "created_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "description": description,
    }
    with open(ver_dir / "meta.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    # Empty diff
    diff = {c: [] for c in CATEGORIES}
    with open(ver_dir / "diff.json", "w", encoding="utf-8") as f:
        json.dump(diff, f, ensure_ascii=False, indent=2)

    # Register
    index = _load_index()
    index.append({
        "id": version_id,
        "name": name,
        "based_on": based_on,
        "readonly": False,
        "created_at": datetime.now().strftime("%Y-%m-%d"),
    })
    _save_index(index)
    return meta


# ---------------------------------------------------------------------------
# Diff file helpers
# ---------------------------------------------------------------------------

def _load_diff(version_id: str) -> dict:
    """Load diff.json for a version."""
    path = _VERSIONS / version_id / "diff.json"
    if path.exists():
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return {c: [] for c in CATEGORIES}


def _save_diff(version_id: str, diff: dict):
    """Save diff.json for a version."""
    path = _VERSIONS / version_id / "diff.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(diff, f, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
# Rule modification (CRUD)
# ---------------------------------------------------------------------------

def _get_match_key(category: str, entry: dict) -> str:
    """Return the canonical key for matching, e.g. '名称' or 'id'."""
    return entry.get("名称") or entry.get("id", "")


def modify_rule(version_id: str, category: str, match: dict, changes: dict) -> dict:
    """Modify an existing rule in a version's diff.

    Args:
        version_id: e.g. "v2.0"
        category: one of weapons/monsters/spells/skills/rules
        match: dict to identify the entry, e.g. {"名称": "AK-47"}
        changes: dict of fields to update, e.g. {"时代": "禁用"}

    Returns:
        The diff entry that was created/updated.
    """
    _validate_modification(version_id, category)
    diff = _load_diff(version_id)
    diff_entries = diff.setdefault(category, [])

    match_key = _get_match_key(category, match)

    # Check if there's already a diff entry for this item
    for entry in diff_entries:
        if _get_match_key(category, entry) == match_key:
            if entry["action"] == "modify":
                entry["changes"].update(changes)
            elif entry["action"] == "remove":
                raise ValueError(f"无法修改已删除的条目 '{match_key}' — 请先 add 恢复")
            else:
                entry["data"].update(changes)
            _save_diff(version_id, diff)
            return entry

    # New diff entry
    new_entry = {
        **match,
        "action": "modify",
        "changes": changes,
    }
    diff_entries.append(new_entry)
    _save_diff(version_id, diff)
    return new_entry


def remove_rule(version_id: str, category: str, match: dict) -> dict:
    """Mark a rule as removed in a version's diff.

    Args:
        version_id: e.g. "v2.0"
        category: one of weapons/monsters/spells/skills/rules
        match: dict to identify the entry

    Returns:
        The diff entry that was created.
    """
    _validate_modification(version_id, category)
    diff = _load_diff(version_id)
    diff_entries = diff.setdefault(category, [])

    match_key = _get_match_key(category, match)

    # Remove any existing diff entry for this item, then add a "remove" entry
    diff[category] = [e for e in diff_entries if _get_match_key(category, e) != match_key]

    new_entry = {**match, "action": "remove"}
    diff[category].append(new_entry)
    _save_diff(version_id, diff)
    return new_entry


def add_rule(version_id: str, category: str, data: dict) -> dict:
    """Add a custom rule to a version's diff.

    Args:
        version_id: e.g. "v2.0"
        category: one of weapons/monsters/spells/skills/rules
        data: full entry data

    Returns:
        The diff entry that was created.
    """
    _validate_modification(version_id, category)
    diff = _load_diff(version_id)
    diff_entries = diff.setdefault(category, [])

    match_key = _get_match_key(category, data)

    # Check if already exists in diff
    for entry in diff_entries:
        if _get_match_key(category, entry) == match_key:
            if entry["action"] == "remove":
                # Re-add previously removed: convert to modify
                diff[category] = [e for e in diff_entries if _get_match_key(category, e) != match_key]
                new_entry = {
                    **{k: data[k] for k in data if k != "action"},
                    "action": "modify",
                    "changes": data,
                }
                diff[category].append(new_entry)
                _save_diff(version_id, diff)
                return new_entry
            raise ValueError(f"条目 '{match_key}' 已在 diff 中存在 (action={entry['action']})")

    new_entry = {"action": "add", "data": data}
    diff[category].append(new_entry)
    _save_diff(version_id, diff)
    return new_entry


def _validate_modification(version_id: str, category: str):
    """Validate that the version is writable and category is valid."""
    if category not in CATEGORIES:
        raise ValueError(f"无效的数据类型 '{category}'。可用: {', '.join(CATEGORIES)}")

    ver = _find_in_index(version_id)
    if not ver:
        ver_dir = _VERSIONS / version_id
        if not ver_dir.exists():
            raise ValueError(f"版本 '{version_id}' 不存在")
    elif ver.get("readonly"):
        raise ValueError(f"版本 '{version_id}' 为只读基线，不可修改")


# ---------------------------------------------------------------------------
# Version-aware data loading
# ---------------------------------------------------------------------------

def _load_baseline_data(category: str) -> list[dict]:
    """Load data from v1.0 baseline."""
    _ensure_baseline()
    if category == "rules":
        path = _BASELINE / "rules.json"
    else:
        path = _BASELINE / f"{category}.json"
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_version_data(version_id: str, category: str) -> list[dict]:
    """Load data for a category, applying the version's diff on top of baseline.

    Args:
        version_id: Version to load, e.g. "v2.0"
        category: One of weapons/monsters/spells/skills/rules

    Returns:
        Merged list of entries (baseline + diff applied).
    """
    if version_id == "v1.0":
        return _load_baseline_data(category)

    if not _find_in_index(version_id):
        ver_dir = _VERSIONS / version_id
        if not ver_dir.exists():
            raise ValueError(f"版本 '{version_id}' 不存在")

    # Load baseline
    base_data = _load_baseline_data(category)

    # Load diff
    diff = _load_diff(version_id)
    diff_entries = diff.get(category, [])
    if not diff_entries:
        return base_data

    match_field = MATCH_FIELDS[category]

    # Build lookup by match key
    base_index = {}
    for entry in base_data:
        key = entry.get(match_field, "")
        base_index[key] = entry

    remove_set = set()
    add_list = []
    modify_map: dict[str, dict] = {}

    for de in diff_entries:
        a = de.get("action")
        key = de.get(match_field, "")
        if a == "remove":
            remove_set.add(key)
        elif a == "add":
            add_list.append(de["data"])
        elif a == "modify":
            modify_map[key] = de.get("changes", {})

    # Build result
    result = []
    for entry in base_data:
        key = entry.get(match_field, "")
        if key in remove_set:
            continue
        if key in modify_map:
            merged = dict(entry)
            merged.update(modify_map[key])
            result.append(merged)
        else:
            result.append(entry)
    result.extend(add_list)
    return result


# ---------------------------------------------------------------------------
# Version diff
# ---------------------------------------------------------------------------

def diff_versions(from_id: str, to_id: str) -> dict:
    """Compare two versions and return structured differences.

    Returns:
        dict of category -> list of change entries:
        {
            "weapons": [
                {"name": "12号泵动式霰弹枪", "change": "modified", "field": "时代",
                 "old": "1920s，现代", "new": "禁用"},
                {"name": "AK-47", "change": "removed"},
                {"name": "激光步枪", "change": "added"}
            ],
            ...
        }
    """
    result = {}
    for cat in CATEGORIES:
        from_data = load_version_data(from_id, cat)
        to_data = load_version_data(to_id, cat)
        result[cat] = _diff_entries(from_data, to_data, cat)
    return result


def _diff_entries(
    from_entries: list[dict],
    to_entries: list[dict],
    category: str,
) -> list[dict]:
    """Compute diff between two lists of entries."""
    match_field = MATCH_FIELDS[category]
    changes = []

    from_index = {}
    for e in from_entries:
        key = e.get(match_field, "")
        from_index[key] = e

    to_index = {}
    for e in to_entries:
        key = e.get(match_field, "")
        to_index[key] = e

    # Detect removed
    for key in from_index:
        if key not in to_index:
            changes.append({"name": key, "change": "removed"})

    # Detect added and modified
    for key in to_index:
        if key not in from_index:
            changes.append({"name": key, "change": "added"})
        else:
            from_e = from_index[key]
            to_e = to_index[key]
            field_diffs = []
            for fk in set(list(from_e.keys()) + list(to_e.keys())):
                old = from_e.get(fk)
                new = to_e.get(fk)
                if old != new:
                    field_diffs.append({
                        "name": key,
                        "change": "modified",
                        "field": fk,
                        "old": old,
                        "new": new,
                    })
            changes.extend(field_diffs)

    return changes


# ---------------------------------------------------------------------------
# Default version
# ---------------------------------------------------------------------------

def set_default_version(version_id: Optional[str]):
    """Set the global default version for subsequent queries."""
    global _set_default_version
    if version_id and version_id != "v1.0":
        ver_dir = _VERSIONS / version_id
        if not ver_dir.exists():
            raise ValueError(f"版本 '{version_id}' 不存在")
    _set_default_version = version_id


def get_default_version() -> Optional[str]:
    """Get the currently set default version."""
    return _set_default_version


# ---------------------------------------------------------------------------
# Export / Import
# ---------------------------------------------------------------------------

def export_version(version_id: str, filepath: str) -> str:
    """Export a version as a single JSON file (diff only, not full data).

    Returns:
        Absolute path of the exported file.
    """
    if not _find_in_index(version_id):
        raise ValueError(f"版本 '{version_id}' 不存在")

    meta = get_version_meta(version_id)
    diff = _load_diff(version_id)

    export_data = {
        "version": version_id,
        "meta": meta,
        "diff": diff,
    }

    out = Path(filepath).resolve()
    with open(out, "w", encoding="utf-8") as f:
        json.dump(export_data, f, ensure_ascii=False, indent=2)
    return str(out)


def import_version(filepath: str, as_name: Optional[str] = None) -> str:
    """Import a version from an exported JSON file.

    Args:
        filepath: Path to the exported JSON file.
        as_name: Use this version ID instead of the original.

    Returns:
        The version ID of the imported version.
    """
    with open(filepath, encoding="utf-8") as f:
        export_data = json.load(f)

    orig_id = export_data["version"]
    meta = export_data["meta"]
    diff = export_data["diff"]

    target_id = as_name or orig_id

    # Create version directory
    ver_dir = _VERSIONS / target_id
    ver_dir.mkdir(parents=True, exist_ok=True)

    # Update meta
    meta["imported_from"] = orig_id
    meta["imported_at"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

    with open(ver_dir / "meta.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    with open(ver_dir / "diff.json", "w", encoding="utf-8") as f:
        json.dump(diff, f, ensure_ascii=False, indent=2)

    # Register in index
    index = _load_index()
    existing = _find_in_index(target_id)
    if existing:
        existing["name"] = meta.get("name", target_id)
    else:
        index.append({
            "id": target_id,
            "name": meta.get("name", target_id),
            "based_on": meta.get("based_on", "v1.0"),
            "readonly": False,
            "created_at": datetime.now().strftime("%Y-%m-%d"),
        })
    _save_index(index)
    return target_id
