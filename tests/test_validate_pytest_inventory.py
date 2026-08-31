from __future__ import annotations

import copy
import hashlib
import io
import json
import os
import platform
import shutil
import signal
import subprocess
import sys
import sysconfig
import time
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from tools import validate_pytest_inventory as validator


COMMIT = "1" * 40
RUNTIME = {
    "python_implementation": "CPython",
    "python_version": platform.python_version(),
    "pytest_version": "7.4.4",
    "pluggy_version": "1.6.0",
    "uv_version": "0.10.0",
    "platform": {
        "os_name": os.name,
        "sys_platform": sys.platform,
        "system": platform.system(),
        "release": platform.release(),
        "machine": platform.machine(),
        "python_platform": sysconfig.get_platform(),
        "cache_tag": sys.implementation.cache_tag,
    },
    "installed_distributions": [
        {"name": "pluggy", "version": "1.6.0"},
        {"name": "pytest", "version": "7.4.4"},
    ],
}


def write_runtime_inputs(root: Path) -> None:
    (root / ".python-version").write_text(
        platform.python_version() + "\n", encoding="utf-8"
    )
    (root / "pyproject.toml").write_text(
        """
[tool.uv]
required-version = "==0.10.0"
""".lstrip(),
        encoding="utf-8",
    )
    (root / "uv.lock").write_text(
        """
version = 1

[[package]]
name = "pytest"
version = "7.4.4"

[[package]]
name = "pluggy"
version = "1.6.0"
""".lstrip(),
        encoding="utf-8",
    )


def runtime_provider(root: Path, process_runner) -> dict:
    return copy.deepcopy(RUNTIME)


def base_collection() -> dict:
    return {
        "pytest_exit_code": 0,
        "worker_runtime": {
            "dont_write_bytecode": True,
            "hash_seed": "0",
            "no_user_site": "1",
            "safe_path": True,
            "utf8_mode": True,
        },
        "node_ids": [
            "tests/test_alpha.py::test_plain",
            "tests/test_alpha.py::test_parameterized[case-a]",
            "tests/test_alpha.py::test_deselected",
        ],
        "selected_node_ids": [
            "tests/test_alpha.py::test_plain",
            "tests/test_alpha.py::test_parameterized[case-a]",
        ],
        "marker_declarations": [
            {
                "node_id": "tests/test_alpha.py::test_plain",
                "markers": [
                    {
                        "name": "skipif",
                        "args": [False],
                        "kwargs": {"reason": "POSIX-only implementation detail"},
                    }
                ],
            }
        ],
        "collection_skips": [
            {"node_id": "tests/test_optional.py", "reason": "optional corpus absent"}
        ],
        "deselected_node_ids": ["tests/test_alpha.py::test_deselected"],
        "collection_errors": [],
    }


def make_inventory(root: Path, collection: dict | None = None) -> dict:
    write_runtime_inputs(root)
    return validator.build_inventory(
        root,
        collection or base_collection(),
        runtime_provider=runtime_provider,
    )


def git_blob_oid(content: bytes) -> str:
    return hashlib.sha1(
        f"blob {len(content)}\0".encode("ascii") + content,
        usedforsecurity=False,
    ).hexdigest()


def repository_files(marker: bytes = b"committed\n") -> dict[str, bytes]:
    return {
        ".python-version": (platform.python_version() + "\n").encode(),
        "pyproject.toml": b'[tool.uv]\nrequired-version = "==0.10.0"\n',
        "tests/test_marker.py": marker,
        "uv.lock": b'version = 1\n[[package]]\nname = "pytest"\nversion = "7.4.4"\n'
        b'[[package]]\nname = "pluggy"\nversion = "1.6.0"\n',
    }


def repository_manifest(files: dict[str, bytes] | None = None) -> bytes:
    files = repository_files() if files is None else files
    return b"".join(
        (
            f"100644 blob {git_blob_oid(content)} {len(content)}\t{path}".encode()
            + b"\0"
        )
        for path, content in sorted(files.items())
    )


def fake_git_io(
    files: dict[str, bytes] | None = None,
    *,
    commit: str = COMMIT,
    manifest: bytes | None = None,
):
    files = repository_files() if files is None else files
    blobs = {git_blob_oid(content): content for content in files.values()}
    calls: list[tuple[str, ...]] = []

    def run(command, cwd, environment, timeout):
        command = tuple(command)
        calls.append(command)
        assert environment["GIT_TERMINAL_PROMPT"] == "0"
        assert environment["GIT_NO_REPLACE_OBJECTS"] == "1"
        if "cat-file" in command and "-e" in command:
            return validator.ProcessResult(0)
        if "rev-parse" in command:
            return validator.ProcessResult(0, (commit + "\n").encode())
        if "ls-tree" in command:
            return validator.ProcessResult(0, manifest or repository_manifest(files))
        raise AssertionError(f"unexpected command: {command}")

    def blob_run(repo, object_id, environment, timeout, max_bytes):
        calls.append(("git", "cat-file", "blob", object_id))
        assert environment["GIT_NO_REPLACE_OBJECTS"] == "1"
        payload = blobs[object_id]
        assert len(payload) <= max_bytes
        return validator.ProcessResult(0, payload)

    return run, blob_run, calls


def test_schema_is_meta_valid_and_accepts_generated_inventory(tmp_path: Path) -> None:
    inventory = make_inventory(tmp_path)
    schema = json.loads(
        (
            validator.REPO
            / "schemas/repository-validation/pytest-inventory.schema.json"
        ).read_text(encoding="utf-8")
    )
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(inventory)
    assert inventory["counts"] == {
        "collected": 3,
        "selected": 2,
        "deselected": 1,
        "collection_skipped": 1,
        "marker_declarations": 1,
    }
    assert inventory["marker_declarations"][0]["markers"][0]["name"] == "skipif"


def test_schema_patterns_use_ecma_absolute_end_and_share_distribution_rule() -> None:
    schema = json.loads(
        (
            validator.REPO
            / "schemas/repository-validation/pytest-inventory.schema.json"
        ).read_text(encoding="utf-8")
    )
    distribution_pattern = schema["properties"]["runtime"]["properties"][
        "installed_distributions"
    ]["items"]["properties"]["name"]["pattern"]
    patterns = [
        distribution_pattern,
        schema["$defs"]["sha256"]["pattern"],
        schema["$defs"]["version"]["pattern"],
        schema["$defs"]["node_id"]["pattern"],
    ]
    assert all(pattern.endswith(r"(?![\s\S])") for pattern in patterns)
    assert distribution_pattern == validator.DISTRIBUTION_NAME_PATTERN


def test_schema_documents_python_semantic_authority_and_i_json_bounds() -> None:
    schema = json.loads(
        (
            validator.REPO
            / "schemas/repository-validation/pytest-inventory.schema.json"
        ).read_text(encoding="utf-8")
    )
    comment = schema["$comment"]
    assert "structural interoperability layer only" in comment
    assert "Python validator is the normative authority" in comment
    assert "lexical 1 and 1.0" in comment
    assert "Schema validation alone never establishes baseline acceptance" in comment
    for count_schema in schema["properties"]["counts"]["properties"].values():
        assert count_schema["maximum"] == validator.I_JSON_EXACT_INTEGER_MAX
    assert schema["$defs"]["input_binding"]["properties"]["byte_size"][
        "maximum"
    ] == validator.I_JSON_EXACT_INTEGER_MAX
    integer_schema = next(
        branch
        for branch in schema["$defs"]["stable_json_value"]["oneOf"]
        if branch.get("type") == "integer"
    )
    assert integer_schema == {
        "type": "integer",
        "minimum": validator.I_JSON_EXACT_INTEGER_MIN,
        "maximum": validator.I_JSON_EXACT_INTEGER_MAX,
    }


