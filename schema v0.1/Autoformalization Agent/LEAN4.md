# 接口 B：固定 Lamport 论证 → Lean 4

本文件是规范性附件。Lean 接口消费的不是任意一段证明文字，而是已固定的数学目标、证明路线、论证快照与环境。Lamport 阅读视图辅助理解，不能替代这些记录。

## 1. 输入：由已有组包操作固定

`utility.assemble-packet` 生成 formalization-packet，`formalization.generate` 只消费它。包里的字段继续使用原 schema：

| 字段 | 固定什么 |
|---|---|
| math_ref、scope_ref | 数学题目与本轮义务范围 |
| argument_ref、proof_plan_ref | 完整论证快照与实际选择的一条路线 |
| source_claim_refs、semantic_refs | 作者主张与需保留的科学含义 |
| environment_ref | Lean 工具链、包锁、构建输入、允许公理及可信机制、命令和网络边界 |
| expected_declarations | 执行前确定的完整目标声明名，不从生成后的代码倒推 |
| open_obligation_ids、mode | 未证义务及 EXPLORATORY／RELEASE_CANDIDATE 工作目的 |

模型需要的节点、推理、定义、假设范围逐条列入 Task.input_refs。为此 formalization 的输入白名单增加既有 argument-node、inference-step；不增加新业务类型或代码执行权限。节点引用原文位置不自动授予读取原文的权限，source-span 未新增为本操作直接输入。

本草稿接口每次只处理一个目标包：Task.target_refs 中恰有一个 formalization-packet，lean-draft.packet_ref 必须与它完全相同。输入中即使可见其他包，也不能替换被指定的目标。

类型允许不等于对象任意：输入和声明对应表中的节点、推理必须属于当前包的所选路线；实际可见输入必须留痕。不得把另一条路线或另一修订的节点混进来。

## 2. 模型返回的代码草稿

lean-draft.schema.json 固定以下字段：

| 字段 | 含义 |
|---|---|
| draft_version | 本内部草稿版本，当前 1.0 |
| packet_ref | 本次使用的精确交接包，不允许替换 |
| files | 模型生成的相对文件路径与完整文本内容 |
| declaration_map | 目标声明、辅助声明和局部步骤到节点／推理的对应 |
| records | 本 Task 预声明时可返回的 frontier-item 草稿，不包括自造的执行记录 |
| open_items、follow_up_requests | 当前缺口与按现有四字段格式提出的后续工作 |

files 只允许运行目录内的 `.lean` 文件：禁止绝对路径、`..`、反斜杠、大小写碰撞和路径重复；宿主写入时还须防止符号链接、拒绝覆盖既有不同字节。已有工具链、lake 配置与包锁不能由生成器修改，环境变化应请求新环境与新 packet。此处路径检查不是执行沙箱。

declaration_map 每项为 `declaration`、`role`、`code_path`、`local_name`、`node_ref`、`inference_ref`：

- TARGET 指包中一个完整目标声明，local_name 为 null；完整代码交付时，每个 expected_declaration 恰有一个 TARGET 对应。主目标节点与所选 plan.conclusion_ref 一致。
- STEP 指该声明内部的 `intro`、`have`、`calc` 或子目标；local_name 给出实际局部名，确无名字时为 null。相同声明可有多条 STEP，不要求一自然语言句子对应一行代码。
- HELPER 指本轮增加的辅助声明，不能冒充已经存在的历史定理。需要新数学引理／新路线时回到 Proof，不能在形式代码中悄悄引入未经论证的前提。
- node_ref／inference_ref 必须定位已登记的所选论证。假设引入或未完成步骤可无 inference_ref；这不把它标为已证明。
- 程序必须进一步检查代码中的声明、局部绑定及实际含义。模型填写对应表，不证明对应是真的；当前草稿检查器不解析 Lean 声明，也不解析整个记录集。

若输入不足，可以返回空 files、空对应表和明确缺口；不得造空文件或声明来满足数量。若只产出部分代码（例如只有辅助声明），可以尚无 TARGET，但 open_items 必须明确解释未完成目标；已有声明仍须如实对应，不能伪填 TARGET。目标齐全也不自动说明证明完成。宿主在装配时记录 PARTIAL，不能把这个例外交付当作完整目标通过。草稿中没有“检查通过”字段。

