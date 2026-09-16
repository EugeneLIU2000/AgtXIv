# AgtXIv V3 schema v0.0：完整中文契约说明

**状态：实验契约 0.0.0，对应 V3 架构。** `schema v0.0` 是用户指定目录，不是旧版 V0 项目。所有 JSON Schema 的字段、枚举、标题和说明均为英文；本文件逐项给出相同对象和字段的中文解释。[英文完整说明](SCHEMA.md)。

先用一个例子理解：原文声称“对所有状态成立”，后来只能证明“对纯态成立”。系统保留原始主张，另建带纯态条件的新命题；论证工作区解释条件从何而来，数学交接单固定本次目标，Lean 证据只支持它实际证明的命题。物理适用性和经验支持继续独立判断。下一篇论文只有在满足相应条件及证据标准时才可复用。

因此主线是：精确论文 → 原文主张与科学语义 → 可修订论证及固定数学交接单 → 按标准选择形式核查 → 六轴独立评估 → 有基准的贡献与特定用途复用 → 独立论文审计和发布 → 逐条知识入库 → 只读查询及局部复核。

**schema 通过只表示数据形状合规。** 字节与引用是否匹配、固定范围有无遗漏、假设是否解除、审阅身份是否真实独立、形式化是否忠实、实验是否执行、冲突是否保留、入库是否原子完成，仍需跨记录校验及真实证据。完成报告应分别写“契约覆盖”“机制已验收”“科学或运行验收”，不能用人工样例替代实际科学判断。

## 通用封套（每条记录共有的身份信息）

所有记录都使用封闭字段集合，不接受未知字段或类型；扩展须发新版 schema。`record_id` 标识同一对象的修订历史，`revision` 固定其中一版，`content_hash` 绑定除其自身之外的完整记录。沿用的规范化方式为 NFC/LF（统一字符表示和换行方式）、只允许安全范围整数、拒绝重复键并排序对象键；科学小数以附单位和解释的精确字符串表达。原始来源字节不做文本规范化再算哈希。

记录类型从离线包清单选择精确 schema，`schema_bundle_hash` 绑定清单，`policy_ref` 引用精确权限政策（政策自举记录例外）。解析 schema 不触网。所有输入和载荷引用必须从明确提供的不可变记录集合解析，不能用同名对象、最新版本或路径代替。

`data_class` 区分 SYNTHETIC 人工样例、RESEARCH 研究材料、OBSERVED 实际取得的输入/运行记录；实测不等于科学正确。身份字段在受信任运行上下文核实前只是声明。本地角色分离不等于机构级独立。

## 六个独立问题

1. 来源忠实性：表示是否与精确原文断言一致。
2. 数学正确性：精确结论是否由显式数学前提推出。
3. 形式对齐：形式声明是否保留预期命题。
4. 科学适用性：对象、模型、近似与可观测量是否对应目标系统。
5. 经验支持：哪些观测支持或反对科学断言。
6. 计算复现性：承重计算能否按指定条件重做。

是否适用、评估结果、执行处置分别记录。程序失败不是数学反例；未做检查不是不适用。形式声明获证，仍需独立对齐才能支持原主张。互相冲突的评估单独保留。

## 记录依赖顺序

来源快照 → 原文跨度/论文结构 → 科学主张/科学语义/数学交接单 → 论证节点、范围与推理 → 完整论证快照 → 审阅和形式交接 → 证据与评估 → 有基准的关系、贡献、复用 → 发布候选清单 → 审计 → 认证 → 发布 → 准入决定 → 新知识快照 → 入库回执。

比较基准可以引用旧知识快照。新知识快照只引用已经产生的准入决定；准入决定绑定旧快照，不绑定尚不存在的新快照，因此不产生循环哈希。后来的异议、评估修订和影响分析追加新记录，不改写目标。

## 公共值结构


### RecordRef

精确不可变记录引用，不允许选择最新版本。

| 字段 | 类型 / 值 | 必填 | 含义 |
|---|---|---|---|
| `record_type` | `agtxiv.v3.processing-profile/0.0.0` / `agtxiv.v3.authority-policy/0.0.0` / `agtxiv.v3.source-snapshot/0.0.0` / `agtxiv.v3.source-span/0.0.0` / `agtxiv.v3.source-transformation/0.0.0` / `agtxiv.v3.paper-structure/0.0.0` / `agtxiv.v3.agentization-plan/0.0.0` / `agtxiv.v3.inventory-discovery/0.0.0` / `agtxiv.v3.scope-decision/0.0.0` / `agtxiv.v3.frozen-scope/0.0.0` / `agtxiv.v3.obligation-disposition/0.0.0` / `agtxiv.v3.scientific-claim/0.0.0` / `agtxiv.v3.derived-claim/0.0.0` / `agtxiv.v3.claim-component-map/0.0.0` / `agtxiv.v3.semantic-context/0.0.0` / `agtxiv.v3.definition/0.0.0` / `agtxiv.v3.math-claim/0.0.0` / `agtxiv.v3.assumption-context/0.0.0` / `agtxiv.v3.argument-node/0.0.0` / `agtxiv.v3.inference-step/0.0.0` / `agtxiv.v3.proof-plan/0.0.0` / `agtxiv.v3.dependency-binding/0.0.0` / `agtxiv.v3.challenge/0.0.0` / `agtxiv.v3.challenge-disposition/0.0.0` / `agtxiv.v3.argument-snapshot/0.0.0` / `agtxiv.v3.argument-review/0.0.0` / `agtxiv.v3.upstream-import/0.0.0` / `agtxiv.v3.work-attempt/0.0.0` / `agtxiv.v3.formal-environment/0.0.0` / `agtxiv.v3.formalization-packet/0.0.0` / `agtxiv.v3.formalization-attempt/0.0.0` / `agtxiv.v3.formal-check/0.0.0` / `agtxiv.v3.backtranslation/0.0.0` / `agtxiv.v3.alignment-assessment/0.0.0` / `agtxiv.v3.empirical-evidence/0.0.0` / `agtxiv.v3.reproduction-record/0.0.0` / `agtxiv.v3.axis-assessment/0.0.0` / `agtxiv.v3.status-view/0.0.0` / `agtxiv.v3.baseline-snapshot/0.0.0` / `agtxiv.v3.relation-assessment/0.0.0` / `agtxiv.v3.contribution-delta/0.0.0` / `agtxiv.v3.reuse-decision/0.0.0` / `agtxiv.v3.environment-check/0.0.0` / `agtxiv.v3.frontier-item/0.0.0` / `agtxiv.v3.release-manifest/0.0.0` / `agtxiv.v3.release-audit/0.0.0` / `agtxiv.v3.release-certificate/0.0.0` / `agtxiv.v3.paper-release/0.0.0` / `agtxiv.v3.archive-receipt/0.0.0` / `agtxiv.v3.admission-decision/0.0.0` / `agtxiv.v3.knowledge-snapshot/0.0.0` / `agtxiv.v3.ingestion-receipt/0.0.0` / `agtxiv.v3.event/0.0.0` / `agtxiv.v3.event-checkpoint/0.0.0` / `agtxiv.v3.impact-analysis/0.0.0` / `agtxiv.v3.revision-record/0.0.0` / `agtxiv.v3.legacy-binding/0.0.0` / `agtxiv.v3.query-receipt/0.0.0` / `agtxiv.v3.evaluation-report/0.0.0` / `agtxiv.v3.source-request/0.0.0` / `agtxiv.v3.source-acquisition/0.0.0` / `agtxiv.v3.evidence-protocol/0.0.0` / `agtxiv.v3.work-completion/0.0.0` / `agtxiv.v3.counterexample/0.0.0` | 是 | 精确注册的记录类型。 |
| `record_id` | string | 是 | 记录谱系的稳定身份。 |
| `revision` | integer | 是 | 精确不可变修订号。 |
| `content_hash` | string | 是 | 除 content_hash 外完整记录的规范化哈希。 |

### ArtifactRef

原始字节的身份；地址本身不提供完整性证据。

| 字段 | 类型 / 值 | 必填 | 含义 |
|---|---|---|---|
| `artifact_id` | string | 是 | 文件或字节对象身份。 |
| `sha256` | string | 是 | 未修改原始字节的 SHA-256。 |
| `byte_size` | integer | 是 | 精确字节长度。 |
| `media_type` | string | 是 | 媒体类型。 |
| `path_hint` | string | 否 | 相对显示位置，不作为权威选择器。 |

### Producer

可归属的生产者及其可见执行边界。

| 字段 | 类型 / 值 | 必填 | 含义 |
|---|---|---|---|
| `principal_id` | string | 是 | 执行记录声明的实际主体身份。 |
| `role` | `SOURCE_PRODUCER` / `CLAIM_PRODUCER` / `ARGUMENT_PRODUCER` / `ARGUMENT_REVIEWER` / `FORMALIZER` / `FORMAL_CHECKER` / `BACKTRANSLATOR` / `ALIGNMENT_REVIEWER` / `SCIENTIFIC_REVIEWER` / `SCOPE_REVIEWER` / `PAPER_AUDITOR` / `CERTIFIER` / `ARCHIVE_SERVICE` / `ADMISSION_REVIEWER` / `KNOWLEDGE_SERVICE` / `QUERY_SERVICE` / `COORDINATOR` / `MAINTAINER` / `MIGRATION_SERVICE` | 是 | 本次操作承担的职责。 |
| `actor_kind` | `HUMAN` / `AGENT` / `MECHANICAL_SERVICE` | 是 | 主体类别，不代表可信等级。 |
| `identity_assurance` | `DECLARED` / `LOCALLY_ATTESTED` / `EXTERNALLY_ATTESTED` | 是 | 身份确认方式；字符串不是认证。 |
| `execution_id` | string | 是 | 精确执行身份。 |
| `model` | string | 否 | 使用 agent 时的模型标识。 |
| `visible_input_refs` | array<RecordRef> | 是 | 主体可见的精确记录。 |
| `identity_evidence` | array<ArtifactRef> | 是 | 独立提供的身份凭据。 |

### ReviewContext

声明的独立性与精确审阅输入，运行层必须核实。

| 字段 | 类型 / 值 | 必填 | 含义 |
|---|---|---|---|
| `reviewed_refs` | array<RecordRef> | 是 | 本决定评估的精确记录。 |
| `producer_principal_ids` | array<string> | 是 | 被审内容所有实际生产者。 |
| `independence` | `UNESTABLISHED` / `ROLE_SEPARATED` / `INDEPENDENTLY_ATTESTED` | 是 | 审阅独立性边界，不保证结论为真。 |
| `conflicts` | array<string> | 是 | 已知利益冲突或同模型局限。 |
| `method` | string | 是 | 公开审阅方法。 |
| `evidence_refs` | array<RecordRef> | 是 | 审阅依据。 |

### Condition

具有来源与解释的关键条件。

