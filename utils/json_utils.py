import json
import logging
import os
import sys

BASE_DIR = getattr(
    sys,
    "_MEIPASS",
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..")),
)


def resource_path(*parts):
    return os.path.join(BASE_DIR, *parts)

logger = logging.getLogger(__name__)

# Папка для пользовательских файлов
USER_DATA_DIR = os.path.join("data", "user")
os.makedirs(USER_DATA_DIR, exist_ok=True)

CONVERSION_CONFIG_PATH = os.path.join(USER_DATA_DIR, "conversion_config.json")


def get_conversion_config_path(log_key: str | None = None) -> str:
    """Return path for a conversion config associated with the given log key."""
    if log_key:
        safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in log_key)
        return os.path.join(USER_DATA_DIR, f"conversion_config_{safe}.json")
    return CONVERSION_CONFIG_PATH

USER_PATTERNS_PATH = os.path.join(USER_DATA_DIR, "patterns_user.json")
BUILTIN_PATTERNS_PATH = resource_path("data", "patterns_builtin.json")
LOG_KEY_MAP_PATH = resource_path("data", "log_key_map.json")
BUILTIN_PATTERN_KEYS_PATH = resource_path("data", "builtin_pattern_keys.json")
CEF_FIELDS_PATH = resource_path("data", "cef_fields.json")
PER_LOG_PATTERNS_PATH = os.path.join(USER_DATA_DIR, "per_log_patterns.json")