def test_schema_may_accept_lexical_float_integer_but_python_rejects_it(
    tmp_path: Path,
) -> None:
    inventory = make_inventory(tmp_path)
    inventory["marker_declarations"][0]["markers"][0]["args"] = [1.0]
    schema = json.loads(
        (
            validator.REPO
            / "schemas/repository-validation/pytest-inventory.schema.json"
        ).read_text(encoding="utf-8")
    )
    # Draft 2020-12 treats mathematically integral 1.0 as an integer.  The
    # top-level schema comment explicitly delegates exact runtime types to Python.
    assert Draft202012Validator(schema).is_valid(inventory)
    with pytest.raises(validator.InventoryError) as error:
        validator._validate_inventory_document(inventory)
    assert error.value.code == "INVALID_BASELINE"


def test_collection_skip_nul_is_rejected_by_schema_and_python(tmp_path: Path) -> None:
    inventory = make_inventory(tmp_path)
    inventory["collection_skips"][0]["reason"] = "invalid\x00reason"
    schema = json.loads(
        (
            validator.REPO
            / "schemas/repository-validation/pytest-inventory.schema.json"
        ).read_text(encoding="utf-8")
    )
    assert not Draft202012Validator(schema).is_valid(inventory)
    with pytest.raises(validator.InventoryError) as error:
        validator._validate_inventory_document(inventory)
    assert error.value.code == "INVALID_BASELINE"


def test_candidate_marker_integer_must_be_in_i_json_exact_range(
    tmp_path: Path,
) -> None:
    write_runtime_inputs(tmp_path)
    collection = base_collection()
    collection["marker_declarations"][0]["markers"][0]["args"] = [
        validator.I_JSON_EXACT_INTEGER_MAX + 1
    ]
    with pytest.raises(validator.InventoryError) as error:
        validator.build_inventory(
            tmp_path, collection, runtime_provider=runtime_provider
        )
    assert error.value.code == "UNSTABLE_MARKER_VALUE"


@pytest.mark.parametrize(
    "name,accepted",
    [
        ("pytest", True),
        ("zope-interface", True),
        ("a1", True),
        ("", False),
        (" pytest", False),
        ("pytest ", False),
        ("pytest\n", False),
        ("café", False),
        ("-pytest", False),
        ("pytest-", False),
        ("pytest_name", False),
        ("Pytest", False),
    ],
    ids=[
        "simple",
        "hyphenated",
        "digit",
        "empty",
        "leading-space",
        "trailing-space",
        "trailing-lf",
        "non-ascii",
        "leading-hyphen",
        "trailing-hyphen",
        "underscore",
        "uppercase",
    ],
)
def test_distribution_name_schema_regex_and_loader_are_differentially_aligned(
    tmp_path: Path, name: str, accepted: bool
) -> None:
    inventory = make_inventory(tmp_path)
    schema = json.loads(
        (
            validator.REPO
            / "schemas/repository-validation/pytest-inventory.schema.json"
        ).read_text(encoding="utf-8")
    )
    name_schema = schema["properties"]["runtime"]["properties"][
        "installed_distributions"
    ]["items"]["properties"]["name"]
    schema_accepts_name = Draft202012Validator(name_schema).is_valid(name)
    python_accepts_name = validator.DISTRIBUTION_NAME_RE.fullmatch(name) is not None
    assert schema_accepts_name is accepted
    assert python_accepts_name is accepted

    if accepted:
        return
    inventory["runtime"]["installed_distributions"][0]["name"] = name
    assert not Draft202012Validator(schema).is_valid(inventory)
    with pytest.raises(validator.InventoryError) as error:
        validator._validate_inventory_document(inventory)
    assert error.value.code == "INVALID_BASELINE"


@pytest.mark.parametrize(
    "field,value",
    [("plugin_autoload", 0), ("double_collection_required", 1)],
    ids=["zero-is-not-false", "one-is-not-true"],
)
def test_collection_contract_rejects_integer_bool_impostors(
    tmp_path: Path, field: str, value: int
) -> None:
    inventory = make_inventory(tmp_path)
    inventory["collection_contract"][field] = value
    schema = json.loads(
        (
            validator.REPO
            / "schemas/repository-validation/pytest-inventory.schema.json"
        ).read_text(encoding="utf-8")
    )
    assert not Draft202012Validator(schema).is_valid(inventory)
    with pytest.raises(validator.InventoryError) as error:
        validator._validate_inventory_document(inventory)
    assert error.value.code == "INVALID_BASELINE"


@pytest.mark.parametrize(
    "pattern_target",
    ["distribution", "sha256", "version", "node_id"],
)
def test_schema_and_loader_both_reject_pattern_values_with_trailing_lf(
    tmp_path: Path, pattern_target: str
) -> None:
    inventory = make_inventory(tmp_path)
    if pattern_target == "distribution":
        inventory["runtime"]["installed_distributions"][0]["name"] += "\n"
    elif pattern_target == "sha256":
        inventory["node_set_sha256"] += "\n"
    elif pattern_target == "version":
        inventory["runtime"]["pytest_version"] += "\n"
        for distribution in inventory["runtime"]["installed_distributions"]:
            if distribution["name"] == "pytest":
                distribution["version"] += "\n"
    else:
        inventory["node_ids"][0] += "\n"
        inventory["selected_node_ids"][0] += "\n"
        inventory["marker_declarations"][0]["node_id"] += "\n"
    schema = json.loads(
        (
            validator.REPO
            / "schemas/repository-validation/pytest-inventory.schema.json"
        ).read_text(encoding="utf-8")
    )
    assert not Draft202012Validator(schema).is_valid(inventory)
    with pytest.raises(validator.InventoryError) as error:
        validator._validate_inventory_document(inventory)
    assert error.value.code == "INVALID_BASELINE"


def test_length_prefixed_set_and_order_digests_have_distinct_semantics() -> None:
    first = ["tests/test_a.py::test_a", "tests/test_b.py::test_b"]
    reversed_nodes = list(reversed(first))
    first_set = validator._length_prefixed_digest(
        validator.NODE_SET_DOMAIN, sorted(first, key=lambda item: item.encode("utf-8"))
    )
    second_set = validator._length_prefixed_digest(
        validator.NODE_SET_DOMAIN,
        sorted(reversed_nodes, key=lambda item: item.encode("utf-8")),
    )
    first_order = validator._length_prefixed_digest(validator.NODE_ORDER_DOMAIN, first)
    second_order = validator._length_prefixed_digest(
        validator.NODE_ORDER_DOMAIN, reversed_nodes
    )
    assert first_set == second_set
    assert first_order != second_order
    assert first_set != first_order