| 字段 | 类型 / 值 | 必填 | 含义 |
|---|---|---|---|
| `condition_id` | string | 是 | 父记录内的条件身份。 |
| `statement` | string | 是 | 保留范围与量词的完整条件。 |
| `origin` | `SOURCE_EXPLICIT` / `SOURCE_RECONSTRUCTED` / `AGENT_ADDED` / `IMPORTED` | 是 | 条件归属。 |
| `source_span_refs` | array<RecordRef → source-span> | 是 | 支持条件的原文跨度。 |

### SourceUnit

来源清点项及其在选定渲染中的活动性。

| 字段 | 类型 / 值 | 必填 | 含义 |
|---|---|---|---|
| `unit_id` | string | 是 | 来源清点项身份。 |
| `relative_path` | string | 是 | 规范相对路径。 |
| `artifact` | ArtifactRef | 是 | 精确原始来源字节。 |
| `activity` | `ACTIVE` / `DORMANT` / `UNKNOWN` | 是 | 是否参与指定渲染。 |
| `kind` | `TEX` / `PDF` / `BIBLIOGRAPHY` / `FIGURE` / `TABLE` / `CODE` / `DATA` / `OTHER` | 是 | 来源对象用途。 |

### StructureEdge

文档结构关系，不是数学推理。

| 字段 | 类型 / 值 | 必填 | 含义 |
|---|---|---|---|
| `source_unit_id` | string | 是 | 包含或引用端。 |
| `target_unit_id` | string | 是 | 被包含或被引用端。 |
| `relation` | `INCLUDES` / `CONTAINS` / `REFERENCES` / `CAPTION_OF` | 是 | 文档关系。 |
| `activity` | `ACTIVE` / `DORMANT` / `UNKNOWN` | 是 | 静态活动性观察。 |
| `locator` | string | 是 | 关系出现位置。 |

### Obligation

冻结分母中的一项处理义务。

| 字段 | 类型 / 值 | 必填 | 含义 |
|---|---|---|---|
| `obligation_id` | string | 是 | 跨尝试保留的义务身份。 |
| `target_refs` | array<RecordRef> | 是 | 已知精确目标；仅未解决发现项可为空。 |
| `source_unit_ids` | array<string> | 是 | 所覆盖来源项。 |
| `stage` | `SOURCE` / `INVENTORY` / `CLAIM` / `ARGUMENT` / `FORMAL` / `ALIGNMENT` / `SEMANTICS` / `EMPIRICAL` / `COMPUTATION` / `CONTRIBUTION` / `RELEASE` | 是 | 所需处理阶段。 |
| `requirement` | `ACCOUNT_FOR` / `SUCCESS_REQUIRED` | 是 | 只需交代或必须成功。 |
| `applicable_axes` | array<`source_fidelity` / `mathematical_correctness` / `formal_alignment` / `semantic_applicability` / `empirical_support` / `computational_reproducibility`> | 是 | 工作相关核查轴。 |
| `reason` | string | 是 | 纳入范围的理由。 |

### Component

原始命题中可独立归属的组成部分。

| 字段 | 类型 / 值 | 必填 | 含义 |
|---|---|---|---|
| `component_id` | string | 是 | 主张内组件身份。 |
| `text` | string | 是 | 完整组件含义。 |
| `role` | `CONCLUSION` / `ASSUMPTION` / `DEFINITION` / `MODEL` / `APPROXIMATION` / `EVIDENCE` / `ATTRIBUTION` / `LIMITATION` | 是 | 语义角色。 |
| `source_span_refs` | array<RecordRef → source-span> | 是 | 精确原文位置。 |

### ComponentMapping

组件在数学、科学语义与未解决部分之间的完整记账。

| 字段 | 类型 / 值 | 必填 | 含义 |
|---|---|---|---|
| `component_id` | string | 是 | 源主张中的精确组件。 |
| `math_refs` | array<RecordRef → math-claim> | 是 | 数学表示。 |
| `semantic_refs` | array<RecordRef → semantic-context> | 是 | 单独保留的科学含义。 |
| `evidence_refs` | array<RecordRef> | 是 | 组件相关证据。 |
| `disposition` | `MAPPED` / `RESIDUAL` / `UNRESOLVED` / `NON_CLAIM` | 是 | 组件处置。 |
| `residual` | string | 是 | 映射未涵盖的含义。 |

### MathObject

含定义、单位与约定的数学对象。

| 字段 | 类型 / 值 | 必填 | 含义 |
|---|---|---|---|
| `symbol` | string | 是 | 带范围的符号。 |
| `object_type` | string | 是 | 数学载体或类型。 |
| `definition_refs` | array<RecordRef → definition> | 是 | 精确导入定义。 |
| `unit` | string | 是 | 单位；无量纲可为空。 |
| `convention` | string | 是 | 归一化和解释约定。 |

### Quantifier

有序约束变量；顺序具有语义。

| 字段 | 类型 / 值 | 必填 | 含义 |
|---|---|---|---|
| `kind` | `FORALL` / `EXISTS` / `UNIQUE_EXISTS` | 是 | 量词类型。 |
| `variable` | string | 是 | 被约束变量。 |
| `domain` | string | 是 | 含限制的量词范围。 |

### FormalDeclaration

在一个形式环境中观察到的精确声明。

| 字段 | 类型 / 值 | 必填 | 含义 |
|---|---|---|---|
| `name` | string | 是 | 完整命名空间下的声明名。 |
| `statement` | string | 是 | 展开或检查过的声明类型。 |
| `source_artifact` | ArtifactRef | 是 | 声明来源字节。 |
| `is_axiom` | boolean | 是 | 声明自身是否为公理。 |
| `axioms` | array<string> | 是 | 检查器报告的传递公理。 |
| `dependencies` | array<string> | 是 | 固定环境中的声明依赖名。 |

### ParameterComparison

复用结果与目标用途的明确比较。

| 字段 | 类型 / 值 | 必填 | 含义 |
|---|---|---|---|
| `dimension` | `OBJECT` / `DEFINITION` / `QUANTIFIER` / `ASSUMPTION` / `CONCLUSION` / `UNIT` / `CONVENTION` / `REGIME` / `EVIDENCE` / `ENVIRONMENT` | 是 | 比较维度。 |
| `source_value` | string | 是 | 被复用端含义。 |
| `target_value` | string | 是 | 目标所需含义。 |
| `relation` | `EQUIVALENT` / `SOURCE_STRONGER` / `TARGET_STRONGER` / `INCOMPARABLE` / `UNKNOWN` | 是 | 评估的对应关系，不是文字相似度。 |
| `witness_refs` | array<RecordRef> | 是 | 比较见证。 |

### AdmissionItem

一个精确候选及其准入决定。

| 字段 | 类型 / 值 | 必填 | 含义 |
|---|---|---|---|
| `candidate_ref` | RecordRef | 是 | 精确知识候选。 |
| `decision` | `ACCEPT` / `REJECT` / `BLOCK` | 是 | 准入处置，不是真假。 |
| `assessment_refs` | array<RecordRef → axis-assessment, relation-assessment, argument-review> | 是 | 相关精确评估。 |
| `reason` | string | 是 | 公开准入理由与条件。 |

### ImpactTarget

一个受影响目标及其类型化、按轴限定的原因。

| 字段 | 类型 / 值 | 必填 | 含义 |
|---|---|---|---|
| `target_ref` | RecordRef | 是 | 精确受影响目标。 |
| `axes` | array<`source_fidelity` / `mathematical_correctness` / `formal_alignment` / `semantic_applicability` / `empirical_support` / `computational_reproducibility`> | 是 | 需要重查的轴。 |
| `proof_plan_ref` | nullable RecordRef → proof-plan | 是 | 受影响证明方案。 |
| `reason` | string | 是 | 需要重新评估的理由。 |

### QueryAssertion

有精确记录支持的公开回答。

| 字段 | 类型 / 值 | 必填 | 含义 |
|---|---|---|---|
| `text` | string | 是 | 回答中的一个承重断言。 |
| `support_refs` | array<RecordRef> | 是 | 支持表述的精确记录。 |
| `limitations` | array<string> | 是 | 范围与未解决限定。 |

### Metric

有冻结分母和比较范围的测量值。

| 字段 | 类型 / 值 | 必填 | 含义 |
|---|---|---|---|
| `name` | string | 是 | 指标名，不得作为论文真假或质量总分。 |
| `measurement_status` | `NOT_MEASURED` / `MEASURED` / `UNDEFINED` | 是 | 是否实测以及比例是否有定义。 |
| `numerator` | nullable integer | 是 | 实测计数；未测时为空。 |
| `denominator` | nullable integer | 是 | 冻结分母；未知为空，仅实测空集合用零。 |
| `unit` | string | 是 | 测量单位。 |
| `method` | string | 是 | 测量方法与范围。 |

### PdfRegion

精确 PDF 的页内定位，不伪造原始文本字节跨度。

| 字段 | 类型 / 值 | 必填 | 含义 |
|---|---|---|---|
| `page_index` | integer | 是 | 从零开始的页码。 |
| `x0` | string | 是 | 归一化页面单位的精确十进制左坐标。 |
| `y0` | string | 是 | 精确十进制上坐标。 |
| `x1` | string | 是 | 精确十进制右坐标。 |
| `y1` | string | 是 | 精确十进制下坐标。 |

## 记录通用封套

| 字段 | 类型 / 值 | 必填 | 含义 |
|---|---|---|---|
| `record_type` | string | 是 | 所选对象族的精确类型标识。 |
| `record_id` | string | 是 | 稳定身份；语义变化可能需要新谱系。 |
| `revision` | integer | 是 | 谱系内精确不可变版本。 |
| `created_at` | string | 是 | 可归属的 UTC 创建时间。 |
| `data_class` | `RESEARCH` / `OBSERVED` / `SYNTHETIC` | 是 | 证据来源类别，不是权威状态。 |
| `schema_bundle_hash` | string | 是 | schema 包清单精确哈希。 |
| `producer` | Producer | 是 | 实际可归属生产者及执行边界。 |
| `policy_ref` | nullable RecordRef → authority-policy | 是 | 精确权限政策；仅其自举记录可为空。 |
| `input_refs` | array<RecordRef> | 是 | 构建记录使用的显式精确输入。 |
| `content_hash` | string | 是 | 仅排除此字段后的记录规范化哈希。 |
| `payload` | object | 是 | 下文列出的对象专属封闭字段集合。 |

## 处理标准（ProcessingProfile）

版本化工作义务，区分必须成功与允许未解决。

Schema：[processing-profile.schema.json](processing-profile.schema.json)。对应任务：P0.2, P1.3。

