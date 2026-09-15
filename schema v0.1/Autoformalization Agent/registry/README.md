# 可信库注册表

本目录把"允许导入哪些外部 Lean 库"从散文变成可查询、可撤销的数据。注册表是**导入准入清单**，不是数学正确性认证：条目记录的是信任来源、锁定方式与已知限制，机器可核对的部分只有登记数据本身。

## 1. 为什么单独成文件

政策（信任谁、为什么）变化慢，运行清单（本轮用哪个 commit）变化快，两者必须分开：

- 注册表回答：哪个库、哪个信任层级、谁在什么时间基于什么理由批准、有哪些 import 限制、有没有被撤销。
- `lake-manifest.json` 回答：这一次构建实际用了哪个 commit、传递依赖有哪些。
- 每个正式交付只能 import 注册表内的库；环境与检查要求见 [../ENVIRONMENT.md](../ENVIRONMENT.md)。

## 2. 信任层级

| 层级 | 含义 | 当前条目 |
|---|---|---|
| `BASE` | 社区主线基础库，有维护者评审与 CI | `mathlib` |
| `PHYSICS` | 领域库；核心与快速通道分目标，默认只准入核心 | `physlib`（仅 Physlib 核心目标） |
| `LOCAL_FROZEN` | 本地 path 依赖，额外固定 git identity 与禁用模块 | 暂未登记（见 `not_registered`） |
| `REVOKED` | 撤销条目；阻止新构建使用，不改写历史 | 暂无 |

## 3. 条目字段

`name`、`url`、`kind`（`GIT` / `LOCAL_PATH`）、`trust_tier`、`status`（`ACTIVE` / `PROBATIONARY` / `REVOKED`）、`rationale`、`pinned_rev_examples`（已实际使用并审计过的 toolchain + rev 记录）、`import_restrictions`、`known_risks`、`approved_at`。

单人维护下这些字段不是给别人看的，是给未来的自己看的：没有第二个人兜底，机器可读的登记与理由就是唯一能拦住"顺手加一个 import"的东西。

## 4. 增、改、撤销

- 新增：先做 import 冒烟测试，记录 toolchain 与实际 mathlib rev，再写条目；`rationale` 必须说明信任来源，不能只写"需要"。
- 升级：更新条目与 manifest，按 [../REVIEW.md](../REVIEW.md) 第 6 节重跑受影响检查；旧环境结论不迁移。
- 撤销：`status` 改为 `REVOKED` 并保留条目与理由；既有历史记录保持原样。

## 5. 第一版说明与待决事项

- 第一版按用户决定只收录 `mathlib` 与 `physlib`。`physlib` 状态为 `PROBATIONARY`：允许使用，但首次使用前必须实测与 `leanprover/lean4:v4.30.0-rc2`、mathlib `c1e30e17…` 的兼容性并回写。
- `physlib` 由 PhysLean（原 HepLean）与 Lean-QuantumInfo 合并而来，仓库内 `PhyslibAlpha`（评审较松、接受 AI 大规模贡献）与 `QuantumInfo`（独立规范）均未自动准入。
- `LeanQuantum` 暂未登记，但既有 `formal/AgtXIvRootMath` 已在用。新形式化在登记为 `LOCAL_FROZEN` 条目（含 `Quantumlib.Data.Error.Operator` 禁用项）之前，不得新导入。
- 注册表尚未接入自动检查：当前 `check_interfaces.py` 不读取本文件，import 与注册表的一致性检查属于待实现项（见 [../validation-report.json](../validation-report.json)）。