@pytest.mark.parametrize(
    "node_id,code",
    [
        ("/tests/test_a.py::test_a", "INVALID_NODE_PATH"),
        ("tests/../outside.py::test_a", "INVALID_NODE_PATH"),
        ("tests\\test_a.py::test_a", "INVALID_NODE_PATH"),
        ("tests/test_a.py::test_a\nextra", "INVALID_NODE_ID"),
        ("tests/test_cafe\u0301.py::test_a", "NON_NFC_NODE_ID"),
        ("src/test_a.py::test_a", "INVALID_NODE_PATH"),
    ],
    ids=["absolute", "traversal", "backslash", "newline", "non-nfc", "outside-tests"],
)
def test_node_id_validation_fails_closed(node_id: str, code: str) -> None:
    with pytest.raises(validator.InventoryError) as error:
        validator.normalize_node_id(node_id)
    assert error.value.code == code


def test_posix_validation_applies_to_path_without_rewriting_parameter_id() -> None:
    node_id = r"tests/test_regex.py::test_pattern[\\d+]"
    assert validator.normalize_node_id(node_id) == node_id


def test_duplicate_and_selected_deselected_overlap_are_rejected(tmp_path: Path) -> None:
    write_runtime_inputs(tmp_path)
    duplicate = base_collection()
    duplicate["node_ids"].append(duplicate["node_ids"][0])
    with pytest.raises(validator.InventoryError) as error:
        validator.build_inventory(
            tmp_path, duplicate, runtime_provider=runtime_provider
        )
    assert error.value.code == "DUPLICATE_NODE_ID"

    overlap = base_collection()
    overlap["deselected_node_ids"] = [overlap["node_ids"][0]]
    with pytest.raises(validator.InventoryError) as error:
        validator.build_inventory(tmp_path, overlap, runtime_provider=runtime_provider)
    assert error.value.code == "INVALID_COLLECTION_PAYLOAD"


@pytest.mark.parametrize(
    "payload,expected_code",
    [
        ('{"\\ud800":1,"\\ud800":2}', "DUPLICATE_JSON_KEY"),
        ('{"\\u7528\\u6237":1,"\\u7528\\u6237":2}', "DUPLICATE_JSON_KEY"),
        ('{"value":"\\ud800"}', "INVALID_JSON"),
    ],
    ids=["surrogate-duplicate-key", "unicode-duplicate-key", "surrogate-value"],
)
def test_strict_json_errors_never_echo_user_unicode(
    payload: str, expected_code: str
) -> None:
    with pytest.raises(validator.InventoryError) as error:
        validator._strict_json_loads(payload, label="baseline")
    assert error.value.code == expected_code
    record = error.value.record()
    encoded = validator._canonical_json_bytes(record)
    encoded.decode("utf-8", errors="strict")
    assert all(ord(character) < 128 for character in record["message"])
    assert "\ud800" not in record["message"]
    assert "\u7528\u6237" not in record["message"]


@pytest.mark.parametrize(
    "payload",
    [
        '{"value":NaN}',
        '{"value":Infinity}',
        '{"value":-Infinity}',
        '{"value":1e999999}',
    ],
    ids=["nan", "positive-infinity", "negative-infinity", "float-overflow"],
)
def test_strict_json_rejects_non_finite_numbers_with_stable_error(
    payload: str,
) -> None:
    with pytest.raises(validator.InventoryError) as error:
        validator._strict_json_loads(payload, label="baseline")
    assert error.value.code == "INVALID_JSON"
    assert validator._canonical_json_bytes(error.value.record()).decode("utf-8")


def test_strict_json_integer_bound_is_independent_of_cpython_digit_limit() -> None:
    payload = '{"value":' + ("1" * 5000) + "}"
    original_limit = sys.get_int_max_str_digits()
    try:
        sys.set_int_max_str_digits(0)
        with pytest.raises(validator.InventoryError) as error:
            validator._strict_json_loads(payload, label="baseline")
    finally:
        sys.set_int_max_str_digits(original_limit)
    assert error.value.code == "INVALID_JSON"
    assert error.value.record()["message"] == (
        "JSON integer is outside the I-JSON exact range"
    )


def test_strict_json_accepts_exact_integer_boundaries_and_rejects_neighbors() -> None:
    parsed = validator._strict_json_loads(
        json.dumps(
            {
                "minimum": validator.I_JSON_EXACT_INTEGER_MIN,
                "maximum": validator.I_JSON_EXACT_INTEGER_MAX,
            }
        ),
        label="baseline",
    )
    assert parsed == {
        "minimum": validator.I_JSON_EXACT_INTEGER_MIN,
        "maximum": validator.I_JSON_EXACT_INTEGER_MAX,
    }
    for value in (
        validator.I_JSON_EXACT_INTEGER_MIN - 1,
        validator.I_JSON_EXACT_INTEGER_MAX + 1,
    ):
        with pytest.raises(validator.InventoryError) as error:
            validator._strict_json_loads(
                '{"value":' + str(value) + "}", label="baseline"
            )
        assert error.value.code == "INVALID_JSON"


def test_error_record_safely_escapes_lone_surrogates_and_user_unicode() -> None:
    error = validator.InventoryError(
        "USER_INPUT_ERROR",
        "bad \ud800 \u7528\u6237",
        details={"value\ud800": "\u503c\ud800", "nested": ["\u7b54\u6848"]},
    )
    record = error.record()
    encoded = validator._canonical_json_bytes(record)
    decoded = encoded.decode("utf-8", errors="strict")
    assert "\ud800" not in decoded
    assert "\u7528\u6237" not in decoded
    assert "\u503c" not in decoded
    assert "\u7b54\u6848" not in decoded
    assert "\\ud800" in decoded
    assert all(ord(character) < 128 for character in decoded)


def test_canonical_json_classifies_lone_surrogate_without_unicode_traceback() -> None:
    with pytest.raises(validator.InventoryError) as error:
        validator._canonical_json_bytes({"value": "\ud800"})
    assert error.value.code == "NON_CANONICAL_JSON"
    assert validator._canonical_json_bytes(error.value.record()).decode("utf-8")


def test_main_replaces_unencodable_result_with_utf8_json_error(
    monkeypatch, capfd
) -> None:
    monkeypatch.setattr(
        validator,
        "evaluate",
        lambda options: (0, {"errors": [{"message": "\ud800"}]}),
    )
    exit_code = validator.main(["--candidate"])
    captured = capfd.readouterr()
    assert captured.err == ""
    result = json.loads(captured.out)
    assert exit_code == 1
    assert result["outcome"] == "ERROR"
    assert result["errors"] == [
        {
            "code": "MACHINE_OUTPUT_ENCODING_FAILED",
            "message": "inventory result could not be encoded as UTF-8 JSON",
        }
    ]


def test_marker_values_reject_unstable_objects(tmp_path: Path) -> None:
    write_runtime_inputs(tmp_path)
    collection = base_collection()
    collection["marker_declarations"][0]["markers"][0]["args"] = [object()]
    with pytest.raises(validator.InventoryError) as error:
        validator.build_inventory(
            tmp_path, collection, runtime_provider=runtime_provider
        )
    assert error.value.code == "UNSTABLE_MARKER_VALUE"