| 字段 | 类型 / 值 | 必填 | 含义 |
|---|---|---|---|
| `name` | `V3_SOURCE_MAP` / `V3_ARGUMENT_AUDIT` / `V3_FORMAL_SUPPORT` | 是 | V3 处理标准名称。 |
| `required_stages` | array<string> | 是 | 每个适用范围必须交代的阶段。 |
| `success_required_stages` | array<string> | 是 | 要求目标实际成功的阶段。 |
| `required_axes` | array<`source_fidelity` / `mathematical_correctness` / `formal_alignment` / `semantic_applicability` / `empirical_support` / `computational_reproducibility`> | 是 | 需要评估的适用轴。 |
| `allowed_terminal_outcomes` | array<string> | 是 | 允许的未解决执行处置。 |
| `empirical_requirement` | `ACCOUNT_FOR` / `REVIEW_REQUIRED` | 是 | 经验性工作要求。 |
| `computation_requirement` | `ACCOUNT_FOR` / `REPRODUCTION_REQUIRED` | 是 | 计算工作要求。 |
| `non_implications` | array<string> | 是 | 满足标准不意味着什么。 |

## 身份与权限政策（AuthorityPolicy）

版本化权限、职责分离与审阅要求。

Schema：[authority-policy.schema.json](authority-policy.schema.json)。对应任务：P0.1, P0.3, P1.6。

| 字段 | 类型 / 值 | 必填 | 含义 |
|---|---|---|---|
| `charter_identity` | `AgtXIv-Charter/1.0` | 是 | 设计依据的 Charter 身份。 |
| `charter_state` | `PROPOSED` / `ADOPTED` | 是 | 治理规定下的实际批准状态。 |
| `ratification_commit` | nullable string | 是 | 批准后才可填写的有效提交。 |
| `minimum_identity_assurance` | `LOCALLY_ATTESTED` / `EXTERNALLY_ATTESTED` | 是 | 权威决定所需最低身份凭据。 |
| `separated_role_pairs` | array<string> | 是 | 同一被评对象上不兼容的角色组合。 |
| `human_review_triggers` | array<string> | 是 | 需人员审阅的科学或治理条件。 |
| `allowed_principal_ids` | array<string> | 是 | 本政策范围获授权的主体。 |

## 来源快照（SourceSnapshot）

一篇精确论文版本的原始字节及取得边界。

Schema：[source-snapshot.schema.json](source-snapshot.schema.json)。对应任务：P2.1。

| 字段 | 类型 / 值 | 必填 | 含义 |
|---|---|---|---|
| `paper_id` | string | 是 | 精确作品标识。 |
| `paper_version` | string | 是 | 明确来源版本，不允许 latest。 |
| `source_uri` | string | 是 | 留作履历的取得位置。 |
| `acquired_at` | string | 是 | 字节取得时间。 |
| `acquisition_ref` | nullable RecordRef → source-acquisition | 是 | 可用时的精确取得报告；本地旧输入可能无此历史。 |
| `acquisition_method` | `ARXIV_SOURCE` / `ARXIV_PDF` / `LOCAL_IMPORT` / `OTHER_EXACT_SOURCE` | 是 | 字节取得方式。 |
| `units` | array<SourceUnit> | 是 | 完整的已提供来源清单。 |
| `archive` | nullable ArtifactRef | 是 | 原始源压缩包。 |
| `missing_material` | array<string> | 是 | 已知缺失材料。 |
| `rights_status` | `KNOWN` / `UNRESOLVED` / `RESTRICTED` | 是 | 可用性与复用许可边界。 |
| `rights_note` | string | 是 | 来源与再分发条件。 |

## 来源跨度（SourceSpan）

用于归属命题或条件的精确原文位置。

Schema：[source-span.schema.json](source-span.schema.json)。对应任务：P2.2, P2.4。

| 字段 | 类型 / 值 | 必填 | 含义 |
|---|---|---|---|
| `source_ref` | RecordRef → source-snapshot | 是 | 包含原文位置的精确快照。 |
| `artifact` | ArtifactRef | 是 | 包含原文的原始字节。 |
| `locator_kind` | `RAW_TEXT_BYTES` / `PDF_REGION` / `TRANSFORMED_TEXT` | 是 | 精确原文位置表示方式。 |
| `byte_start` | nullable integer | 是 | 包含端点的零起点字节位置；PDF 页内区域为空。 |
| `byte_end` | nullable integer | 是 | 不包含端点的字节终点；PDF 页内区域为空。 |
| `span_sha256` | nullable string | 是 | 所选文本字节精确哈希；PDF 页内区域为空。 |
| `pdf_region` | nullable PdfRegion | 是 | PDF 位置的页码与区域。 |
| `transformation_ref` | nullable RecordRef → source-transformation | 是 | 使用派生文本时的精确映射。 |
| `locator` | string | 是 | 页码、行号或标签等可读位置。 |
| `activity` | `ACTIVE` / `DORMANT` / `UNKNOWN` | 是 | 是否参与指定原文渲染。 |

## 来源变换（SourceTransformation）

原始材料到派生表示的可审计映射。

Schema：[source-transformation.schema.json](source-transformation.schema.json)。对应任务：P2.2。

| 字段 | 类型 / 值 | 必填 | 含义 |
|---|---|---|---|
| `source_ref` | RecordRef → source-snapshot | 是 | 精确来源输入。 |
| `inputs` | array<ArtifactRef> | 是 | 未修改输入字节。 |
| `outputs` | array<ArtifactRef> | 是 | 身份独立的派生字节。 |
| `method` | string | 是 | 提取、展开或渲染方法。 |
| `environment` | string | 是 | 固定工具与配置身份。 |
| `mapping_artifact` | ArtifactRef | 是 | 明确的原文到输出位置映射。 |
| `limitations` | array<string> | 是 | 未解决渲染或解码歧义。 |

## 论文结构（PaperStructure）

来源包含及活动关系，与数学依赖分离。

Schema：[paper-structure.schema.json](paper-structure.schema.json)。对应任务：P2.2。

| 字段 | 类型 / 值 | 必填 | 含义 |
|---|---|---|---|
| `source_ref` | RecordRef → source-snapshot | 是 | 精确来源清单。 |
| `main_unit_id` | string | 是 | 明确选定文档入口。 |
| `edges` | array<StructureEdge> | 是 | 文档结构关系。 |
| `unclassified_unit_ids` | array<string> | 是 | 活动性或用途未知的来源项。 |
| `blockers` | array<string> | 是 | 解析或活动性限制。 |

## 论文处理计划（AgentizationPlan）

详细发现前固定、与查询无关的论文计划。

Schema：[agentization-plan.schema.json](agentization-plan.schema.json)。对应任务：P1.3, P2.3。

| 字段 | 类型 / 值 | 必填 | 含义 |
|---|---|---|---|
| `source_ref` | RecordRef → source-snapshot | 是 | 精确计划来源。 |
| `profile_ref` | RecordRef → processing-profile | 是 | 精确工作要求。 |
| `baseline_ref` | nullable RecordRef → baseline-snapshot | 是 | 后续比较所选旧知识。 |
| `source_unit_ids` | array<string> | 是 | 来源发现的固定分母。 |
| `max_steps` | integer | 是 | 有界工作最大步数。 |
| `max_seconds` | integer | 是 | 工作时间上限。 |
| `max_cost_units` | integer | 是 | 声明的整数资源预算。 |
| `no_progress_limit` | integer | 是 | 停止前连续无进展尝试数。 |
| `trigger_note` | string | 是 | 触发理由，不定义正式范围。 |

## 全文发现记录（InventoryDiscovery）

独立范围决定前，对全部来源项进行分类。

Schema：[inventory-discovery.schema.json](inventory-discovery.schema.json)。对应任务：P2.3, P2.6。

| 字段 | 类型 / 值 | 必填 | 含义 |
|---|---|---|---|
| `plan_ref` | RecordRef → agentization-plan | 是 | 精确发现计划。 |
| `structure_ref` | RecordRef → paper-structure | 是 | 用于发现的来源结构。 |
| `classified_unit_ids` | array<string> | 是 | 已分类来源项。 |
| `unclassified_unit_ids` | array<string> | 是 | 未解决但仍保留在分母中的项。 |
| `obligations` | array<Obligation> | 是 | 提议的完整工作分母。 |
| `claim_refs` | array<RecordRef → scientific-claim> | 是 | 候选或已归属原文命题。 |
| `coverage_rationale` | string | 是 | 覆盖与排除的公开理由。 |

## 范围冻结决定（ScopeFreezeDecision）

对精确发现结果的独立接受或阻塞决定。

Schema：[scope-decision.schema.json](scope-decision.schema.json)。对应任务：P2.6。

| 字段 | 类型 / 值 | 必填 | 含义 |
|---|---|---|---|
| `discovery_ref` | RecordRef → inventory-discovery | 是 | 被审的精确发现结果。 |
| `review` | ReviewContext | 是 | 独立审阅边界。 |
| `decision` | `BLOCK` / `ACCEPT` | 是 | 冻结决定，不是科学认可。 |
| `reason` | string | 是 | 公开决定理由。 |

## 冻结处理范围（FrozenInventoryScope）

独立冻结决定之后的不可变工作分母。

Schema：[frozen-scope.schema.json](frozen-scope.schema.json)。对应任务：P1.3, P2.5。

| 字段 | 类型 / 值 | 必填 | 含义 |
|---|---|---|---|
| `plan_ref` | RecordRef → agentization-plan | 是 | 精确计划。 |
| `discovery_ref` | RecordRef → inventory-discovery | 是 | 精确清点义务。 |
| `decision_ref` | RecordRef → scope-decision | 是 | 接受冻结的独立决定。 |
| `obligations` | array<Obligation> | 是 | 完整记账所需精确义务。 |
| `predecessor_ref` | nullable RecordRef → frozen-scope | 是 | 修订前的不可变范围。 |
| `change_reason` | string | 是 | 初始原因或明确扩展、纠错理由。 |
| `removed_obligation_dispositions` | array<RecordRef> | 是 | 所有被移除旧义务的明确审阅处置。 |

## 义务处置（ObligationDisposition）

一项固定义务的当前处置，保留全部尝试。

Schema：[obligation-disposition.schema.json](obligation-disposition.schema.json)。对应任务：P1.3。

| 字段 | 类型 / 值 | 必填 | 含义 |
|---|---|---|---|
| `scope_ref` | RecordRef → frozen-scope | 是 | 精确冻结分母。 |
| `obligation_id` | string | 是 | 精确被记账义务。 |
| `outcome` | `BLOCKED` / `DEFERRED` / `FAILED` / `COMPLETED` / `NOT_APPLICABLE` | 是 | 仅执行记账。 |
| `result_refs` | array<RecordRef> | 是 | 实际产物记录，不是虚构占位符。 |
| `attempt_refs` | array<RecordRef → work-attempt> | 是 | 精确工作尝试。 |
| `reason` | string | 是 | 处置说明与剩余边界。 |
| `previous_ref` | nullable RecordRef → obligation-disposition | 是 | 先前不可变处置。 |

## 科学主张（ScientificClaim）

保留条件、归属和科学范围的忠实原文命题。

