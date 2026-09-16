# 多轮审阅：本流水线的轮次编号与退回层

本文件是 AGENT.md 的规范性附件，也是 Paper → Proof → Lean 4 这条流水线轮次编号 R0–R5（含 R3 之后的 R3b）的唯一来源。通用审阅契约由 [Review Agent](<../Review Agent/AGENT.md>) 拥有：身份与独立性隔离、八个 `review.*` 操作的调用边界、可执行审阅意见的最低内容、盲反译首轮输入隔离与中性化、通用修订失效规则，细则见 [Review Agent INTERFACE](<../Review Agent/INTERFACE.md>) 与 [Review Agent CONFORMANCE](<../Review Agent/CONFORMANCE.md>)。本文件只写这些规则在本流水线的落点、轮次顺序与退回层，不复述其内容。不变量见 [AGENT.md](AGENT.md) §1 的 I1–I6；操作目录与身份底线见 [AGENT-CONTRACTS.md](../AGENT-CONTRACTS.md) §4.5、§6。

## 1. 轮次与接口

| 轮次 | 输入与检查问题 | 既有操作／产物 | 不通过时 |
|---|---|---|---|
| R0 草稿结构 | 当前草稿、Task、实际来源与记录；格式、引用、共同前提、作用范围与闭包 | 宿主机械校验，输出分层诊断 | 同一目标下修草稿；缺输入则等待 |
| R1 原文到 Lamport | MathClaim、来源、完整 snapshot、所选 plan；目标忠实、推理理由、前提适用、范围解除 | `review.argument` → argument-review；需要时 `review.alignment` → SOURCE_TO_ARGUMENT／SOURCE_TO_MATH | Proof 修订；来源提取错误退 Paper；历史依赖退 Dependency／`review.reuse` |
| R2 声明与生成 | 固定 packet 与形式环境；**先固定完整 Lean 声明并通过可复用性关**，再生成证明代码与对应表 | `formalization.generate` → 实际生成尝试 | 记号／实现问题修 Lean；陈述不忠实或不可复用则回 R2 重定声明；需新前提、目标或路线退上游并重新组包 |
| R3 形式检查 | 固定 packet、真实 attempt、环境、实际代码与构建产物 | `utility.formal-check` → formal-check，包含实际声明与审计日志 | 编译／tactic 错误回生成器；数学缺步回 Proof；环境缺失回 Utility |
| R3b 精简迭代 | R3 已通过的字节；仅证明体，收敛即停、上限 2 轮 | 生成者修订 → 对最终字节重跑 `utility.formal-check` | 无可测量改进即停；动到陈述则不是精简，按新定理回 R2 |
| R4 盲反译 | 只给 formal-environment 与必要的代码／定义字节；首轮输入白名单与中性化规则见 [Review Agent INTERFACE](<../Review Agent/INTERFACE.md>) | `review.backtranslate` → backtranslation，解释实际量词、假设、类型与结论 | 不明确则保留疑问，不从原文补答案 |
| R5 独立对齐 | 已冻结的反译、原数学／源目标、实际 formalization-attempt／formal-check | `review.alignment` → MATH_TO_FORMAL／必要的 SOURCE_TO_FORMAL | 目标不匹配则退对应生产层；保留 MISALIGNED／PARTIAL 等结论 |

本流水线对 R4 首轮补充两项禁项，因为它们是本目录的运行附件而不是 v0.0 业务记录，通用白名单管不到：lamport-view 阅读视图与 `declaration_map` 不得进入 R4 的可见输入。

“论证审阅支持”（R1 的 SUPPORTED）、“形式证明检查通过”（R3 的 KERNEL_CHECKED）、“与原目标含义对齐”（R5 的 ALIGNED）是三项不同结果，分别记录；`Result.outcome` 各值的含义见 [AGENT-CONTRACTS.md](../AGENT-CONTRACTS.md) §2.1。

早期声明检查可避免在错误的题目上耗费证明成本。轮次是七个检查边界，不是调用次数；本流水线要求每个边界各有归属，不要求固定跑满（见 [AGENT.md](AGENT.md) §2）。

## 2. R2 陈述可复用性关

目标：定理一旦被下游引用就从“成果”变成“接口”；跨项目复用时消费者只能看到声明，看不到证明体，而错误声明无法靠漂亮的证明补救。因此完整声明在写证明**之前**固定，并同时过两关。

1. **忠实**：声明与 MathClaim 的对象、量词顺序、假设、结论一致；标准化选择（实数／复数、矩阵维度、纯态／混态、归一化、对数底、近似范围）显式记录。
2. **可复用**：泛化到下游真正需要的范围（不锁死具体维数或域）；每个假设都被实际使用；复用 mathlib／physlib 既有定义而不是自造平行定义；公开命名稳定，不暴露局部辅助名。