def test_skip_deselection_and_raw_binding_drift_change_inventory_digest(
    tmp_path: Path,
) -> None:
    original = make_inventory(tmp_path)
    changed_collection = base_collection()
    changed_collection["collection_skips"][0]["reason"] = "a different reviewed reason"
    changed_collection["deselected_node_ids"] = [
        "tests/test_alpha.py::test_other_deselection"
    ]
    changed_collection["node_ids"][-1] = changed_collection["deselected_node_ids"][0]
    changed = validator.build_inventory(
        tmp_path, changed_collection, runtime_provider=runtime_provider
    )
    assert validator._inventory_digest(changed) != validator._inventory_digest(original)

    (tmp_path / "pyproject.toml").write_text(
        (tmp_path / "pyproject.toml").read_text(encoding="utf-8") + "\n# byte drift\n",
        encoding="utf-8",
    )
    rebound = validator.build_inventory(
        tmp_path, base_collection(), runtime_provider=runtime_provider
    )
    assert rebound["input_bindings"]["pyproject.toml"] != original["input_bindings"][
        "pyproject.toml"
    ]
    assert validator._inventory_digest(rebound) != validator._inventory_digest(original)


def test_collection_environment_clears_pytest_injection(monkeypatch) -> None:
    monkeypatch.setenv("PYTEST_ADDOPTS", "-k injected")
    monkeypatch.setenv("PYTEST_PLUGINS", "malicious.plugin")
    monkeypatch.setenv("PYTHONPATH", "/untrusted")
    environment = validator._collection_environment()
    assert "PYTEST_ADDOPTS" not in environment
    assert "PYTEST_PLUGINS" not in environment
    assert "PYTHONPATH" not in environment
    assert environment["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] == "1"
    assert environment["PYTHONHASHSEED"] == "0"


def test_git_environment_and_command_prefix_disable_local_injection(
    monkeypatch,
) -> None:
    monkeypatch.setenv("GIT_OBJECT_DIRECTORY", "/untrusted/objects")
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", "/untrusted/config")
    environment = validator._git_environment()
    assert "GIT_OBJECT_DIRECTORY" not in environment
    assert environment["GIT_CONFIG_GLOBAL"] == os.devnull
    assert environment["GIT_CONFIG_SYSTEM"] == os.devnull
    assert environment["GIT_CONFIG_NOSYSTEM"] == "1"
    assert environment["GIT_NO_REPLACE_OBJECTS"] == "1"
    prefix = validator._git_command_prefix()
    assert f"core.hooksPath={os.devnull}" in prefix
    assert "core.fsmonitor=false" in prefix
    assert all("attributes" not in value for value in prefix)
    assert all("filter" not in value for value in prefix)
    assert all("tar" not in value for value in prefix)


def test_two_collection_mismatch_fails_with_stable_code(tmp_path: Path) -> None:
    calls = 0

    def unstable(root):
        nonlocal calls
        calls += 1
        payload = base_collection()
        payload["node_ids"] = [f"tests/test_a.py::test_case[{calls}]"]
        payload["selected_node_ids"] = list(payload["node_ids"])
        payload["marker_declarations"] = []
        payload["collection_skips"] = []
        payload["deselected_node_ids"] = []
        return payload

    with pytest.raises(validator.InventoryError) as error:
        validator._collect_twice(tmp_path, unstable)
    assert error.value.code == "NONDETERMINISTIC_COLLECTION"


def test_collection_error_and_worker_error_do_not_become_inventory(
    tmp_path: Path,
) -> None:
    write_runtime_inputs(tmp_path)
    collection = base_collection()
    collection["pytest_exit_code"] = 2
    collection["collection_errors"] = [
        {"node_id": "tests/test_bad.py", "reason": "import failed"}
    ]
    with pytest.raises(validator.InventoryError) as error:
        validator.build_inventory(
            tmp_path, collection, runtime_provider=runtime_provider
        )
    assert error.value.code == "PYTEST_COLLECTION_FAILED"

    collection = base_collection()
    collection["worker_error"] = {
        "code": "PYTEST_IMPORT_FAILED",
        "message": "pytest import failed",
    }
    with pytest.raises(validator.InventoryError) as error:
        validator.build_inventory(
            tmp_path, collection, runtime_provider=runtime_provider
        )
    assert error.value.code == "PYTEST_IMPORT_FAILED"


def test_runtime_is_bound_to_python_pytest_pluggy_and_uv_pins(
    tmp_path: Path, monkeypatch
) -> None:
    write_runtime_inputs(tmp_path)
    versions = {"pytest": "7.4.4", "pluggy": "1.6.0"}
    monkeypatch.setattr(validator.metadata, "version", lambda name: versions[name])

    class Distribution:
        def __init__(self, name: str, version: str) -> None:
            self.metadata = {"Name": name}
            self.version = version

    distributions = [Distribution(name, version) for name, version in versions.items()]
    monkeypatch.setattr(validator.metadata, "distributions", lambda: distributions)

    def uv_runner(command, cwd, environment, timeout):
        assert tuple(command) == ("uv", "--version")
        return validator.ProcessResult(0, b"uv 0.10.0 (test build)\n")

    assert validator._default_runtime_provider(tmp_path, uv_runner) == RUNTIME
    versions["pytest"] = "8.0.0"
    with pytest.raises(validator.InventoryError) as error:
        validator._default_runtime_provider(tmp_path, uv_runner)
    assert error.value.code == "RUNTIME_LOCK_MISMATCH"
    assert error.value.details["mismatches"]["pytest"] == {
        "expected": "7.4.4",
        "actual": "8.0.0",
    }
    versions["pytest"] = "7.4.4"
    distributions.append(Distribution("unlocked-package", "1.0.0"))
    with pytest.raises(validator.InventoryError) as error:
        validator._default_runtime_provider(tmp_path, uv_runner)
    assert error.value.code == "RUNTIME_LOCK_MISMATCH"
    assert error.value.details["distributions"]["unlocked-package"] == {
        "installed": "1.0.0",
        "locked": None,
    }


def test_source_ref_must_be_a_full_lowercase_commit_before_git_runs(
    tmp_path: Path,
) -> None:
    def must_not_run(*args):
        raise AssertionError("invalid source ref must fail before spawning git")

    with pytest.raises(validator.InventoryError) as error:
        with validator.source_tree(tmp_path, "abc123", must_not_run):
            pass
    assert error.value.code == "INVALID_SOURCE_REF"


def test_bounded_raw_blob_failure_is_machine_classified(tmp_path: Path) -> None:
    runner, _, _ = fake_git_io()

    def limited_blob(repo, object_id, environment, timeout, max_bytes):
        return validator.ProcessResult(
            validator.PROCESS_OUTPUT_LIMIT_EXIT,
            b"x" * 16,
            output_limited=True,
        )

    with pytest.raises(validator.InventoryError) as error:
        validator._resolve_source_ref(
            tmp_path, COMMIT, runner, git_blob_runner=limited_blob
        )
    assert error.value.code == "GIT_BLOB_READ_FAILED"
    assert error.value.details["exit_code"] == validator.PROCESS_OUTPUT_LIMIT_EXIT
    assert error.value.details["output_limited"] is True


def test_source_ref_uses_verified_raw_blobs_not_dirty_worktree(
    tmp_path: Path,
) -> None:
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests/test_marker.py").write_bytes(b"dirty\n")
    runner, blob_runner, calls = fake_git_io()
    with validator.source_tree(
        tmp_path, COMMIT, runner, git_blob_runner=blob_runner
    ) as (snapshot, source):
        assert (snapshot / "tests/test_marker.py").read_bytes() == b"committed\n"
        assert snapshot != tmp_path
        assert source == {
            "mode": "GIT_BLOB_SNAPSHOT",
            "assurance_tier": "COMMIT_SNAPSHOT_UNSANDBOXED_DIAGNOSTIC",
            "requested_ref": COMMIT,
            "evaluated_commit": COMMIT,
            "content_may_differ_from_evaluated_commit": False,
            "baseline_commit_binding": "EXCLUDED_TO_AVOID_SELF_REFERENCE",
            "git_manifest_sha256": source["git_manifest_sha256"],
            "branch_evidence_eligible": False,
            "filesystem_isolation_enforced": False,
            "network_isolation_enforced": False,
        }
    assert sum("rev-parse" in call for call in calls) == 1
    assert sum("ls-tree" in call for call in calls) == 1
    assert any(call[1:3] == ("cat-file", "blob") for call in calls)
    assert all("archive" not in call for call in calls)


@pytest.mark.parametrize(
    "manifest,code",
    [
        (b"100644 blob " + b"0" * 40 + b" 3\t../escape.py\0", "INVALID_GIT_MANIFEST"),
        (b"120000 blob " + b"0" * 40 + b" 3\ttests/link.py\0", "UNSUPPORTED_GIT_ENTRY"),
        (
            b"100644 blob " + b"0" * 40 + b" 3\ttests/A.py\0"
            + b"100644 blob " + b"1" * 40 + b" 3\ttests/a.py\0",
            "GIT_PATH_COLLISION",
        ),
        (
            b"100644 blob " + b"0" * 40 + b" 3\ttests/a\0"
            + b"100644 blob " + b"1" * 40 + b" 3\ttests/a/file.py\0",
            "INVALID_GIT_MANIFEST",
        ),
        (
            (
                "100644 blob " + "0" * 40 + " 3\ttests/cafe\u0301.py\0"
            ).encode("utf-8"),
            "INVALID_GIT_MANIFEST",
        ),
    ],
    ids=["traversal", "symlink", "casefold", "file-parent", "non-nfc"],
)
def test_git_manifest_rejects_unsafe_paths_and_types(
    manifest: bytes, code: str
) -> None:
    with pytest.raises(validator.InventoryError) as error:
        validator._parse_git_tree_manifest(manifest)
    assert error.value.code == code


def test_worktree_evaluation_is_explicitly_diagnostic(tmp_path: Path) -> None:
    runner, _, _ = fake_git_io()
    with validator.source_tree(tmp_path, None, runner) as (root, source):
        assert root == tmp_path.resolve()
        assert source["mode"] == "WORKTREE"
        assert source["assurance_tier"] == "WORKTREE_DIAGNOSTIC"
        assert source["content_may_differ_from_evaluated_commit"] is True
        assert source["branch_evidence_eligible"] is False


def test_git_unavailability_is_injectable_and_machine_classified(tmp_path: Path) -> None:
    def missing_git(command, cwd, environment, timeout):
        return validator.ProcessResult(127, b"", b"git not found")

    code, result = validator.evaluate(
        validator.EvaluationOptions("CANDIDATE"),
        repo=tmp_path,
        process_runner=missing_git,
        collection_runner=lambda root: pytest.fail("collection must not start"),
        runtime_provider=runtime_provider,
    )
    assert code == 1
    assert result["outcome"] == "ERROR"
    assert result["errors"] == [
        {
            "code": "GIT_COMMAND_FAILED",
            "message": "git rev-parse failed",
            "details": {"exit_code": 127},
        }
    ]


def test_candidate_and_check_are_machine_readable_without_commit_self_reference(
    tmp_path: Path,
) -> None:
    write_runtime_inputs(tmp_path)
    runner, _, _ = fake_git_io()
    candidate_code, candidate = validator.evaluate(
        validator.EvaluationOptions("CANDIDATE"),
        repo=tmp_path,
        process_runner=runner,
        collection_runner=lambda root: base_collection(),
        runtime_provider=runtime_provider,
    )
    assert candidate_code == 0
    assert candidate["outcome"] == "PASS"
    assert candidate["source"]["evaluated_commit"] == COMMIT
    assert "source" not in candidate["inventory"]

    baseline = tmp_path / "baseline.json"
    baseline.write_text(
        json.dumps(candidate["inventory"], ensure_ascii=False), encoding="utf-8"
    )
    check_code, check = validator.evaluate(
        validator.EvaluationOptions("CHECK", baseline=baseline),
        repo=tmp_path,
        process_runner=runner,
        collection_runner=lambda root: base_collection(),
        runtime_provider=runtime_provider,
    )
    assert check_code == 0
    assert check["outcome"] == "PASS"
    assert check["baseline_sha256"] == validator._sha256_file(baseline)

    changed = json.loads(baseline.read_text(encoding="utf-8"))
    changed["node_ids"][0] = "tests/test_alpha.py::test_replaced"
    changed["selected_node_ids"][0] = "tests/test_alpha.py::test_replaced"
    changed["marker_declarations"][0]["node_id"] = (
        "tests/test_alpha.py::test_replaced"
    )
    changed["node_set_sha256"] = validator._length_prefixed_digest(
        validator.NODE_SET_DOMAIN,
        sorted(changed["node_ids"], key=lambda item: item.encode("utf-8")),
    )
    changed["node_order_sha256"] = validator._length_prefixed_digest(
        validator.NODE_ORDER_DOMAIN, changed["selected_node_ids"]
    )
    baseline.write_text(json.dumps(changed), encoding="utf-8")
    mismatch_code, mismatch = validator.evaluate(
        validator.EvaluationOptions("CHECK", baseline=baseline),
        repo=tmp_path,
        process_runner=runner,
        collection_runner=lambda root: base_collection(),
        runtime_provider=runtime_provider,
    )
    assert mismatch_code == 1
    assert mismatch["outcome"] == "FAIL"
    details = mismatch["errors"][0]["details"]
    assert details["added_node_ids"] == ["tests/test_alpha.py::test_plain"]
    assert details["removed_node_ids"] == ["tests/test_alpha.py::test_replaced"]


def test_real_collection_worker_ignores_pytest_environment_injection(
    tmp_path: Path, monkeypatch
) -> None:
    (tmp_path / "tests").mkdir()
    (tmp_path / "pyproject.toml").write_text(
        '[tool.pytest.ini_options]\ntestpaths = ["tests"]\n'
        'addopts = "-k nothing_matches"\n',
        encoding="utf-8",
    )
    (tmp_path / "tests/test_sample.py").write_text(
        """
import pytest

@pytest.mark.skipif(False, reason="stable condition")
@pytest.mark.parametrize("value", [1, 2], ids=["one", "two"])
def test_sample(value):
    assert value
""".lstrip(),
        encoding="utf-8",
    )
    monkeypatch.setenv("PYTEST_ADDOPTS", "-k nothing_matches")
    monkeypatch.setenv("PYTEST_PLUGINS", "plugin_that_must_not_be_imported")
    payload = validator._collect_twice(tmp_path, validator._default_collection_runner)
    assert payload["pytest_exit_code"] == 0
    assert payload["node_ids"] == [
        "tests/test_sample.py::test_sample[one]",
        "tests/test_sample.py::test_sample[two]",
    ]
    assert payload["selected_node_ids"] == payload["node_ids"]
    assert len(payload["marker_declarations"]) == 2
    assert all(
        record["markers"][0]["name"] == "skipif"
        for record in payload["marker_declarations"]
    )


def test_schema_and_tool_share_structural_node_id_rules() -> None:
    schema = json.loads(
        (
            validator.REPO
            / "schemas/repository-validation/pytest-inventory.schema.json"
        ).read_text(encoding="utf-8")
    )
    node_schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        **schema["$defs"]["node_id"],
    }
    node_validator = Draft202012Validator(node_schema)
    invalid = [
        "/tests/test_a.py::test_a",
        "tests/../test_a.py::test_a",
        "tests/./test_a.py::test_a",
        "tests\\test_a.py::test_a",
        "tests/test_a.py::::test_a",
        "tests/test_a.py:test_a",
        "src/test_a.py::test_a",
    ]
    for node_id in invalid:
        assert not node_validator.is_valid(node_id), node_id
        with pytest.raises(validator.InventoryError):
            validator.normalize_node_id(node_id)
    # NFC is a semantic invariant documented by the schema and enforced by the tool.
    with pytest.raises(validator.InventoryError) as error:
        validator.normalize_node_id("tests/test_cafe\u0301.py::test_a")
    assert error.value.code == "NON_NFC_NODE_ID"