Schema：[scientific-claim.schema.json](scientific-claim.schema.json)。对应任务：P2.4, P2.5。

| 字段 | 类型 / 值 | 必填 | 含义 |
|---|---|---|---|
| `statement` | string | 是 | 可独立修订的完整原文命题。 |
| `source_span_refs` | array<RecordRef → source-span> | 是 | 支持各关键部分的精确原文。 |
| `components` | array<Component> | 是 | 可独立定位的主张部分。 |
| `conditions` | array<Condition> | 是 | 所有影响真假判断的原文条件。 |
| `modality` | `ASSERTED` / `CONJECTURED` / `OBSERVED` / `APPROXIMATE` / `CONDITIONAL` / `INTERPRETIVE` | 是 | 原文断言强度与语气。 |
| `attribution` | string | 是 | 谁断言哪部分。 |
| `system` | string | 是 | 模型、物理系统或数学域。 |
| `comparison_baseline` | string | 是 | 原文声明的比较基准。 |

## 系统派生命题（DerivedClaim）

明确变换来源、不伪造原文归属的新命题。

Schema：[derived-claim.schema.json](derived-claim.schema.json)。对应任务：P2.5, P4.5。

| 字段 | 类型 / 值 | 必填 | 含义 |
|---|---|---|---|
| `statement` | string | 是 | 完整新命题。 |
| `origin` | `SYSTEM_DERIVATION` / `CONDITIONALIZATION` / `REPAIR` / `INDEPENDENT_PROPOSITION` | 是 | 新命题产生原因。 |
| `parent_refs` | array<RecordRef → scientific-claim, derived-claim, math-claim> | 是 | 派生或区分的精确原命题。 |
| `added_conditions` | array<Condition> | 是 | 原命题没有的新增条件。 |
| `relation` | `DERIVES` / `SPECIALIZES` / `CORRECTS` / `ALTERNATIVE` / `INDEPENDENT` | 是 | 需独立评估的声明关系。 |
| `rationale` | string | 是 | 变换的公开理由。 |

## 主张组件对应（ClaimComponentMap）

完整映射或残余记账，不升级科学状态。

Schema：[claim-component-map.schema.json](claim-component-map.schema.json)。对应任务：P2.4。

| 字段 | 类型 / 值 | 必填 | 含义 |
|---|---|---|---|
| `claim_ref` | RecordRef → scientific-claim | 是 | 精确原始主张。 |
| `mappings` | array<ComponentMapping> | 是 | 每个原文组件恰一条记账。 |
| `review` | ReviewContext | 是 | 来源到表示的审阅。 |
| `coverage` | `PARTIAL` / `COMPLETE` | 是 | 数学与语义记账覆盖，不是真假。 |

## 科学语义上下文（SemanticContext）

形式证明之外保留的科学含义、近似和可观测量。

Schema：[semantic-context.schema.json](semantic-context.schema.json)。对应任务：P4.6。

| 字段 | 类型 / 值 | 必填 | 含义 |
|---|---|---|---|
| `claim_ref` | RecordRef → scientific-claim, derived-claim | 是 | 精确被解释命题。 |
| `physical_system` | string | 是 | 目标物理或模型系统。 |
| `object_mapping` | array<ParameterComparison> | 是 | 数学到科学对象的对应。 |
| `assumptions` | array<Condition> | 是 | 科学模型假设。 |
| `approximation_regime` | string | 是 | 有效范围和近似条件。 |
| `error_bound` | string | 是 | 有来源支持的误差或明确未知说明。 |
| `observables` | array<string> | 是 | 观测量操作定义。 |
| `limitations` | array<string> | 是 | 未解决科学含义或适用性。 |

## 数学定义（MathematicalDefinition）

具有载体、约定和来源的精确定义。

Schema：[definition.schema.json](definition.schema.json)。对应任务：P1.4, P3.3。

| 字段 | 类型 / 值 | 必填 | 含义 |
|---|---|---|---|
| `name` | string | 是 | 定义名称。 |
| `statement` | string | 是 | 完整数学定义。 |
| `objects` | array<MathObject> | 是 | 所定义对象及载体。 |
| `source_span_refs` | array<RecordRef → source-span> | 是 | 来源位置；系统定义才可为空。 |
| `origin` | `SOURCE` / `IMPORTED` / `SYSTEM` | 是 | 定义归属。 |

## 数学交接单（MathClaimIR）

不含可变验证状态的精确数学目标。

Schema：[math-claim.schema.json](math-claim.schema.json)。对应任务：P1.4, P4.1。

| 字段 | 类型 / 值 | 必填 | 含义 |
|---|---|---|---|
| `claim_ref` | RecordRef → scientific-claim, derived-claim | 是 | 精确原文或独立派生命题。 |
| `component_ids` | array<string> | 是 | 本目标表示的数学组件。 |
| `objects` | array<MathObject> | 是 | 载体、单位和约定。 |
| `quantifiers` | array<Quantifier> | 是 | 有序量词。 |
| `assumptions` | array<Condition> | 是 | 全部显式数学前提。 |
| `conclusion` | string | 是 | 精确数学结论。 |
| `exactness` | `EXACT` / `APPROXIMATE` / `ASYMPTOTIC` | 是 | 目标精确程度。 |
| `approximation_error` | string | 是 | 非精确时的误差及范围。 |
| `definition_refs` | array<RecordRef → definition> | 是 | 精确数学定义。 |
| `semantic_refs` | array<RecordRef → semantic-context> | 是 | 剩余科学含义。 |
| `normalization` | string | 是 | 不改变范围的符号、约定规范化。 |

## 假设范围（AssumptionContext）

局部假设及其嵌套；解除须明确推理。

Schema：[assumption-context.schema.json](assumption-context.schema.json)。对应任务：P3.3, P3.6。

| 字段 | 类型 / 值 | 必填 | 含义 |
|---|---|---|---|
| `parent_ref` | nullable RecordRef → assumption-context | 是 | 外层上下文，不允许循环。 |
| `assumptions` | array<Condition> | 是 | 本上下文引入的假设。 |
| `introduction_reason` | string | 是 | 局部前提引入位置和原因。 |
| `allowed_use` | string | 是 | 有效使用边界。 |

## 论证节点（ArgumentNode）

数学论证中的一条可归属陈述。

Schema：[argument-node.schema.json](argument-node.schema.json)。对应任务：P3.2, P3.3。

| 字段 | 类型 / 值 | 必填 | 含义 |
|---|---|---|---|
| `statement` | string | 是 | 完整节点命题。 |
| `kind` | `CLAIM` / `DEFINITION` / `ASSUMPTION` / `LEMMA` / `CONSTRUCTION` / `CONCLUSION` | 是 | 数学角色。 |
| `origin` | `SOURCE` / `RECONSTRUCTED` / `REPAIRED` / `ALTERNATIVE` / `IMPORTED` | 是 | 论证内容归属。 |
| `claim_refs` | array<RecordRef → scientific-claim, derived-claim, math-claim> | 是 | 精确主张对应。 |
| `context_ref` | nullable RecordRef → assumption-context | 是 | 局部假设范围。 |
| `definition_refs` | array<RecordRef → definition> | 是 | 节点使用的定义。 |
| `source_span_refs` | array<RecordRef → source-span> | 是 | 适用时的精确原文支持。 |

## 推理步骤（InferenceStep）

多前提联合推理，与文稿包含关系分离。

Schema：[inference-step.schema.json](inference-step.schema.json)。对应任务：P1.4, P3.3。

| 字段 | 类型 / 值 | 必填 | 含义 |
|---|---|---|---|
| `premise_refs` | array<RecordRef → argument-node> | 是 | 共同前提，不是各自单独蕴含。 |
| `conclusion_ref` | RecordRef → argument-node | 是 | 精确结论节点。 |
| `rule` | `DIRECT` / `MODUS_PONENS` / `DEFINITIONAL` / `CONTRADICTION` / `INDUCTION` / `CASE_SPLIT` / `ASSUMPTION_DISCHARGE` / `EXTERNAL_RESULT` | 是 | 明确推理规则。 |
| `justification` | string | 是 | 公开数学理由。 |
| `context_ref` | nullable RecordRef → assumption-context | 是 | 推理有效范围。 |
| `discharged_context_refs` | array<RecordRef → assumption-context> | 是 | 本步骤解除的精确范围。 |
| `rule_evidence_refs` | array<RecordRef> | 是 | 推理规则条件的见证。 |

## 证明方案（ProofPlan）

支持结论的一条独立证明路线。

Schema：[proof-plan.schema.json](proof-plan.schema.json)。对应任务：P3.3, P4.5。

| 字段 | 类型 / 值 | 必填 | 含义 |
|---|---|---|---|
| `scope_ref` | RecordRef → frozen-scope | 是 | 必需证明义务所属的精确冻结范围。 |
| `conclusion_ref` | RecordRef → argument-node | 是 | 精确目标结论。 |
| `route` | `ORIGINAL` / `RECONSTRUCTED` / `REPAIRED` / `ALTERNATIVE` | 是 | 证明方法归属。 |
| `node_refs` | array<RecordRef → argument-node> | 是 | 本路线节点。 |
| `inference_refs` | array<RecordRef → inference-step> | 是 | 精确联合前提推理。 |
| `required_obligation_ids` | array<string> | 是 | 删除节点不能抹去的固定证明义务。 |
| `open_obligation_ids` | array<string> | 是 | 尚未解除的义务。 |

## 依赖绑定（DependencyBinding）

前提、定义或外部结果的一次精确使用。

Schema：[dependency-binding.schema.json](dependency-binding.schema.json)。对应任务：P3.6, P5.4。

| 字段 | 类型 / 值 | 必填 | 含义 |
|---|---|---|---|
| `dependent_ref` | RecordRef | 是 | 需要依赖的精确对象。 |
| `prerequisite_ref` | RecordRef | 是 | 精确所需输入。 |
| `kind` | `MATHEMATICAL` / `DEFINITION` / `SCOPE` / `FORMAL_ENVIRONMENT` / `SEMANTIC` / `EMPIRICAL` / `COMPUTATIONAL` / `VALIDATION` | 是 | 决定审查传播的依赖类型。 |
| `affected_axes` | array<`source_fidelity` / `mathematical_correctness` / `formal_alignment` / `semantic_applicability` / `empirical_support` / `computational_reproducibility`> | 是 | 该依赖影响的轴。 |
| `proof_plan_ref` | nullable RecordRef → proof-plan | 是 | 需要输入的证明路线。 |
| `comparison` | array<ParameterComparison> | 是 | 精确前提与对象兼容性。 |
| `reuse_decision_ref` | nullable RecordRef → reuse-decision | 是 | 对目标用途的独立复用决定。 |

## 异议（Challenge）

精确定位的异议；回复不等于解决。

Schema：[challenge.schema.json](challenge.schema.json)。对应任务：P3.5。

