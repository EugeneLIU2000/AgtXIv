# Autoformalization Agent：从结构化证明到 Lean 4

agent-spec-version: 1.0
applies-to-business-contract: v3/0.0.0
applies-to-orchestration-overlay: 0.1.0
status: 接口规范、离线契约检查与教学案例；不是已上线的自动形式化系统。本次为 1.0 内部重排（2026-09-15），草稿 schema 与业务记录接口未变；实现边界见 [validation-report.json](validation-report.json)。

本目录承接 Paper Agent 的数学目标，分两步：**先把证明写清楚**（`proof.expand`），**再把证明转成 Lean 4**（`formalization.generate`）。它不是可以同时生产、审阅和批准自己的全能 agent。本文件只规定不变量、流水线与边界；运行接口见 [INTERFACE.md](INTERFACE.md)，证明与代码细则见 [LAMPORT.md](LAMPORT.md) 与 [LEAN4.md](LEAN4.md)，本流水线的审阅轮次见 [REVIEW.md](REVIEW.md)，通用审阅契约见 [Review Agent](<../Review Agent/AGENT.md>)，Lean 环境与可信库见 [ENVIRONMENT.md](ENVIRONMENT.md) 与 [registry/](registry/README.md)。

## 1. 不变量 I1–I6

以下六条不随版本演进，是整套证据链的地基；放宽其中任何一条都等于换掉这套规范。

| 编号 | 不变量 | 落地要求 |
|---|---|---|
| I1 | **生产、审阅、批准分离** | 生产者不得审阅或批准自己的产物；换模型名、换昵称或换进程不构成独立。审批来自其它操作白名单，不来自提示词约定。 |
| I2 | **宿主拥有执行事实** | 编号、修订、时间、哈希、附件引用与运行记录由宿主依据真实执行装配；模型草稿不含执行回执，也不得编造 work-attempt、formalization-attempt 或 formal-check。 |
| I3 | **编译通过不是验收** | 不合成笼统的 `verified`；Lamport 写完、Lean 生成、检查器接受、含义对齐分别记账。禁止 `sorry`、把目标声明为公理、把定理当作自己的假设；允许的公理与可信机制只来自固定环境政策。 |
| I4 | **目标不漂移** | 始终定位同一个精确 MathClaim。增加适用假设、削弱结论、改变定义域或量词，一律作为新命题／新范围／新包处理；旧目标、旧失败与旧异议继续保留。 |
| I5 | **理由与来源可核对** | 每个推理给出全部共同前提、结论、规则与公开理由；来源、上下文重建、修复与替代路线分别标注；缺口不能靠删步骤、改名或只展示通过子集来消除。 |
| I6 | **局部假设不越界** | 局部假设只在引入它的证明范围内使用；向外推出蕴含、反证、分情况或归纳结论时必须显式解除，并保留作用范围。 |

## 2. 流水线索引

**本流水线的**轮次编号以 [REVIEW.md](REVIEW.md) 为唯一来源，本节只给顺序与分工。阅读视图（lamport-view）是派生附件，不是生产步骤。

| 阶段 | 操作／角色 | 产物 | 检查门 | 细则 |
|---|---|---|---|---|
| 输入准备 | 宿主 | Proof：MathClaim + frozen-scope；Lean：formalization-packet | 输入不足先保存材料与缺口 | [INTERFACE.md](INTERFACE.md) |
| R0 结构 | 宿主机械检查 | 分层校验报告 | 格式、引用、共同前提、作用范围、闭包 | [REVIEW.md](REVIEW.md) |
| R1 论证 | `proof.expand` → `review.argument`；必要时 `review.alignment` | proof-draft、argument-review | 推理与原文忠实 | [LAMPORT.md](LAMPORT.md)、REVIEW |
| 组包 | `utility.assemble-packet` | formalization-packet | 固定目标、所选路线、论证快照、环境 | INTERFACE |
| R2 声明与生成 | `formalization.generate` | 完整定理声明 + lean-draft | 陈述与原文一致，且过**可复用性关** | [LEAN4.md](LEAN4.md)、REVIEW |
| R3 形式检查 | `utility.formal-check` | formal-check + 构建产物 | 目标声明、公理依赖、构建产物 | [ENVIRONMENT.md](ENVIRONMENT.md)、REVIEW |
| R3b 精简迭代 | 生成者修订 → 重跑 `utility.formal-check` | 最终代码字节 | 只改证明体；收敛即停、上限 2 轮；动到陈述即按新定理回 R2 | ENVIRONMENT、REVIEW |
| R4 盲反译 | `review.backtranslate` | backtranslation | 输入隔离：不给原文与预期答案 | REVIEW、[Review Agent INTERFACE](<../Review Agent/INTERFACE.md>) |
| R5 独立对齐 | `review.alignment` | MATH_TO_FORMAL 等对齐结论 | 形式代码含义与源目标一致 | REVIEW |
| 完成 | 宿主 | Result + 分层状态记录 | `DELIVERED` 只表示产物交齐 | AGENT §5、[AGENT-CONTRACTS.md](../AGENT-CONTRACTS.md) §2.1 |

这些是不同检查边界，不要求每篇论文固定调用同样次数；没有独立执行条件时明确报告缺失，不换个模型名字假装独立审阅。

## 3. 术语

frozen-scope = 本轮固定的证明范围；packet = 形式化交接包（formalization-packet）；snapshot = 本轮论证的完整版本；frontier = 新发现、待处理事项；宿主 = 负责保存与调度的程序。保留英文只为与机器字段对应。

## 4. 输入与开始前

- 每次调用完整加载本文件及 INTERFACE、LAMPORT、LEAN4、REVIEW、ENVIRONMENT 与当前阶段的草稿 schema；REVIEW 只用于定位本流水线的轮次，`review.*` 调用改为加载 [Review Agent](<../Review Agent/AGENT.md>) 模块。只提供路径不算模型已经读取。
- 只使用当次 Task 提供的记录与字节。需要新记录时先保存，再创建新 Task；不猜未来引用，不隐式展开未授权输入。
- 没有 frozen-scope 时不能启动正式 `proof.expand`；这不要求 Paper 停止候选提取。
- 统一使用现有 Task → Result；不新增 `autoformalization.run` 操作，也不合并原有权限。Review、Dependency 和 Utility 按各自操作参与；逐项输入白名单与草稿形状见 INTERFACE。

## 5. 完成与边界

- `Result.outcome=DELIVERED` 只表示本轮约定产物交齐；Lamport 写完、Lean 文件生成、检查器接受、原文含义对齐分别记录，不能合成一个笼统的 `verified`。
- 正式报告不能依赖 `sorry`、把目标声明为公理，或把定理当作自己的假设；允许的公理与额外可信机制必须来自固定环境政策（见 ENVIRONMENT）。
- 已实现：草稿 schema、只读接口检查、教学案例；未实现：自动组包、调度、独立审阅、隔离构建与独立 formal-check 回执。完整清单见 [validation-report.json](validation-report.json)。
- 正反例见 [CONFORMANCE.md](CONFORMANCE.md)；1.0 原文见 [history/AGENT-1.0.md](history/AGENT-1.0.md)。Paper Agent 及其规范本轮不修改。
