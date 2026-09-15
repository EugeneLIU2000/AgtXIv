# 0.1.0 编排覆盖层与 v3/0.0.0 的兼容边界

状态：实验规范。0.1.0 是任务编排契约版本；基础业务契约仍为 v3/0.0.0。这里的兼容表示可以精确引用既有业务记录，不表示已经有可运行的迁移、生产调度器或科学准入系统。

## 1. 三种身份分别保留

| 对象 | 使用的身份 | 不允许的替换 |
|---|---|---|
| agents.json、Task、Result | contract_version = 0.1.0 | 不把它写入 v0.0 业务封套，或交给旧 RecordSet 当作业务记录 |
| 来源、主张、论证、审阅、发布等业务记录 | agtxiv.v3.<短名>/0.0.0 及原 record_id/revision/content_hash | 不批量替换成 /0.1.0，不重新封存成“同一个旧对象” |
| 基础契约与规则 | 精确 schema bundle、processing-profile、authority-policy 及所引用版本 | 不以目录名、最新 Git 分支或模型说明代替精确规则 |

agents.json 的 input_record_types/output_record_types 使用 [v0.0 catalog](../schema%20v0.0/catalog.json) 中的短名。例如 math-claim 对应 agtxiv.v3.math-claim/0.0.0；这种简写只用于白名单匹配，不改变实际引用。

本层不复制 v0.0 schema、不增加其字段、不重解释旧状态、不覆写来源字节。Task/Result 的编排格式检查与基础业务记录校验分别执行。

## 2. 最小校验边界

| 检查层 | 应检查的内容 | 不能推出的结论 |
|---|---|---|
| 编排格式 | 固定版本、已登记 agent/operation、有限能力、全部必填字段、非空 brief、目标为输入子集、附件引用一致、实际输入短类型及声明输出集合 | 运行已经发生、模型确实只看过所声明材料、科学证据足够 |
| 类型交付 | DELIVERED 覆盖全部 expected_record_types；所有业务 output_refs 的类型都在本任务 expected 集合，并且该集合属于 operation 白名单 | 某条评估为正面、必需成功义务已成功、依赖 EVIDENCE 可放行 |
| v0.0 记录及关联 | 封套、内容指纹、精确引用、必需附件、对应范围、历史及已有跨记录规则 | 来源科学主张已完整发现、全部科学含义正确、记录中的身份声明真实 |
| 目标级证据门控 | 指定目标/范围/标准、实际证据方法、条件、独立性、政策与适用冲突 | 超出该用途的结论、整篇论文为真；该层仍需运行时实现 |

除 review.backtranslate 外，各操作的输入白名单额外允许 authority-policy、processing-profile、agentization-plan 三种上下文；其余直接输入按 agents.json 白名单检查。review.backtranslate 不适用通用上下文许可，首轮业务输入仅允许 formal-environment，政策由 host 私有保管。input_record_types 是可接受集合，必需组合以 [AGENT-CONTRACTS.md](AGENT-CONTRACTS.md) 各操作为准。类型允许不授予读取权限。

Task 全部字段必填，包括非空简短指令 brief、target_refs 和 input_artifacts。target_refs 必须为 input_refs 的精确子集；相同背景输入下，由目标集合与 brief 明确实际审查对象和比较方向。input_artifacts 是固定 ArtifactRef 列表，execution.visible_artifact_refs 与其附件集合按 artifact_id、sha256、byte_size、media_type 比较必须完全相同。path_hint 只是显示定位提示，不参与身份比较或授权。这些字段记录字节身份和可见性，不授予文件路径访问，也不证明沙箱实际隔离成功。

数组在无相应项且不违背 operation 最低要求时可以为空。Reader/Planner 尚无业务记录时，以 brief 记录真实用户意图，input_refs/target_refs 可为空，不依赖未记录的 host 上下文。首次来源取得可用 source-request 作目标；尚未取得的远程字节属于后续 Result.artifacts，不倒填到原 Task.input_artifacts。

Task.acceptance 和 depends_on[].gate 均保持 DELIVERY/EVIDENCE 两值，不扩展成自由文本对象。acceptance=EVIDENCE 时，input_refs 须显式包含精确 authority-policy 与 processing-profile；缺失则不满足接口条件。有两种输入也不能代替实际目标级检查，Result.outcome=DELIVERED 不能作为 EVIDENCE 通过凭证。

