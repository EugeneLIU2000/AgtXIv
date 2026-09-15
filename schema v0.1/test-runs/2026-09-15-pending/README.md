# 2026-09-15 PENDING_TESTS 执行证据

用户指定范围：`schema v0.1/PENDING_TESTS.md` 第 3–5 节全部条目。
执行原则：有执行入口的先跑；无入口/被明令禁止的如实记录，不补假记录。
未执行：Lean 构建（U-06 禁止）、Git/数据库/Docker（U-08 禁止）、模型调用（C-07、X-07 无运行器）、A07 案例重放（D-01 要求不重放）。

环境：macOS arm64，仓库 `.venv` Python 3.12.2，pytest 7.4.4。代码版本：HEAD `8de080c` + 未提交的 readme/契约修改与六个新 Agent 目录、handoff。

## 日志索引

| 文件 | 命令（仓库根目录执行） | 结果 |
|---|---|---|
| `01-validate-check.log` | `.venv/bin/python -B 'schema v0.1/validate.py' --check` | exit 0，`valid: true` |
| `02-repo-tests.log` | `.venv/bin/python -B -m unittest discover -s 'schema v0.1/tests' -v` | 28 passed |
| `03-agent-pytest.log` | `.venv/bin/python -B -m pytest 'schema v0.1/Paper Agent/tests' 'schema v0.1/Autoformalization Agent/tests' -q` | 89 passed |
| `04-handoff-tests.log` | `.venv/bin/python -B -m unittest discover -s 'schema v0.1/handoff/tests' -v` | 28 passed（57.2s） |
| `05-reader-pytest.log` | `.venv/bin/python -B -m pytest 'schema v0.1/Reader Agent/tests' -q` | 2 failed / 40 passed（测试工具缺陷，见 13） |
| `06-planner-conformance.log` | `Planner Agent/check_interfaces.py --kind propose --input conformance/...` | 正例通过；反例 `SELF_REDISPATCH` + `PROPOSAL_INPUT` |
| `07-delta-conformance.log` | `Delta Agent/check_interfaces.py --kind delta --input conformance/...` | 正例通过；反例 4 个码 |
| `08-probe-planner.log` | `probes/probe_planner.py`（P-01…P-05） | 6/6 MATCH；P-02、P-04 记录已知缺口 |
| `09-probe-delta.log` | `probes/probe_delta.py`（DL-01…DL-04） | 6/6 MATCH；DL-02 记录 G-07，DL-04 为人审层 |
| `10-schema-meta.log` | `probes/probe_schema_meta.py` | 24 个 schema 全部通过 2020-12 元校验与 $ref 解析 |
| `11-collected-agent-tests.log` | `pytest --collect-only -q`（Paper+AF） | 89 个测试节点 |
| `12-collected-reader-tests.log` | `pytest --collect-only -q`（Reader） | 42 个测试节点 |
| `13-reader-harness-diagnosis.log` | 直接调用测试 helper | 证明 `target=None` 被替换为默认对象 |

## 追加执行（N-01、N-05，2026-09-15 晚）

| 文件 | 命令 | 结果 |
|---|---|---|
| `14-reader-pytest-after-fix.log` | `pytest 'schema v0.1/Reader Agent/tests' -q` | 42 通过（N-01 修复后） |
| `15-agent-runner.log` | `.venv/bin/python -B 'schema v0.1/tests/run_agent_tests.py'` | 9/9 PASS（约 76s） |
| `16-validate-repo-only.log` | `tools/validate_repo.py --profile fast --only schema-v0.1-agent-tests` | PASS（77s，CI 接线验证） |
| `17-root-validate-repo-tests.log` | `pytest tests/test_validate_repo.py -q` | 142 通过 |

## 追加执行（N-02、N-03、N-04，2026-09-15 晚）

| 文件 | 命令 | 结果 |
|---|---|---|
| `18-agent-runner-after-N02-N04.log` | `python -B 'schema v0.1/tests/run_agent_tests.py'` | 21/21 PASS（含 3 Dependency、2 Review、4 Utility 新步骤） |
| `19-validate-repo-after-N04.log` | `tools/validate_repo.py --profile fast --only schema-v0.1-agent-tests` | PASS（82s） |
| `20-root-tests-after-N04.log` | `pytest tests/test_validate_repo.py -q` | 142 通过 |

## 关键结论

- 失败仅来自 Reader 测试工具本身：`tests/test_interfaces.py` 的 `explanation(target=None)` 把 None 替换成默认 `math-claim`，导致两个"无依据"用例从未真正构造成无依据；检查器逻辑正确。
- P-02（阻塞建议进入 follow_up）与 P-04（同输入不同用途被误判重复）按预期暴露规范缺口，尚未机器拦截。
- DL-02 确认为 G-07：检查器只要求比较集合与指派目标相交，3 个目标只比较 1 个仍通过。
- Dependency / Review / Utility 没有语义检查器，本轮只能做 schema 元校验。
- 这些 Agent 测试不在 CI：`make check` 走 `tools/validate_repo.py --fast`，其 `test-suite` 检查运行根目录 `pytest`，而 `pyproject.toml` 的 `testpaths = ["tests"]` 不含 `schema v0.1/**/tests`。
