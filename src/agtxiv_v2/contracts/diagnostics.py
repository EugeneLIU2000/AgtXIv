"""Stable diagnostics emitted by the V2 contract kernel."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class DiagnosticCode(StrEnum):
    """Stable machine codes for canonical JSON validation."""

    BOM_FORBIDDEN = "AGTXIV.CANON.BOM_FORBIDDEN"
    INVALID_UTF8 = "AGTXIV.CANON.INVALID_UTF8"
    INVALID_JSON = "AGTXIV.CANON.INVALID_JSON"
    DUPLICATE_KEY = "AGTXIV.CANON.DUPLICATE_KEY"
    NORMALIZED_KEY_COLLISION = "AGTXIV.CANON.NORMALIZED_KEY_COLLISION"
    UNPAIRED_SURROGATE = "AGTXIV.CANON.UNPAIRED_SURROGATE"
    UNSUPPORTED_NUMBER = "AGTXIV.CANON.UNSUPPORTED_NUMBER"
    INTEGER_OUT_OF_RANGE = "AGTXIV.CANON.INTEGER_OUT_OF_RANGE"
    NESTING_TOO_DEEP = "AGTXIV.CANON.NESTING_TOO_DEEP"
    UNSUPPORTED_PROGRAMMATIC_TYPE = "AGTXIV.CANON.UNSUPPORTED_PROGRAMMATIC_TYPE"
    NON_STRING_OBJECT_KEY = "AGTXIV.CANON.NON_STRING_OBJECT_KEY"
    CYCLIC_PROGRAMMATIC_VALUE = "AGTXIV.CANON.CYCLIC_PROGRAMMATIC_VALUE"
    INVALID_RECORD_SHAPE = "AGTXIV.CANON.INVALID_RECORD_SHAPE"
    INVALID_INTERNAL_VALUE = "AGTXIV.CANON.INVALID_INTERNAL_VALUE"


@dataclass(frozen=True, slots=True)
class Diagnostic:
    """One deterministic validation failure.

    ``byte_offset`` is present when a failure can be located in raw input.
    ``json_pointer`` is an RFC 6901-style pointer rooted at the submitted value.
    Human-readable messages may improve while ``code`` retains its meaning.
    """

    code: DiagnosticCode
    message: str
    json_pointer: str = ""
    byte_offset: int | None = None

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "code": str(self.code),
            "message": self.message,
            "json_pointer": self.json_pointer,
        }
        if self.byte_offset is not None:
            result["byte_offset"] = self.byte_offset
        return result
