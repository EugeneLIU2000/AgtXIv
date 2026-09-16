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

`name`、`url`、`kind`（`GIT` / `LOCAL_PATH`）、`trust_tier`、`status`（`ACTIVE` / `PROBATIONARY` / `REVOKED`）、`rationale`、`pinned_rev_examples`（已实际使用并审计过的 toolchain + rev 记录）、`upstream_observed`（直接读上游构建文件得到的事实：其 toolchain、mathlib pin 及 pin 方式、全部 lean_lib、defaultTargets、额外依赖、编译参数，附观测日期与来源）、`import_restrictions`、`known_risks`、`approved_at`。

`pinned_rev_examples` 记的是**我们用过什么**，`upstream_observed` 记的是**上游当时是什么**。两者分开，是因为前者能审计、后者会变；上游变了就重新观测并改写日期，不要把旧观测当现状。

单人维护下这些字段不是给别人看的，是给未来的自己看的：没有第二个人兜底，机器可读的登记与理由就是唯一能拦住"顺手加一个 import"的东西。

## 4. 增、改、撤销

- 新增：先做 import 冒烟测试，记录 toolchain 与实际 mathlib rev，再写条目；`rationale` 必须说明信任来源，不能只写"需要"。
- 升级：更新条目与 manifest，按 [../REVIEW.md](../REVIEW.md) 第 4 节重跑受影响检查；旧环境结论不迁移。
- 撤销：`status` 改为 `REVOKED` 并保留条目与理由；既有历史记录保持原样。

## 5. 第一版说明与待决事项

- 第一版按用户决定只收录 `mathlib` 与 `physlib`。`physlib` 状态为 `PROBATIONARY`：政策上准入，**实际上当前被阻断**（见下条）。
- 2026-09-15 直接读上游构建文件得到三项事实，已写入条目：
  1. **三个 lean_lib 全部设 `-Dwarn.sorry=false`**——physlib 刻意保留 `sorry` 并关闭警告。我们 import 它之后，目标的 `#print axioms` 可能报 `sorryAx`，对允许集 `{propext, Classical.choice, Quot.sound}` 是硬失败。这是 [CONFORMANCE E06](../CONFORMANCE.md) 的情形，属于预期会发生，不是理论风险。
  2. **版本冲突已确证**，不再是“待验证”：physlib 用 Lean `v4.33.0` + mathlib `v4.33.0`，本仓库锁 `v4.30.0-rc2` + mathlib `c1e30e17…`。一个 lake 项目只有一个 toolchain 和一个 mathlib，所以不升级整条链就装不进来；升级则三个 `formal/` 项目的既有通过全部作废重跑（[REVIEW](../REVIEW.md) §4）。
  3. physlib 的 lakefile 用 **tag** `v4.33.0` 作 mathlib 的 `rev`，与本注册表 `pin_rule` 的“完整 commit”要求不一致；真实 pin 必须从它自己的 `lake-manifest.json` 读，不能信 lakefile。另外它还 require `doc-gen4`，一个文档生成器会进入依赖闭包。
- `PhyslibAlpha`（评审较松、接受 AI 大规模贡献）与 `QuantumInfo`（独立规范）均未自动准入。注意 `defaultTargets` 只管 physlib 仓库内 `lake build` 构建什么，**对下游 import 没有任何约束**：`PhyslibAlpha` 是已声明的 `lean_lib`，`import PhyslibAlpha.X` 照样能用。这条限制只能由我们自己的 import 扫描执行，目前属待实现项。
- `LeanQuantum` 暂未登记，但既有 `formal/AgtXIvRootMath` 已在用。新形式化在登记为 `LOCAL_FROZEN` 条目（含 `Quantumlib.Data.Error.Operator` 禁用项）之前，不得新导入。
- 注册表尚未接入自动检查：当前 `check_interfaces.py` 不读取本文件，import 与注册表的一致性检查属于待实现项（见 [../validation-report.json](../validation-report.json)）。