## 3. 从 Lamport 到 Lean 的保真规则

| Lamport 内容 | Lean 中如何保留 | 检查重点 |
|---|---|---|
| 数学对象与量词 | 完整声明的参数、类型、隐式参数与依赖关系 | 对象类型、量词顺序及范围没有变 |
| 全局适用前提 | 目标原本要求的前提与参数 | 没增加未批准前提，也没漏掉原条件 |
| 局部假设 | `intro`／局部分支／子证明绑定 | 只在局部使用，最终定理不是多带了一个假设 |
| 中间断言 | `have`、辅助 lemma、`calc` 或具名子证明 | 陈述对应指定节点，不只依靠注释说对应 |
| 共同前提推理 | 显式应用引理或在明确上下文执行 tactic | 没把共同前提拆成独立证明，没有漏前提 |
| QED | 返回完整目标的证明项 | 证明的是预期声明，不是无关的 True 或弱化版本 |

保留标准化说明：例如实数／复数、矩阵维度、纯态／混态、有限性、归一化、对数底、近似范围、零点和极限。Lean 能接受一个声明，不表示这些科学选择与论文一致。

定义复用必须绑定实际声明与版本、必要条件及形式环境兼容性；名字相同、搜索到相似 lemma 或 import 成功都不等于可以承接目标。

允许小范围 tactic 调整和实现细节变化。若自动化实际上换用了另一证明路线、增加承重引理或依赖，与原 Lamport 路线不一致，需回到 Proof 更新 plan／snapshot 并重新组包，不能只改对应表掩盖变化。

## 4. 真实运行记录由谁生成

模型输出原始代码；宿主保存实际字节并生成 ArtifactRef。宿主先封存真实 work-attempt，再装配 formalization-attempt，后者继续使用：packet_ref、attempt_ref、outcome、artifacts、diagnostics。

formalization-attempt.outcome 只有 GENERATED／PARTIAL／FAILED，表示文件生成结果，不是 Lean 已证明。没有真实执行归属时只保存诊断，不造 work-attempt。主模型不得填写独立 formal-check 的日志、退出码、审阅身份或 KERNEL_CHECKED。

## 5. Lean 检查的最低要求

独立检查服务在固定环境执行获准命令，禁用未授权网络与凭据。Lean 的 tactic／元程序可能执行操作，模型代码应视为不可信输入，不在高权限宿主直接构建。隔离、资源限制和真实日志由运行服务实现，本目录未实现该沙箱。

至少核对：

1. 固定 Lean 工具链与依赖锁，实际构建包含 expected_declarations 的目标文件；不是只检查了另一个空模块。
2. 每个完整目标声明的实际 elaborated type，与可信目标比较对象、量词、假设和结论；检查名称遮蔽、局部实例、记号或新增定义是否改变含义。
3. 目标及其依赖中的占位符、额外公理与额外可信机制；按环境白名单检查传递依赖。不能只搜索文本中是否有 `sorry`。
4. 保存真实命令、工具版本、代码／包锁哈希、构建日志、声明与公理审计结果。机械结果不替代反译与对齐。

`#print axioms` 可用于查看声明的传递公理依赖；普通编译成功不排除依赖中的 sorry。正式成功不允许 sorryAx 或把原目标直接声明成公理；标准公理是否允许取决于固定环境，不一律要求“零公理”。高风险或所选政策要求时，还需独立的构建产物重检／可信目标比较工具，不能把其未运行记为通过。依据见 [Lean 官方验证指南](https://lean-lang.org/doc/reference/latest/ValidatingProofs/) 与 [公理说明](https://lean-lang.org/doc/reference/latest/Axioms/)。

## 6. 接口交付与实现边界

每轮保留 task.json、原始 draft.json、已装配 records.json、真实 result.json、生成代码、对应表和分层 validation.json；没有真实运行回执时不制造 result。Lamport 视图和声明对应表属于附件，不混入业务 records。

当前提供草稿 schema、只读基础检查和教学案例。完整共享装配器、目标声明解析／比较、自动代码生成服务、隔离构建与独立检查回执仍待接入。用一个教学例子运行本地 Lean，不等于这些服务已实现。
