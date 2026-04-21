import json
import uuid
import os
import stat
import tempfile
from datetime import datetime

DATA_FILE = os.path.join(os.path.dirname(__file__), "library.json")
HISTORY_FILE = os.path.join(os.path.dirname(__file__), "history.json")
SETTINGS_FILE = os.path.join(os.path.dirname(__file__), "settings.json")

DEFAULT_SETTINGS = {
    "max_history": 200  # -1 = unlimited
}

DEFAULT_DATA = {
    "categories": [
        {
            "id": str(uuid.uuid4()),
            "name": "SQL Queries",
            "items": [
                {
                    "id": str(uuid.uuid4()),
                    "title": "Example: Select all from table",
                    "content": "SELECT * FROM table_name LIMIT 100;"
                }
            ]
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Important Numbers",
            "items": []
        }
    ]
}


def _atomic_write(path: str, data, **json_kwargs):
    """Write JSON to a temp file then rename — prevents corruption on crash."""
    dir_ = os.path.dirname(path)
    fd, tmp = tempfile.mkstemp(dir=dir_)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, **json_kwargs)
        os.replace(tmp, path)          # atomic on POSIX / Windows
        if os.name != "nt":            # chmod is a no-op on Windows
            os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)  # 600 — owner only
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def load() -> dict:
    if not os.path.exists(DATA_FILE):
        save(DEFAULT_DATA)
        return DEFAULT_DATA
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if "categories" not in data:
            raise ValueError("missing categories key")
        return data
    except Exception:
        save(DEFAULT_DATA)
        return DEFAULT_DATA


def save(data: dict):
    _atomic_write(DATA_FILE, data, indent=2, ensure_ascii=False)


# --- Category operations ---

def add_category(data: dict, name: str) -> dict:
    cat = {"id": str(uuid.uuid4()), "name": name, "items": []}
    data["categories"].append(cat)
    save(data)
    return cat


def rename_category(data: dict, cat_id: str, new_name: str):
    for cat in data["categories"]:
        if cat["id"] == cat_id:
            cat["name"] = new_name
            break
    save(data)


def delete_category(data: dict, cat_id: str):
    data["categories"] = [c for c in data["categories"] if c["id"] != cat_id]
    save(data)


# --- Item operations ---

def _derive_title(content: str) -> str:
    """First non-empty line, truncated to 60 chars."""
    for line in content.splitlines():
        line = line.strip()
        if line:
            return line[:60] + ("…" if len(line) > 60 else "")
    return content[:60]


def add_item(data: dict, cat_id: str, content: str) -> dict:
    item = {"id": str(uuid.uuid4()), "title": _derive_title(content), "content": content}
    for cat in data["categories"]:
        if cat["id"] == cat_id:
            cat["items"].append(item)
            break
    save(data)
    return item


def update_item(data: dict, cat_id: str, item_id: str, content: str):
    for cat in data["categories"]:
        if cat["id"] == cat_id:
            for item in cat["items"]:
                if item["id"] == item_id:
                    item["title"] = _derive_title(content)
                    item["content"] = content
                    break
    save(data)


def delete_item(data: dict, cat_id: str, item_id: str):
    for cat in data["categories"]:
        if cat["id"] == cat_id:
            cat["items"] = [i for i in cat["items"] if i["id"] != item_id]
            break
    save(data)


def update_item_used(data: dict, cat_id: str, item_id: str):
    """Increment use_count and stamp last_used when an item is copied."""
    for cat in data["categories"]:
        if cat["id"] == cat_id:
            for item in cat["items"]:
                if item["id"] == item_id:
                    item["use_count"] = item.get("use_count", 0) + 1
                    item["last_used"] = datetime.now().isoformat(timespec="seconds")
                    break
    save(data)


def get_recently_used(data: dict, n: int = 5) -> list[dict]:
    """Return up to n items sorted by last_used, most recent first."""
    all_items = []
    for cat in data["categories"]:
        for item in cat["items"]:
            if "last_used" in item:
                all_items.append({**item, "cat_id": cat["id"], "category": cat["name"]})
    all_items.sort(key=lambda x: x.get("last_used", ""), reverse=True)
    return all_items[:n]


def reorder_data(data: dict, new_order: list[dict]):
    """Reorder categories and items from tree state.
    new_order = [{"id": cat_id, "item_ids": [item_id, ...]}, ...]
    Items may have moved between categories, so use a global item map.
    """
    global_item_map = {i["id"]: i for c in data["categories"] for i in c["items"]}
    cat_map = {c["id"]: c for c in data["categories"]}
    new_categories = []
    for entry in new_order:
        cat = cat_map.get(entry["id"])
        if not cat:
            continue
        cat["items"] = [global_item_map[iid] for iid in entry["item_ids"] if iid in global_item_map]
        new_categories.append(cat)
    data["categories"] = new_categories
    save(data)


# --- Settings ---

def load_settings() -> dict:
    if not os.path.exists(SETTINGS_FILE):
        save_settings(DEFAULT_SETTINGS.copy())
        return DEFAULT_SETTINGS.copy()
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            return {**DEFAULT_SETTINGS, **json.load(f)}
    except Exception:
        return DEFAULT_SETTINGS.copy()


def save_settings(settings: dict):
    _atomic_write(SETTINGS_FILE, settings, indent=2)


# --- History ---
# Each entry: {"text": str, "ts": ISO-8601 string}

def load_history() -> list[dict]:
    if not os.path.exists(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Validate: must be a list of dicts with "text" and "ts"
        return [
            h for h in data
            if isinstance(h, dict) and "text" in h and "ts" in h
        ]
    except Exception:
        return []


def save_history(history: list[dict]):
    _atomic_write(HISTORY_FILE, history, ensure_ascii=False)


def clear_history_before(history: list[dict], cutoff: datetime) -> list[dict]:
    """Return new list with entries on or after cutoff date (time ignored)."""
    cutoff_date = cutoff.date()
    result = []
    for h in history:
        try:
            if datetime.fromisoformat(h["ts"]).date() >= cutoff_date:
                result.append(h)
        except (ValueError, KeyError):
            result.append(h)  # keep entries with unparseable timestamps
    return result


# --- Library search ---

def search(data: dict, query: str) -> list[dict]:
    """Return flat list of matching items with their category name attached."""
    query = query.lower()
    results = []
    for cat in data["categories"]:
        for item in cat["items"]:
            if query in item["title"].lower() or query in item["content"].lower():
                results.append({**item, "category": cat["name"], "cat_id": cat["id"]})
    return results
