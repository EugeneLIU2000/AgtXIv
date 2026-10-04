"""Bounded BibTeX source reader, without macro expansion or TeX execution.

``parse_bibtex(bytes)`` returns ``{"entries": [...], "issues": [...]}``.
Entry and issue offsets are half-open *original byte* intervals. An entry has
``key`` (str, or None for an invalid key), lower-case ``entry_type``, ``fields``,
``start``, ``end``, and ``field_issues``. Field names are lower-case ASCII.

Field values are UTF-8 strings only for completely literal expressions; an
unresolved macro, invalid encoding, or duplicate field gives None. Only the
outer value delimiters are removed: inner braces, TeX escapes, whitespace and
percent signs inside literals are preserved. Literal ``#`` parts concatenate
without adding whitespace. Unquoted decimal integers are literal strings.

All diagnostics appear in ``issues``; field diagnostics also appear in their
entry's ``field_issues``. Invalid entries and partial entries may be returned:
callers MUST inspect diagnostics rather than infer validity from membership in
``entries``. Directives are skipped with diagnostics, never evaluated. Text
outside entries is BibTeX commentary, not an executable instruction.

This module does not resolve crossref/xdata, decode LaTeX, infer identifiers,
deduplicate citation keys, or establish that a citation supports a claim.
"""
from __future__ import annotations


MAX_INPUT_BYTES = 8 * 1024 * 1024
MAX_ENTRIES = 10_000
MAX_FIELDS_PER_ENTRY = 1_024
MAX_VALUE_BYTES = 1024 * 1024
MAX_VALUE_PARTS = 4_096
MAX_NESTING = 128
MAX_ISSUES = 10_000

_SPACE = b" \t\r\n\f\v"
_IDENT_STOP = _SPACE + b'"#%\'(),={}@'
_VALUE_STOP = _SPACE + b",#%{}()\"@"
_DIRECTIVES = {"string", "preamble", "comment"}


class _Halt(Exception):
    """A recorded resource or unrecoverable source-boundary problem."""