@pytest.mark.parametrize("mutation", ["add", "rewrite", "pyc"])
def test_collection_source_mutation_is_rejected(
    tmp_path: Path, mutation: str
) -> None:
    write_runtime_inputs(tmp_path)
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests/test_sample.py").write_text("def test_sample(): pass\n")

    def mutating_collection(root: Path) -> dict:
        if mutation == "add":
            (root / "added.txt").write_text("new\n")
        elif mutation == "rewrite":
            (root / "tests/test_sample.py").write_text("def test_changed(): pass\n")
        else:
            cache = root / "tests/__pycache__"
            cache.mkdir()
            (cache / "test_sample.cpython-312.pyc").write_bytes(b"pyc")
        return base_collection()

    with pytest.raises(validator.InventoryError) as error:
        validator._guarded_collection(
            tmp_path,
            collection_runner=mutating_collection,
            process_runner=lambda *args: validator.ProcessResult(0),
            runtime_provider=runtime_provider,
        )
    assert error.value.code == "SOURCE_TREE_MUTATED_DURING_COLLECTION"
    assert any(error.value.details.values())


def test_commit_evaluation_collects_two_fresh_exact_snapshots(tmp_path: Path) -> None:
    runner, blob_runner, _ = fake_git_io()
    roots: list[Path] = []

    def recording_collection(root: Path) -> dict:
        roots.append(root)
        assert (root / "tests/test_marker.py").read_bytes() == b"committed\n"
        return base_collection()

    code, result = validator.evaluate(
        validator.EvaluationOptions("CANDIDATE", source_ref=COMMIT),
        repo=tmp_path,
        process_runner=runner,
        git_blob_runner=blob_runner,
        collection_runner=recording_collection,
        runtime_provider=runtime_provider,
    )
    assert code == 0
    assert result["outcome"] == "PASS"
    assert len(roots) == 2
    assert roots[0] != roots[1]
    assert all(not root.exists() for root in roots)
    assert result["source"]["branch_evidence_eligible"] is False
    assert result["source"]["filesystem_isolation_enforced"] is False
    assert result["source"]["network_isolation_enforced"] is False
    assert result["inventory"]["evidence_scope"] == validator.EVIDENCE_SCOPE
    baseline = tmp_path / "source-ref-baseline.json"
    baseline.write_text(json.dumps(result["inventory"]), encoding="utf-8")
    check_code, check = validator.evaluate(
        validator.EvaluationOptions("CHECK", baseline=baseline, source_ref=COMMIT),
        repo=tmp_path,
        process_runner=runner,
        git_blob_runner=blob_runner,
        collection_runner=lambda root: base_collection(),
        runtime_provider=runtime_provider,
    )
    assert check_code == 0
    assert check["outcome"] == "PASS"