review.backtranslate 是固定 DELIVERY 的首轮解释任务，不能改为 EVIDENCE 并向首轮添加政策或处理标准。后续独立 alignment 或其他任务先接收该解释，再按其自身目标和政策判断 EVIDENCE；反译交付本身不是科学认可。

expected_record_types 表示本任务必须交付的业务类型集合，不是“可能输出”的提示。额外记录输出同样必须在该集合中；业务内容无法完成时返回 BLOCKED/FAILED/DEFERRED 和已声明的部分输出，不伪造必需类型。新增类型需求通过后续任务或执行前明确的新任务版本解决。

Reader/Planner 的 output_record_types 为空；utility.persist 同样只交操作回执附件。旧业务记录中有 work-attempt 或 work-completion，不意味着可以把 Task/Result 直接改名后导入；映射必须以真实运行及原记录所需字段为依据。

## 3. 现有业务记录如何进入新分工

| v0.0 记录族 | 本层操作及边界 |
|---|---|
| source-request/source-acquisition/source-snapshot/source-transformation | 已固定请求由 utility.capture 执行；原始字节、取得失败和缺失边界保留。请求本身可由现有受控入口提供 |
| agentization-plan | utility.register-plan 将 scheduler 已接纳的固定计划登记为业务记录；planner.propose 仅提出建议 |
| source-span/paper-structure/inventory-discovery/scientific-claim | paper.extract 生产候选；scope-decision/frozen-scope 由 review.scope 在独立接受后生成 |
| definition/math-claim/claim-component-map/semantic-context | Paper 提取与解释；新增条件形成不同命题，不能覆盖原文 |
| derived-claim/argument-node/assumption-context/inference-step/proof-plan/argument-snapshot/counterexample | proof.expand 生产公开论证及有归属的修复/反例；review.argument 独立检查 |
| baseline-snapshot/dependency-binding | dependency.search 固定基准、提出具体依赖；绑定不等于认可复用 |
| relation-assessment/reuse-decision | review.reuse 独立判断端点关系及具体用途；条件与证据要求随目标保留 |
| formal-environment/formalization-packet/formalization-attempt | 环境由受控集成方按实际输入提供；utility.assemble-packet 组装固定包；formalization.generate 消费包并产生尝试 |
| formal-check/environment-check | utility.formal-check 依据独立实际运行产生证据；无运行则不能编造检查记录 |
| backtranslation/alignment-assessment | 反向解释先冻结；host 后置装配隐藏的 packet 归属；独立 review.alignment 检查各自对应边界 |
| argument-review/axis-assessment/challenge/challenge-disposition | Review 对精确对象和证据处置；生产者不能关闭自己的独立异议 |
| empirical-evidence/reproduction-record/evidence-protocol | 可作为 review.scientific 的证据输入；本最小层没有声称实现实验或计算复现生产服务 |
| contribution-delta/frontier-item | delta.compare 评估固定基准下的变化；不同生产/审阅任务仅输出预声明且符合各自权限的未解项 |
| release-manifest/release-audit/release-certificate | utility.export 组装清单，review.audit 独立审计，utility.certify 另行机械认证；不能由一个主体包办 |
| paper-release/archive-receipt | utility.export 在精确审计、认证及实际持久化前置条件具备后生成；普通 Git 导出没有这些业务含义 |
| admission-decision/knowledge-snapshot/ingestion-receipt | review.admission 仅给逐条决定；正式事务执行与后两类业务记录创建尚需另行实现的受控集成服务 |
| status-view/impact-analysis | utility.project 可生成只读六轴视图；当前潜在依赖分析只交附件，不冒充具备完整科学失效传播的 impact-analysis 生产者 |
| work-attempt/work-completion/obligation-disposition/event | 由真实运行和明确义务的集成适配形成；本文件不生成运行历史，utility.persist 仅保存已形成的记录 |
| authority-policy/processing-profile/revision-record/legacy-binding/event-checkpoint/query-receipt/evaluation-report/upstream-import | 复用已有精确输入或交通用候选存储；本目录不为每类记录新增一个生产角色，不赋予迁移、任命、签名或独立评估权限 |

不能形成满足基础业务契约的记录时，先保留 Result.open_items 和真实附件。它们不是对基础义务的自动处置；后续映射为 frontier-item/obligation-disposition 等时仍要满足各自目标、引用、身份和历史规则。