class _Parser:
    def __init__(self, data: bytes):
        self.data = data
        self.size = len(data)
        self.pos = 0
        self.entries: list[dict] = []
        self.issues: list[dict] = []
        self.active: dict | None = None
        self.key_starts: dict[str, int] = {}

    def issue(self, code: str, start: int, end: int, detail: str,
              field: str | None = None, **extra) -> None:
        if len(self.issues) >= MAX_ISSUES - 1:
            self.issues.append({
                "code": "ISSUE_LIMIT_REACHED", "start": self.pos,
                "end": self.size, "detail": "Parsing stopped; the remaining bytes are unparsed.",
                "limit": MAX_ISSUES,
            })
            raise _Halt
        row = {"code": code, "start": start, "end": end, "detail": detail, **extra}
        if self.active is not None:
            row["entry_start"] = self.active["start"]
            row["key"] = self.active["key"]
        if field is not None:
            row["field"] = field
            if self.active is not None:
                self.active["field_issues"].append(row)
        self.issues.append(row)

    def halt(self, code: str, start: int, detail: str,
             field: str | None = None, **extra) -> None:
        self.issue(code, start, self.size, detail + " Remaining bytes are unparsed.",
                   field, **extra)
        raise _Halt

    def layout(self) -> None:
        while self.pos < self.size:
            char = self.data[self.pos]
            if char in _SPACE:
                self.pos += 1
            elif char == 37:  # Percent comments only outside literal values.
                newline = self.data.find(b"\n", self.pos + 1)
                self.pos = self.size if newline < 0 else newline + 1
            else:
                return

    def identifier(self) -> bytes:
        start = self.pos
        while self.pos < self.size and self.data[self.pos] not in _IDENT_STOP:
            self.pos += 1
        return self.data[start:self.pos]

    def decode(self, raw: bytes, start: int, end: int,
               subject: str, field: str | None = None) -> str | None:
        try:
            return raw.decode("utf-8", errors="strict")
        except UnicodeDecodeError:
            self.issue("INVALID_UTF8_" + subject, start, end,
                       "Bytes are not valid UTF-8; no replacement text was invented.", field)
            return None

    def literal(self, field: str | None = None) -> tuple[bytes, bool]:
        """Consume one braced or quoted literal iteratively, retaining its bytes."""
        start = self.pos
        opener = self.data[self.pos]
        self.pos += 1
        content_start = self.pos
        depth = 1 if opener == 123 else 0
        valid = True
        while self.pos < self.size:
            if self.pos - start > MAX_VALUE_BYTES:
                self.halt("VALUE_SIZE_LIMIT_REACHED", start,
                          "Literal exceeded the byte limit.", field, limit=MAX_VALUE_BYTES)
            char = self.data[self.pos]
            if char == 92:  # Preserve an escape and suppress its delimiter meaning.
                self.pos += min(2, self.size - self.pos)
                continue
            if char == 123:
                depth += 1
                if depth > MAX_NESTING:
                    self.halt("NESTING_LIMIT_REACHED", start,
                              "Literal nesting exceeded the limit.", field, limit=MAX_NESTING)
            elif char == 125:
                if depth == 0:
                    valid = False
                    self.issue("UNMATCHED_BRACE_IN_QUOTED_VALUE", self.pos, self.pos + 1,
                               "A quoted value has an unmatched closing brace.", field)
                else:
                    depth -= 1
                    if opener == 123 and depth == 0:
                        raw = self.data[content_start:self.pos]
                        self.pos += 1
                        return raw, valid
            elif char == 34 and opener == 34 and depth == 0:
                raw = self.data[content_start:self.pos]
                self.pos += 1
                return raw, valid
            self.pos += 1
        self.halt("UNTERMINATED_LITERAL", start,
                  "Literal has no balanced closing delimiter; later entry boundaries are uncertain.", field)

    def value(self, field: str) -> str | None:
        start = self.pos
        parts: list[str] = []
        valid = True
        part_count = 0
        while True:
            self.layout()
            if part_count >= MAX_VALUE_PARTS:
                self.halt("VALUE_PART_LIMIT_REACHED", start,
                          "Concatenation has too many parts.", field, limit=MAX_VALUE_PARTS)
            if self.pos - start > MAX_VALUE_BYTES:
                self.halt("VALUE_SIZE_LIMIT_REACHED", start,
                          "Value expression exceeded the byte limit.", field, limit=MAX_VALUE_BYTES)
            atom_start = self.pos
            if self.pos >= self.size or self.data[self.pos] in b",})#":
                self.issue("MISSING_VALUE_ATOM", atom_start, self.pos,
                           "Expected a literal or a macro name, including after '#'.", field)
                return None
            if self.data[self.pos] in b'{"':
                raw, balanced = self.literal(field)
                value = self.decode(raw, atom_start, self.pos, "VALUE", field)
                valid = valid and balanced and value is not None
                if value is not None:
                    parts.append(value)
            else:
                while self.pos < self.size and self.data[self.pos] not in _VALUE_STOP:
                    self.pos += 1
                    if self.pos - start > MAX_VALUE_BYTES:
                        self.halt("VALUE_SIZE_LIMIT_REACHED", start,
                                  "Value expression exceeded the byte limit.", field, limit=MAX_VALUE_BYTES)
                token = self.data[atom_start:self.pos]
                if not token:
                    self.issue("INVALID_VALUE_TOKEN", atom_start, min(self.size, atom_start + 1),
                               "Unexpected delimiter where a value atom was required.", field)
                    return None
                if token.isdigit():
                    parts.append(token.decode("ascii"))
                else:
                    macro = self.decode(token, atom_start, self.pos, "MACRO", field)
                    valid = False
                    self.issue("UNEXPANDED_MACRO", atom_start, self.pos,
                               "Bare nonnumeric values are not literals; no macro was expanded.",
                               field, macro=macro)
            part_count += 1
            self.layout()
            if self.pos - start > MAX_VALUE_BYTES:
                self.halt("VALUE_SIZE_LIMIT_REACHED", start,
                          "Value expression exceeded the byte limit.", field, limit=MAX_VALUE_BYTES)
            if self.pos >= self.size or self.data[self.pos] != 35:
                return "".join(parts) if valid else None
            self.pos += 1

    def recover_field(self, closer: int, field: str | None = None) -> None:
        """Skip malformed field content only to a structurally visible separator."""
        while self.pos < self.size:
            self.layout()
            if self.pos >= self.size or self.data[self.pos] in (44, closer, 41, 125):
                return
            if self.data[self.pos] in b'{"':
                self.literal(field)
            else:
                self.pos += 1

    def skip_directive(self, start: int, entry_type: str, opener: int) -> None:
        if opener == 123:
            self.literal()
        else:
            self.pos += 1
            depth = 1
            while self.pos < self.size and depth:
                self.layout()
                if self.pos >= self.size:
                    break
                char = self.data[self.pos]
                if char in b'{"':
                    self.literal()
                elif char == 92:
                    self.pos += min(2, self.size - self.pos)
                else:
                    self.pos += 1
                    if char == 40:
                        depth += 1
                        if depth > MAX_NESTING:
                            self.halt("NESTING_LIMIT_REACHED", start,
                                      "Ignored directive exceeded the nesting limit.", limit=MAX_NESTING)
                    elif char == 41:
                        depth -= 1
            if depth:
                self.halt("UNTERMINATED_DIRECTIVE", start,
                          "Ignored directive has no balanced closing delimiter.")
        self.issue("DIRECTIVE_NOT_EVALUATED", start, self.pos,
                   "Directive was retained only as a source interval; it was not evaluated.",
                   directive=entry_type)

    def entry(self) -> None:
        start = self.pos
        self.pos += 1
        self.layout()
        type_start = self.pos
        raw_type = self.identifier()
        if (not raw_type or not raw_type[:1].isalpha()
                or any(char > 127 or not (chr(char).isalnum() or char in b"_-:")
                       for char in raw_type)):
            self.halt("INVALID_ENTRY_TYPE", start,
                      "Entry type is missing or invalid; no subsequent boundary was guessed.")
        entry_type = raw_type.decode("ascii").lower()
        self.layout()
        if self.pos >= self.size or self.data[self.pos] not in b"{(":
            if entry_type == "comment":
                # Its following free text uses the ordinary outside-entry scan.
                # In particular, do not consume a subsequent @entry after the
                # whitespace already skipped above, even on the same line.
                self.issue("DIRECTIVE_NOT_EVALUATED", start, self.pos,
                           "Unbraced @comment was ignored; following text is outside-entry commentary.",
                           directive=entry_type)
                return
            self.halt("ENTRY_OPEN_DELIMITER_MISSING", type_start,
                      "Entry has no braced or parenthesized body.")
        opener = self.data[self.pos]
        if entry_type in _DIRECTIVES:
            self.skip_directive(start, entry_type, opener)
            return
        if len(self.entries) >= MAX_ENTRIES:
            self.halt("ENTRY_LIMIT_REACHED", start, "Entry count exceeded the limit.", limit=MAX_ENTRIES)
        closer = 125 if opener == 123 else 41
        self.pos += 1
        self.layout()
        key_start = self.pos
        raw_key = self.identifier()
        key = self.decode(raw_key, key_start, self.pos, "KEY") if raw_key else None
        row = {"key": key, "entry_type": entry_type, "fields": {},
               "start": start, "end": self.pos, "field_issues": []}
        self.entries.append(row)
        self.active = row
        if not raw_key:
            self.issue("EMPTY_CITATION_KEY", key_start, self.pos, "Entry has no citation key.")
        if key is not None:
            if key in self.key_starts:
                self.issue("DUPLICATE_CITATION_KEY", key_start, self.pos,
                           "All entries are retained; this citation key is ambiguous.",
                           previous_entry_start=self.key_starts[key])
            else:
                self.key_starts[key] = start
        if entry_type == "xdata":
            self.issue("XDATA_ENTRY_NOT_EXPANDED", start, self.pos,
                       "This is an inheritance-data entry, not an automatically resolved bibliographic work.")
        self.layout()
        if self.pos < self.size and self.data[self.pos] == closer:
            self.pos += 1
            row["end"] = self.pos
            self.active = None
            return
        if self.pos >= self.size or self.data[self.pos] != 44:
            self.halt("KEY_SEPARATOR_MISSING", key_start,
                      "Citation key is not followed by a comma or its entry's closing delimiter.")
        self.pos += 1
        field_count = 0
        seen_fields: dict[str, int] = {}
        while self.pos < self.size:
            self.layout()
            if self.pos >= self.size:
                break
            char = self.data[self.pos]
            if char in (125, 41):
                if char != closer:
                    self.issue("MISMATCHED_ENTRY_DELIMITER", self.pos, self.pos + 1,
                               "Entry closes with a delimiter different from its opener.")
                self.pos += 1
                row["end"] = self.pos
                self.active = None
                return
            if char == 44:
                self.issue("EMPTY_FIELD", self.pos, self.pos + 1,
                           "An extra comma does not identify a field.")
                self.pos += 1
                continue
            if field_count >= MAX_FIELDS_PER_ENTRY:
                self.halt("FIELD_LIMIT_REACHED", self.pos,
                          "Field count exceeded the per-entry limit.", limit=MAX_FIELDS_PER_ENTRY)
            field_count += 1
            field_start = self.pos
            raw_field = self.identifier()
            if (not raw_field or not raw_field[:1].isalpha()
                    or any(char > 127 or not (chr(char).isalnum() or char in b"_-:")
                           for char in raw_field)):
                self.issue("INVALID_FIELD_NAME", field_start, max(self.pos, field_start + 1),
                           "Field name is not a supported ASCII identifier.")
                self.recover_field(closer)
                if self.pos < self.size and self.data[self.pos] == 44:
                    self.pos += 1
                continue
            field = raw_field.decode("ascii").lower()
            duplicate = field in seen_fields
            if duplicate:
                self.issue("DUPLICATE_FIELD", field_start, self.pos,
                           "No first/last field wins; the resulting field value is null.", field,
                           previous_field_start=seen_fields[field])
            else:
                seen_fields[field] = field_start
            self.layout()
            if self.pos >= self.size or self.data[self.pos] != 61:
                self.issue("FIELD_EQUALS_MISSING", field_start, self.pos,
                           "Field has no '=' assignment.", field)
                row["fields"][field] = None
                self.recover_field(closer, field)
            else:
                self.pos += 1
                self.layout()
                # Set a null placeholder before parsing, so a halted partial row
                # cannot accidentally present an earlier duplicate as resolved.
                row["fields"][field] = None
                value = self.value(field)
                row["fields"][field] = None if duplicate else value
                if field in {"crossref", "xdata"}:
                    self.issue("UNRESOLVED_" + field.upper(), field_start, self.pos,
                               "Literal reference text is preserved, but no inherited fields were expanded.", field)
            self.layout()
            if self.pos < self.size and self.data[self.pos] == 44:
                self.pos += 1
            elif self.pos < self.size and self.data[self.pos] not in (closer, 125, 41):
                self.issue("FIELD_SEPARATOR_MISSING", self.pos, self.pos + 1,
                           "Expected a comma or entry closer after the value; trailing content was not part of the field.", field)
                row["fields"][field] = None
                self.recover_field(closer, field)
                if self.pos < self.size and self.data[self.pos] == 44:
                    self.pos += 1
        self.issue("UNTERMINATED_ENTRY", start, self.size,
                   "Entry has no closing delimiter; its fields are only a partial extraction.")
        row["end"] = self.size
        self.active = None

    def parse(self) -> dict:
        if self.size > MAX_INPUT_BYTES:
            self.issue("INPUT_SIZE_LIMIT_REACHED", 0, self.size,
                       "Input was not parsed or truncated.", limit=MAX_INPUT_BYTES)
            return {"entries": [], "issues": self.issues}
        try:
            while self.pos < self.size:
                self.layout()
                if self.pos >= self.size:
                    break
                if self.data[self.pos] == 64:
                    self.entry()
                else:
                    self.pos += 1
        except _Halt:
            if self.active is not None:
                self.active["end"] = self.pos
        return {"entries": self.entries, "issues": self.issues}


def parse_bibtex(data: bytes) -> dict:
    """Read bounded BibTeX bytes as source data; never expand or execute them."""
    if not isinstance(data, bytes):
        raise TypeError("parse_bibtex expects bytes so source offsets remain byte offsets")
    return _Parser(data).parse()