| 字段 | 类型 / 值 | 必填 | 含义 |
|---|---|---|---|
| `target_ref` | RecordRef | 是 | 被质疑节点、推理或绑定。 |
| `category` | `INFERENCE` / `SCOPE` / `DEFINITION` / `PROVENANCE` / `COUNTEREXAMPLE` / `ALIGNMENT` / `DEPENDENCY` / `AUTHORITY` | 是 | 问题类型。 |
| `severity` | `CRITICAL` / `MAJOR` / `MINOR` / `NOTE` | 是 | 审阅优先级，不是错误概率。 |
| `statement` | string | 是 | 公开具体异议。 |
| `evidence_refs` | array<RecordRef> | 是 | 异议支持证据。 |

## 异议处置（ChallengeDisposition）

对精确异议与回复的独立处置。

Schema：[challenge-disposition.schema.json](challenge-disposition.schema.json)。对应任务：P3.5, P3.7。

| 字段 | 类型 / 值 | 必填 | 含义 |
|---|---|---|---|
| `challenge_ref` | RecordRef → challenge | 是 | 精确原异议。 |
| `response` | string | 是 | 公开回复，不包含模型私有思维链。 |
| `response_refs` | array<RecordRef> | 是 | 修订或新增数学证据。 |
| `review` | ReviewContext | 是 | 是否解决异议的独立审阅。 |
| `outcome` | `OPEN` / `RESOLVED` / `WITHDRAWN` / `SUPERSEDED` / `DISPUTED` | 是 | 保留原异议的处置。 |
| `replacement_ref` | nullable RecordRef → challenge | 是 | 被替代时的新异议。 |
| `reason` | string | 是 | 处置适用该版本的理由。 |

## 完整论证快照（ArgumentSnapshot）

完整固定论证，而非仅上游图投影。

Schema：[argument-snapshot.schema.json](argument-snapshot.schema.json)。对应任务：P3.2。

| 字段 | 类型 / 值 | 必填 | 含义 |
|---|---|---|---|
| `scope_ref` | RecordRef → frozen-scope | 是 | 精确且与查询无关的论证范围。 |
| `source_claim_refs` | array<RecordRef → scientific-claim, derived-claim> | 是 | 精确论证目标。 |
| `math_refs` | array<RecordRef → math-claim> | 是 | 关联的固定数学目标。 |
| `node_refs` | array<RecordRef → argument-node> | 是 | 完整节点清单。 |
| `inference_refs` | array<RecordRef → inference-step> | 是 | 联合前提推理。 |
| `context_refs` | array<RecordRef → assumption-context> | 是 | 全部局部假设范围。 |
| `proof_plan_refs` | array<RecordRef → proof-plan> | 是 | 不同证明路线。 |
| `dependency_refs` | array<RecordRef → dependency-binding> | 是 | 全部引用及定义依赖。 |
| `challenge_refs` | array<RecordRef → challenge> | 是 | 包括归档路线的所有异议。 |
| `challenge_disposition_refs` | array<RecordRef → challenge-disposition> | 是 | 完整已知异议处置历史。 |
| `upstream_import_ref` | nullable RecordRef → upstream-import | 是 | 精确保留的上游输入；原生论证可为空。 |
| `missing_items` | array<string> | 是 | 本快照明确缺失项。 |

## 论证审阅（ArgumentReview）

保留未解义务的独立论证评估。

Schema：[argument-review.schema.json](argument-review.schema.json)。对应任务：P3.8。

| 字段 | 类型 / 值 | 必填 | 含义 |
|---|---|---|---|
| `snapshot_ref` | RecordRef → argument-snapshot | 是 | 精确完整审阅上下文。 |
| `proof_plan_refs` | array<RecordRef → proof-plan> | 是 | 实际审阅的证明路线。 |
| `review` | ReviewContext | 是 | 实际审阅身份和方法。 |
| `outcome` | `INCONCLUSIVE` / `CONDITIONAL` / `SUPPORTED` / `COUNTEREVIDENCE` | 是 | 有范围的论证结果，不是内核证明。 |
| `open_obligation_ids` | array<string> | 是 | 剩余承重义务。 |
| `open_challenge_refs` | array<RecordRef → challenge> | 是 | 未解决相关异议。 |
| `conditions` | array<Condition> | 是 | 结论保留的条件。 |

## 上游导入记录（UpstreamImport）

保留引擎原始报告及独立检查的导入边界。

Schema：[upstream-import.schema.json](upstream-import.schema.json)。对应任务：P3.1, P3.2, P3.8。

| 字段 | 类型 / 值 | 必填 | 含义 |
|---|---|---|---|
| `engine` | `vibefeld` | 是 | 上游引擎身份。 |
| `commit` | string | 是 | 精确源码提交。 |
| `protocol_version` | string | 是 | 精确支持的导出协议。 |
| `adapter_version` | string | 是 | 精确导入器版本。 |
| `ledger` | nullable ArtifactRef | 是 | 原始事件账本；缺失时为空。 |
| `graph` | nullable ArtifactRef | 是 | 原始图投影；缺失时为空。 |
| `context_artifacts` | array<ArtifactRef> | 是 | 可取得的范围、定义、外部引用、身份和完整异议。 |
| `identity_map` | nullable ArtifactRef | 是 | 精确身份映射；缺失时为空。 |
| `reported_states` | nullable ArtifactRef | 是 | 原始报告状态；缺失时为空。 |
| `import_checks` | array<string> | 是 | 实际执行的检查。 |
| `outcome` | `INCOMPLETE` / `REJECTED` / `STRUCTURALLY_IMPORTED` | 是 | 导入结果，不是科学支持。 |
| `missing_items` | array<string> | 是 | 缺失的必要上游信息。 |

## 工作尝试（WorkAttempt）

有界、可归属且记录资源使用的执行。

Schema：[work-attempt.schema.json](work-attempt.schema.json)。对应任务：P3.5, P8.3。

| 字段 | 类型 / 值 | 必填 | 含义 |
|---|---|---|---|
| `plan_ref` | RecordRef → agentization-plan | 是 | 工作预算依据。 |
| `operation` | string | 是 | 执行操作。 |
| `target_refs` | array<RecordRef> | 是 | 精确输入或目标。 |
| `started_at` | string | 是 | 开始时间。 |
| `finished_at` | string | 是 | 停止时间。 |
| `outcome` | `FAILED` / `BLOCKED` / `DEFERRED` / `SUCCEEDED` | 是 | 不升级科学状态的执行结果。 |
| `output_refs` | array<RecordRef> | 是 | 仅已生成输出；反向引用本尝试的记录由后置完成回执列出。 |
| `logs` | array<ArtifactRef> | 是 | 保留的公开执行日志。 |
| `cost_units` | integer | 是 | 实测资源单位。 |
| `progress_observed` | boolean | 是 | 是否获得新结果或可行动诊断。 |

## 形式环境（FormalEnvironment）

精确工具链、依赖包、构建输入和可信政策。

Schema：[formal-environment.schema.json](formal-environment.schema.json)。对应任务：P4.2, P4.3。

| 字段 | 类型 / 值 | 必填 | 含义 |
|---|---|---|---|
| `prover` | `Lean4` | 是 | 形式检查器类别。 |
| `toolchain` | string | 是 | 精确 Lean 工具链标识。 |
| `package_manifest` | ArtifactRef | 是 | 精确依赖提交锁。 |
| `source_artifacts` | array<ArtifactRef> | 是 | 所有形式构建输入。 |
| `allowed_axioms` | array<string> | 是 | 明确允许的公理名。 |
| `allowed_trust_mechanisms` | array<string> | 是 | 额外允许的检查机制。 |
| `command` | array<string> | 是 | 参数向量命令，不是插值 shell 字符串。 |
| `network_access` | `DISABLED` / `CONTROLLED_ACQUISITION` | 是 | 声明的执行网络边界。 |

## 形式化交接包（FormalizationPacket）

固定数学目标、论证路线、语义与环境。

Schema：[formalization-packet.schema.json](formalization-packet.schema.json)。对应任务：P4.1。

| 字段 | 类型 / 值 | 必填 | 含义 |
|---|---|---|---|
| `scope_ref` | RecordRef → frozen-scope | 是 | 交接义务所属精确范围。 |
| `math_ref` | RecordRef → math-claim | 是 | 精确数学目标。 |
| `argument_ref` | RecordRef → argument-snapshot | 是 | 精确完整论证快照。 |
| `proof_plan_ref` | RecordRef → proof-plan | 是 | 所选证明路线。 |
| `source_claim_refs` | array<RecordRef → scientific-claim, derived-claim> | 是 | 精确原文或派生目标。 |
| `semantic_refs` | array<RecordRef → semantic-context> | 是 | 剩余科学含义。 |
| `environment_ref` | RecordRef → formal-environment | 是 | 固定检查环境。 |
| `expected_declarations` | array<string> | 是 | 所需输出声明全名。 |
| `open_obligation_ids` | array<string> | 是 | 交接时未证义务。 |
| `mode` | `EXPLORATORY` / `RELEASE_CANDIDATE` | 是 | 工作目的；均不授予权威。 |

## 形式生成尝试（FormalizationAttempt）

生成的形式文件与诊断，与独立检查分离。

Schema：[formalization-attempt.schema.json](formalization-attempt.schema.json)。对应任务：P4.1, P4.3。

| 字段 | 类型 / 值 | 必填 | 含义 |
|---|---|---|---|
| `packet_ref` | RecordRef → formalization-packet | 是 | 精确交接包。 |
| `attempt_ref` | RecordRef → work-attempt | 是 | 精确生成执行。 |
| `outcome` | `FAILED` / `PARTIAL` / `GENERATED` | 是 | 仅文件生成结果。 |
| `artifacts` | array<ArtifactRef> | 是 | 实际生成源码。 |
| `diagnostics` | array<string> | 是 | 公开错误与未解决工作。 |

## 形式检查记录（FormalCheckRecord）

独立目标级内核及传递公理证据。

Schema：[formal-check.schema.json](formal-check.schema.json)。对应任务：P4.3。

| 字段 | 类型 / 值 | 必填 | 含义 |
|---|---|---|---|
| `packet_ref` | RecordRef → formalization-packet | 是 | 精确目标交接。 |
| `attempt_ref` | RecordRef → formalization-attempt | 是 | 实际被检查文件。 |
| `environment_ref` | RecordRef → formal-environment | 是 | 精确检查环境。 |
| `review` | ReviewContext | 是 | 与形式代码生产的独立性。 |
| `outcome` | `FAILED` / `BLOCKED` / `KERNEL_CHECKED` | 是 | 有范围的检查器实测结果。 |
| `built_declarations` | array<FormalDeclaration> | 是 | 在环境中实际检查的声明。 |
| `placeholder_findings` | array<string> | 是 | 未解决占位符或禁止机制。 |
| `logs` | array<ArtifactRef> | 是 | 独立检查与公理审计日志。 |
| `exit_code` | integer | 是 | 非负整数表示的实际进程退出码。 |

