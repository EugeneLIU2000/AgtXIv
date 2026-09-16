# 宿主参考版：固定程序调度，Pydantic AI 调用专业 Agent

日期：2026-09-15。状态：**参考代码已编写，仅静态阅读；未安装、导入、运行或测试。不是可直接启动的完整服务。**

最重要的分工：**宿主决定“这张工作单能不能做、用什么输入、怎样保存”；专业 Agent 只回答“这张工作单要求我产出什么”。** 宿主不是另一个有权自行调用所有工具的模型。

本目录把这个分工写成 Python 控制流，并给出真实的 Pydantic AI 调用适配。数据库、身份认证、独立审阅、固定程序执行仍需接入下列强制接口；没有默认放行器或伪造成功的存储实现。原业务 schema、Agent 草稿格式及旧 handoff 不变。

## 1. 先读哪三个文件

| 入口 | 先理解什么 | 当前交付 |
|---|---|---|
| [host.py](agtxiv_host/host.py) | 一张 Task 如何经过检查、模型、保存和交付 | 单次模型尝试的确定性控制流 |
| [ports.py](agtxiv_host/ports.py) | 数据库、权限与证据服务必须承诺什么 | 必须实现的接口；不是现成后端 |
| [pydantic_adapter.py](agtxiv_host/pydantic_adapter.py) | 怎样按指定草稿格式调用模型并保留失败信息 | SDK 调用代码；尚未执行 |
| [inputs.py](agtxiv_host/inputs.py) | 只读取明确授权的精确版本，冻结模型实际输入 | 文本输入装配与清单代码 |
| [contracts.py](agtxiv_host/contracts.py) | 怎样沿用已有规范与检查器 | 15 个模型操作的映射、规范指纹及 schema 传输适配 |
| [policy.py](agtxiv_host/policy.py) | 哪些格式合格的草稿仍不能交付 | Planner／Delta 补充关卡、产物类型检查及工作去重键 |
| [types.py](agtxiv_host/types.py) | 宿主内部怎样传递任务、租约和调用结果 | 严格宿主类型，不重新生成业务 schema |

本目录没有后台循环、HTTP 服务、CLI 或默认模型。阅读入口是 `Host.model_once(assignment)`；调用前必须由应用提供 `Catalog`、`ExactReader`、`EvidenceGate`、`RuntimePort` 和获准的 `PydanticAdapter`。Python 导入路径需包含仓库 `src/` 与本目录；当前不是独立发布包。

## 2. 一张工作单怎样走完参考控制流

1. **接纳已固定的任务。** 上游先把实际 Task 字节与受控 `WorkBinding` 交来。宿主核对哈希、原 Task 契约、操作映射及模型配置绑定；不让模型自行创造执行身份。
2. **检查前置条件。** `EvidenceGate.before_attempt` 核对真实前置交付、所需证据、用途、执行资格与预算。缺条件记录 WAITING，此时没有模型调用，也不编造 attempt。
3. **读取并冻结允许输入。** `ExactReader` 只提供 Task 明列的精确版本；装配器复核记录与附件字节。不读 latest、不递归展开引用、不在线查询图。把规范、来源及转换方式记入输入清单。
4. **检查实际可见内容。** `before_inputs` 必须审查最终提示内容，包括 brief、记录外壳和附件。输入类型白名单不等于盲审隔离。通过后由 `RuntimePort.claim` 原子预留父计划预算、保存清单并取得带代次的租约。
5. **发起一次 SDK 模型请求。** Pydantic AI 使用对应 Agent 规范与草稿 schema；不注入数据库客户端、shell、检索工具或跨任务聊天历史。SDK 自动重试关闭。
6. **先保留原草稿，再判断交付。** 合法、不合法、取消和超时均保留可取得的 SDK 消息、检查报告与用量观察。草稿经过原检查器后，还需用途、目标覆盖与产物检查；缺项可停在 DRAFT_STAGED，不丢弃已有工作。
7. **原子交付。** `before_delivery` 再核对用途与证据。`deliver_atomic` 必须装配完整业务记录，检查完整 RecordSet／字节闭包，然后把业务、真实 Result、事件及 outbox 消息在同一事务内提交。返回的是真实已提交 Result，不是宿主臆造回执。
8. **下轮另外派单。** follow-up/search 请求仍只是建议。任务接纳模块按已批准模板解析，取得并保存新来源，再固定下一张 Task。参考 `model_once` 不自动启动子任务。

步骤 2、4、7 中的 ALLOW 必须对应可回源、绑定版本的真实关卡回执。代码拒绝空回执列表；真正的身份认证和过期判断必须由接口实现，不能通过随手填写几个字符串完成。

## 3. Pydantic AI 在这里究竟负责什么