def test_raw_blob_oid_and_size_mismatch_fail_closed(tmp_path: Path) -> None:
    files = repository_files()
    runner, _, _ = fake_git_io(files)

    def wrong_blob(repo, object_id, environment, timeout, max_bytes):
        expected = {git_blob_oid(value): value for value in files.values()}[object_id]
        changed = b"x" * len(expected)
        return validator.ProcessResult(0, changed)

    with pytest.raises(validator.InventoryError) as error:
        validator._resolve_source_ref(
            tmp_path, COMMIT, runner, git_blob_runner=wrong_blob
        )
    assert error.value.code == "GIT_BLOB_OID_MISMATCH"


def test_raw_blob_materialization_preserves_git_executable_mode(
    tmp_path: Path,
) -> None:
    payload = b"#!/bin/sh\nexit 0\n"
    object_id = git_blob_oid(payload)
    prepared = validator.PreparedGitSource(
        COMMIT,
        (
            validator.GitTreeEntry(
                "bin/tool", "100755", "blob", object_id, len(payload)
            ),
        ),
        (validator.GitBlob(object_id, payload),),
    )
    validator._materialize_git_source(prepared, tmp_path)
    target = tmp_path / "bin/tool"
    assert target.read_bytes() == payload
    assert target.stat().st_mode & 0o777 == 0o755