## 独立反向解释（BacktranslationRecord）

披露可见输入的形式声明反向解释。

Schema：[backtranslation.schema.json](backtranslation.schema.json)。对应任务：P4.4。

| 字段 | 类型 / 值 | 必填 | 含义 |
|---|---|---|---|
| `packet_ref` | RecordRef → formalization-packet | 是 | 精确目标包身份，不代表允许读取原文。 |
| `formal_artifacts` | array<ArtifactRef> | 是 | 实际可见的形式声明与必要定义。 |
| `visible_record_refs` | array<RecordRef> | 是 | 解释者实际可见记录。 |
| `source_blind` | boolean | 是 | 需执行证据支持的来源盲化声明。 |
| `interpretation` | string | 是 | 形式声明含义及前提。 |
| `conditions` | array<Condition> | 是 | 声明中的条件。 |
| `visibility_evidence` | array<ArtifactRef> | 是 | 独立输入可见性证据。 |

## 含义对齐评估（AlignmentAssessment）

有精确端点和独立审阅的语义比较。

Schema：[alignment-assessment.schema.json](alignment-assessment.schema.json)。对应任务：P4.4。

| 字段 | 类型 / 值 | 必填 | 含义 |
|---|---|---|---|
| `comparison_kind` | `SOURCE_TO_ARGUMENT` / `SOURCE_TO_MATH` / `MATH_TO_FORMAL` / `SOURCE_TO_FORMAL` | 是 | 检查的对齐边界。 |
| `source_refs` | array<RecordRef> | 是 | 精确源侧对象。 |
| `target_refs` | array<RecordRef> | 是 | 精确目标侧对象。 |
| `review` | ReviewContext | 是 | 独立语义审阅。 |
| `comparisons` | array<ParameterComparison> | 是 | 量词、类型、前提、含义与强度比较。 |
| `outcome` | `UNKNOWN` / `PARTIAL` / `MISALIGNED` / `ALIGNED` | 是 | 有范围的对齐，不是证明正确性。 |
| `backtranslation_refs` | array<RecordRef → backtranslation> | 是 | 独立生成的形式解释。 |

## 经验证据（EmpiricalEvidence）

绑定精确科学目标的观测、不确定性与方法。

Schema：[empirical-evidence.schema.json](empirical-evidence.schema.json)。对应任务：P4.7。

| 字段 | 类型 / 值 | 必填 | 含义 |
|---|---|---|---|
| `target_refs` | array<RecordRef → scientific-claim, derived-claim, semantic-context> | 是 | 检查的精确科学前提或结论。 |
| `data` | array<ArtifactRef> | 是 | 精确观测数据。 |
| `method` | string | 是 | 数据采集和分析方法。 |
| `population_regime` | string | 是 | 群体、系统和适用范围。 |
| `uncertainty` | string | 是 | 误差模型和不确定性报告。 |
| `limitations` | array<string> | 是 | 偏倚、缺失与推广限制。 |
| `role` | `ILLUSTRATIVE` / `SUPPORTING` / `LOAD_BEARING` | 是 | 对结论的证据作用。 |

## 计算复现记录（ReproductionRecord）

固定过程和比较规则下观察到的复现结果。

Schema：[reproduction-record.schema.json](reproduction-record.schema.json)。对应任务：P4.7。

| 字段 | 类型 / 值 | 必填 | 含义 |
|---|---|---|---|
| `protocol_ref` | RecordRef → evidence-protocol | 是 | 执行前冻结的精确比较和输入政策。 |
| `attempt_ref` | RecordRef → work-attempt | 是 | 固定输入包含该协议的执行。 |
| `target_refs` | array<RecordRef> | 是 | 精确计算主张或产物。 |
| `code` | array<ArtifactRef> | 是 | 精确执行代码。 |
| `inputs` | array<ArtifactRef> | 是 | 精确数据与参数输入。 |
| `environment` | ArtifactRef | 是 | 精确环境和依赖说明。 |
| `command` | array<string> | 是 | 执行参数向量。 |
| `seeds` | array<integer> | 是 | 随机种子；确定性过程可为空。 |
| `comparison_rule` | string | 是 | 预先规定容差或统计比较方法。 |
| `outcome` | `FAILED` / `BLOCKED` / `DISAGREEMENT` / `REPRODUCED` | 是 | 复现结果，不是科学有效性。 |
| `outputs` | array<ArtifactRef> | 是 | 实际数值输出。 |
| `logs` | array<ArtifactRef> | 是 | 精确独立执行证据。 |

## 单轴评估（AxisAssessment）

以有界证据回答 Charter 六个问题之一。

Schema：[axis-assessment.schema.json](axis-assessment.schema.json)。对应任务：P1.2, P4.8。

| 字段 | 类型 / 值 | 必填 | 含义 |
|---|---|---|---|
| `target_refs` | array<RecordRef> | 是 | 本轴评估的精确对象。 |
| `axis` | `source_fidelity` / `mathematical_correctness` / `formal_alignment` / `semantic_applicability` / `empirical_support` / `computational_reproducibility` | 是 | 一个独立 Charter 核查轴。 |
| `applicability` | `UNDETERMINED` / `APPLICABLE` / `NOT_APPLICABLE` | 是 | 此问题是否适用目标。 |
| `result` | `NOT_ASSESSED` / `INCONCLUSIVE` / `PARTIALLY_SUPPORTED` / `SUPPORTED` / `COUNTEREVIDENCE` | 是 | 证据结论，与执行成功独立。 |
| `execution` | `DEFERRED` / `BLOCKED` / `FAILED` / `COMPLETED` | 是 | 实际评估工作处置。 |
| `method` | `SOURCE_REVIEW` / `ARGUMENT_REVIEW` / `KERNEL_AND_ALIGNMENT` / `FORMAL_ALIGNMENT` / `SEMANTIC_REVIEW` / `EMPIRICAL_REVIEW` / `REPRODUCTION_REVIEW` / `COUNTEREXAMPLE_REVIEW` / `UNASSESSED` | 是 | 证据方法和强度。 |
| `review` | ReviewContext | 是 | 可归属独立评估边界。 |
| `support_refs` | array<RecordRef> | 是 | 精确支持证据。 |
| `counterevidence_refs` | array<RecordRef> | 是 | 精确相关反对证据。 |
| `conditions` | array<Condition> | 是 | 本评估保留的条件。 |
| `frontier_refs` | array<RecordRef → frontier-item> | 是 | 相关未解决问题。 |
| `rationale` | string | 是 | 公开有界结论及不适用理由。 |

## 派生状态视图（StatusView）

可重建六轴视图，保留所有精确与冲突评估。

Schema：[status-view.schema.json](status-view.schema.json)。对应任务：P4.8, P7.4。

| 字段 | 类型 / 值 | 必填 | 含义 |
|---|---|---|---|
| `target_ref` | RecordRef | 是 | 精确查询对象。 |
| `assessment_refs` | array<RecordRef → axis-assessment> | 是 | 完整所选评估证据。 |
| `conflicting_assessment_refs` | array<RecordRef → axis-assessment> | 是 | 可独立检查的分歧。 |
| `axes` | array<`source_fidelity` / `mathematical_correctness` / `formal_alignment` / `semantic_applicability` / `empirical_support` / `computational_reproducibility`> | 是 | 六个轴恰各一次。 |
| `frontier_refs` | array<RecordRef → frontier-item> | 是 | 未解决边界。 |
| `projection_method` | string | 是 | 确定性视图规则，不是真值评分。 |

## 比较基准快照（BaselineSnapshot）

贡献比较所用的固定旧知识与检索覆盖。

Schema：[baseline-snapshot.schema.json](baseline-snapshot.schema.json)。对应任务：P5.1。

| 字段 | 类型 / 值 | 必填 | 含义 |
|---|---|---|---|
| `knowledge_ref` | nullable RecordRef → knowledge-snapshot | 是 | 精确旧知识快照。 |
| `entry_refs` | array<RecordRef> | 是 | 比较中包含的精确旧条目。 |
| `domain` | string | 是 | 科学和数学比较域。 |
| `selection_method` | string | 是 | 旧知识选择方式。 |
| `search_coverage` | string | 是 | 有界检索来源、问题和覆盖。 |
| `limitations` | array<string> | 是 | 已知知识缺失及不代表优先权的限制。 |

## 关系评估（RelationAssessment）

精确主张或知识记录间有见证的关系。

Schema：[relation-assessment.schema.json](relation-assessment.schema.json)。对应任务：P5.2。

| 字段 | 类型 / 值 | 必填 | 含义 |
|---|---|---|---|
| `source_ref` | RecordRef | 是 | 源端；读作源 relation 目标。 |
| `target_ref` | RecordRef | 是 | 与源端不同的目标端。 |
| `relation` | `EQUIVALENT` / `SPECIALIZES` / `GENERALIZES` / `CORRECTS` / `QUALIFIES` / `REFUTES` / `SUPPORTS` / `INCOMPARABLE` / `CONFLICTING` / `SAME_OCCURRENCE` / `MATH_EQUIVALENT_SEMANTICS_DISTINCT` | 是 | 精确类型化关系。 |
| `review` | ReviewContext | 是 | 独立关系评估。 |
| `comparisons` | array<ParameterComparison> | 是 | 范围、前提和语义对应见证。 |
| `outcome` | `PROPOSED` / `BLOCKED` / `DISPUTED` / `ACCEPTED` / `REJECTED` | 是 | 关系评估状态，不是端点真假。 |
| `witness_refs` | array<RecordRef> | 是 | 数学与科学支持。 |

## 贡献变化（ContributionDelta）

相对一个固定基准的可归属知识变化。

Schema：[contribution-delta.schema.json](contribution-delta.schema.json)。对应任务：P5.3。

| 字段 | 类型 / 值 | 必填 | 含义 |
|---|---|---|---|
| `baseline_ref` | RecordRef → baseline-snapshot | 是 | 精确比较基准，不是之后事务快照。 |
| `current_refs` | array<RecordRef> | 是 | 本文精确结果、方法或证据。 |
| `prior_refs` | array<RecordRef> | 是 | 比较的既有对象。 |
| `operation` | `INTRODUCES` / `DERIVES` / `REPROVES` / `GENERALIZES` / `SPECIALIZES` / `WEAKENS_ASSUMPTIONS` / `CORRECTS` / `QUALIFIES` / `REFUTES` / `REPRODUCES` / `INDEPENDENTLY_VERIFIES` / `UNIFIES` / `APPLIES` | 是 | 可归属变化类型，不是重要性分数。 |
| `relation_refs` | array<RecordRef → relation-assessment> | 是 | 已评估比较关系。 |
| `author_declaration` | string | 是 | 单独归属的作者新颖性自述。 |
| `review` | ReviewContext | 是 | 独立贡献评估。 |
| `outcome` | `PROPOSED` / `BLOCKED` / `DISPUTED` / `SUPPORTED` / `REJECTED` | 是 | 有界变化评估。 |
| `qualifications` | array<string> | 是 | 基准覆盖与未解决限制。 |

