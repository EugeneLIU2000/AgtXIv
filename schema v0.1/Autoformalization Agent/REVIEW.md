# 多轮审阅：检查哪一层，错误退回哪一层

这是规范性附件。审阅针对精确目标及版本，不是让几个模型轮流说“看起来没问题”。读者意见也不是正式科学证据。Review 不修改被审对象，生产者修订后再送审。

## 1. 审阅轮次与接口

| 轮次 | 输入与检查问题 | 既有操作／产物 | 不通过时 |
|---|---|---|---|
| R0 草稿结构 | 当前草稿、Task、实际来源／记录；格式、引用、共同前提、范围与闭包 | 宿主机械校验；错误是诊断，不生成科学认可 | 同一目标下修草稿；缺输入则等待 |
| R1 原文到 Lamport | MathClaim、来源、完整 snapshot、所选 plan；目标忠实、推理理由、前提适用、范围解除 | `review.argument` → argument-review；需要时 `review.alignment` → SOURCE_TO_ARGUMENT／SOURCE_TO_MATH 对齐 | Proof 修订；来源提取错误退 Paper；历史依赖退 Dependency／review.reuse |
| R2 声明与生成 | 固定 packet 与形式环境；先核对完整 Lean 声明，再补证明代码 | `formalization.generate` → 实际生成尝试；早期声明检查可请求独立反译／对齐，仍不能冒充已证明 | 记号／实现问题修 Lean；需新前提、目标或路线退上游并重新组包 |
| R3 形式检查 | 固定 packet、真实 attempt、环境、实际代码与构建产物 | `utility.formal-check` → formal-check，包含实际声明和审计日志 | 编译／tactic 错误回生成器；数学缺步回 Proof；环境缺失回 Utility |
| R4 盲反译 | 只给形式环境及必要的代码／定义字节，不给原文或预期答案 | `review.backtranslate` → backtranslation，解释实际量词、假设、类型和结论 | 不明确则保留疑问，不从原文补答案 |
| R5 独立对齐 | 已冻结的反译、原数学／源目标、实际 formalization-attempt／formal-check | `review.alignment` → MATH_TO_FORMAL／必要的 SOURCE_TO_FORMAL 对齐 | 目标不匹配则退对应生产层；保留 MISALIGNED／PARTIAL 等结论 |

“论证审阅支持”（R1 的 SUPPORTED）、“形式证明检查通过”（R3 的 KERNEL_CHECKED）、“与原目标含义对齐”（R5 的 ALIGNED）是三项不同结果，分别记录。DELIVERED 仅表示本轮产物交齐。只比较 packet 与原目标而不定位实际生成代码，不能完成形式对齐。

早期声明检查可避免在错误的题目上耗费证明成本，但若之后声明、定义或环境有改动，先前结论必须按新版本重新检查。最终状态由所选标准规定的检查集合决定，不按固定“审了三次”决定。

## 2. 每条审阅意见必须可执行

复用 argument-review、challenge、challenge-disposition、alignment-assessment、frontier-item 与 Result，不创造第二套 review 业务类型。

每条问题至少说明：精确对象／步骤／声明、违反的要求、原文或代码依据、影响的目标，以及需要哪一层处理。业务 schema 无对应字段时，使用现有说明字段和诊断附件，不临时扩字段。不得要求生产者公开隐藏思考；需要的是可检查的数学理由和执行证据。

- Reviewer 提出问题，生产者响应并产生新修订；独立 Reviewer 决定异议如何处置，生产者不能自己关闭针对自己的异议。
- 所有未解决问题保留在新快照和相应处置中；删除有问题的步骤不能让它从历史中消失。
- 原正式 formal-check／alignment-assessment 目前不在 formalization.generate 的直接输入白名单。返工通过允许的 challenge／frontier-item 明确指出问题，必要原始错误日志作为固定附件；不得把完整业务检查记录藏进附件绕过白名单。
- FollowUp 仍为 agent、operation、input_refs、reason。缺少未来材料时只描述缺什么，保存后由调度程序选择实际产物创建 Task。

## 3. 反译输入隔离

首轮 backtranslate 的业务 input_refs 只允许 formal-environment；Task.acceptance 固定 DELIVERY，实际代码附件非空。不给 MathClaim、源文、Lamport 视图、declaration_map、packet、生成器诊断全文、预期答案或先前对齐意见。

必要定义通过固定的形式代码附件提供。代码注释、文件名或附加说明若泄漏原文答案，宿主应提供经过记录的中性输入版本；保留原始字节、转换规则、新附件身份与可见性记录，不静默修改数学声明。转换是否保持形式含义要另外核对，不能把删除注释就称为严格盲审。

模型先冻结自己的解释；隐藏的 packet_ref 仅在随后由宿主按可追踪的工作链装配。实际可见附件记录在 backtranslation.formal_artifacts；不得用隐藏包的逻辑归属冒充“反译者读过这个包”。对齐者随后读取源目标、反译和实际生成／检查记录，明确检查两端。

## 4. 修订后的失效范围

| 改动 | 需要重做 |
|---|---|
| 只修改无语义变化的 Lean 实现 | 新 attempt、机器检查；新字节的反译／对齐不能直接套用旧结论，是否可复用须有明确的版本化复用依据 |
| 修改 Lean 声明、定义或类型实例 | 声明反译、形式检查、对齐；若与 packet 不符先重新组包 |
| 修改 Lamport 步骤或实际依赖路线 | 新 plan／snapshot、受影响的论证审阅、新 packet，再检查受影响形式结果 |
| 新增前提、改变数学目标或范围 | 新命题／提取修订及必要 scope review；保留旧目标的失败或未完成处置 |
| 修改工具链、库锁或公理政策 | 新环境与新 packet、重新构建和相应检查；旧环境的通过不能迁移为新环境通过 |

审阅对象以精确引用和字节绑定；不得把旧批准覆盖成“针对最新版本”。没有真正实现证据复用规则时，不自行跳过重审。

## 5. 停止和预算

所有轮次使用 Task 与总体计划中的固定预算、尝试次数及无进展上限，子任务不能刷新额度。无新材料、无新证据、无减少缺口的重复尝试算无进展。

- BLOCKED：缺来源、冻结范围、可用依赖、形式环境或独立执行条件。
- FAILED：一次实际尝试失败；不能等同于数学命题为假。
- DEFERRED：预算或无进展上限到达，保留恢复位置。
- DELIVERED：本轮交付完整，仍可含负面或未定的审阅结果；不等于目标成功。

若独立审阅者不足，只阻塞相关证据门，候选生成可在授权范围内继续。换模型、换昵称或换进程不自动证明独立，生产参与者及真实可见输入须由宿主核对。

## 6. 本轮实现与规范审阅

本目录的 schema 和 check_interfaces.py 只检查草稿格式及明确的基础约束；不会运行模型、派单、查文献、展开完整 RecordSet、认证审阅者、解析 Lean 含义或生成独立 formal-check。真正运行系统仍需宿主装配、引用集合检查、受控构建和各证据门实现。

本轮采用“接口兼容审阅 → 规范与例子复审 → 机械正反例及 Reader 复核”来打磨文件。它们是开发审阅，不是一个论文案例的独立科学审阅。实际结果与未完成边界记录在 validation-report.json，不借本目录存在宣称生产系统已连通。