操作性定义：在写证明体之前模拟一次未来的 `reuse-decision`——假设下一篇论文要在目标 T 上引用这条定理，`comparisons` 的五项匹配几项、`conditions` 会剩下几条。剩余条件越多，越难复用。该记录的字段语义、独立性要求与 CONDITIONAL 剩余条件的传递义务见 [Review Agent INTERFACE](<../Review Agent/INTERFACE.md>) §1 的 `review.reuse` 与 [Review Agent CONFORMANCE](<../Review Agent/CONFORMANCE.md>) E07；这里只把它用作 R2 的放行条件，模拟结果不是已登记的 reuse-decision。环境不匹配（toolchain／mathlib 版本不同）按 §4 处理。

发现声明不可复用时，修改声明属于新定理：回 R2 重开工，不在证明写完后再“顺手泛化”。简单的未使用假设警告与 `#lint` 由机器给出，泛化判断仍需人工或独立审阅，不能被格式检查替代。

## 3. R3b 精简迭代（收敛即停，上限 2 轮）

- 位置：R3 形式检查通过之后、R4 盲反译之前；它是 R3 与 R4 之间的独立轮次，不是 R3 的一部分，使昂贵的独立审阅只对最终字节运行一次。
- 只允许修改证明体。任何陈述、定义或类型实例的改变都不是精简，按新定理回 R2。
- 每轮红线，以及各自实际能拦住什么：
  1. `#print axioms` 输出一致——拦得住新引入的 `sorryAx` 与新公理；**拦不住**陈述改动（改弱一个仍可证的定理，公理依赖不变）。
  2. TARGET 声明名集合一致（`check_interfaces.py --expect-target-names`，错误码 `TARGET_NAME_BASELINE`／`TARGET_NAME_DRIFT`）——拦得住改名、增删目标；**拦不住**同名之下陈述被改写，因为摘要取的是 draft 中 `declaration` 字段（一个全限定名），不是陈述本身。
  3. 因此**同名改写陈述目前没有机器拦截**：R3b 的陈述红线靠人工复核加 R3 的可信目标比较，最终由 R4／R5 兜底。elaborated 类型摘要属于未实现项（见 validation-report.json）。
- 每轮记录至少一项可测量改进：未使用假设警告／`#lint`、import 足迹、构建时间、mathlib 定义复用、禁用构造清单。没有可测量改进即停；简单引理允许一轮就停，最多 2 轮。
- 最终字节必须重跑 formal-check；字节变化后 R4／R5 不能沿用旧结论。
- 环境与工具细节见 [ENVIRONMENT.md](ENVIRONMENT.md) 第 5 节。

## 4. 修订后的失效范围（本流水线）

| 改动 | 需要重做 |
|---|---|
| 只修改无语义变化的 Lean 实现（含 R3b 精简轮） | 新 attempt、机器检查；新字节的反译／对齐不能直接套用旧结论。只有字节哈希未变时才可复用旧结论 |
| 修改 Lean 声明、定义或类型实例 | 声明反译、形式检查、对齐；若与 packet 不符先重新组包 |
| 修改 Lamport 步骤或实际依赖路线 | 新 plan／snapshot、受影响的论证审阅、新 packet，再检查受影响形式结果 |
| 新增前提、改变数学目标或范围 | 新命题／提取修订及必要 scope review；保留旧目标的失败或未完成处置 |
| 修改工具链、库锁或公理政策 | 新环境与新 packet、重新构建和相应检查；旧环境的通过不能迁移为新环境通过 |

本表只给本流水线各类改动的重做清单。通用规则——审阅结论绑定精确引用与字节、旧批准不覆盖新版本、没有已实现的证据复用规则就不跳过重审——见 [Review Agent INTERFACE](<../Review Agent/INTERFACE.md>) §6 与 [AGENT-CONTRACTS.md](../AGENT-CONTRACTS.md) §5。

## 5. 本流水线的实现边界

本目录的 schema 与 `check_interfaces.py` 只检查草稿格式及明确的基础约束；不运行模型、不派单、不查文献、不展开完整 RecordSet、不认证审阅者、不解析 Lean 含义、不生成独立 formal-check。真正运行的系统仍需宿主装配、引用集合检查、受控构建和各证据门实现。已运行命令、实现边界与未实现清单见 [validation-report.json](validation-report.json)；`review.*` 一侧的实现边界见 [Review Agent 的 validation-report](<../Review Agent/validation-report.json>)。