## 用途复用决定（ReuseDecision）

按指定目标和证据标准复用精确结果的决定。

Schema：[reuse-decision.schema.json](reuse-decision.schema.json)。对应任务：P5.4。

| 字段 | 类型 / 值 | 必填 | 含义 |
|---|---|---|---|
| `source_ref` | RecordRef | 是 | 精确可复用结果。 |
| `target_ref` | RecordRef | 是 | 精确目标用途。 |
| `profile_ref` | RecordRef → processing-profile | 是 | 此用途所需证据标准。 |
| `comparisons` | array<ParameterComparison> | 是 | 必需的对象、前提、范围、证据和环境匹配。 |
| `assessment_refs` | array<RecordRef> | 是 | 支持复用的证据与关系决定。 |
| `review` | ReviewContext | 是 | 独立用途审阅。 |
| `outcome` | `UNKNOWN` / `REJECT` / `CONDITIONAL` / `ALLOW` | 是 | 用途许可，不是新定理证明。 |
| `conditions` | array<Condition> | 是 | 目标仍需满足的条件。 |
| `conflict_refs` | array<RecordRef → relation-assessment> | 是 | 相关冲突或限定关系。 |
| `environment_check_ref` | nullable RecordRef → environment-check | 是 | 适用时的精确形式导入兼容性。 |

## 环境兼容检查（EnvironmentCompatibility）

实际观察的形式导入兼容性，不是文字匹配。

Schema：[environment-check.schema.json](environment-check.schema.json)。对应任务：P4.2, P5.4。

| 字段 | 类型 / 值 | 必填 | 含义 |
|---|---|---|---|
| `source_environment_ref` | RecordRef → formal-environment | 是 | 原环境。 |
| `target_environment_ref` | RecordRef → formal-environment | 是 | 目标使用环境。 |
| `declarations` | array<string> | 是 | 精确导入声明。 |
| `outcome` | `INCOMPATIBLE` / `BLOCKED` / `COMPATIBLE` | 是 | 兼容性实测结果。 |
| `logs` | array<ArtifactRef> | 是 | 实际构建、导入证据。 |
| `assumption_comparison` | array<ParameterComparison> | 是 | 前提和定义对应。 |

## 未解决前沿（FrontierItem）

持久未解决问题及下一步所需证据。

Schema：[frontier-item.schema.json](frontier-item.schema.json)。对应任务：P5.5, P7.3。

| 字段 | 类型 / 值 | 必填 | 含义 |
|---|---|---|---|
| `target_refs` | array<RecordRef> | 是 | 精确受影响目标。 |
| `kind` | `MISSING_SOURCE` / `UNPROVED_LEMMA` / `SCOPE_AMBIGUITY` / `ALIGNMENT_GAP` / `MODEL_ASSUMPTION` / `DATA_MISSING` / `CONFLICT` / `ENVIRONMENT` / `RESOURCE_LIMIT` | 是 | 未解决边界类型。 |
| `axes` | array<`source_fidelity` / `mathematical_correctness` / `formal_alignment` / `semantic_applicability` / `empirical_support` / `computational_reproducibility`> | 是 | 受影响的适用轴。 |
| `statement` | string | 是 | 具体未解决问题。 |
| `next_evidence` | string | 是 | 能解决或缩小问题的证据。 |
| `attempt_refs` | array<RecordRef → work-attempt> | 是 | 精确先前尝试。 |
| `state` | `OPEN` / `BLOCKED` / `DEFERRED` / `RESOLVED` / `SUPERSEDED` | 是 | 保留历史的前沿生命周期。 |
| `resolution_refs` | array<RecordRef> | 是 | 已解决或替代时的证据。 |

## 论文候选清单（PaperAgentManifest）

独立论文审计之前固定的候选内容。

Schema：[release-manifest.schema.json](release-manifest.schema.json)。对应任务：P6.1。

| 字段 | 类型 / 值 | 必填 | 含义 |
|---|---|---|---|
| `source_ref` | RecordRef → source-snapshot | 是 | 精确论文来源。 |
| `scope_ref` | RecordRef → frozen-scope | 是 | 精确固定工作分母。 |
| `profile_ref` | RecordRef → processing-profile | 是 | 精确完成要求。 |
| `record_refs` | array<RecordRef> | 是 | 所有包内结构记录。 |
| `artifacts` | array<ArtifactRef> | 是 | 精确字节产物。 |
| `disposition_refs` | array<RecordRef → obligation-disposition> | 是 | 每个固定义务恰一个当前处置。 |
| `frontier_refs` | array<RecordRef → frontier-item> | 是 | 全部相关未解决边界。 |
| `contribution_refs` | array<RecordRef → contribution-delta> | 是 | 至少一条已评估、候选或阻塞的知识变化。 |
| `non_implications` | array<string> | 是 | 包完成的明确边界。 |

## 论文审计（ReleaseAudit）

对精确候选及范围的独立论文级审阅。

Schema：[release-audit.schema.json](release-audit.schema.json)。对应任务：P6.2。

| 字段 | 类型 / 值 | 必填 | 含义 |
|---|---|---|---|
| `manifest_ref` | RecordRef → release-manifest | 是 | 审计的精确固定候选。 |
| `review` | ReviewContext | 是 | 实际独立论文审计者。 |
| `ordered_target_refs` | array<RecordRef> | 是 | 按依赖顺序审计的目标。 |
| `assessment_refs` | array<RecordRef → axis-assessment> | 是 | 未被改写的精确所选评估。 |
| `frontier_refs` | array<RecordRef → frontier-item> | 是 | 完整保留前沿。 |
| `recommendation` | `DO_NOT_RELEASE` / `RECOMMEND_PROFILE_RELEASE` | 是 | 相对标准的建议，不是论文真假。 |
| `findings` | array<string> | 是 | 公开审计发现与限制。 |

## 机械认证（ReleaseCertificate）

对精确候选、审计和权限政策的机械绑定。

Schema：[release-certificate.schema.json](release-certificate.schema.json)。对应任务：P6.3。

| 字段 | 类型 / 值 | 必填 | 含义 |
|---|---|---|---|
| `manifest_ref` | RecordRef → release-manifest | 是 | 被认证或拒绝的精确候选。 |
| `audit_ref` | RecordRef → release-audit | 是 | 精确独立审计。 |
| `checks` | array<string> | 是 | 实际执行的机械检查。 |
| `outcome` | `REJECTED` / `CERTIFIED` | 是 | 仅机械认证结果。 |
| `failed_checks` | array<string> | 是 | 所有失败的必需检查。 |

## 论文发布包（PaperAgentRelease）

清单、审计和认证之后创建的不可变聚合包。

Schema：[paper-release.schema.json](paper-release.schema.json)。对应任务：P6.1, P6.4。

| 字段 | 类型 / 值 | 必填 | 含义 |
|---|---|---|---|
| `manifest_ref` | RecordRef → release-manifest | 是 | 精确内容清单。 |
| `audit_ref` | RecordRef → release-audit | 是 | 精确论文审计。 |
| `certificate_ref` | RecordRef → release-certificate | 是 | 精确成功认证。 |
| `release_name` | string | 是 | 可读发布版本。 |
| `publication_uri` | nullable string | 是 | 实际公开发布位置；本地未公开包为空。 |

## 归档回执（ArchiveReceipt）

独立于知识准入的实际持久化回执。

Schema：[archive-receipt.schema.json](archive-receipt.schema.json)。对应任务：P6.4。

| 字段 | 类型 / 值 | 必填 | 含义 |
|---|---|---|---|
| `release_ref` | RecordRef → paper-release | 是 | 精确归档包。 |
| `objects` | array<ArtifactRef> | 是 | 已检查持久化的字节。 |
| `checkpoint_ref` | nullable RecordRef → event-checkpoint | 是 | 可用时的独立历史锚点。 |
| `assurance` | `LOCAL_PERSISTENCE` / `INDEPENDENTLY_ANCHORED` | 是 | 实际归档完整性边界。 |
| `location` | string | 是 | 实际归档位置。 |

## 逐条准入决定（AdmissionDecision）

对一个领域快照的精确候选集合做独立处置。

Schema：[admission-decision.schema.json](admission-decision.schema.json)。对应任务：P6.5。

| 字段 | 类型 / 值 | 必填 | 含义 |
|---|---|---|---|
| `release_ref` | RecordRef → paper-release | 是 | 精确来源包。 |
| `before_ref` | RecordRef → knowledge-snapshot | 是 | 精确事务输入快照。 |
| `review` | ReviewContext | 是 | 独立准入审阅。 |
| `items` | array<AdmissionItem> | 是 | 候选的完整互斥处置。 |
| `domain` | string | 是 | 科学复用领域。 |

## 知识快照（KnowledgeSnapshot）

保留精确记录、关系和冲突的不可变领域知识。

Schema：[knowledge-snapshot.schema.json](knowledge-snapshot.schema.json)。对应任务：P6.6, P6.7。

| 字段 | 类型 / 值 | 必填 | 含义 |
|---|---|---|---|
| `domain` | string | 是 | 领域和解释范围。 |
| `predecessor_ref` | nullable RecordRef → knowledge-snapshot | 是 | 旧不可变快照；初始快照为空。 |
| `entry_refs` | array<RecordRef> | 是 | 获准入库的来源、证据、定理或前沿记录。 |
| `relation_refs` | array<RecordRef → relation-assessment> | 是 | 包括冲突的已评估关系。 |
| `release_refs` | array<RecordRef → paper-release> | 是 | 精确支持论文包。 |
| `admission_refs` | array<RecordRef → admission-decision> | 是 | 授权新增的决定。 |

## 知识入库回执（KnowledgeIngestionReceipt）

完整候选划分的原子前后快照事务。

Schema：[ingestion-receipt.schema.json](ingestion-receipt.schema.json)。对应任务：P6.6。

| 字段 | 类型 / 值 | 必填 | 含义 |
|---|---|---|---|
| `before_ref` | RecordRef → knowledge-snapshot | 是 | 修改前比较的精确快照。 |
| `after_ref` | RecordRef → knowledge-snapshot | 是 | 结果快照；中止时必须相同。 |
| `decision_ref` | RecordRef → admission-decision | 是 | 精确接受、拒绝、阻塞划分。 |
| `candidate_refs` | array<RecordRef> | 是 | 完整事务候选全集。 |
| `accepted_refs` | array<RecordRef> | 是 | 全部且仅授权新增条目。 |
| `rejected_refs` | array<RecordRef> | 是 | 被拒绝候选。 |
| `blocked_refs` | array<RecordRef> | 是 | 仍被阻塞候选。 |
| `outcome` | `ABORTED` / `COMMITTED` | 是 | 实际原子事务结果。 |

