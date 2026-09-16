# Lean 环境、可信库与形式检查

本文件是 AGENT.md 的规范性附件，规定 Lean 阶段的运行环境、依赖锁定、公理政策、形式检查与精简迭代。事实基础：`formal/` 下已有三个真实项目按同一配方构建（`AgtXIvRootMath`、`AgtXIvVarela`、`AgtXIvStabilizerness`）；本文件把在跑的做法写成规范，不是从零设计。

## 1. 工具链与构建

- 每个 Lean 项目以单行 `lean-toolchain` 固定版本；当前三个项目均为 `leanprover/lean4:v4.30.0-rc2`（release commit `3dc1a088b6d2d8eafe25a7cd7ec7b58d731bd7cc`）。换工具链等于换环境，按 REVIEW §4 重跑受影响检查。
- 工具链装在仓库本地（`.tools/elan`，已 gitignore），构建时设 `ELAN_HOME` 指向它并调用其 `lake`，例如：
  - `ELAN_HOME=<repo>/.tools/elan <repo>/.tools/elan/bin/lake build`
  - 审计：`… lake env lean Audit.lean`
- 构建会执行 tactic 与元程序，能力上等同于运行代码。模型生成的 Lean 源码是不可信输入；应在隔离、凭证最小化的环境中构建，不在高权限宿主直接构建。凭证最小化环境不是网络出口沙箱：禁用未授权网络与凭据由运行服务负责，本目录未实现该沙箱。
- 验收必须在干净环境重跑。增量构建受 `.lake` 缓存影响，缓存命中只说明之前构建过，不等于本轮验证；接受检查应记录实际命令、工具版本与日志。

## 2. 依赖与锁定

- 直接依赖声明在 `lakefile.toml`；解析结果在 `lake-manifest.json`，含传递依赖的精确 commit。信任是传递的：信任 mathlib 等于同时信任它拖入的全部包（当前 RootMath 的 manifest 有 10 个条目）。
- 复现必须使用 manifest 记录的 resolved `rev`，不得重新解析 `inputRev`（`main` 等符号名会漂移）。`lake update` 不会更新传递依赖的 pins（Lean 仓库公开 issue `lean4#13084`），升级后须自行核对 manifest。
- 本地 path 依赖（如 `Reference/LeanQuantum`）须额外固定 git identity；其自身 `lakefile.lean` 以无 revision 方式 require mathlib，是已知复现陷阱：记录实际解析到的 rev，不能假定它与本仓库锁定值一致。
- LeanQuantum 的 `Quantumlib.Data.Error.Operator` 因无关 Shor code 例子里含占位符而被刻意排除（见 `formal/AgtXIvRootMath/README.md`），在准入登记完成前不得新导入。
- 可导入的外部库以 [registry/trusted-packages.json](registry/trusted-packages.json) 为准；不在清单内的 import 不得进入正式交付。新增库=registry 新条目 + 固定 toolchain/mathlib rev + 公开理由；撤销条目阻止新构建使用，但不改写既有历史记录。

## 3. 公理与占位符政策

- 正式验收的公理允许集是 `{propext, Classical.choice, Quot.sound}`（Lean 三标准逻辑公理）。"零公理"不是标准，也不是真实数学定理的常态；是否允许其它公理由 registry 与环境政策决定。
- `sorry` 会展开为公理 `sorryAx`；tactic 失败时 Lean 还可能自动插入没有文字 `sorry` 的 synthetic sorry。因此必须对最终目标及其传递依赖执行 `#print axioms`，不能只搜索源码文本。
- 目标声明出现 `sorryAx`、项目自定义公理、把原目标直接声明为公理、或额外可信机制不在允许集内，均判失败。
- 源码级禁用构造（olean 级工具看不到，需单独扫描并在诊断中解释）：
  - 原生计算：`native_decide`、`decide +native`（自 Lean 4.29 起每个原生计算会生成独立可审计公理，仍不作为默认允许项）；
  - 编译期替换：`@[implemented_by]`、`@[extern]`、`@[csimp]`（已知可绕过 `#print axioms` 的公开 bug `lean4#7463`）；
  - 绕过内核或环境：`debug.skipKernelTC`、`addDeclWithoutChecking`；
  - 承重声明使用 `unsafe`／`partial`；
  - 自定义 `notation`／`macro`／`elab` 重定义目标陈述中的记号。
  使用前必须显式记录理由并纳入固定环境政策；未记录的按违规处理。
