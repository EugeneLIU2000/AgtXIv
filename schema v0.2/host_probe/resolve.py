"""Host-side source_locator resolution.  CONTRACT.md section 4, exact-byte convention.
The model supplies only markers; the host computes byte range + hash.  Never guesses."""
import hashlib, json

class LocatorError(Exception):
    def __init__(self, code, msg): super().__init__(msg); self.code=code

def resolve(source_bytes: bytes, start_marker: str, end_marker: str):
    s = start_marker.encode("utf-8")
    e = end_marker.encode("utf-8")
    if not s or not e:
        raise LocatorError("EMPTY_MARKER", "markers must be non-empty")
    # unique start match
    first = source_bytes.find(s)
    if first < 0:
        raise LocatorError("START_NOT_FOUND", f"start marker not present")
    if source_bytes.find(s, first + 1) >= 0:
        raise LocatorError("START_AMBIGUOUS", "start marker occurs more than once")
    # search end FROM start onward, require unique match there too
    e_first = source_bytes.find(e, first)
    if e_first < 0:
        raise LocatorError("END_NOT_FOUND", "end marker not present at or after start")
    if source_bytes.find(e, e_first + 1) >= 0:
        raise LocatorError("END_AMBIGUOUS", "end marker occurs more than once at or after start")
    end = e_first + len(e)          # include both markers: [start, end-of-end-marker)
    if end <= first:
        raise LocatorError("RANGE_REVERSED", "resolved range is empty or reversed")
    span = source_bytes[first:end]
    return {
        "byte_start": first,
        "byte_end": end,
        "span_sha256": "sha256:" + hashlib.sha256(span).hexdigest(),
        "source_sha256": "sha256:" + hashlib.sha256(source_bytes).hexdigest(),
        "byte_length": end - first,
    }

def resolve_output(items, sources_by_alias):
    """Returns (source_bindings, issues) for every source_locator item."""
    bindings, issues = [], []
    for it in items:
        if it.get("kind") != "source_locator": continue
        alias = (it.get("source") or {}).get("input")
        raw = sources_by_alias.get(alias)
        if raw is None:
            issues.append({"code":"SOURCE_NOT_SUPPLIED","locator_id":it["id"],"alias":alias}); continue
        try:
            b = resolve(raw, it["start_marker"], it["end_marker"])
            bindings.append({"locator_id": it["id"], "input": alias, **b})
        except LocatorError as ex:
            issues.append({"code": ex.code, "locator_id": it["id"], "detail": str(ex)})
    return bindings, issues