## 4. 形式接口与可见性兼容

proof.expand 至少需要 math-claim 与 frozen-scope；formalization.generate 至少需要 formalization-packet。因此形式包必须由更早的 utility.assemble-packet 调用生成并固定，不能由生成任务事后用其产物倒推或改写交接目标。

review.backtranslate 首轮业务输入仅允许 formal-environment，input_artifacts 必须非空，声明及必要定义只以固定形式代码字节进入。不得独立输入 definition、work-attempt 或通用 authority-policy/processing-profile/agentization-plan；政策由 host 私有保管。Task.acceptance 固定 DELIVERY，brief 只含解释实际代码的中性指令，不含预期结论。execution.visible_artifact_refs 与 Task.input_artifacts 按 artifact_id、sha256、byte_size、media_type 比较必须完全相同，path_hint 不参与身份比较或授权。不得另挂源文或答案日志；实际内容隔离仍需运行时证据。

v0.0 backtranslation 必需 packet_ref，而首轮不得看 formalization-packet。这不是删除基础字段：host 从已记录的 depends_on 工作链及上游精确产物私有保留逻辑绑定，在模型输出解释并冻结后装配该引用、实际可见输入和外部可见性材料。packet 不列入首轮 input_refs/target_refs；后者仍须是实际 input_refs 的子集。首轮只有 formal-environment 业务记录与固定代码附件，其他业务类型及通用上下文均不得直接可见。

FormalCheck、Backtranslation、Alignment 的封套合法，不证明它们来自实际独立运行。execution 自报、producer 字符串、JSON 校验通过或人为写入 source_blind 均不能补足该事实。受控 host 的材料缺失时，停止相应独立证据交付，不造默认身份。

业务记录的公共引用顺序继续遵守 v0.0：work-attempt 不引用尚未存在且将反过来引用自己的结果；必要关联通过后置 work-completion 完成。清单也不得包含尚未生成的证书身份。

## 5. SQLite、Git 与 Neo4j：一份记录，多种用途

现有 [V3 LocalStore](../src/agtxiv_v3/storage.py) 保存规范 JSON 和原始附件，提供本地候选事务、精确历史读取及临时候选头更新。它不是正式知识准入服务，也不只是可随时删除的索引。[本地机制说明](../docs/architecture/v3-local-mechanisms.md) 明确其查询为 PROVISIONAL。

旧 [database 原型](../database/README.md) 所说的“Git 文件为事实来源、SQLite 仅为索引”，不能直接当作现有 V3 候选持久化已经完成的迁移。目标安排是：

1. SQL 保存候选及后续集成的运行状态；当前 LocalStore 并未提供完整任务队列和调度状态机。候选尚未封存导出前，数据库不能作为可丢弃缓存。
2. 单一受控路径将指定记录、全部所需原始附件和精确规则导出并核对，最后固定该批次的封存清单。SQL 与 Git 之间的失败重试、完整性检查和状态适配仍需实现，不能假设跨介质存在一个原子事务。
3. Git 携带可审阅的封存记录及快照清单，Git 分支名或提交成功不定义科学状态。大附件可采用另行可取得的内容寻址对象，但必须有实际导出/取得途径；只有一个 hash 不能宣称快照已完整可携带。
4. Neo4j 只从指定快照重建图投影，标明来源快照和构建边界。图节点、边或缓存命中不得反向改写权威记录、批准复用或定义新的已封存头。

canonical/sealed 表示内容规范化、身份固定、字节可核对，不表示科学成立或正式准入。候选封存可以保留失败和冲突；正式发布、认证和知识准入分别需要现行政策与真实记录，不能因数据库写入而升级。

本层不建立 SQL、Git、Neo4j 三个可以互相覆盖的主库。唯一业务身份仍是不可变记录及其精确快照，载体和投影不得各自重新解释记录含义。

## 6. 明确未实现的部分

工作目录和最小编排格式检查不构成生产运行能力。受控运行身份、模型输入隔离、目标级 EVIDENCE 门控、Lean 声明实际执行、实验/计算复现、SQL 运行状态与 Git 封存适配、生产持久性、正式认证和准入事务，均需要单独的实现与运行证据。

utility.register-plan 和 utility.assemble-packet 明确业务记录的组装归属。是否存在可调用实现、是否符合既定政策、是否真的执行，分别由可复查实现、实际运行材料和独立核查证明。