本参考采用其模型调用、结构化输出与消息/用量接口，不把整个研究调度写成一个 SDK Agent。[官方概览](https://pydantic.dev/docs/ai/overview/)

既有 JSON Schema 仍是真源。`StructuredDict` 用于向模型声明输出形状；它本身不替代完整 JSON Schema 约束验证，因此 `output_validator` 仍调用原 Agent 检查器。对 provider 的 schema 展开只服务传输，不能用展开版代替原契约或改变 `schema_bundle_hash`。[结构化输出文档](https://pydantic.dev/docs/ai/core-concepts/output/)

`deps` 仅传递可见上下文的哈希，不传数据库、私有 packet、身份服务或凭证。依赖注入是组织输入的方法，不是操作系统沙箱；真正隔离由宿主及部署边界负责。[依赖注入文档](https://pydantic.dev/docs/ai/core-concepts/dependencies/)

`capture_run_messages` 和消息序列化用于留存 SDK 所见的请求/响应。它们不是原始 HTTP 报文，也不证明调用者身份或审阅独立。日志内容可能包含论文与代码，存储适配必须控制访问，不能默认发往公共追踪服务。[Agent API](https://pydantic.dev/docs/ai/api/pydantic-ai/agent/)、[消息 API](https://pydantic.dev/docs/ai/api/pydantic-ai/messages/)

这里没有接 Temporal、DBOS 等持久执行后端。Pydantic AI 提供相关集成，但安装 SDK 不会自动产生本项目的事务、租约或恢复能力；这些仍由 `RuntimePort` 承担。[持久执行文档](https://pydantic.dev/docs/ai/capabilities/durable_execution/overview/)

## 4. 哪些操作已有适配，哪些还不能正式交付

| 操作组 | 参考代码覆盖 | 必须保留的限制 |
|---|---|---|
| Paper / Proof / Dependency | 对应规范、草稿 schema、原检查器和模型调用路径 | 不等于真实语义生产已验收；输入登记与存储接口须先接通 |
| Planner / Delta / Reader | 同上，另有 Planner / Delta 交付关卡 | 建议不自动派单；比较需覆盖实际目标；解释不生成科学证据 |
| Review 的 8 种操作 | 原检查器映射与模型草稿调用 | 独立身份、目标级证据与合法装配须由真实服务支持 |
| `review.backtranslate` | 可生成、检查并暂存解释草稿 | 通用交付路径明确停止，待实现“先冻结解释、再私有绑定 packet” |
| `formalization.generate` | Lean 草稿生成与原静态检查入口 | formalization-attempt 需宿主专用装配；没有真实 Lean 执行或证明成立声明 |
| Utility 的 8 种操作 | 单独的 `ProgramPort` 接口 | 不交给模型；固定程序路由、request/receipt 检查接入及实际执行尚未实现 |

共 15 个模型操作映射，不等于 15 个已运行的服务。AF 的 `lamport-view` 是辅助产物接口，不被新增成一个调度操作。原检查器报告里的 `unchecked` / 未检查层原样保留。

## 5. 任务身份：不再只比较输入集合

`Assignment` 保存原 Task 字节和原字节哈希。额外的 `WorkBinding` 属于**宿主内部接纳信息**：父计划、模板及其内容哈希、用途、政策、模型配置、实际规范/代码指纹。它不偷偷改变旧 FollowUp 草稿接口。

模型提出同样输入、不同目的的建议时，宿主只能按批准模板明确解释；不能从一段 reason 自动选择证明路线或授予权限。旧 Planner 草稿表示仍有歧义，G-05 没有因此彻底解决。

`dispatch_key` 将这些绑定连同真实 brief 哈希、精确目标/输入、附件身份、前置门、权限、回避名单、限额和交付要求交给运行库作为保守去重索引。相同 task_id 仍必须原字节完全相同。去重命中不能继承过期批准；跨模型、跨用途的科学复用不是这个函数的工作。

## 6. 保存和恢复：数据库实现不能省略什么

`RuntimePort` 是最重要的未接通部分。需要与现有候选库协调事务所有权；不能先调用会自行提交的 `LocalStore.ingest`，再另开一次事务登记 Result/outbox，随后声称原子保存。

每次尝试必须能找回：Task 原字节、接纳绑定、输入清单、真实身份/关卡回执、租约与代次、预留预算、SDK 消息、原草稿、检查报告、实际费用或未知费用、装配映射、最终 Result，以及待处理派生消息。附件可先固定为不可变内容对象，数据库事务只提交其身份与成员关系；未引用对象另按明确保留政策回收。

| 中断位置 | 宿主应如何继续 |
|---|---|
| 尚未领取、缺少来源或资格 | WAITING；不制造已执行记录 |
| 请求已发出但响应/费用不确定 | 保留该 attempt 的不确定状态与预算，先对账，不盲目重新调用 |
| 草稿已保存，装配条件不足 | DRAFT_STAGED；读取原草稿继续装配，不再次支付模型生成成本 |
| SQL 提交结果不确定 | COMMIT_UNKNOWN；按 task/attempt 查实际提交，不写 FAILED 覆盖可能成功的事务 |
| 旧 worker 在租约换代后返回 | 可按专用诊断通道保留，不得更新当前工作状态 |
| 已提交，但图/Git 失败 | 单独重试派生消息，不重跑科学任务 |

DRAFT_STAGED / COMMIT_UNKNOWN 是参考宿主返回状态，不是对现有 `Result.outcome` 或旧 SQL CHECK 枚举的静默扩展；持久化适配需显式映射或版本化迁移。`IntegrationRequired` 在提交接口中只允许表示“尚未发生副作用”；提交中断必须进入对账分支。

## 7. 费用和递归怎样收住

一次持久化尝试最多发起一次 SDK 模型请求；修订草稿另建 attempt，引用原草稿与检查报告，并再次占用同一父计划预算。子任务、图查询、来源取得及失败不能重置父预算或无进展计数。

SDK 请求次数限制不等于供应商 HTTP 请求次数；供应商重试策略必须显式配置并计入受控模型配置。Token 用量也不等于实际费用，响应后的 token 检查不能保证事前美元硬上限。参考代码把未知费用留为 null，由账本保留预留额度并对账。[用量接口](https://pydantic.dev/docs/ai/api/pydantic-ai/usage/)

这里没有“无限递归直到成功”的循环。后续调度服务需要基于已提交状态、固定模板和父预算逐轮展开，共同上游共享实际获取/提取产物，各个复用用途仍分别审阅。取消、累计尝试和无进展上限必须在真实领取事务中检查；本目录尚未提供该队列实现。

## 8. Neo4j 与 Git 放在哪里

沿用 [GRAPH-INTERFACE](../GRAPH-INTERFACE.md) 与 [STORAGE](../STORAGE.md)：SQL 保存候选和任务；经验证的不可变本地封存批次可分别交给图投影与 Git 归档。Neo4j 不在线不阻止已有精确引用上的合法工作。

`GraphPort` 只允许固定查询，发生在两个模型任务之间；结果必须回源核验与授权后才能成为下一 Task 输入。`ArchivePort` 只发布既定封存字节，远端读回之后才记发布成功。两个端口本轮只有接口，没有导入器、查询后端、发布器或自动派生消费者。

## 9. 参考实现明确拒绝的情况

- 输入超限、二进制 PDF/图片、非 UTF-8 文本：不静默截断或遗漏。先由独立获取/转换流程产生有来源的新文本附件。
- schema 存在不能安全展开的动态/循环引用，或 provider 不支持其复杂度：报告适配缺口，不删约束迎合 provider。
- SDK 只能给出解析后的工具参数 dict：保留消息，但不把重新编码的 JSON 冒称模型原参数。当前严格路径要求一个 `submit_draft` 的原 JSON 参数字符串，用于重复键与原草稿检查。
- 盲反译 brief、记录外壳或附件泄露原命题，或执行者资格不明：权限门必须阻止发送，不只检查顶层引用类型。
- 规范文件在尝试期间改变：拒绝按新规范解释旧任务；固定新版本并重启对应运行环境，不能自动追随修改。

这些是代码/端口的设计边界，**尚无本轮执行证据证明全部成立**。

## 10. 依赖选择与完成边界

[pyproject.toml](pyproject.toml) 单独选择 Python 3.12、`pydantic-ai-slim==2.43.0`、`pydantic==2.13.5`，并列出已有检查器所需的 JSON Schema 依赖。版本来自本轮查看的 [Pydantic AI 发布页](https://pypi.org/project/pydantic-ai-slim/) 与 [Pydantic 发布页](https://pypi.org/project/pydantic/)，**没有解析依赖、生成锁文件或确认可安装性**。没有改仓库主环境，也没有选择供应商、配置密钥或安装 provider extra。[安装说明](https://pydantic.dev/docs/ai/overview/install/)

既有测试复核结论与本目录所有待测项统一见 [PENDING_TESTS §8–9](../PENDING_TESTS.md)。旧 runner 的 21 步通过不覆盖本目录；不能据此宣称全自动论文处理、持久恢复、独立审阅或 Neo4j 集成已运行。

**下一项实现优先级：`RuntimePort` 的单任务领取、草稿持久化及业务/Result/outbox 同事务适配，同时接入真实 `EvidenceGate`。** 在这些必要接口补齐之前，不增加新的“宿主 Agent”，也不把一个演示内存库当作生产底座。
