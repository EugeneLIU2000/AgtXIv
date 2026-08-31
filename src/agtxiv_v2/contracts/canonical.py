"""Canonical JSON parsing, serialization, and record hashing for V2.

Untrusted JSON must enter through :func:`parse_canonical_json`.  The parser
retains lexical information long enough to reject duplicate keys and number
forms that a host JSON parser could silently erase.  Programmatically created
values use the deliberately separate :func:`build_canonical_value` boundary.
Only the opaque :class:`ParsedCanonicalValue` returned by those functions may be
serialized or hashed.

Python cannot make an object tamper-proof against arbitrary malicious code in
the same interpreter: such code can call ``object.__setattr__`` or inspect
module-private names.  The boundary therefore combines ordinary immutability
with recursive fail-closed validation every time an opaque value is consumed.
"""

from __future__ import annotations

import hashlib
import unicodedata
from dataclasses import dataclass
from typing import Any, Never

from .diagnostics import Diagnostic, DiagnosticCode

IJSON_MIN_INTEGER = -9_007_199_254_740_991
IJSON_MAX_INTEGER = 9_007_199_254_740_991
MAX_NESTING = 256
PROFILE_ID = "agtxiv.record-canonical-json/2.0.0-candidate.1"

_UTF8_BOM = b"\xef\xbb\xbf"
_CONSTRUCTION_TOKEN = object()


@dataclass(frozen=True, slots=True)
class _RawObject:
    pairs: tuple[tuple[str, Any], ...]


@dataclass(frozen=True, slots=True)
class _CanonicalObject:
    pairs: tuple[tuple[str, Any], ...]


class ParsedCanonicalValue:
    """Opaque normalized JSON value accepted by the canonical profile.

    Instances cannot be constructed directly.  This makes a host ``dict`` that
    may already have lost duplicate keys visibly different from validated JSON.
    """

    __slots__ = ("__node",)

    def __init__(self, node: Any, *, _token: object) -> None:
        if _token is not _CONSTRUCTION_TOKEN:
            raise TypeError(
                "ParsedCanonicalValue is created only by parse_canonical_json "
                "or build_canonical_value"
            )
        diagnostic = _validate_canonical_node(node, "", 0, set())
        if diagnostic is not None:
            raise CanonicalValueIntegrityError(diagnostic)
        object.__setattr__(self, "_ParsedCanonicalValue__node", node)

    def __setattr__(self, name: str, value: Any) -> Never:
        raise AttributeError("ParsedCanonicalValue is immutable")

    def __delattr__(self, name: str) -> Never:
        raise AttributeError("ParsedCanonicalValue is immutable")

    def to_python(self) -> Any:
        """Return a detached conventional Python representation for inspection."""

        return _to_python(_require_parsed(self))

    def __repr__(self) -> str:
        return "ParsedCanonicalValue(<validated>)"


class CanonicalValueIntegrityError(ValueError):
    """Raised when an opaque value has been forged or mutated internally."""

    def __init__(self, diagnostic: Diagnostic) -> None:
        super().__init__(f"{diagnostic.code}: {diagnostic.message}")
        self.diagnostic = diagnostic