- 机器检查通过只说明"该声明在此环境下有证明"，不说明"该声明就是原命题"。陈述含义由 R4 盲反译与 R5 对齐负责，不能用编译成功替代。

## 4. 形式检查（R3）

独立检查服务在固定环境执行获准命令，实际构建包含 `expected_declarations` 的目标文件；至少核对：

1. 固定 Lean 工具链与依赖锁，构建的是目标文件，不是另一个空模块。
2. 每个完整目标声明的实际 elaborated type 与可信目标比较：对象、量词顺序、假设、结论；检查名称遮蔽、局部实例、记号或新增定义是否改变含义。
3. 目标及依赖中的占位符、额外公理与额外可信机制，按环境白名单审查传递依赖。
4. 保存真实命令、工具版本、代码与包锁哈希、构建日志、声明与公理审计结果。
5. 高风险或政策要求时，加做 `.olean` 级重放（`lake env leanchecker`，Lean v4.28 起随工具链分发）或外部内核／comparator；未运行就记录未运行，不能记为通过。

`#print axioms` 是传递检查；普通编译成功不排除依赖中的 sorry。机械结果不替代反译与对齐。工具入口：`check_interfaces.py --kind audit` 可按允许集核对审计输出；Lean 草稿的 **声明名摘要**（`declaration_name_digests`，sha256 取自全限定名）随检查报告输出，供宿主在精简迭代间比对名集合，不能用来判断陈述是否被改写。

## 5. 精简迭代（R3b，收敛即停）

- 轮次为 R3b（编号定义见 [REVIEW.md](REVIEW.md) §1／§3）：位于 R3 形式检查通过之后、R4 盲反译之前，使昂贵的独立审阅只对最终字节运行一次。
- 目的：提升跨项目可复用性、降低构建成本，不改变数学含义。
- 只允许修改证明体。每轮红线（必须重跑并保持不变）：`#print axioms` 输出一致；TARGET 声明**名**集合一致（`--expect-target-names`）。
- 这两条红线的实际覆盖范围必须说清楚：公理比对拦不住陈述改动（改弱一个仍可证的定理，公理依赖一模一样）；名摘要拦不住同名改写（摘要取的是全限定名，不是陈述）。**同名改写陈述目前没有机器拦截**，靠人工复核与 R3 的可信目标比较，R4／R5 兜底；elaborated 类型摘要是未实现项。
- 修改陈述、定义或类型实例不是精简：视为新定理，回 R2 重新走声明关与组包，按 REVIEW §4 重跑对应检查。
- 每轮至少记录一项可测量指标：未使用假设警告／`#lint`、import 足迹（importGraph）、构建时间、mathlib 既有定义的复用、禁用构造清单。没有可测量改进即停；最多 2 轮。
- 最终字节必须重跑 formal-check；若精简前后字节哈希不同，R4／R5 不能沿用旧结论。

## 6. 环境变更与失效

修改工具链、库锁、定义、类型实例或公理政策时，旧环境的通过结论不能迁移；按 REVIEW §4 的失效范围表处理。新环境与新 packet 绑定，历史通过记录保持原环境归属。

## 7. 当前实现边界

- 未实现：自动组包与调度、隔离构建服务、独立 formal-check 回执、目标声明解析与语义对应检查、statement 摘要的宿主侧冻结流程。
- 已知缺口：没有 tracked bootstrap 创建 `.tools/elan`；没有单一环境锁文件；历史校验器的工具链绑定方式不完全一致；CI 不构建 Lean；构建从未在干净缓存下作为验收运行。
- 教学案例 `example/and-swap/` 的 Lean 冒烟测试只能说明该小例可编译，不说明上述服务已接入。
