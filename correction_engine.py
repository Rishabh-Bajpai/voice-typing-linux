import json
import os
import re
import difflib
import uuid
import time

CORRECTIONS_FILE = os.path.join(
    os.path.expanduser("~"), ".voice_typing_corrections.json"
)
MIN_PATTERN_LENGTH = 3
MAX_CORRECTIONS = 200


def load_corrections():
    if not os.path.exists(CORRECTIONS_FILE):
        return []
    try:
        with open(CORRECTIONS_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"[CORR] Error loading corrections: {e}", flush=True)
        return []


def save_corrections(corrections):
    try:
        with open(CORRECTIONS_FILE, "w") as f:
            json.dump(corrections, f, indent=2)
    except Exception as e:
        print(f"[CORR] Error saving corrections: {e}", flush=True)


def new_correction(pattern, replacement, source="manual", context_left="", context_right=""):
    return {
        "id": str(uuid.uuid4()),
        "pattern": pattern.strip(),
        "replacement": replacement.strip(),
        "case_sensitive": False,
        "whole_word": True,
        "context_left": context_left,
        "context_right": context_right,
        "exceptions": [],
        "enabled": True,
        "hits": 0,
        "last_hit": None,
        "source": source,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }


def validate_correction(pattern, replacement):
    errors = []
    if not pattern or not pattern.strip():
        errors.append("Pattern is required")
    elif len(pattern.strip()) < MIN_PATTERN_LENGTH:
        errors.append(f"Pattern must be at least {MIN_PATTERN_LENGTH} characters")
    if not replacement or not replacement.strip():
        errors.append("Replacement is required")
    if pattern.strip() == replacement.strip():
        errors.append("Pattern and replacement must differ")
    return errors


def _match_has_exception(full_text, start, end, exceptions):
    if not exceptions:
        return False
    before = full_text[:start].rstrip()
    after = full_text[end:].lstrip()
    left_word = before.split()[-1] if before else ""
    right_word = after.split()[0] if after else ""
    for exc in exceptions:
        el = exc.get("left", "").strip().lower()
        er = exc.get("right", "").strip().lower()
        if el and er:
            if left_word.lower() == el and right_word.lower() == er:
                return True
        elif el:
            if left_word.lower() == el:
                return True
        elif er:
            if right_word.lower() == er:
                return True
    return False


def apply_corrections(text, corrections):
    if not text or not corrections:
        return text, []
    result = text
    applied = []
    for corr in corrections:
        if not corr.get("enabled", True):
            continue
        pattern = corr.get("pattern", "").strip()
        replacement = corr.get("replacement", "").strip()
        if not pattern or not replacement:
            continue
        try:
            escaped = re.escape(pattern)
            cl = re.escape(corr.get("context_left", "") or "")
            cr = re.escape(corr.get("context_right", "") or "")
            flags = 0 if corr.get("case_sensitive", False) else re.IGNORECASE
            exceptions = corr.get("exceptions", [])

            prefix_group = None
            if corr.get("whole_word", True):
                if cl and cr:
                    regex = rf'({cl}\s+)({escaped})(?=\s+{cr})'
                    prefix_group = 1
                    pattern_group = 2
                elif cl:
                    regex = rf'({cl}\s+)({escaped})'
                    prefix_group = 1
                    pattern_group = 2
                elif cr:
                    regex = rf'({escaped})(?=\s+{cr})'
                    pattern_group = 1
                else:
                    regex = rf'\b({escaped})\b'
                    pattern_group = 1
            else:
                regex = escaped
                pattern_group = 0

            corr_id = corr.get("id", "")
            actual_count = [0]

            def _replacer(m):
                if _match_has_exception(m.string, m.start(pattern_group), m.end(pattern_group), exceptions):
                    return m.group(0)
                corr["hits"] = corr.get("hits", 0) + 1
                corr["last_hit"] = time.time()
                actual_count[0] += 1
                return (m.group(prefix_group) + replacement) if prefix_group is not None else replacement

            new_result = re.sub(regex, _replacer, result, flags=flags)
            if actual_count[0] > 0:
                applied.append({"corr_id": corr_id, "pattern": pattern, "replacement": replacement, "count": actual_count[0]})
                result = new_result
        except Exception as e:
            print(f"[CORR] Error applying '{pattern}': {e}", flush=True)
    return result, applied


def suggest_corrections(old_text, new_text, max_suggestions=5):
    if old_text == new_text:
        return []

    matcher = difflib.SequenceMatcher(None, old_text, new_text)
    suggestions = []

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "replace":
            old_part = old_text[i1:i2].strip()
            new_part = new_text[j1:j2].strip()
            if old_part and new_part and old_part != new_part:
                suggestions.append({
                    "pattern": old_part,
                    "replacement": new_part,
                })
        if len(suggestions) >= max_suggestions:
            break

    return suggestions


def extract_context(text, pattern, window=1):
    words = text.split()
    for i, w in enumerate(words):
        if pattern.lower() in w.lower():
            left = words[i - window] if i >= window else ""
            right = words[i + window] if i + window < len(words) else ""
            return left, right
    return "", ""