def load_builtin_pattern_keys():
    try:
        with open(BUILTIN_PATTERN_KEYS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def load_all_patterns():
    """Загружает объединённые пользовательские и встроенные шаблоны."""

    builtin_keys = load_builtin_pattern_keys()

    def _read(path, is_builtin=False):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                data = data.get("patterns", []) if isinstance(data, dict) else data
                for p in data:
                    if "regex" not in p and "pattern" in p:
                        p["regex"] = p.pop("pattern")
                    p["source"] = "builtin" if is_builtin else "user"
                    if is_builtin:
                        p["log_keys"] = builtin_keys.get(p.get("name"), [])
                return data
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    return _read(USER_PATTERNS_PATH) + _read(BUILTIN_PATTERNS_PATH, is_builtin=True)


def load_per_log_patterns_for_file(source_file: str) -> list[dict]:
    """Return patterns tied to the given log file."""

    try:
        with open(PER_LOG_PATTERNS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

    result = []
    for name, entry in data.items():
        file_path = entry.get("file")
        if file_path == source_file or os.path.basename(file_path) == os.path.basename(source_file):
            patterns = entry.get("patterns", {})
            for pat_name, pat in patterns.items():
                pat = pat.copy()
                if "regex" not in pat and "pattern" in pat:
                    pat["regex"] = pat.pop("pattern")
                pat.setdefault("name", pat_name)
                pat.setdefault("enabled", True)
                pat.setdefault("source", "per_log")
                result.append(pat)
            break
    return result


def load_per_log_patterns_by_key(log_key: str) -> list[dict]:
    """Return patterns associated with a saved log key."""

    try:
        with open(PER_LOG_PATTERNS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

    entry = data.get(log_key)
    if not entry:
        return []

    result = []
    for pat_name, pat in entry.get("patterns", {}).items():
        pat = pat.copy()
        if "regex" not in pat and "pattern" in pat:
            pat["regex"] = pat.pop("pattern")
        pat.setdefault("name", pat_name)
        pat.setdefault("enabled", True)
        pat.setdefault("source", "per_log")
        result.append(pat)
    return result


def save_user_patterns(patterns):
    """Сохраняет пользовательские шаблоны."""
    to_save = {"patterns": patterns}
    try:
        os.makedirs(os.path.dirname(USER_PATTERNS_PATH), exist_ok=True)
        with open(USER_PATTERNS_PATH, "w", encoding="utf-8") as f:
            json.dump(to_save, f, indent=4, ensure_ascii=False)
    except IOError as e:
        logger.error("[Ошибка сохранения] %s", e)

def save_user_pattern(new_pattern):
    patterns = load_all_patterns()
    user_patterns = [p for p in patterns if p.get("source") != "builtin"]

    # Удалить старый паттерн с тем же именем
    user_patterns = [p for p in user_patterns if p.get("name") != new_pattern.get("name")]
    user_patterns.append(new_pattern)

    save_user_patterns(user_patterns)


def load_log_key_map():
    try:
        with open(LOG_KEY_MAP_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_log_key_mapping(source_file, keys, log_name=None):
    """Сохраняет сопоставление между лог-файлом и ключами."""

    log_key = log_name if log_name else os.path.basename(source_file)
    data = load_log_key_map()
    data[log_key] = {"file": source_file, "keys": list(keys)}

    try:
        os.makedirs(os.path.dirname(LOG_KEY_MAP_PATH), exist_ok=True)
        with open(LOG_KEY_MAP_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        logger.error("[Ошибка сохранения сопоставления лог-ключей] %s", e)


def get_log_keys_for_file(source_file):
    """Возвращает список ключей, связанных с файлом лога."""

    data = load_log_key_map()
    base = os.path.basename(source_file)
    for name, entry in data.items():
        if entry.get("file") == source_file or name == base:
            return entry.get("keys", [])
    return []


def get_log_name_for_file(source_file):
    """Совместимая обёртка, возвращающая имя (ключ) для файла."""

    data = load_log_key_map()
    for name, entry in data.items():
        if entry.get("file") == source_file:
            return name
    return None


def save_per_log_pattern(source_file, pattern_name, pattern_data, log_name=None):
    """Сохраняет паттерн, привязанный к конкретному логу."""

    try:
        log_key = log_name if log_name else os.path.basename(source_file)

        if os.path.exists(PER_LOG_PATTERNS_PATH):
            with open(PER_LOG_PATTERNS_PATH, "r", encoding="utf-8") as f:
                all_data = json.load(f)
        else:
            all_data = {}

        entry = all_data.get(log_key, {"file": source_file, "patterns": {}})
        entry["file"] = source_file
        pat = pattern_data.copy()
        if "regex" not in pat and "pattern" in pat:
            pat["regex"] = pat.pop("pattern")
        pat.setdefault("enabled", True)
        pat["source"] = "per_log"
        entry.setdefault("patterns", {})[pattern_name] = pat
        all_data[log_key] = entry

        os.makedirs(os.path.dirname(PER_LOG_PATTERNS_PATH), exist_ok=True)
        with open(PER_LOG_PATTERNS_PATH, "w", encoding="utf-8") as f:
            json.dump(all_data, f, indent=4, ensure_ascii=False)

        save_log_key_mapping(source_file, pattern_data.get("log_keys", []), log_name=log_name)
    except Exception as e:
        logger.error("[Ошибка сохранения пер-лог паттерна] %s", e)


def load_cef_fields():
    """Возвращает список словарей с описанием CEF-полей."""
    try:
        with open(CEF_FIELDS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("fields", [])
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def load_cef_field_keys():
    """Возвращает список ключей CEF-полей."""
    return [fld.get("key") for fld in load_cef_fields() if "key" in fld]


def load_conversion_config(log_key: str | None = None) -> dict:
    """Load converter configuration for the given log key."""
    path = get_conversion_config_path(log_key)
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            header = data.get("header", {})
            mappings = data.get("mappings", [])
            log_key_in_file = data.get("log_key")

            # Replace saved pattern names with their regex text
            pattern_map = {p.get("name"): p.get("regex") for p in load_all_patterns()}
            for m in mappings:
                name = m.get("pattern")
                if name and "regex" not in m:
                    regex = pattern_map.get(name)
                    if regex:
                        m["regex"] = regex
            result = {"header": header, "mappings": mappings}
            if log_key_in_file:
                result["log_key"] = log_key_in_file
            return result
    except (FileNotFoundError, json.JSONDecodeError):
        return {"header": {}, "mappings": []}


def save_conversion_config(data: dict, log_key: str | None = None):
    """Save converter configuration for the given log key."""
    path = get_conversion_config_path(log_key)
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        mappings = []
        for m in data.get("mappings", []):
            entry = m.copy()
            # Only persist pattern names
            if isinstance(entry.get("pattern"), dict):
                entry["pattern"] = entry["pattern"].get("name")
            entry.pop("regex", None)
            mappings.append(entry)

        to_save = {"header": data.get("header", {}), "mappings": mappings}
        if log_key:
            to_save["log_key"] = log_key
        with open(path, "w", encoding="utf-8") as f:
            json.dump(to_save, f, indent=4, ensure_ascii=False)
    except Exception as e:
        logger.error("[Ошибка сохранения конвертер-конфига] %s", e)