## 事件记录（EventRecord）

绑定实际主体和上一事件的追加状态变更。

Schema：[event.schema.json](event.schema.json)。对应任务：P3.4, P6.4。

| 字段 | 类型 / 值 | 必填 | 含义 |
|---|---|---|---|
| `stream_id` | string | 是 | 精确事件流。 |
| `sequence` | integer | 是 | 连续递增流位置。 |
| `previous_ref` | nullable RecordRef → event | 是 | 精确前一事件；仅首事件为空。 |
| `operation` | string | 是 | 可归属状态变更。 |
| `target_refs` | array<RecordRef> | 是 | 精确受影响记录。 |
| `receipt_artifacts` | array<ArtifactRef> | 是 | 实际外部执行证据。 |

## 事件检查点（EventCheckpoint）

单独保存且明确可信边界的历史锚点。

Schema：[event-checkpoint.schema.json](event-checkpoint.schema.json)。对应任务：P6.4。

| 字段 | 类型 / 值 | 必填 | 含义 |
|---|---|---|---|
| `event_ref` | RecordRef → event | 是 | 精确被锚定事件。 |
| `anchor_artifact` | ArtifactRef | 是 | 实际检查点或签名证明字节。 |
| `holder_principal_id` | string | 是 | 在工作者之外保管检查点的主体。 |
| `assurance` | `LOCAL_COPY` / `INDEPENDENTLY_HELD` / `SIGNATURE_VERIFIED` | 是 | 实测锚定可信性，不从哈希推断。 |
| `verification_method` | string | 是 | 如何独立检查锚点。 |

## 影响分析（ImpactAnalysis）

类型化依赖影响，不改写历史评估。

Schema：[impact-analysis.schema.json](impact-analysis.schema.json)。对应任务：P7.2。

| 字段 | 类型 / 值 | 必填 | 含义 |
|---|---|---|---|
| `trigger_refs` | array<RecordRef> | 是 | 触发复核的新来源、证据、政策或采用版本。 |
| `dependency_refs` | array<RecordRef → dependency-binding> | 是 | 影响遍历使用的完整图输入。 |
| `affected` | array<ImpactTarget> | 是 | 精确受影响目标与轴。 |
| `unaffected_proof_plan_refs` | array<RecordRef → proof-plan> | 是 | 明确保留的独立路线。 |
| `algorithm` | string | 是 | 版本化确定性遍历算法。 |

## 修订记录（RevisionRecord）

保留旧身份的明确语义或表示变化。

Schema：[revision-record.schema.json](revision-record.schema.json)。对应任务：P2.5, P7.3。

| 字段 | 类型 / 值 | 必填 | 含义 |
|---|---|---|---|
| `old_ref` | RecordRef | 是 | 精确旧对象。 |
| `new_ref` | RecordRef | 是 | 精确新版本或派生对象。 |
| `change_kind` | `REPRESENTATION_CORRECTION` / `NEW_PROPOSITION` / `SCOPE_EXTENSION` / `ENVIRONMENT_CHANGE` / `ASSESSMENT_UPDATE` | 是 | 变化语义类型。 |
| `reason` | string | 是 | 公开差异及保留或改变身份的理由。 |
| `impact_ref` | nullable RecordRef → impact-analysis | 是 | 精确影响集合分析。 |
| `review` | ReviewContext | 是 | 独立身份和范围审阅。 |

## 旧版绑定（LegacyBinding）

不伪造历史或升级 V3 状态的精确旧版证据。

Schema：[legacy-binding.schema.json](legacy-binding.schema.json)。对应任务：P8.1。

| 字段 | 类型 / 值 | 必填 | 含义 |
|---|---|---|---|
| `legacy_contract` | string | 是 | 原 V1、V2 或研究契约身份。 |
| `legacy_artifact` | ArtifactRef | 是 | 未修改的旧版字节。 |
| `original_identity` | string | 是 | 原身份、修订和权威范围。 |
| `original_status` | string | 是 | 原状态含义及上下文。 |
| `v3_target_ref` | nullable RecordRef | 是 | 单独评估的 V3 对象。 |
| `missing_information` | array<string> | 是 | 缺失身份、审阅、核查轴或事件。 |
| `non_promotion` | `LEGACY_STATUS_PRESERVED` | 是 | 不自动升级状态。 |

## 查询回执（QueryReceipt）

基于精确知识的只读回答，保留相关冲突。

Schema：[query-receipt.schema.json](query-receipt.schema.json)。对应任务：P7.4, P7.6。

| 字段 | 类型 / 值 | 必填 | 含义 |
|---|---|---|---|
| `query` | string | 是 | 用于检索的用户请求，不修改正式记录。 |
| `knowledge_ref` | RecordRef → knowledge-snapshot | 是 | 精确查询知识快照。 |
| `mode` | `PACKAGE_BACKED` / `PROVISIONAL` | 是 | 回答权威边界。 |
| `returned_refs` | array<RecordRef> | 是 | 精确返回记录。 |
| `relation_refs` | array<RecordRef → relation-assessment> | 是 | 相关返回关系及反方端点。 |
| `assertions` | array<QueryAssertion> | 是 | 有精确支持记录的公开文字。 |
| `frontier_refs` | array<RecordRef → frontier-item> | 是 | 相关未解问题。 |
| `work_request_ref` | nullable RecordRef → agentization-plan | 是 | 触发时单独授权的工作计划。 |
| `canonical_mutation` | `FORBIDDEN` | 是 | 查询不能修改权威知识。 |

## 效果评估报告（EvaluationReport）

固定任务、标准与资源边界下的实测比较。

Schema：[evaluation-report.schema.json](evaluation-report.schema.json)。对应任务：P8.3, P8.4。

| 字段 | 类型 / 值 | 必填 | 含义 |
|---|---|---|---|
| `corpus` | ArtifactRef | 是 | 精确冻结评估集合。 |
| `profile_ref` | RecordRef → processing-profile | 是 | 比较使用的同一工作标准。 |
| `methods` | array<string> | 是 | 对比的处理方法。 |
| `attempt_refs` | array<RecordRef → work-attempt> | 是 | 提供测量的实际执行。 |
| `metrics` | array<Metric> | 是 | 带分母的实测结果。 |
| `limitations` | array<string> | 是 | 限制更强结论的对照缺失与不确定性。 |

## 来源请求（SourceRequest）

在取得任何来源字节前即可建立的文献请求。

Schema：[source-request.schema.json](source-request.schema.json)。对应任务：P2.1。

| 字段 | 类型 / 值 | 必填 | 含义 |
|---|---|---|---|
| `paper_id` | string | 是 | 所请求的精确作品身份。 |
| `paper_version` | string | 是 | 明确版本，不允许最新版本别名。 |
| `source_uri` | string | 是 | 请求的来源位置。 |
| `allowed_hosts` | array<string> | 是 | 明确允许的取得主机。 |
| `max_bytes` | integer | 是 | 响应字节上限。 |
| `timeout_seconds` | integer | 是 | 请求时长上限。 |

## 来源取得报告（SourceAcquisition）

实际取得成功或失败，包括尚无来源快照时的失败。

Schema：[source-acquisition.schema.json](source-acquisition.schema.json)。对应任务：P2.1。

| 字段 | 类型 / 值 | 必填 | 含义 |
|---|---|---|---|
| `request_ref` | RecordRef → source-request | 是 | 精确请求与取得政策。 |
| `outcome` | `FAILED` / `BLOCKED` / `ACQUIRED` | 是 | 实际取得结果，不是来源忠实性。 |
| `started_at` | string | 是 | 实际请求开始时间。 |
| `finished_at` | string | 是 | 实际请求结束时间。 |
| `artifacts` | array<ArtifactRef> | 是 | 实际返回来源字节。 |
| `final_uri` | nullable string | 是 | 实际最终地址；未知为空。 |
| `transport_evidence` | array<ArtifactRef> | 是 | 保留的传输证据。 |
| `reason` | string | 是 | 成败条件与限制。 |

## 预先固定证据协议（EvidenceProtocol）

执行前固定的证据目标、输入及比较规则。

Schema：[evidence-protocol.schema.json](evidence-protocol.schema.json)。对应任务：P4.7, P8.3。

| 字段 | 类型 / 值 | 必填 | 含义 |
|---|---|---|---|
| `scope_ref` | RecordRef → frozen-scope | 是 | 精确工作义务分母。 |
| `obligation_ids` | array<string> | 是 | 本协议的证据工作义务。 |
| `target_refs` | array<RecordRef> | 是 | 精确主张或证据目标。 |
| `method` | `COMPUTATION` / `EMPIRICAL_ANALYSIS` / `CONTROLLED_COMPARISON` | 是 | 证据生产方法。 |
| `inputs` | array<ArtifactRef> | 是 | 执行前固定的数据、代码与配置。 |
| `environment` | ArtifactRef | 是 | 冻结执行环境。 |
| `comparison_rule` | string | 是 | 预先规定的容差或统计决定规则。 |
| `required_outcome` | `ACCOUNT_FOR` / `SUCCESS_REQUIRED` | 是 | 所需证据义务。 |

## 工作完成回执（WorkCompletion）

执行之后引用反向绑定尝试的结果，避免循环身份。

Schema：[work-completion.schema.json](work-completion.schema.json)。对应任务：P3.5, P4.3。

| 字段 | 类型 / 值 | 必填 | 含义 |
|---|---|---|---|
| `attempt_ref` | RecordRef → work-attempt | 是 | 精确先前执行记录。 |
| `result_refs` | array<RecordRef> | 是 | 后来产生且引用该执行的结果。 |
| `limitations` | array<string> | 是 | 剩余产物或证据限制。 |

## 反例记录（CounterexampleRecord）

针对一个精确量化命题的具体反例。

Schema：[counterexample.schema.json](counterexample.schema.json)。对应任务：P3.5, P4.8。

| 字段 | 类型 / 值 | 必填 | 含义 |
|---|---|---|---|
| `target_ref` | RecordRef → scientific-claim, derived-claim, math-claim, argument-node | 是 | 被质疑的精确命题。 |
| `construction` | string | 是 | 明确数学实例或科学观测。 |
| `premise_checks` | array<ParameterComparison> | 是 | 实例满足目标前提及范围的理由。 |
| `violated_conclusion` | string | 是 | 被实例反对的精确目标结论。 |
| `evidence_refs` | array<RecordRef> | 是 | 推导、检查计算或观测支持。 |
| `limitations` | array<string> | 是 | 仍需独立审阅的条件。 |

## 跨记录校验与实现证据

参见 [INVARIANTS.md](INVARIANTS.md) 区分形状检查与完整语义/运行检查，[README.md](README.md) 查看命令，[执行状态](../docs/roadmaps/v3-execution-status.md) 查看有证据的进展。契约目录是版本化实验包，不代表这些服务已经全部实现。