def _run_git_test_command(repo: Path, *arguments: str) -> str:
    result = subprocess.run(
        ("git", *arguments),
        cwd=repo,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return result.stdout.strip()


def _initialize_git_repository(tmp_path: Path, files: dict[str, str]) -> str:
    _run_git_test_command(tmp_path, "init", "-q")
    _run_git_test_command(tmp_path, "config", "user.name", "Inventory Test")
    _run_git_test_command(tmp_path, "config", "user.email", "inventory@example.invalid")
    _run_git_test_command(tmp_path, "config", "commit.gpgsign", "false")
    for relative, content in files.items():
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    _run_git_test_command(tmp_path, "add", "--all")
    _run_git_test_command(tmp_path, "commit", "-q", "-m", "fixture")
    return _run_git_test_command(tmp_path, "rev-parse", "HEAD")


@pytest.mark.skipif(shutil.which("git") is None, reason="git executable unavailable")
def test_git_replace_is_disabled_for_raw_blob_snapshot(tmp_path: Path) -> None:
    commit = _initialize_git_repository(tmp_path, {"tracked.txt": "original\n"})
    original_oid = _run_git_test_command(tmp_path, "hash-object", "tracked.txt")
    replacement = tmp_path / "replacement.txt"
    replacement.write_text("replacement\n", encoding="utf-8")
    replacement_oid = _run_git_test_command(
        tmp_path, "hash-object", "-w", "replacement.txt"
    )
    _run_git_test_command(tmp_path, "replace", original_oid, replacement_oid)
    assert _run_git_test_command(tmp_path, "cat-file", "-p", original_oid) == (
        "replacement"
    )

    prepared = validator._resolve_source_ref(
        tmp_path, commit, validator._default_process_runner
    )
    snapshot = tmp_path / "snapshot"
    snapshot.mkdir()
    validator._materialize_git_source(prepared, snapshot)
    assert (snapshot / "tracked.txt").read_text(encoding="utf-8") == "original\n"


@pytest.mark.parametrize("attribute_location", ["committed", "info"])
@pytest.mark.skipif(shutil.which("git") is None, reason="git executable unavailable")
def test_raw_blob_snapshot_never_executes_attribute_filters(
    tmp_path: Path, attribute_location: str
) -> None:
    attributes = "tracked.txt filter=evil export-ignore export-subst\n"
    committed_files = {"tracked.txt": "$Format:%H$\n"}
    if attribute_location == "committed":
        committed_files[".gitattributes"] = attributes
    commit = _initialize_git_repository(tmp_path, committed_files)
    if attribute_location == "info":
        (tmp_path / ".git/info/attributes").write_text(attributes, encoding="utf-8")

    side_effect = tmp_path / "FILTER_WAS_EXECUTED"
    filter_script = tmp_path / "evil-filter.sh"
    filter_script.write_text(
        "#!/bin/sh\ntouch '" + str(side_effect) + "'\ncat\n",
        encoding="utf-8",
    )
    filter_script.chmod(0o755)
    _run_git_test_command(
        tmp_path, "config", "filter.evil.clean", str(filter_script)
    )
    _run_git_test_command(
        tmp_path, "config", "filter.evil.smudge", str(filter_script)
    )
    _run_git_test_command(
        tmp_path, "config", "filter.evil.process", str(filter_script)
    )
    _run_git_test_command(tmp_path, "config", "filter.evil.required", "true")

    prepared = validator._resolve_source_ref(
        tmp_path, commit, validator._default_process_runner
    )
    snapshot = tmp_path / "snapshot"
    snapshot.mkdir()
    validator._materialize_git_source(prepared, snapshot)
    assert (snapshot / "tracked.txt").read_text(encoding="utf-8") == (
        "$Format:%H$\n"
    )
    assert not side_effect.exists()


def test_bounded_process_runner_limits_output_and_timeout(tmp_path: Path) -> None:
    output_limited = validator._run_streaming_process(
        (sys.executable, "-c", "import sys; sys.stdout.write('x' * 10000)"),
        tmp_path,
        validator._collection_environment(),
        5,
        max_stdout_bytes=32,
        max_stderr_bytes=32,
    )
    assert output_limited.returncode == validator.PROCESS_OUTPUT_LIMIT_EXIT
    assert output_limited.output_limited is True
    assert len(output_limited.stdout) == 32

    timed_out = validator._run_streaming_process(
        (sys.executable, "-c", "import time; time.sleep(10)"),
        tmp_path,
        validator._collection_environment(),
        0,
        max_stdout_bytes=32,
        max_stderr_bytes=32,
    )
    assert timed_out.returncode == validator.PROCESS_TIMEOUT_EXIT
    assert timed_out.timed_out is True


@pytest.mark.skipif(os.name != "posix", reason="POSIX process groups required")
def test_sigkill_wait_is_bounded_when_process_never_confirms_exit(
    tmp_path: Path, monkeypatch
) -> None:
    class StuckProcess:
        pid = 424242
        returncode = None

        def __init__(self) -> None:
            self.stdout = io.BytesIO()
            self.stderr = io.BytesIO()
            self.wait_timeouts: list[float | None] = []

        def poll(self):
            return None

        def wait(self, timeout=None):
            self.wait_timeouts.append(timeout)
            raise subprocess.TimeoutExpired("stuck", timeout)

    process = StuckProcess()
    signalled: list[tuple[int, int]] = []
    monkeypatch.setattr(validator.subprocess, "Popen", lambda *args, **kwargs: process)
    monkeypatch.setattr(
        validator, "_original_process_group_exists", lambda process_group_id: False
    )
    monkeypatch.setattr(
        validator,
        "_signal_original_process_group",
        lambda process_group_id, signal_number: signalled.append(
            (process_group_id, signal_number)
        )
        or True,
    )
    monkeypatch.setattr(validator, "PROCESS_TERMINATION_GRACE_SECONDS", 0.001)

    result = validator._run_streaming_process(
        ("stuck-command",),
        tmp_path,
        {},
        0,
        max_stdout_bytes=32,
        max_stderr_bytes=32,
    )
    assert result.returncode == validator.PROCESS_GROUP_LEAK_EXIT
    assert result.cleanup_unconfirmed is True
    assert result.timed_out is True
    assert process.wait_timeouts == [0.001, 0.001]
    assert None not in process.wait_timeouts
    assert signalled == [
        (process.pid, signal.SIGTERM),
        (process.pid, signal.SIGKILL),
    ]


@pytest.mark.skipif(os.name != "posix", reason="POSIX process groups required")
def test_stuck_original_group_cleanup_is_bounded_and_machine_classified(
    tmp_path: Path, monkeypatch
) -> None:
    class ExitedLeader:
        pid = 434343
        returncode = 0
        stdout = io.BytesIO()
        stderr = io.BytesIO()

        def poll(self):
            return 0

    process = ExitedLeader()
    signalled: list[tuple[int, int]] = []
    monkeypatch.setattr(validator.subprocess, "Popen", lambda *args, **kwargs: process)
    monkeypatch.setattr(
        validator, "_original_process_group_exists", lambda process_group_id: True
    )
    monkeypatch.setattr(
        validator,
        "_signal_original_process_group",
        lambda process_group_id, signal_number: signalled.append(
            (process_group_id, signal_number)
        )
        or True,
    )
    monkeypatch.setattr(validator, "PROCESS_TERMINATION_GRACE_SECONDS", 0)

    started = time.monotonic()
    result = validator._run_streaming_process(
        ("exited-command",),
        tmp_path,
        {},
        5,
        max_stdout_bytes=32,
        max_stderr_bytes=32,
    )
    assert time.monotonic() - started < 0.5
    assert result.returncode == validator.PROCESS_GROUP_LEAK_EXIT
    assert result.process_group_leaked is True
    assert result.cleanup_unconfirmed is True
    assert signalled == [
        (process.pid, signal.SIGTERM),
        (process.pid, signal.SIGKILL),
    ]


@pytest.mark.skipif(os.name != "posix", reason="POSIX process groups required")
def test_leader_exit_cleans_only_its_original_devnull_child_group(
    tmp_path: Path,
) -> None:
    leaked_marker = tmp_path / "leaked-child-survived"
    unrelated = subprocess.Popen(
        (sys.executable, "-c", "import time; time.sleep(10)"),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    leader_script = (
        "import subprocess,sys; "
        "child=subprocess.Popen([sys.executable,'-c',"
        + repr(
            "import pathlib,time; time.sleep(0.4); "
            f"pathlib.Path({str(leaked_marker)!r}).write_text('survived')"
        )
        + "],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); "
        "print(child.pid,flush=True)"
    )
    try:
        result = validator._run_streaming_process(
            (sys.executable, "-c", leader_script),
            tmp_path,
            validator._collection_environment(),
            5,
            max_stdout_bytes=128,
            max_stderr_bytes=128,
        )
        assert result.returncode == validator.PROCESS_GROUP_LEAK_EXIT
        assert result.process_group_leaked is True
        assert unrelated.poll() is None
        time.sleep(0.6)
        assert not leaked_marker.exists()
    finally:
        unrelated.terminate()
        unrelated.wait(timeout=5)


def test_invalid_or_unsafe_baseline_fails_before_any_subprocess(
    tmp_path: Path,
) -> None:
    calls = 0

    def must_not_run(*args):
        nonlocal calls
        calls += 1
        raise AssertionError("no subprocess may run before baseline validation")

    invalid = tmp_path / "invalid.json"
    invalid.write_text("{not-json", encoding="utf-8")
    code, result = validator.evaluate(
        validator.EvaluationOptions("CHECK", baseline=invalid),
        repo=tmp_path,
        process_runner=must_not_run,
        collection_runner=lambda root: pytest.fail("collection must not start"),
        runtime_provider=runtime_provider,
    )
    assert code == 1
    assert result["errors"][0]["code"] == "INVALID_JSON"
    assert calls == 0


@pytest.mark.skipif(os.name != "posix", reason="dirfd/openat safety is POSIX-only")
@pytest.mark.parametrize("unsafe_kind", ["symlink", "ancestor-symlink", "fifo"])
def test_baseline_symlink_ancestor_and_fifo_fail_without_blocking_or_spawning(
    tmp_path: Path, unsafe_kind: str
) -> None:
    target = tmp_path / "target.json"
    target.write_text("{}", encoding="utf-8")
    if unsafe_kind == "symlink":
        baseline = tmp_path / "baseline.json"
        baseline.symlink_to(target)
    elif unsafe_kind == "ancestor-symlink":
        real_parent = tmp_path / "real-parent"
        real_parent.mkdir()
        (real_parent / "baseline.json").write_text("{}", encoding="utf-8")
        linked_parent = tmp_path / "linked-parent"
        linked_parent.symlink_to(real_parent, target_is_directory=True)
        baseline = linked_parent / "baseline.json"
    else:
        baseline = tmp_path / "baseline.fifo"
        os.mkfifo(baseline)
    calls = 0

    def must_not_run(*args):
        nonlocal calls
        calls += 1
        raise AssertionError("unsafe baseline must fail before spawning")

    started = time.monotonic()
    code, result = validator.evaluate(
        validator.EvaluationOptions("CHECK", baseline=baseline),
        repo=tmp_path,
        process_runner=must_not_run,
        collection_runner=lambda root: pytest.fail("collection must not start"),
        runtime_provider=runtime_provider,
    )
    assert time.monotonic() - started < 1
    assert code == 1
    assert result["errors"][0]["code"] == "BASELINE_UNSAFE"
    assert calls == 0


@pytest.mark.parametrize("baseline_location", ["inside", "outside"])
def test_collection_cannot_rewrite_baseline_to_self_pass(
    tmp_path: Path, baseline_location: str
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    inventory = make_inventory(repo)
    if baseline_location == "inside":
        baseline = repo / "baseline.json"
    else:
        external = tmp_path / "external"
        external.mkdir()
        baseline = external / "baseline.json"
    baseline.write_text(json.dumps(inventory, indent=2), encoding="utf-8")
    runner, _, _ = fake_git_io()

    def rewriting_collection(root: Path) -> dict:
        baseline.write_text(
            json.dumps(inventory, sort_keys=True, separators=(",", ":")),
            encoding="utf-8",
        )
        return base_collection()

    code, result = validator.evaluate(
        validator.EvaluationOptions("CHECK", baseline=baseline),
        repo=repo,
        process_runner=runner,
        collection_runner=rewriting_collection,
        runtime_provider=runtime_provider,
    )
    assert code == 1
    assert result["outcome"] == "ERROR"
    assert result["errors"][0]["code"] == "BASELINE_CHANGED_DURING_EVALUATION"


def test_baseline_ancestor_swap_is_detected_after_collection(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    inventory = make_inventory(repo)
    holder = tmp_path / "baseline-holder"
    holder.mkdir()
    baseline = holder / "baseline.json"
    baseline_bytes = json.dumps(inventory).encode("utf-8")
    baseline.write_bytes(baseline_bytes)
    old_holder = tmp_path / "old-baseline-holder"
    swapped = False
    runner, _, _ = fake_git_io()

    def swapping_collection(root: Path) -> dict:
        nonlocal swapped
        if not swapped:
            holder.rename(old_holder)
            holder.mkdir()
            baseline.write_bytes(baseline_bytes)
            swapped = True
        return base_collection()

    code, result = validator.evaluate(
        validator.EvaluationOptions("CHECK", baseline=baseline),
        repo=repo,
        process_runner=runner,
        collection_runner=swapping_collection,
        runtime_provider=runtime_provider,
    )
    assert code == 1
    assert result["errors"][0]["code"] == "BASELINE_CHANGED_DURING_EVALUATION"


@pytest.mark.skipif(os.name != "posix", reason="FIFO counterexample is POSIX-only")
def test_input_and_manifest_fifo_checks_do_not_block(tmp_path: Path) -> None:
    write_runtime_inputs(tmp_path)
    (tmp_path / ".python-version").unlink()
    os.mkfifo(tmp_path / ".python-version")
    started = time.monotonic()
    with pytest.raises(validator.InventoryError) as error:
        validator._input_bindings(tmp_path)
    assert time.monotonic() - started < 1
    assert error.value.code == "UNSAFE_INPUT_BINDING"

    (tmp_path / ".python-version").unlink()
    (tmp_path / ".python-version").write_text(
        platform.python_version() + "\n", encoding="utf-8"
    )
    (tmp_path / "tests").mkdir()
    os.mkfifo(tmp_path / "tests/collection.fifo")
    started = time.monotonic()
    with pytest.raises(validator.InventoryError) as error:
        validator._filesystem_manifest(tmp_path)
    assert time.monotonic() - started < 1
    assert error.value.code == "UNSUPPORTED_SOURCE_ENTRY"


def test_baseline_is_bounded_and_semantically_validated(
    tmp_path: Path, monkeypatch
) -> None:
    inventory = make_inventory(tmp_path)
    baseline = tmp_path / "baseline.json"

    invalid_variants = []
    extra = copy.deepcopy(inventory)
    extra["unexpected"] = True
    invalid_variants.append(extra)
    wrong_count = copy.deepcopy(inventory)
    wrong_count["counts"]["selected"] += 1
    invalid_variants.append(wrong_count)
    wrong_set = copy.deepcopy(inventory)
    wrong_set["deselected_node_ids"] = []
    invalid_variants.append(wrong_set)
    wrong_digest = copy.deepcopy(inventory)
    wrong_digest["node_set_sha256"] = "0" * 64
    invalid_variants.append(wrong_digest)
    for invalid in invalid_variants:
        baseline.write_text(json.dumps(invalid), encoding="utf-8")
        with pytest.raises(validator.InventoryError) as error:
            validator._load_baseline(baseline)
        assert error.value.code == "INVALID_BASELINE"

    monkeypatch.setattr(validator, "MAX_BASELINE_BYTES", 16)
    baseline.write_bytes(b"{" + b" " * 32 + b"}")
    with pytest.raises(validator.InventoryError) as error:
        validator._load_baseline(baseline)
    assert error.value.code == "BASELINE_TOO_LARGE"


def test_baseline_depth_and_selected_order_diff_are_explicit(tmp_path: Path) -> None:
    baseline = tmp_path / "baseline.json"
    nested: object = None
    for _ in range(validator.MAX_JSON_DEPTH + 1):
        nested = [nested]
    baseline.write_text(json.dumps(nested), encoding="utf-8")
    with pytest.raises(validator.InventoryError) as error:
        validator._load_baseline(baseline)
    assert error.value.code == "INVALID_BASELINE"

    expected_root = tmp_path / "expected"
    expected_root.mkdir()
    expected = make_inventory(expected_root)
    actual = copy.deepcopy(expected)
    actual["selected_node_ids"].reverse()
    actual["node_order_sha256"] = validator._length_prefixed_digest(
        validator.NODE_ORDER_DOMAIN, actual["selected_node_ids"]
    )
    validator._validate_inventory_document(actual)
    difference = validator._baseline_difference(expected, actual)
    assert difference["node_order_changed"] is False
    assert difference["selected_order_changed"] is True