class _ParseProblem(Exception):
    def __init__(
        self,
        code: DiagnosticCode,
        message: str,
        character_offset: int,
        json_pointer: str = "",
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.character_offset = character_offset
        self.json_pointer = json_pointer


def _pointer_child(pointer: str, token: str | int) -> str:
    encoded = str(token).replace("~", "~0").replace("/", "~1")
    return f"{pointer}/{encoded}"


def _integer_token_out_of_range(token: str) -> bool:
    """Compare a grammar-valid integer token without constructing an integer."""

    magnitude = token[1:] if token.startswith("-") else token
    limit = "9007199254740991"
    return len(magnitude) > len(limit) or (
        len(magnitude) == len(limit) and magnitude > limit
    )


class _RawJsonParser:
    def __init__(self, text: str) -> None:
        self.text = text
        self.length = len(text)
        self.position = 0

    def parse(self) -> Any:
        self._skip_whitespace()
        if self.position == self.length:
            self._fail(DiagnosticCode.INVALID_JSON, "expected one JSON value")
        value = self._parse_value("", 0)
        self._skip_whitespace()
        if self.position != self.length:
            self._fail(
                DiagnosticCode.INVALID_JSON,
                "trailing non-whitespace data after the top-level JSON value",
            )
        return value

    def _parse_value(self, pointer: str, depth: int) -> Any:
        if depth > MAX_NESTING:
            self._fail(
                DiagnosticCode.NESTING_TOO_DEEP,
                f"JSON nesting exceeds the limit of {MAX_NESTING}",
                pointer,
            )
        if self.position >= self.length:
            self._fail(DiagnosticCode.INVALID_JSON, "unexpected end of JSON input", pointer)

        character = self.text[self.position]
        if character == '"':
            return self._parse_string(pointer)
        if character == "{":
            return self._parse_object(pointer, depth)
        if character == "[":
            return self._parse_array(pointer, depth)
        if character == "t":
            return self._parse_literal("true", True, pointer)
        if character == "f":
            return self._parse_literal("false", False, pointer)
        if character == "n":
            if self.text.startswith("null", self.position):
                return self._parse_literal("null", None, pointer)
            if self.text.startswith("nan", self.position):
                self._fail(DiagnosticCode.UNSUPPORTED_NUMBER, "NaN is not permitted", pointer)
        if character in "-+0123456789" or self.text.startswith(
            ("NaN", "Infinity"), self.position
        ):
            return self._parse_number(pointer)

        self._fail(
            DiagnosticCode.INVALID_JSON,
            f"unexpected character U+{ord(character):04X}",
            pointer,
        )

    def _parse_literal(self, spelling: str, value: Any, pointer: str) -> Any:
        if not self.text.startswith(spelling, self.position):
            self._fail(DiagnosticCode.INVALID_JSON, f"invalid literal; expected {spelling}", pointer)
        self.position += len(spelling)
        return value

    def _parse_object(self, pointer: str, depth: int) -> _RawObject:
        self.position += 1
        self._skip_whitespace()
        pairs: list[tuple[str, Any]] = []
        decoded_keys: set[str] = set()
        if self._consume("}"):
            return _RawObject(())

        while True:
            if self.position >= self.length or self.text[self.position] != '"':
                self._fail(DiagnosticCode.INVALID_JSON, "object key must be a JSON string", pointer)
            key_position = self.position
            key = self._parse_string(pointer)
            if key in decoded_keys:
                self._fail_at(
                    DiagnosticCode.DUPLICATE_KEY,
                    f"duplicate decoded object key {key!r}",
                    key_position,
                    _pointer_child(pointer, key),
                )
            decoded_keys.add(key)
            self._skip_whitespace()
            if not self._consume(":"):
                self._fail(DiagnosticCode.INVALID_JSON, "expected ':' after object key", pointer)
            self._skip_whitespace()
            child_pointer = _pointer_child(pointer, key)
            value = self._parse_value(child_pointer, depth + 1)
            pairs.append((key, value))
            self._skip_whitespace()
            if self._consume("}"):
                return _RawObject(tuple(pairs))
            if not self._consume(","):
                self._fail(DiagnosticCode.INVALID_JSON, "expected ',' or '}' in object", pointer)
            self._skip_whitespace()

    def _parse_array(self, pointer: str, depth: int) -> list[Any]:
        self.position += 1
        self._skip_whitespace()
        values: list[Any] = []
        if self._consume("]"):
            return values

        while True:
            values.append(self._parse_value(_pointer_child(pointer, len(values)), depth + 1))
            self._skip_whitespace()
            if self._consume("]"):
                return values
            if not self._consume(","):
                self._fail(DiagnosticCode.INVALID_JSON, "expected ',' or ']' in array", pointer)
            self._skip_whitespace()

    def _parse_string(self, pointer: str) -> str:
        self.position += 1
        characters: list[str] = []
        while self.position < self.length:
            character = self.text[self.position]
            self.position += 1
            if character == '"':
                return "".join(characters)
            if character == "\\":
                characters.append(self._parse_escape(pointer))
                continue
            code_point = ord(character)
            if code_point < 0x20:
                self._fail_at(
                    DiagnosticCode.INVALID_JSON,
                    "unescaped control character in JSON string",
                    self.position - 1,
                    pointer,
                )
            if 0xD800 <= code_point <= 0xDFFF:
                self._fail_at(
                    DiagnosticCode.UNPAIRED_SURROGATE,
                    "unpaired surrogate in JSON string",
                    self.position - 1,
                    pointer,
                )
            characters.append(character)
        self._fail(DiagnosticCode.INVALID_JSON, "unterminated JSON string", pointer)

    def _parse_escape(self, pointer: str) -> str:
        if self.position >= self.length:
            self._fail(DiagnosticCode.INVALID_JSON, "unterminated JSON escape", pointer)
        escape_position = self.position - 1
        character = self.text[self.position]
        self.position += 1
        simple = {
            '"': '"',
            "\\": "\\",
            "/": "/",
            "b": "\b",
            "f": "\f",
            "n": "\n",
            "r": "\r",
            "t": "\t",
        }
        if character in simple:
            return simple[character]
        if character != "u":
            self._fail_at(
                DiagnosticCode.INVALID_JSON,
                f"invalid JSON escape \\{character}",
                escape_position,
                pointer,
            )

        first = self._parse_hex_quad(pointer)
        if 0xDC00 <= first <= 0xDFFF:
            self._fail_at(
                DiagnosticCode.UNPAIRED_SURROGATE,
                "low surrogate has no preceding high surrogate",
                escape_position,
                pointer,
            )
        if 0xD800 <= first <= 0xDBFF:
            if not self.text.startswith("\\u", self.position):
                self._fail_at(
                    DiagnosticCode.UNPAIRED_SURROGATE,
                    "high surrogate has no following low surrogate",
                    escape_position,
                    pointer,
                )
            self.position += 2
            second = self._parse_hex_quad(pointer)
            if not 0xDC00 <= second <= 0xDFFF:
                self._fail_at(
                    DiagnosticCode.UNPAIRED_SURROGATE,
                    "high surrogate is not followed by a low surrogate",
                    escape_position,
                    pointer,
                )
            scalar = 0x10000 + ((first - 0xD800) << 10) + (second - 0xDC00)
            return chr(scalar)
        return chr(first)

    def _parse_hex_quad(self, pointer: str) -> int:
        start = self.position
        end = start + 4
        if end > self.length:
            self._fail_at(
                DiagnosticCode.INVALID_JSON,
                "incomplete Unicode escape",
                start,
                pointer,
            )
        digits = self.text[start:end]
        if any(character not in "0123456789abcdefABCDEF" for character in digits):
            self._fail_at(
                DiagnosticCode.INVALID_JSON,
                "Unicode escape must contain four hexadecimal digits",
                start,
                pointer,
            )
        self.position = end
        return int(digits, 16)

    def _parse_number(self, pointer: str) -> int:
        start = self.position
        if self.text.startswith(("NaN", "Infinity", "-Infinity"), start):
            self._fail_at(
                DiagnosticCode.UNSUPPORTED_NUMBER,
                "non-finite numbers are not permitted",
                start,
                pointer,
            )
        if self.text[self.position] == "+":
            self._fail_at(
                DiagnosticCode.UNSUPPORTED_NUMBER,
                "a leading plus sign is not permitted",
                start,
                pointer,
            )

        negative = self._consume("-")
        if self.position >= self.length or self.text[self.position] not in "0123456789":
            self._fail_at(
                DiagnosticCode.UNSUPPORTED_NUMBER,
                "number must contain decimal digits",
                start,
                pointer,
            )

        first_digit = self.text[self.position]
        if first_digit == "0":
            self.position += 1
            if negative:
                self._fail_at(
                    DiagnosticCode.UNSUPPORTED_NUMBER,
                    "negative zero is not permitted",
                    start,
                    pointer,
                )
            if self.position < self.length and (
                self.text[self.position] in "0123456789.eE"
            ):
                self._fail_at(
                    DiagnosticCode.UNSUPPORTED_NUMBER,
                    "leading zero, decimal, and exponent number forms are not permitted",
                    start,
                    pointer,
                )
        else:
            while (
                self.position < self.length
                and self.text[self.position] in "0123456789"
            ):
                self.position += 1
            if self.position < self.length and self.text[self.position] in ".eE":
                self._fail_at(
                    DiagnosticCode.UNSUPPORTED_NUMBER,
                    "decimal and exponent number forms are not permitted",
                    start,
                    pointer,
                )

        token = self.text[start:self.position]
        if _integer_token_out_of_range(token):
            self._fail_at(
                DiagnosticCode.INTEGER_OUT_OF_RANGE,
                "integer is outside the I-JSON interoperable range",
                start,
                pointer,
            )
        # The lexical comparison above bounds the token to 16 digits before
        # conversion, so Python's configurable integer-string digit limit can
        # never leak an implementation exception through this API.
        return int(token)

    def _skip_whitespace(self) -> None:
        while self.position < self.length and self.text[self.position] in " \t\r\n":
            self.position += 1

    def _consume(self, spelling: str) -> bool:
        if self.text.startswith(spelling, self.position):
            self.position += len(spelling)
            return True
        return False

    def _fail(self, code: DiagnosticCode, message: str, pointer: str = "") -> Never:
        raise _ParseProblem(code, message, self.position, pointer)

    def _fail_at(
        self,
        code: DiagnosticCode,
        message: str,
        position: int,
        pointer: str = "",
    ) -> Never:
        raise _ParseProblem(code, message, position, pointer)


def parse_canonical_json(raw_utf8_bytes: bytes) -> ParsedCanonicalValue | Diagnostic:
    """Parse and normalize untrusted raw JSON bytes.

    A diagnostic is returned for user-data failures.  Passing anything other
    than ``bytes`` is API misuse and raises ``TypeError``.
    """

    if type(raw_utf8_bytes) is not bytes:
        raise TypeError("parse_canonical_json requires raw bytes")
    if raw_utf8_bytes.startswith(_UTF8_BOM):
        return Diagnostic(
            DiagnosticCode.BOM_FORBIDDEN,
            "a UTF-8 byte-order mark is not permitted",
            byte_offset=0,
        )
    try:
        text = raw_utf8_bytes.decode("utf-8", errors="strict")
    except UnicodeDecodeError as error:
        return Diagnostic(
            DiagnosticCode.INVALID_UTF8,
            "input is not strict UTF-8",
            byte_offset=error.start,
        )

    parser = _RawJsonParser(text)
    try:
        raw_value = parser.parse()
    except _ParseProblem as error:
        return Diagnostic(
            error.code,
            error.message,
            error.json_pointer,
            len(text[: error.character_offset].encode("utf-8")),
        )
    except RecursionError:
        return Diagnostic(
            DiagnosticCode.NESTING_TOO_DEEP,
            f"JSON nesting exceeds the limit of {MAX_NESTING}",
        )

    normalized = _normalize_raw_value(raw_value, "")
    if isinstance(normalized, Diagnostic):
        return normalized
    return ParsedCanonicalValue(normalized, _token=_CONSTRUCTION_TOKEN)


def build_canonical_value(value: Any) -> ParsedCanonicalValue | Diagnostic:
    """Validate a value intentionally constructed by trusted program logic.

    This API cannot recover duplicates already discarded by a host dictionary.
    It is therefore not a replacement for :func:`parse_canonical_json` at a raw
    JSON boundary.  Its separate name makes that trust decision explicit.
    """

    if isinstance(value, ParsedCanonicalValue):
        _require_parsed(value)
        return value
    normalized = _normalize_programmatic_value(value, "", set(), 0)
    if isinstance(normalized, Diagnostic):
        return normalized
    return ParsedCanonicalValue(normalized, _token=_CONSTRUCTION_TOKEN)


def canonical_bytes(value: ParsedCanonicalValue) -> bytes:
    """Serialize a previously validated value to exact canonical UTF-8 bytes."""

    node = _require_parsed(value)
    output: list[str] = []
    _emit(node, output)
    return "".join(output).encode("utf-8", errors="strict")


def canonical_sha256(value: ParsedCanonicalValue) -> str:
    """Hash the exact canonical bytes of a validated value."""

    return "sha256:" + hashlib.sha256(canonical_bytes(value)).hexdigest()


def record_hash_projection_bytes(
    record: ParsedCanonicalValue,
) -> bytes | Diagnostic:
    """Return canonical bytes of exactly ``{envelope, payload}``.

    The accepted outer record keys are ``envelope``, ``payload``, and optional
    ``content_hash``.  Rejecting unknown outer keys prevents accidental unhashed
    metadata.  Nested fields named ``content_hash`` remain in the projection.
    """

    node = _require_parsed(record)
    if not isinstance(node, _CanonicalObject):
        return Diagnostic(
            DiagnosticCode.INVALID_RECORD_SHAPE,
            "record must be a JSON object",
        )
    fields = dict(node.pairs)
    required = {"envelope", "payload"}
    allowed = required | {"content_hash"}
    if not required <= fields.keys() or not fields.keys() <= allowed:
        return Diagnostic(
            DiagnosticCode.INVALID_RECORD_SHAPE,
            "record must contain envelope and payload and may contain only outer content_hash",
        )
    projection = ParsedCanonicalValue(
        _CanonicalObject(
            (
                ("envelope", fields["envelope"]),
                ("payload", fields["payload"]),
            )
        ),
        _token=_CONSTRUCTION_TOKEN,
    )
    return canonical_bytes(projection)


def record_content_hash(record: ParsedCanonicalValue) -> str | Diagnostic:
    """Compute the V2 immutable-record content hash."""

    projection = record_hash_projection_bytes(record)
    if isinstance(projection, Diagnostic):
        return projection
    return "sha256:" + hashlib.sha256(projection).hexdigest()


def _require_parsed(value: ParsedCanonicalValue) -> Any:
    if not isinstance(value, ParsedCanonicalValue):
        raise TypeError(
            "canonical operations require ParsedCanonicalValue; use "
            "parse_canonical_json for raw JSON or build_canonical_value for "
            "trusted programmatic values"
        )
    if type(value) is not ParsedCanonicalValue:
        raise CanonicalValueIntegrityError(
            Diagnostic(
                DiagnosticCode.INVALID_INTERNAL_VALUE,
                "opaque canonical value has an unexpected runtime type",
            )
        )
    try:
        node = object.__getattribute__(value, "_ParsedCanonicalValue__node")
    except AttributeError as error:
        raise CanonicalValueIntegrityError(
            Diagnostic(
                DiagnosticCode.INVALID_INTERNAL_VALUE,
                "opaque canonical value has no internal node",
            )
        ) from error
    diagnostic = _validate_canonical_node(node, "", 0, set())
    if diagnostic is not None:
        raise CanonicalValueIntegrityError(diagnostic)
    return node


def _normalize_string(value: str, pointer: str) -> str | Diagnostic:
    for character in value:
        if 0xD800 <= ord(character) <= 0xDFFF:
            return Diagnostic(
                DiagnosticCode.UNPAIRED_SURROGATE,
                "unpaired surrogate in string",
                pointer,
            )
    return unicodedata.normalize("NFC", value.replace("\r\n", "\n").replace("\r", "\n"))


def _invalid_internal(message: str, pointer: str = "") -> Diagnostic:
    return Diagnostic(DiagnosticCode.INVALID_INTERNAL_VALUE, message, pointer)


def _validate_canonical_node(
    node: Any,
    pointer: str,
    depth: int,
    active_container_ids: set[int],
) -> Diagnostic | None:
    """Recursively validate an opaque node every time it crosses the boundary."""

    if depth > MAX_NESTING:
        return _invalid_internal(
            f"internal canonical value exceeds nesting limit {MAX_NESTING}",
            pointer,
        )
    if node is None or node is True or node is False:
        return None
    if type(node) is int:
        if node < IJSON_MIN_INTEGER or node > IJSON_MAX_INTEGER:
            return _invalid_internal(
                "internal integer is outside the I-JSON interoperable range",
                pointer,
            )
        return None
    if type(node) is str:
        normalized = _normalize_string(node, pointer)
        if isinstance(normalized, Diagnostic) or normalized != node:
            return _invalid_internal(
                "internal string is not newline-normalized NFC Unicode",
                pointer,
            )
        return None

    if type(node) is tuple:
        identity = id(node)
        if identity in active_container_ids:
            return _invalid_internal("internal array contains a cycle", pointer)
        active_container_ids.add(identity)
        try:
            for index, item in enumerate(node):
                diagnostic = _validate_canonical_node(
                    item,
                    _pointer_child(pointer, index),
                    depth + 1,
                    active_container_ids,
                )
                if diagnostic is not None:
                    return diagnostic
            return None
        finally:
            active_container_ids.remove(identity)

    if type(node) is _CanonicalObject:
        try:
            pairs = object.__getattribute__(node, "pairs")
        except AttributeError:
            return _invalid_internal("internal object has no member tuple", pointer)
        if type(pairs) is not tuple:
            return _invalid_internal("internal object pairs must be an immutable tuple", pointer)
        identity = id(node)
        if identity in active_container_ids:
            return _invalid_internal("internal object contains a cycle", pointer)
        active_container_ids.add(identity)
        try:
            previous_key: str | None = None
            seen_keys: set[str] = set()
            for pair in pairs:
                if type(pair) is not tuple or len(pair) != 2:
                    return _invalid_internal(
                        "internal object member must be a two-item tuple",
                        pointer,
                    )
                key, child = pair
                if type(key) is not str:
                    return _invalid_internal("internal object key must be a string", pointer)
                normalized_key = _normalize_string(key, _pointer_child(pointer, key))
                if isinstance(normalized_key, Diagnostic) or normalized_key != key:
                    return _invalid_internal(
                        "internal object key is not newline-normalized NFC Unicode",
                        pointer,
                    )
                if key in seen_keys:
                    return _invalid_internal(
                        "internal object contains a duplicate key",
                        _pointer_child(pointer, key),
                    )
                if previous_key is not None and previous_key >= key:
                    return _invalid_internal(
                        "internal object keys are not in Unicode scalar-value order",
                        _pointer_child(pointer, key),
                    )
                seen_keys.add(key)
                previous_key = key
                diagnostic = _validate_canonical_node(
                    child,
                    _pointer_child(pointer, key),
                    depth + 1,
                    active_container_ids,
                )
                if diagnostic is not None:
                    return diagnostic
            return None
        finally:
            active_container_ids.remove(identity)

    return _invalid_internal(
        f"unsupported internal canonical node type: {type(node).__name__}",
        pointer,
    )


def _normalize_raw_value(value: Any, pointer: str) -> Any | Diagnostic:
    if value is None or isinstance(value, bool) or type(value) is int:
        return value
    if isinstance(value, str):
        return _normalize_string(value, pointer)
    if isinstance(value, list):
        normalized_items: list[Any] = []
        for index, item in enumerate(value):
            normalized = _normalize_raw_value(item, _pointer_child(pointer, index))
            if isinstance(normalized, Diagnostic):
                return normalized
            normalized_items.append(normalized)
        return tuple(normalized_items)
    if isinstance(value, _RawObject):
        normalized_pairs: list[tuple[str, Any]] = []
        normalized_keys: set[str] = set()
        for raw_key, raw_child in value.pairs:
            key = _normalize_string(raw_key, _pointer_child(pointer, raw_key))
            if isinstance(key, Diagnostic):
                return key
            if key in normalized_keys:
                return Diagnostic(
                    DiagnosticCode.NORMALIZED_KEY_COLLISION,
                    f"object keys collide after newline/NFC normalization: {key!r}",
                    _pointer_child(pointer, key),
                )
            normalized_keys.add(key)
            child = _normalize_raw_value(raw_child, _pointer_child(pointer, key))
            if isinstance(child, Diagnostic):
                return child
            normalized_pairs.append((key, child))
        normalized_pairs.sort(key=lambda pair: pair[0])
        return _CanonicalObject(tuple(normalized_pairs))
    raise AssertionError(f"unexpected raw parser value: {type(value).__name__}")


def _normalize_programmatic_value(
    value: Any,
    pointer: str,
    active_container_ids: set[int],
    depth: int,
) -> Any | Diagnostic:
    if depth > MAX_NESTING:
        return Diagnostic(
            DiagnosticCode.NESTING_TOO_DEEP,
            f"JSON nesting exceeds the limit of {MAX_NESTING}",
            pointer,
        )
    if value is None or isinstance(value, bool):
        return value
    if type(value) is int:
        if value < IJSON_MIN_INTEGER or value > IJSON_MAX_INTEGER:
            return Diagnostic(
                DiagnosticCode.INTEGER_OUT_OF_RANGE,
                "integer is outside the I-JSON interoperable range",
                pointer,
            )
        return value
    if isinstance(value, str):
        return _normalize_string(value, pointer)
    if type(value) not in (list, dict):
        return Diagnostic(
            DiagnosticCode.UNSUPPORTED_PROGRAMMATIC_TYPE,
            f"unsupported programmatic JSON type: {type(value).__name__}",
            pointer,
        )

    identity = id(value)
    if identity in active_container_ids:
        return Diagnostic(
            DiagnosticCode.CYCLIC_PROGRAMMATIC_VALUE,
            "programmatic JSON value contains a cycle",
            pointer,
        )
    active_container_ids.add(identity)
    try:
        if isinstance(value, list):
            normalized_items: list[Any] = []
            for index, item in enumerate(value):
                normalized = _normalize_programmatic_value(
                    item,
                    _pointer_child(pointer, index),
                    active_container_ids,
                    depth + 1,
                )
                if isinstance(normalized, Diagnostic):
                    return normalized
                normalized_items.append(normalized)
            return tuple(normalized_items)

        normalized_pairs: list[tuple[str, Any]] = []
        normalized_keys: set[str] = set()
        for raw_key, raw_child in value.items():
            if not isinstance(raw_key, str):
                return Diagnostic(
                    DiagnosticCode.NON_STRING_OBJECT_KEY,
                    "programmatic JSON object keys must be strings",
                    pointer,
                )
            key = _normalize_string(raw_key, _pointer_child(pointer, raw_key))
            if isinstance(key, Diagnostic):
                return key
            if key in normalized_keys:
                return Diagnostic(
                    DiagnosticCode.NORMALIZED_KEY_COLLISION,
                    f"object keys collide after newline/NFC normalization: {key!r}",
                    _pointer_child(pointer, key),
                )
            normalized_keys.add(key)
            child = _normalize_programmatic_value(
                raw_child,
                _pointer_child(pointer, key),
                active_container_ids,
                depth + 1,
            )
            if isinstance(child, Diagnostic):
                return child
            normalized_pairs.append((key, child))
        normalized_pairs.sort(key=lambda pair: pair[0])
        return _CanonicalObject(tuple(normalized_pairs))
    finally:
        active_container_ids.remove(identity)


def _escape_string(value: str) -> str:
    output = ['"']
    short_escapes = {
        '"': '\\"',
        "\\": "\\\\",
        "\b": "\\b",
        "\t": "\\t",
        "\n": "\\n",
        "\f": "\\f",
    }
    for character in value:
        escaped = short_escapes.get(character)
        if escaped is not None:
            output.append(escaped)
        elif ord(character) <= 0x1F:
            output.append(f"\\u{ord(character):04x}")
        else:
            output.append(character)
    output.append('"')
    return "".join(output)


def _emit(node: Any, output: list[str]) -> None:
    if node is None:
        output.append("null")
    elif node is True:
        output.append("true")
    elif node is False:
        output.append("false")
    elif type(node) is int:
        output.append(str(node))
    elif isinstance(node, str):
        output.append(_escape_string(node))
    elif isinstance(node, tuple):
        output.append("[")
        for index, item in enumerate(node):
            if index:
                output.append(",")
            _emit(item, output)
        output.append("]")
    elif isinstance(node, _CanonicalObject):
        output.append("{")
        for index, (key, value) in enumerate(node.pairs):
            if index:
                output.append(",")
            output.append(_escape_string(key))
            output.append(":")
            _emit(value, output)
        output.append("}")
    else:
        raise AssertionError(f"unexpected canonical value: {type(node).__name__}")


def _to_python(node: Any) -> Any:
    if isinstance(node, _CanonicalObject):
        return {key: _to_python(value) for key, value in node.pairs}
    if isinstance(node, tuple):
        return [_to_python(value) for value in node]
    return node
