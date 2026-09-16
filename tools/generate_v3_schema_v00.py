#!/usr/bin/env python3
"""Generate the English V3 0.0.0 schemas and matched bilingual field reference.

The compact declarations below are the maintained source of truth. Generated
JSON contains English only; the Chinese descriptions live in SCHEMA.zh-CN.md.
No generated record or schema grants scientific or release authority.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'schema v0.0'
BASE = 'https://agtxiv.org/schema/v3/0.0.0/'
DRAFT = 'https://json-schema.org/draft/2020-12/schema'
AXES = ['source_fidelity', 'mathematical_correctness', 'formal_alignment',
        'semantic_applicability', 'empirical_support', 'computational_reproducibility']
MAX_INTEGER = 9007199254740991
DEFINITIONS: dict[str, dict] = {}
RECORDS: dict[str, dict] = {}


def ref(name: str) -> dict:
    return {'$ref': BASE + 'common.schema.json#/$defs/' + name}


def schema_type(code: str) -> dict:
    if code.startswith('nullable('):
        return {'anyOf': [schema_type(code[9:-1]), {'type': 'null'}]}
    if code.startswith('enum:'):
        return {'type': 'string', 'enum': code[5:].split(',')}
    if code.startswith('const:'):
        return {'const': code[6:]}
    if code.startswith('list:'):
        return {'type': 'array', 'items': schema_type(code[5:]), 'maxItems': 10000}
    if code.startswith('nonempty:'):
        return {**schema_type('list:' + code[9:]), 'minItems': 1}
    if code.startswith('r@'):
        kinds = code[2:].split('+')
        return {'allOf': [ref('RecordRef'), {'properties': {'record_type': {
            'enum': ['agtxiv.v3.' + k + '/0.0.0' for k in kinds]}}}]}
    primitives = {
        'text': {'type': 'string', 'minLength': 1, 'maxLength': 65536},
        'short': {'type': 'string', 'minLength': 1, 'maxLength': 4096},
        'string': {'type': 'string', 'maxLength': 65536},
        'int': {'type': 'integer', 'minimum': 0, 'maximum': MAX_INTEGER},
        'positive': {'type': 'integer', 'minimum': 1, 'maximum': MAX_INTEGER},
        'bool': {'type': 'boolean'},
        'digest': {'type': 'string', 'pattern': '^sha256:[0-9a-f]{64}$', 'minLength': 71, 'maxLength': 71},
        'id': {'type': 'string', 'pattern': '^[a-z][a-z0-9._-]*:[A-Za-z0-9][A-Za-z0-9._:/-]*(?![\\s\\S])', 'maxLength': 512},
        'uri': {'type': 'string', 'format': 'uri', 'maxLength': 4096},
        'date': {'type': 'string', 'format': 'date-time', 'pattern': 'Z$', 'maxLength': 40},
        'commit': {'type': 'string', 'pattern': '^[0-9a-f]{40}([0-9a-f]{24})?(?![\\s\\S])', 'maxLength': 64},
        'axis': {'type': 'string', 'enum': AXES},
        'path': {'type': 'string', 'minLength': 1, 'maxLength': 4096,
                 'pattern': '^(?!/)(?!.*(?:^|/)\\.\\.?(?:/|$))(?!.*//)(?!.*\\\\)[^\\u0000-\\u001f]+(?![\\s\\S])'},
    }
    return dict(primitives[code]) if code in primitives else ref(code)


def fields(rows: str) -> dict:
    properties, required = {}, []
    for line in rows.strip().splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        key, kind, en, zh = [x.strip() for x in line.split('|', 3)]
        optional = key.endswith('?')
        key = key.rstrip('?')
        if key in properties:
            raise ValueError('duplicate field: ' + key)
        properties[key] = {**schema_type(kind), 'description': en, '_zh': zh}
        if not optional:
            required.append(key)
    return {'type': 'object', 'properties': properties, 'required': required, 'additionalProperties': False}


def common(name: str, en: str, zh: str, rows: str) -> None:
    DEFINITIONS[name] = {'title': name, 'description': en, '_zh': zh, **fields(rows)}


def record(name: str, title: str, zh: str, purpose: str, zh_purpose: str, tasks: str, rows: str) -> None:
    RECORDS[name] = {'title': title, 'zh': zh, 'purpose': purpose, 'zh_purpose': zh_purpose,
                     'tasks': tasks.split(','), 'payload': fields(rows)}


common('RecordRef', 'An exact immutable record reference, never a latest-version selector.', '精确不可变记录引用，不允许选择最新版本。', '''
record_type | short | Exact registered record discriminator. | 精确注册的记录类型。
record_id | id | Stable record lineage identity. | 记录谱系的稳定身份。
revision | positive | Exact immutable revision. | 精确不可变修订号。
content_hash | digest | Canonical complete-record hash excluding only content_hash. | 除 content_hash 外完整记录的规范化哈希。
''')
common('ArtifactRef', 'Identity of supplied raw bytes; a locator is not integrity evidence.', '原始字节的身份；地址本身不提供完整性证据。', '''
artifact_id | id | Stable artifact identity. | 文件或字节对象身份。
sha256 | digest | SHA-256 of unmodified raw bytes. | 未修改原始字节的 SHA-256。
byte_size | int | Exact byte length. | 精确字节长度。
media_type | short | Declared media type. | 媒体类型。
path_hint? | path | Relative display locator, never an authority selector. | 相对显示位置，不作为权威选择器。
''')
common('Producer', 'Attributed producer and its visible execution boundary.', '可归属的生产者及其可见执行边界。', '''
principal_id | id | Actual principal identity asserted by the execution record. | 执行记录声明的实际主体身份。
role | enum:SOURCE_PRODUCER,CLAIM_PRODUCER,ARGUMENT_PRODUCER,ARGUMENT_REVIEWER,FORMALIZER,FORMAL_CHECKER,BACKTRANSLATOR,ALIGNMENT_REVIEWER,SCIENTIFIC_REVIEWER,SCOPE_REVIEWER,PAPER_AUDITOR,CERTIFIER,ARCHIVE_SERVICE,ADMISSION_REVIEWER,KNOWLEDGE_SERVICE,QUERY_SERVICE,COORDINATOR,MAINTAINER,MIGRATION_SERVICE | Role used for this operation. | 本次操作承担的职责。
actor_kind | enum:HUMAN,AGENT,MECHANICAL_SERVICE | Producer class, not an assurance level. | 主体类别，不代表可信等级。
identity_assurance | enum:DECLARED,LOCALLY_ATTESTED,EXTERNALLY_ATTESTED | How identity was established; strings alone are not authentication. | 身份确认方式；字符串不是认证。
execution_id | id | Exact attributed execution. | 精确执行身份。
model? | short | Model identifier when an agent is used. | 使用 agent 时的模型标识。
visible_input_refs | list:RecordRef | Exact records visible to the actor. | 主体可见的精确记录。
identity_evidence | list:ArtifactRef | Independently supplied identity evidence. | 独立提供的身份凭据。
''')
common('ReviewContext', 'Declared independence plus exact reviewed input; a runtime must verify it.', '声明的独立性与精确审阅输入，运行层必须核实。', '''
reviewed_refs | nonempty:RecordRef | Exact records assessed by this decision. | 本决定评估的精确记录。
producer_principal_ids | nonempty:id | All actual producers of the reviewed content. | 被审内容所有实际生产者。
independence | enum:UNESTABLISHED,ROLE_SEPARATED,INDEPENDENTLY_ATTESTED | Review boundary, not a truth guarantee. | 审阅独立性边界，不保证结论为真。
conflicts | list:short | Known conflicts of interest or shared-model limitations. | 已知利益冲突或同模型局限。
method | text | Public review procedure. | 公开审阅方法。
evidence_refs | list:RecordRef | Evidence supporting the review. | 审阅依据。
''')
common('Condition', 'A material condition with provenance and interpretation.', '具有来源与解释的关键条件。', '''
condition_id | id | Stable condition identity within its parent record. | 父记录内的条件身份。
statement | text | Complete condition including range and quantifiers. | 保留范围与量词的完整条件。
origin | enum:SOURCE_EXPLICIT,SOURCE_RECONSTRUCTED,AGENT_ADDED,IMPORTED | Attribution of the condition. | 条件归属。
source_span_refs | list:r@source-span | Exact supporting source spans. | 支持条件的原文跨度。
''')
common('SourceUnit', 'An inventoried source object and its activity in the selected rendering.', '来源清点项及其在选定渲染中的活动性。', '''
unit_id | id | Source inventory item identity. | 来源清点项身份。
relative_path | path | Canonical relative path. | 规范相对路径。
artifact | ArtifactRef | Exact unmodified source bytes. | 精确原始来源字节。
activity | enum:ACTIVE,DORMANT,UNKNOWN | Participation in the designated rendering. | 是否参与指定渲染。
kind | enum:TEX,PDF,BIBLIOGRAPHY,FIGURE,TABLE,CODE,DATA,OTHER | Source object role. | 来源对象用途。
''')
common('StructureEdge', 'Document structure only, not mathematical inference.', '文档结构关系，不是数学推理。', '''
source_unit_id | id | Including or containing source unit. | 包含或引用端。
target_unit_id | id | Included or contained source unit. | 被包含或被引用端。
relation | enum:INCLUDES,CONTAINS,REFERENCES,CAPTION_OF | Document relation. | 文档关系。
activity | enum:ACTIVE,DORMANT,UNKNOWN | Static activity observation. | 静态活动性观察。
locator | short | Location of the relation in the source. | 关系出现位置。
''')
common('Obligation', 'One immutable processing obligation in a frozen denominator.', '冻结分母中的一项处理义务。', '''
obligation_id | id | Identity preserved across attempts. | 跨尝试保留的义务身份。
target_refs | list:RecordRef | Exact known targets; empty only for unresolved discovery items. | 已知精确目标；仅未解决发现项可为空。
source_unit_ids | nonempty:id | Source units covered by the obligation. | 所覆盖来源项。
stage | enum:SOURCE,INVENTORY,CLAIM,ARGUMENT,FORMAL,ALIGNMENT,SEMANTICS,EMPIRICAL,COMPUTATION,CONTRIBUTION,RELEASE | Required work stage. | 所需处理阶段。
requirement | enum:ACCOUNT_FOR,SUCCESS_REQUIRED | Accounting versus a required successful result. | 只需交代或必须成功。
applicable_axes | list:axis | Axes to which this work is relevant. | 工作相关核查轴。
reason | text | Why this obligation belongs in scope. | 纳入范围的理由。
''')
common('Component', 'An independently attributable part of a source proposition.', '原始命题中可独立归属的组成部分。', '''
component_id | id | Component identity within the claim. | 主张内组件身份。
text | text | Complete component meaning. | 完整组件含义。
role | enum:CONCLUSION,ASSUMPTION,DEFINITION,MODEL,APPROXIMATION,EVIDENCE,ATTRIBUTION,LIMITATION | Semantic role. | 语义角色。
source_span_refs | nonempty:r@source-span | Exact source anchors. | 精确原文位置。
''')
common('ComponentMapping', 'Total mathematical, semantic and unresolved accounting for one component.', '组件在数学、科学语义与未解决部分之间的完整记账。', '''
component_id | id | Exact component in the source claim. | 源主张中的精确组件。
math_refs | list:r@math-claim | Mathematical representations. | 数学表示。
semantic_refs | list:r@semantic-context | Scientific meanings retained separately. | 单独保留的科学含义。
evidence_refs | list:RecordRef | Evidence associated with this component. | 组件相关证据。
disposition | enum:MAPPED,RESIDUAL,UNRESOLVED,NON_CLAIM | Component disposition. | 组件处置。
residual | string | Exact meaning still outside the mapped representations. | 映射未涵盖的含义。
''')
common('MathObject', 'A mathematical carrier with definitions, units and conventions.', '含定义、单位与约定的数学对象。', '''
symbol | short | Fully scoped symbol. | 带范围的符号。
object_type | text | Mathematical carrier or type. | 数学载体或类型。
definition_refs | list:r@definition | Exact imported definitions. | 精确导入定义。
unit | string | Unit, or empty for a dimensionless object. | 单位；无量纲可为空。
convention | string | Normalization and interpretation convention. | 归一化和解释约定。
''')
common('Quantifier', 'Ordered binder; order is semantically significant.', '有序约束变量；顺序具有语义。', '''
kind | enum:FORALL,EXISTS,UNIQUE_EXISTS | Quantifier kind. | 量词类型。
variable | short | Bound variable name. | 被约束变量。
domain | text | Quantified domain with restrictions. | 含限制的量词范围。
''')
common('FormalDeclaration', 'An exact declaration observed in one formal environment.', '在一个形式环境中观察到的精确声明。', '''
name | short | Fully qualified declaration name. | 完整命名空间下的声明名。
statement | text | Elaborated or inspected declaration type. | 展开或检查过的声明类型。
source_artifact | ArtifactRef | Exact declaration source bytes. | 声明来源字节。
is_axiom | bool | Whether the declaration itself is an axiom. | 声明自身是否为公理。
axioms | list:short | Transitive axiom names reported by the checker. | 检查器报告的传递公理。
dependencies | list:short | Exact declaration dependency names in the fixed environment. | 固定环境中的声明依赖名。
''')
common('ParameterComparison', 'Explicit comparison of a reusable result with its target use.', '复用结果与目标用途的明确比较。', '''
dimension | enum:OBJECT,DEFINITION,QUANTIFIER,ASSUMPTION,CONCLUSION,UNIT,CONVENTION,REGIME,EVIDENCE,ENVIRONMENT | Compared dimension. | 比较维度。
source_value | text | Meaning on the reusable side. | 被复用端含义。
target_value | text | Meaning required by the target. | 目标所需含义。
relation | enum:EQUIVALENT,SOURCE_STRONGER,TARGET_STRONGER,INCOMPARABLE,UNKNOWN | Assessed comparison, not text similarity. | 评估的对应关系，不是文字相似度。
witness_refs | list:RecordRef | Evidence for the comparison. | 比较见证。
''')
common('AdmissionItem', 'One exact candidate and its admission decision.', '一个精确候选及其准入决定。', '''
candidate_ref | RecordRef | Exact proposed knowledge record. | 精确知识候选。
decision | enum:ACCEPT,REJECT,BLOCK | Admission disposition, not truth. | 准入处置，不是真假。
assessment_refs | list:r@axis-assessment+relation-assessment+argument-review | Relevant exact assessments. | 相关精确评估。
reason | text | Public admission rationale and conditions. | 公开准入理由与条件。
''')
common('ImpactTarget', 'One affected target with a typed and axis-limited reason.', '一个受影响目标及其类型化、按轴限定的原因。', '''
target_ref | RecordRef | Exact affected target. | 精确受影响目标。
axes | nonempty:axis | Axes needing review. | 需要重查的轴。
proof_plan_ref | nullable(r@proof-plan) | Affected proof route, if applicable. | 受影响证明方案。
reason | text | Why this target needs re-evaluation. | 需要重新评估的理由。
''')
common('QueryAssertion', 'Public answer text backed by exact records.', '有精确记录支持的公开回答。', '''
text | text | One load-bearing assertion in the answer. | 回答中的一个承重断言。
support_refs | nonempty:RecordRef | Exact records supporting the wording. | 支持表述的精确记录。
limitations | list:text | Scope and unresolved qualifications. | 范围与未解决限定。
''')
common('Metric', 'A measured value with a frozen denominator and comparison scope.', '有冻结分母和比较范围的测量值。', '''
name | short | Metric name, never a paper truth or quality score. | 指标名，不得作为论文真假或质量总分。
measurement_status | enum:NOT_MEASURED,MEASURED,UNDEFINED | Whether a value was observed and a ratio can be defined. | 是否实测以及比例是否有定义。
numerator | nullable(int) | Observed count; null when not measured. | 实测计数；未测时为空。
denominator | nullable(int) | Frozen eligible count; null when unknown and zero only for a measured empty set. | 冻结分母；未知为空，仅实测空集合用零。
unit | short | Measurement unit. | 测量单位。
method | text | Measurement protocol and scope. | 测量方法与范围。
''')
common('PdfRegion', 'A page-local locator in an exact PDF, not a fabricated raw-byte text span.', '精确 PDF 的页内定位，不伪造原始文本字节跨度。', '''
page_index | int | Zero-based page index. | 从零开始的页码。
x0 | short | Exact decimal left coordinate in normalized page units. | 归一化页面单位的精确十进制左坐标。
y0 | short | Exact decimal top coordinate. | 精确十进制上坐标。
x1 | short | Exact decimal right coordinate. | 精确十进制右坐标。
y1 | short | Exact decimal bottom coordinate. | 精确十进制下坐标。
''')

record('processing-profile','ProcessingProfile','处理标准','Versioned work obligations, including required success and permitted unresolved work.','版本化工作义务，区分必须成功与允许未解决。','P0.2,P1.3','''
name | enum:V3_SOURCE_MAP,V3_ARGUMENT_AUDIT,V3_FORMAL_SUPPORT | Named V3 processing profile. | V3 处理标准名称。
required_stages | nonempty:short | Stages every applicable scope must account for. | 每个适用范围必须交代的阶段。
success_required_stages | list:short | Stages whose required targets must actually succeed. | 要求目标实际成功的阶段。
required_axes | nonempty:axis | Applicable axes whose assessments are required. | 需要评估的适用轴。
allowed_terminal_outcomes | nonempty:short | Explicit permitted unresolved execution outcomes. | 允许的未解决执行处置。
empirical_requirement | enum:ACCOUNT_FOR,REVIEW_REQUIRED | Empirical work obligation. | 经验性工作要求。
computation_requirement | enum:ACCOUNT_FOR,REPRODUCTION_REQUIRED | Computational work obligation. | 计算工作要求。
non_implications | nonempty:text | What completion of this profile does not establish. | 满足标准不意味着什么。
''')
record('authority-policy','AuthorityPolicy','身份与权限政策','Versioned authority, separation and review requirements.','版本化权限、职责分离与审阅要求。','P0.1,P0.3,P1.6','''
charter_identity | const:AgtXIv-Charter/1.0 | Charter identity used as the design basis. | 设计依据的 Charter 身份。
charter_state | enum:PROPOSED,ADOPTED | Actual ratification state under governance. | 治理规定下的实际批准状态。
ratification_commit | nullable(commit) | Qualifying adoption commit only after ratification. | 批准后才可填写的有效提交。
minimum_identity_assurance | enum:LOCALLY_ATTESTED,EXTERNALLY_ATTESTED | Minimum runtime identity evidence for authoritative decisions. | 权威决定所需最低身份凭据。
separated_role_pairs | nonempty:short | Explicit incompatible roles on the same assessed artifact. | 同一被评对象上不兼容的角色组合。
human_review_triggers | nonempty:text | Scientific or governance conditions requiring a human reviewer. | 需人员审阅的科学或治理条件。
allowed_principal_ids | list:id | Principals authorized in this exact policy scope. | 本政策范围获授权的主体。
''')
record('source-snapshot','SourceSnapshot','来源快照','Immutable source bytes and acquisition boundary for one paper version.','一篇精确论文版本的原始字节及取得边界。','P2.1','''
paper_id | short | Exact bibliographic work identifier. | 精确作品标识。
paper_version | short | Explicit source version, never latest. | 明确来源版本，不允许 latest。
source_uri | uri | Acquisition location retained as provenance. | 留作履历的取得位置。
acquired_at | date | Time the bytes were acquired. | 字节取得时间。
acquisition_ref | nullable(r@source-acquisition) | Exact acquisition report when available; local legacy inputs may have no such history. | 可用时的精确取得报告；本地旧输入可能无此历史。
acquisition_method | enum:ARXIV_SOURCE,ARXIV_PDF,LOCAL_IMPORT,OTHER_EXACT_SOURCE | How these bytes were obtained. | 字节取得方式。
units | nonempty:SourceUnit | Complete supplied source inventory. | 完整的已提供来源清单。
archive | nullable(ArtifactRef) | Original source archive if available. | 原始源压缩包。
missing_material | list:text | Source material known to be absent. | 已知缺失材料。
rights_status | enum:KNOWN,UNRESOLVED,RESTRICTED | Recorded availability and reuse-rights boundary. | 可用性与复用许可边界。
rights_note | text | Public source and redistribution conditions. | 来源与再分发条件。
''')
record('source-span','SourceSpan','来源跨度','Exact source occurrence used to attribute a proposition or condition.','用于归属命题或条件的精确原文位置。','P2.2,P2.4','''
source_ref | r@source-snapshot | Exact source snapshot containing this occurrence. | 包含原文位置的精确快照。
artifact | ArtifactRef | Raw source bytes containing the occurrence. | 包含原文的原始字节。
locator_kind | enum:RAW_TEXT_BYTES,PDF_REGION,TRANSFORMED_TEXT | Exact source occurrence representation. | 精确原文位置表示方式。
byte_start | nullable(int) | Inclusive zero-based byte offset; null for a PDF page region. | 包含端点的零起点字节位置；PDF 页内区域为空。
byte_end | nullable(positive) | Exclusive byte offset, null for a PDF page region. | 不包含端点的字节终点；PDF 页内区域为空。
span_sha256 | nullable(digest) | Exact selected text-byte digest; null for a PDF page region. | 所选文本字节精确哈希；PDF 页内区域为空。
pdf_region | nullable(PdfRegion) | Page and box for a PDF occurrence. | PDF 位置的页码与区域。
transformation_ref | nullable(r@source-transformation) | Exact mapping when using derived text. | 使用派生文本时的精确映射。
locator | short | Human-readable page, line or label. | 页码、行号或标签等可读位置。
activity | enum:ACTIVE,DORMANT,UNKNOWN | Occurrence participation in the chosen source rendering. | 是否参与指定原文渲染。
''')
record('source-transformation','SourceTransformation','来源变换','An auditable mapping from raw material to a derived representation.','原始材料到派生表示的可审计映射。','P2.2','''
source_ref | r@source-snapshot | Exact source input. | 精确来源输入。
inputs | nonempty:ArtifactRef | Unmodified input bytes. | 未修改输入字节。
outputs | nonempty:ArtifactRef | Derived bytes with distinct identities. | 身份独立的派生字节。
method | text | Extraction, expansion or rendering procedure. | 提取、展开或渲染方法。
environment | text | Fixed tool and configuration identity. | 固定工具与配置身份。
mapping_artifact | ArtifactRef | Explicit source-to-output location map. | 明确的原文到输出位置映射。
limitations | list:text | Unresolved rendering or decoding ambiguity. | 未解决渲染或解码歧义。
''')
record('paper-structure','PaperStructure','论文结构','Source containment and activity, distinct from mathematical dependence.','来源包含及活动关系，与数学依赖分离。','P2.2','''
source_ref | r@source-snapshot | Exact source inventory. | 精确来源清单。
main_unit_id | id | Explicit chosen document entry point. | 明确选定文档入口。
edges | list:StructureEdge | Document structure relations. | 文档结构关系。
unclassified_unit_ids | list:id | Units whose activity or role could not be established. | 活动性或用途未知的来源项。
blockers | list:text | Parsing or source-activity limitations. | 解析或活动性限制。
''')
record('agentization-plan','AgentizationPlan','论文处理计划','Query-independent plan fixed before detailed discovery.','详细发现前固定、与查询无关的论文计划。','P1.3,P2.3','''
source_ref | r@source-snapshot | Exact planned paper source. | 精确计划来源。
profile_ref | r@processing-profile | Exact work requirements. | 精确工作要求。
baseline_ref | nullable(r@baseline-snapshot) | Prior knowledge selected for later comparison. | 后续比较所选旧知识。
source_unit_ids | nonempty:id | Fixed source denominator for discovery. | 来源发现的固定分母。
max_steps | positive | Maximum bounded work steps. | 有界工作最大步数。
max_seconds | positive | Maximum wall-clock work budget. | 工作时间上限。
max_cost_units | int | Declared integer resource budget. | 声明的整数资源预算。
no_progress_limit | positive | Consecutive unproductive attempts before deferral. | 停止前连续无进展尝试数。
trigger_note | text | Why work began; it does not define canonical scope. | 触发理由，不定义正式范围。
''')
record('inventory-discovery','InventoryDiscovery','全文发现记录','All source units classified before an independent scope decision.','独立范围决定前，对全部来源项进行分类。','P2.3,P2.6','''
plan_ref | r@agentization-plan | Exact discovery plan. | 精确发现计划。
structure_ref | r@paper-structure | Source structure used for discovery. | 用于发现的来源结构。
classified_unit_ids | list:id | Units assigned an explicit role. | 已分类来源项。
unclassified_unit_ids | list:id | Units still unresolved but retained in the denominator. | 未解决但仍保留在分母中的项。
obligations | nonempty:Obligation | Proposed complete work denominator. | 提议的完整工作分母。
claim_refs | list:r@scientific-claim | Candidate or attributed source propositions. | 候选或已归属原文命题。
coverage_rationale | text | Public account of completeness and exclusions. | 覆盖与排除的公开理由。
''')
record('scope-decision','ScopeFreezeDecision','范围冻结决定','Independent acceptance or blocking of an exact discovery.','对精确发现结果的独立接受或阻塞决定。','P2.6','''
discovery_ref | r@inventory-discovery | Exact discovery under review. | 被审的精确发现结果。
review | ReviewContext | Independent review boundary. | 独立审阅边界。
decision | enum:BLOCK,ACCEPT | Freeze decision, not scientific acceptance. | 冻结决定，不是科学认可。
reason | text | Public decision rationale. | 公开决定理由。
''')
record('frozen-scope','FrozenInventoryScope','冻结处理范围','Immutable work denominator after an independent freeze decision.','独立冻结决定之后的不可变工作分母。','P1.3,P2.5','''
plan_ref | r@agentization-plan | Exact governing plan. | 精确计划。
discovery_ref | r@inventory-discovery | Exact inventoried obligations. | 精确清点义务。
decision_ref | r@scope-decision | Accepting independent freeze decision. | 接受冻结的独立决定。
obligations | nonempty:Obligation | Exact obligations retained for total accounting. | 完整记账所需精确义务。
predecessor_ref | nullable(r@frozen-scope) | Previous immutable scope, if revised. | 修订前的不可变范围。
change_reason | text | Genesis reason or explicit scope extension/correction rationale. | 初始原因或明确扩展、纠错理由。
removed_obligation_dispositions | list:RecordRef | Explicit reviewed accounting for every removed prior obligation. | 所有被移除旧义务的明确审阅处置。
''')
record('obligation-disposition','ObligationDisposition','义务处置','Current disposition of one frozen obligation, retaining all attempts.','一项固定义务的当前处置，保留全部尝试。','P1.3','''
scope_ref | r@frozen-scope | Exact frozen denominator. | 精确冻结分母。
obligation_id | id | Exact obligation being accounted for. | 精确被记账义务。
outcome | enum:BLOCKED,DEFERRED,FAILED,COMPLETED,NOT_APPLICABLE | Execution accounting only. | 仅执行记账。
result_refs | list:RecordRef | Actual produced records, not invented placeholders. | 实际产物记录，不是虚构占位符。
attempt_refs | list:r@work-attempt | Exact work attempts. | 精确工作尝试。
reason | text | Outcome explanation and remaining boundary. | 处置说明与剩余边界。
previous_ref | nullable(r@obligation-disposition) | Prior immutable disposition. | 先前不可变处置。
''')
record('scientific-claim','ScientificClaim','科学主张','Source-faithful proposition preserving conditions, attribution and scientific scope.','保留条件、归属和科学范围的忠实原文命题。','P2.4,P2.5','''
statement | text | Complete independently revisable source proposition. | 可独立修订的完整原文命题。
source_span_refs | nonempty:r@source-span | Exact source occurrences supporting every material part. | 支持各关键部分的精确原文。
components | nonempty:Component | Independently addressable statement parts. | 可独立定位的主张部分。
conditions | list:Condition | All truth-relevant source conditions. | 所有影响真假判断的原文条件。
modality | enum:ASSERTED,CONJECTURED,OBSERVED,APPROXIMATE,CONDITIONAL,INTERPRETIVE | Source strength and modality. | 原文断言强度与语气。
attribution | text | Who asserts which part. | 谁断言哪部分。
system | text | Model, physical system or mathematical domain. | 模型、物理系统或数学域。
comparison_baseline | string | Source comparison baseline when asserted. | 原文声明的比较基准。
''')
record('derived-claim','DerivedClaim','系统派生命题','New proposition with explicit transformation and no fabricated source attribution.','明确变换来源、不伪造原文归属的新命题。','P2.5,P4.5','''
statement | text | Complete new proposition. | 完整新命题。
origin | enum:SYSTEM_DERIVATION,CONDITIONALIZATION,REPAIR,INDEPENDENT_PROPOSITION | Why a separate proposition exists. | 新命题产生原因。
parent_refs | list:r@scientific-claim+derived-claim+math-claim | Exact propositions from which it was derived or distinguished. | 派生或区分的精确原命题。
added_conditions | list:Condition | Conditions absent from the original proposition. | 原命题没有的新增条件。
relation | enum:DERIVES,SPECIALIZES,CORRECTS,ALTERNATIVE,INDEPENDENT | Declared relation requiring separate assessment. | 需独立评估的声明关系。
rationale | text | Public reason for the transformation. | 变换的公开理由。
''')
record('claim-component-map','ClaimComponentMap','主张组件对应','Complete mapped-or-residual accounting without scientific promotion.','完整映射或残余记账，不升级科学状态。','P2.4','''
claim_ref | r@scientific-claim | Exact original claim. | 精确原始主张。
mappings | nonempty:ComponentMapping | Exactly one accounting row for each source component. | 每个原文组件恰一条记账。
review | ReviewContext | Source-to-representation review. | 来源到表示的审阅。
coverage | enum:PARTIAL,COMPLETE | Mathematical/semantic accounting coverage, not truth. | 数学与语义记账覆盖，不是真假。
''')
record('semantic-context','SemanticContext','科学语义上下文','Scientific meaning, approximation and observable retained outside formal proof.','形式证明之外保留的科学含义、近似和可观测量。','P4.6','''
claim_ref | r@scientific-claim+derived-claim | Exact interpreted proposition. | 精确被解释命题。
physical_system | text | Intended physical or modeled system. | 目标物理或模型系统。
object_mapping | nonempty:ParameterComparison | Mathematical-to-scientific object correspondence. | 数学到科学对象的对应。
assumptions | list:Condition | Scientific model assumptions. | 科学模型假设。
approximation_regime | text | Range of validity and approximation conditions. | 有效范围和近似条件。
error_bound | string | Source-supported uncertainty or explicit unknown wording. | 有来源支持的误差或明确未知说明。
observables | list:text | Operational definitions of observed quantities. | 观测量操作定义。
limitations | list:text | Unresolved scientific meaning or applicability. | 未解决科学含义或适用性。
''')
record('definition','MathematicalDefinition','数学定义','Exact definition with carrier, convention and provenance.','具有载体、约定和来源的精确定义。','P1.4,P3.3','''
name | short | Definition name. | 定义名称。
statement | text | Complete mathematical definition. | 完整数学定义。
objects | nonempty:MathObject | Defined objects and carriers. | 所定义对象及载体。
source_span_refs | list:r@source-span | Source anchors; empty only for explicit system definitions. | 来源位置；系统定义才可为空。
origin | enum:SOURCE,IMPORTED,SYSTEM | Definition attribution. | 定义归属。
''')
record('math-claim','MathClaimIR','数学交接单','Exact mathematical target without mutable verification status.','不含可变验证状态的精确数学目标。','P1.4,P4.1','''
claim_ref | r@scientific-claim+derived-claim | Exact source or independently derived proposition. | 精确原文或独立派生命题。
component_ids | list:id | Mathematical components represented by this target. | 本目标表示的数学组件。
objects | nonempty:MathObject | Carriers, units and conventions. | 载体、单位和约定。
quantifiers | list:Quantifier | Ordered quantifiers. | 有序量词。
assumptions | list:Condition | Complete explicit mathematical premises. | 全部显式数学前提。
conclusion | text | Exact mathematical conclusion. | 精确数学结论。
exactness | enum:EXACT,APPROXIMATE,ASYMPTOTIC | Strength of the target. | 目标精确程度。
approximation_error | string | Error and regime when nonexact. | 非精确时的误差及范围。
definition_refs | list:r@definition | Exact mathematical definitions. | 精确数学定义。
semantic_refs | list:r@semantic-context | Scientific residual meaning. | 剩余科学含义。
normalization | text | Symbol and convention normalization with no scope change. | 不改变范围的符号、约定规范化。
''')
record('assumption-context','AssumptionContext','假设范围','Local assumptions and their nesting; discharge is an explicit inference.','局部假设及其嵌套；解除须明确推理。','P3.3,P3.6','''
parent_ref | nullable(r@assumption-context) | Enclosing context, never a cyclic parent. | 外层上下文，不允许循环。
assumptions | nonempty:Condition | Assumptions introduced in this context. | 本上下文引入的假设。
introduction_reason | text | Where and why these local premises enter. | 局部前提引入位置和原因。
allowed_use | text | Boundaries of valid use. | 有效使用边界。
''')
record('argument-node','ArgumentNode','论证节点','One attributed statement in a mathematical argument.','数学论证中的一条可归属陈述。','P3.2,P3.3','''
statement | text | Complete node proposition. | 完整节点命题。
kind | enum:CLAIM,DEFINITION,ASSUMPTION,LEMMA,CONSTRUCTION,CONCLUSION | Mathematical role. | 数学角色。
origin | enum:SOURCE,RECONSTRUCTED,REPAIRED,ALTERNATIVE,IMPORTED | Attribution of this argument content. | 论证内容归属。
claim_refs | list:r@scientific-claim+derived-claim+math-claim | Exact claim correspondence. | 精确主张对应。
context_ref | nullable(r@assumption-context) | Local assumption scope. | 局部假设范围。
definition_refs | list:r@definition | Definitions used by the node. | 节点使用的定义。
source_span_refs | list:r@source-span | Exact source support where applicable. | 适用时的精确原文支持。
''')
record('inference-step','InferenceStep','推理步骤','Joint-premise inference distinct from document containment.','多前提联合推理，与文稿包含关系分离。','P1.4,P3.3','''
premise_refs | list:r@argument-node | Jointly required premises, not separate entailments. | 共同前提，不是各自单独蕴含。
conclusion_ref | r@argument-node | Exact concluded node. | 精确结论节点。
rule | enum:DIRECT,MODUS_PONENS,DEFINITIONAL,CONTRADICTION,INDUCTION,CASE_SPLIT,ASSUMPTION_DISCHARGE,EXTERNAL_RESULT | Explicit inference rule. | 明确推理规则。
justification | text | Public mathematical justification. | 公开数学理由。
context_ref | nullable(r@assumption-context) | Scope in which the inference is valid. | 推理有效范围。
discharged_context_refs | list:r@assumption-context | Exact contexts discharged by this step. | 本步骤解除的精确范围。
rule_evidence_refs | list:RecordRef | Witnesses for rule-specific conditions. | 推理规则条件的见证。
''')
record('proof-plan','ProofPlan','证明方案','One independent route supporting a conclusion.','支持结论的一条独立证明路线。','P3.3,P4.5','''
scope_ref | r@frozen-scope | Exact frozen source of required proof obligations. | 必需证明义务所属的精确冻结范围。
conclusion_ref | r@argument-node | Exact target conclusion. | 精确目标结论。
route | enum:ORIGINAL,RECONSTRUCTED,REPAIRED,ALTERNATIVE | Attribution of the proof method. | 证明方法归属。
node_refs | nonempty:r@argument-node | Nodes participating in this route. | 本路线节点。
inference_refs | list:r@inference-step | Exact joint-premise steps. | 精确联合前提推理。
required_obligation_ids | list:id | Frozen proof obligations that cannot disappear on deletion. | 删除节点不能抹去的固定证明义务。
open_obligation_ids | list:id | Obligations still not discharged. | 尚未解除的义务。
''')
record('dependency-binding','DependencyBinding','依赖绑定','Exact use of a premise, definition or external result.','前提、定义或外部结果的一次精确使用。','P3.6,P5.4','''
dependent_ref | RecordRef | Exact object that needs the dependency. | 需要依赖的精确对象。
prerequisite_ref | RecordRef | Exact required input. | 精确所需输入。
kind | enum:MATHEMATICAL,DEFINITION,SCOPE,FORMAL_ENVIRONMENT,SEMANTIC,EMPIRICAL,COMPUTATIONAL,VALIDATION | Type governing review propagation. | 决定审查传播的依赖类型。
affected_axes | nonempty:axis | Axes affected by this dependency. | 该依赖影响的轴。
proof_plan_ref | nullable(r@proof-plan) | Proof route requiring this input. | 需要输入的证明路线。
comparison | nonempty:ParameterComparison | Exact assumption and object compatibility. | 精确前提与对象兼容性。
reuse_decision_ref | nullable(r@reuse-decision) | Separate authorization for the intended use. | 对目标用途的独立复用决定。
''')
record('challenge','Challenge','异议','Precisely targeted objection; a response does not resolve it.','精确定位的异议；回复不等于解决。','P3.5','''
target_ref | RecordRef | Exact questioned node, inference or binding. | 被质疑节点、推理或绑定。
category | enum:INFERENCE,SCOPE,DEFINITION,PROVENANCE,COUNTEREXAMPLE,ALIGNMENT,DEPENDENCY,AUTHORITY | Question category. | 问题类型。
severity | enum:CRITICAL,MAJOR,MINOR,NOTE | Review priority, not probability of error. | 审阅优先级，不是错误概率。
statement | text | Public concrete objection. | 公开具体异议。
evidence_refs | list:RecordRef | Supporting evidence for the objection. | 异议支持证据。
''')
record('challenge-disposition','ChallengeDisposition','异议处置','Independent disposition of an exact objection and response.','对精确异议与回复的独立处置。','P3.5,P3.7','''
challenge_ref | r@challenge | Exact original objection. | 精确原异议。
response | text | Public response without private model reasoning. | 公开回复，不包含模型私有思维链。
response_refs | list:RecordRef | Revised or additional mathematical evidence. | 修订或新增数学证据。
review | ReviewContext | Independent review of whether the objection is answered. | 是否解决异议的独立审阅。
outcome | enum:OPEN,RESOLVED,WITHDRAWN,SUPERSEDED,DISPUTED | Disposition retaining the original challenge. | 保留原异议的处置。
replacement_ref | nullable(r@challenge) | New objection if superseded. | 被替代时的新异议。
reason | text | Why the disposition applies to this exact revision. | 处置适用该版本的理由。
''')
record('argument-snapshot','ArgumentSnapshot','完整论证快照','Full fixed argument, not merely the upstream graph projection.','完整固定论证，而非仅上游图投影。','P3.2','''
scope_ref | r@frozen-scope | Exact query-independent argument work scope. | 精确且与查询无关的论证范围。
source_claim_refs | nonempty:r@scientific-claim+derived-claim | Exact argument targets. | 精确论证目标。
math_refs | list:r@math-claim | Fixed mathematical targets associated with the argument. | 关联的固定数学目标。
node_refs | nonempty:r@argument-node | Full node inventory. | 完整节点清单。
inference_refs | list:r@inference-step | Joint-premise inferences. | 联合前提推理。
context_refs | list:r@assumption-context | All local assumption scopes. | 全部局部假设范围。
proof_plan_refs | nonempty:r@proof-plan | Distinct proof routes. | 不同证明路线。
dependency_refs | list:r@dependency-binding | Full reference and definition dependencies. | 全部引用及定义依赖。
challenge_refs | list:r@challenge | All objections including archived paths. | 包括归档路线的所有异议。
challenge_disposition_refs | list:r@challenge-disposition | Complete known objection history. | 完整已知异议处置历史。
upstream_import_ref | nullable(r@upstream-import) | Exact preserved engine input; null for native arguments. | 精确保留的上游输入；原生论证可为空。
missing_items | list:text | Explicit incompleteness of this snapshot. | 本快照明确缺失项。
''')
record('argument-review','ArgumentReview','论证审阅','Independent argument assessment with explicit open obligations.','保留未解义务的独立论证评估。','P3.8','''
snapshot_ref | r@argument-snapshot | Exact complete review context. | 精确完整审阅上下文。
proof_plan_refs | nonempty:r@proof-plan | Routes actually reviewed. | 实际审阅的证明路线。
review | ReviewContext | Actual review identity and procedure. | 实际审阅身份和方法。
outcome | enum:INCONCLUSIVE,CONDITIONAL,SUPPORTED,COUNTEREVIDENCE | Scoped argument result, not kernel proof. | 有范围的论证结果，不是内核证明。
open_obligation_ids | list:id | Remaining load-bearing obligations. | 剩余承重义务。
open_challenge_refs | list:r@challenge | Unresolved relevant objections. | 未解决相关异议。
conditions | list:Condition | Conditions retained with the conclusion. | 结论保留的条件。
''')
record('upstream-import','UpstreamImport','上游导入记录','Preserved engine report and independently checked import boundary.','保留引擎原始报告及独立检查的导入边界。','P3.1,P3.2,P3.8','''
engine | const:vibefeld | Upstream engine identity. | 上游引擎身份。
commit | commit | Exact source commit. | 精确源码提交。
protocol_version | short | Exact supported export protocol. | 精确支持的导出协议。
adapter_version | short | Exact AgtXIv importer version. | 精确导入器版本。
ledger | nullable(ArtifactRef) | Raw event ledger, or null when unavailable. | 原始事件账本；缺失时为空。
graph | nullable(ArtifactRef) | Raw graph projection, or null when unavailable. | 原始图投影；缺失时为空。
context_artifacts | list:ArtifactRef | Available scope, definitions, externals, identity and full objections. | 可取得的范围、定义、外部引用、身份和完整异议。
identity_map | nullable(ArtifactRef) | Exact identity mapping, null if unavailable. | 精确身份映射；缺失时为空。
reported_states | nullable(ArtifactRef) | Original reported states, null if unavailable. | 原始报告状态；缺失时为空。
import_checks | nonempty:short | Explicit checks that actually ran. | 实际执行的检查。
outcome | enum:INCOMPLETE,REJECTED,STRUCTURALLY_IMPORTED | Import result, never scientific support. | 导入结果，不是科学支持。
missing_items | list:text | Required upstream information absent. | 缺失的必要上游信息。
''')
record('work-attempt','WorkAttempt','工作尝试','Bounded attributable execution with measured resource use.','有界、可归属且记录资源使用的执行。','P3.5,P8.3','''
plan_ref | r@agentization-plan | Governing work budget. | 工作预算依据。
operation | short | Executed operation. | 执行操作。
target_refs | nonempty:RecordRef | Exact inputs or targets. | 精确输入或目标。
started_at | date | Execution start time. | 开始时间。
finished_at | date | Execution stop time. | 停止时间。
outcome | enum:FAILED,BLOCKED,DEFERRED,SUCCEEDED | Execution outcome without scientific promotion. | 不升级科学状态的执行结果。
output_refs | list:RecordRef | Already-created outputs only; records referring back to this attempt are listed by a later completion receipt. | 仅已生成输出；反向引用本尝试的记录由后置完成回执列出。
logs | list:ArtifactRef | Preserved public execution logs. | 保留的公开执行日志。
cost_units | int | Observed resource units. | 实测资源单位。
progress_observed | bool | Whether a new result or actionable diagnosis was obtained. | 是否获得新结果或可行动诊断。
''')
record('formal-environment','FormalEnvironment','形式环境','Exact toolchain, packages, build inputs and permitted trust policy.','精确工具链、依赖包、构建输入和可信政策。','P4.2,P4.3','''
prover | const:Lean4 | Formal checker family. | 形式检查器类别。
toolchain | short | Exact Lean toolchain identifier. | 精确 Lean 工具链标识。
package_manifest | ArtifactRef | Exact package commit lock. | 精确依赖提交锁。
source_artifacts | nonempty:ArtifactRef | All supplied formal build inputs. | 所有形式构建输入。
allowed_axioms | list:short | Explicit permitted axiom names. | 明确允许的公理名。
allowed_trust_mechanisms | list:short | Explicit additional accepted checker mechanisms. | 额外允许的检查机制。
command | nonempty:short | Argument-vector command, never an interpolated shell string. | 参数向量命令，不是插值 shell 字符串。
network_access | enum:DISABLED,CONTROLLED_ACQUISITION | Declared execution network boundary. | 声明的执行网络边界。
''')
record('formalization-packet','FormalizationPacket','形式化交接包','Fixed mathematical target, argument route, semantics and environment.','固定数学目标、论证路线、语义与环境。','P4.1','''
scope_ref | r@frozen-scope | Exact source of handoff obligations. | 交接义务所属精确范围。
math_ref | r@math-claim | Exact mathematical target. | 精确数学目标。
argument_ref | r@argument-snapshot | Exact complete argument snapshot. | 精确完整论证快照。
proof_plan_ref | r@proof-plan | Selected proof route. | 所选证明路线。
source_claim_refs | nonempty:r@scientific-claim+derived-claim | Exact original or derived targets. | 精确原文或派生目标。
semantic_refs | list:r@semantic-context | Residual scientific meaning. | 剩余科学含义。
environment_ref | r@formal-environment | Fixed checker environment. | 固定检查环境。
expected_declarations | nonempty:short | Required fully qualified output declarations. | 所需输出声明全名。
open_obligation_ids | list:id | Explicit unproved obligations at handoff. | 交接时未证义务。
mode | enum:EXPLORATORY,RELEASE_CANDIDATE | Work purpose; neither value grants authority. | 工作目的；均不授予权威。
''')
record('formalization-attempt','FormalizationAttempt','形式生成尝试','Generated formal files and diagnostics, distinct from independent checking.','生成的形式文件与诊断，与独立检查分离。','P4.1,P4.3','''
packet_ref | r@formalization-packet | Exact handoff. | 精确交接包。
attempt_ref | r@work-attempt | Exact generation run. | 精确生成执行。
outcome | enum:FAILED,PARTIAL,GENERATED | File-generation result only. | 仅文件生成结果。
artifacts | list:ArtifactRef | Actual generated source files. | 实际生成源码。
diagnostics | list:text | Public errors and unresolved work. | 公开错误与未解决工作。
''')
record('formal-check','FormalCheckRecord','形式检查记录','Independent target-level kernel and transitive axiom evidence.','独立目标级内核及传递公理证据。','P4.3','''
packet_ref | r@formalization-packet | Exact target handoff. | 精确目标交接。
attempt_ref | r@formalization-attempt | Files actually checked. | 实际被检查文件。
environment_ref | r@formal-environment | Exact checker environment. | 精确检查环境。
review | ReviewContext | Independence from formal source generation. | 与形式代码生产的独立性。
outcome | enum:FAILED,BLOCKED,KERNEL_CHECKED | Scoped observed checker result. | 有范围的检查器实测结果。
built_declarations | list:FormalDeclaration | Declarations actually inspected in the environment. | 在环境中实际检查的声明。
placeholder_findings | list:text | Detected unresolved placeholders or forbidden mechanisms. | 未解决占位符或禁止机制。
logs | nonempty:ArtifactRef | Independent checker and axiom-audit logs. | 独立检查与公理审计日志。
exit_code | int | Actual process exit code represented as a nonnegative integer. | 非负整数表示的实际进程退出码。
''')
record('backtranslation','BacktranslationRecord','独立反向解释','Formal statement interpretation with disclosed input visibility.','披露可见输入的形式声明反向解释。','P4.4','''
packet_ref | r@formalization-packet | Exact target packet identity, not permission to read source text. | 精确目标包身份，不代表允许读取原文。
formal_artifacts | nonempty:ArtifactRef | Formal statements and required definitions actually visible. | 实际可见的形式声明与必要定义。
visible_record_refs | list:RecordRef | Exact records visible to the interpreter. | 解释者实际可见记录。
source_blind | bool | Declared source blindness requiring execution evidence. | 需执行证据支持的来源盲化声明。
interpretation | text | What the formal statement means including assumptions. | 形式声明含义及前提。
conditions | list:Condition | Conditions found in the declaration. | 声明中的条件。
visibility_evidence | nonempty:ArtifactRef | Independent input-visibility evidence. | 独立输入可见性证据。
''')
record('alignment-assessment','AlignmentAssessment','含义对齐评估','One explicit semantic comparison with exact endpoints and independent review.','有精确端点和独立审阅的语义比较。','P4.4','''
comparison_kind | enum:SOURCE_TO_ARGUMENT,SOURCE_TO_MATH,MATH_TO_FORMAL,SOURCE_TO_FORMAL | Which alignment boundary was checked. | 检查的对齐边界。
source_refs | nonempty:RecordRef | Exact source-side objects. | 精确源侧对象。
target_refs | nonempty:RecordRef | Exact target-side objects. | 精确目标侧对象。
review | ReviewContext | Independent semantic review. | 独立语义审阅。
comparisons | nonempty:ParameterComparison | Quantifiers, types, assumptions, meaning and strength comparisons. | 量词、类型、前提、含义与强度比较。
outcome | enum:UNKNOWN,PARTIAL,MISALIGNED,ALIGNED | Scoped alignment only, not proof correctness. | 有范围的对齐，不是证明正确性。
backtranslation_refs | list:r@backtranslation | Independently generated formal interpretations. | 独立生成的形式解释。
''')
record('empirical-evidence','EmpiricalEvidence','经验证据','Observations, uncertainty and methods tied to exact scientific targets.','绑定精确科学目标的观测、不确定性与方法。','P4.7','''
target_refs | nonempty:r@scientific-claim+derived-claim+semantic-context | Exact scientific assumptions or conclusions examined. | 检查的精确科学前提或结论。
data | nonempty:ArtifactRef | Exact observation data. | 精确观测数据。
method | text | Data collection and analysis method. | 数据采集和分析方法。
population_regime | text | Population, system and applicable regime. | 群体、系统和适用范围。
uncertainty | text | Error model and uncertainty reporting. | 误差模型和不确定性报告。
limitations | list:text | Bias, missingness and generalization limits. | 偏倚、缺失与推广限制。
role | enum:ILLUSTRATIVE,SUPPORTING,LOAD_BEARING | Evidence importance to the stated conclusion. | 对结论的证据作用。
''')
record('reproduction-record','ReproductionRecord','计算复现记录','Observed reproduction result under a fixed procedure and comparison rule.','固定过程和比较规则下观察到的复现结果。','P4.7','''
protocol_ref | r@evidence-protocol | Exact comparison and input policy frozen before execution. | 执行前冻结的精确比较和输入政策。
attempt_ref | r@work-attempt | Execution whose fixed inputs included the protocol. | 固定输入包含该协议的执行。
target_refs | nonempty:RecordRef | Exact computational claims or artifacts. | 精确计算主张或产物。
code | nonempty:ArtifactRef | Exact executed code. | 精确执行代码。
inputs | nonempty:ArtifactRef | Exact data and parameter inputs. | 精确数据与参数输入。
environment | ArtifactRef | Exact environment and dependency description. | 精确环境和依赖说明。
command | nonempty:short | Executed argument-vector command. | 执行参数向量。
seeds | list:int | Random seeds or an empty list for a deterministic procedure. | 随机种子；确定性过程可为空。
comparison_rule | text | Predetermined tolerance or statistical comparison method. | 预先规定容差或统计比较方法。
outcome | enum:FAILED,BLOCKED,DISAGREEMENT,REPRODUCED | Reproduction result, not scientific validity. | 复现结果，不是科学有效性。
outputs | list:ArtifactRef | Actual produced numerical outputs. | 实际数值输出。
logs | nonempty:ArtifactRef | Exact independent execution evidence. | 精确独立执行证据。
''')
record('axis-assessment','AxisAssessment','单轴评估','Exactly one of the six Charter questions with bounded evidence.','以有界证据回答 Charter 六个问题之一。','P1.2,P4.8','''
target_refs | nonempty:RecordRef | Exact objects assessed on this axis. | 本轴评估的精确对象。
axis | axis | One independent Charter verification axis. | 一个独立 Charter 核查轴。
applicability | enum:UNDETERMINED,APPLICABLE,NOT_APPLICABLE | Whether this question applies to these targets. | 此问题是否适用目标。
result | enum:NOT_ASSESSED,INCONCLUSIVE,PARTIALLY_SUPPORTED,SUPPORTED,COUNTEREVIDENCE | Evidence conclusion, independent of execution success. | 证据结论，与执行成功独立。
execution | enum:DEFERRED,BLOCKED,FAILED,COMPLETED | What assessment work actually completed. | 实际评估工作处置。
method | enum:SOURCE_REVIEW,ARGUMENT_REVIEW,KERNEL_AND_ALIGNMENT,FORMAL_ALIGNMENT,SEMANTIC_REVIEW,EMPIRICAL_REVIEW,REPRODUCTION_REVIEW,COUNTEREXAMPLE_REVIEW,UNASSESSED | Evidence method and strength. | 证据方法和强度。
review | ReviewContext | Attributable independent assessment boundary. | 可归属独立评估边界。
support_refs | list:RecordRef | Exact supporting evidence. | 精确支持证据。
counterevidence_refs | list:RecordRef | Exact relevant contrary evidence. | 精确相关反对证据。
conditions | list:Condition | Conditions retained with this assessment. | 本评估保留的条件。
frontier_refs | list:r@frontier-item | Relevant unresolved problems. | 相关未解决问题。
rationale | text | Public scoped conclusion including non-applicability reasons. | 公开有界结论及不适用理由。
''')
record('status-view','StatusView','派生状态视图','Rebuildable six-axis view preserving all exact and conflicting assessments.','可重建六轴视图，保留所有精确与冲突评估。','P4.8,P7.4','''
target_ref | RecordRef | Exact queried subject. | 精确查询对象。
assessment_refs | list:r@axis-assessment | Full selected assessment evidence. | 完整所选评估证据。
conflicting_assessment_refs | list:r@axis-assessment | Independently inspectable disagreements. | 可独立检查的分歧。
axes | nonempty:axis | Exactly the six axes, each appearing once. | 六个轴恰各一次。
frontier_refs | list:r@frontier-item | Unresolved boundaries. | 未解决边界。
projection_method | text | Deterministic view policy, never a truth-score aggregation. | 确定性视图规则，不是真值评分。
''')
record('baseline-snapshot','BaselineSnapshot','比较基准快照','Fixed prior knowledge and search coverage for a contribution comparison.','贡献比较所用的固定旧知识与检索覆盖。','P5.1','''
knowledge_ref | nullable(r@knowledge-snapshot) | Exact previous knowledge snapshot, if available. | 精确旧知识快照。
entry_refs | list:RecordRef | Exact prior entries included in the comparison. | 比较中包含的精确旧条目。
domain | text | Scientific and mathematical comparison domain. | 科学和数学比较域。
selection_method | text | How the prior knowledge was chosen. | 旧知识选择方式。
search_coverage | text | Bounded retrieval sources, queries and coverage. | 有界检索来源、问题和覆盖。
limitations | nonempty:text | Known missing knowledge and non-priority implications. | 已知知识缺失及不代表优先权的限制。
''')
record('relation-assessment','RelationAssessment','关系评估','Witness-backed relation between exact claims or knowledge records.','精确主张或知识记录间有见证的关系。','P5.2','''
source_ref | RecordRef | Source endpoint; read source relation target. | 源端；读作源 relation 目标。
target_ref | RecordRef | Target endpoint, distinct from the source. | 与源端不同的目标端。
relation | enum:EQUIVALENT,SPECIALIZES,GENERALIZES,CORRECTS,QUALIFIES,REFUTES,SUPPORTS,INCOMPARABLE,CONFLICTING,SAME_OCCURRENCE,MATH_EQUIVALENT_SEMANTICS_DISTINCT | Exact typed relation. | 精确类型化关系。
review | ReviewContext | Independent relation assessment. | 独立关系评估。
comparisons | nonempty:ParameterComparison | Domain, assumption and semantic alignment witnesses. | 范围、前提和语义对应见证。
outcome | enum:PROPOSED,BLOCKED,DISPUTED,ACCEPTED,REJECTED | Relation assessment state, not endpoint truth. | 关系评估状态，不是端点真假。
witness_refs | list:RecordRef | Mathematical and scientific support. | 数学与科学支持。
''')
record('contribution-delta','ContributionDelta','贡献变化','Attributable knowledge change relative to one fixed baseline.','相对一个固定基准的可归属知识变化。','P5.3','''
baseline_ref | r@baseline-snapshot | Exact comparison baseline, not the later transaction snapshot. | 精确比较基准，不是之后事务快照。
current_refs | nonempty:RecordRef | This paper's exact result, method or evidence. | 本文精确结果、方法或证据。
prior_refs | list:RecordRef | Prior objects compared. | 比较的既有对象。
operation | enum:INTRODUCES,DERIVES,REPROVES,GENERALIZES,SPECIALIZES,WEAKENS_ASSUMPTIONS,CORRECTS,QUALIFIES,REFUTES,REPRODUCES,INDEPENDENTLY_VERIFIES,UNIFIES,APPLIES | Attributable type of change, not an importance score. | 可归属变化类型，不是重要性分数。
relation_refs | list:r@relation-assessment | Assessed comparison relations. | 已评估比较关系。
author_declaration | string | The paper's own novelty statement, attributed separately. | 单独归属的作者新颖性自述。
review | ReviewContext | Independent contribution evaluation. | 独立贡献评估。
outcome | enum:PROPOSED,BLOCKED,DISPUTED,SUPPORTED,REJECTED | Bounded delta assessment. | 有界变化评估。
qualifications | nonempty:text | Baseline coverage and unresolved limitations. | 基准覆盖与未解决限制。
''')
record('reuse-decision','ReuseDecision','用途复用决定','Permission to reuse an exact result for one specified target and evidence standard.','按指定目标和证据标准复用精确结果的决定。','P5.4','''
source_ref | RecordRef | Exact reusable result. | 精确可复用结果。
target_ref | RecordRef | Exact proposed target use. | 精确目标用途。
profile_ref | r@processing-profile | Evidence standard required by this use. | 此用途所需证据标准。
comparisons | nonempty:ParameterComparison | Required object, premise, scope, evidence and environment matching. | 必需的对象、前提、范围、证据和环境匹配。
assessment_refs | nonempty:RecordRef | Evidence and relation decisions supporting reuse. | 支持复用的证据与关系决定。
review | ReviewContext | Independent use-specific review. | 独立用途审阅。
outcome | enum:UNKNOWN,REJECT,CONDITIONAL,ALLOW | Use permission, not a new theorem proof. | 用途许可，不是新定理证明。
conditions | list:Condition | Remaining conditions required at the target. | 目标仍需满足的条件。
conflict_refs | list:r@relation-assessment | Relevant contradictory or limiting relations. | 相关冲突或限定关系。
environment_check_ref | nullable(r@environment-check) | Exact formal import compatibility when relevant. | 适用时的精确形式导入兼容性。
''')
record('environment-check','EnvironmentCompatibility','环境兼容检查','Observed exact formal import compatibility, never text matching.','实际观察的形式导入兼容性，不是文字匹配。','P4.2,P5.4','''
source_environment_ref | r@formal-environment | Original environment. | 原环境。
target_environment_ref | r@formal-environment | Intended use environment. | 目标使用环境。
declarations | nonempty:short | Exact declarations imported. | 精确导入声明。
outcome | enum:INCOMPATIBLE,BLOCKED,COMPATIBLE | Observed compatibility result. | 兼容性实测结果。
logs | nonempty:ArtifactRef | Actual build/import evidence. | 实际构建、导入证据。
assumption_comparison | nonempty:ParameterComparison | Assumptions and definition correspondence. | 前提和定义对应。
''')
record('frontier-item','FrontierItem','未解决前沿','Durable unresolved question and the precise next evidence needed.','持久未解决问题及下一步所需证据。','P5.5,P7.3','''
target_refs | nonempty:RecordRef | Exact affected targets. | 精确受影响目标。
kind | enum:MISSING_SOURCE,UNPROVED_LEMMA,SCOPE_AMBIGUITY,ALIGNMENT_GAP,MODEL_ASSUMPTION,DATA_MISSING,CONFLICT,ENVIRONMENT,RESOURCE_LIMIT | Type of unresolved boundary. | 未解决边界类型。
axes | nonempty:axis | Applicable affected axes. | 受影响的适用轴。
statement | text | Concrete unresolved issue. | 具体未解决问题。
next_evidence | text | What could resolve or narrow the issue. | 能解决或缩小问题的证据。
attempt_refs | list:r@work-attempt | Exact previous attempts. | 精确先前尝试。
state | enum:OPEN,BLOCKED,DEFERRED,RESOLVED,SUPERSEDED | Frontier lifecycle, preserving history. | 保留历史的前沿生命周期。
resolution_refs | list:RecordRef | Evidence when resolved or superseded. | 已解决或替代时的证据。
''')
record('release-manifest','PaperAgentManifest','论文候选清单','Exact candidate contents fixed before independent paper audit.','独立论文审计之前固定的候选内容。','P6.1','''
source_ref | r@source-snapshot | Exact paper source. | 精确论文来源。
scope_ref | r@frozen-scope | Exact fixed work denominator. | 精确固定工作分母。
profile_ref | r@processing-profile | Exact completion requirements. | 精确完成要求。
record_refs | nonempty:RecordRef | All packaged structured records. | 所有包内结构记录。
artifacts | list:ArtifactRef | Exact byte artifacts. | 精确字节产物。
disposition_refs | nonempty:r@obligation-disposition | One current disposition per frozen obligation. | 每个固定义务恰一个当前处置。
frontier_refs | list:r@frontier-item | All relevant unresolved boundaries. | 全部相关未解决边界。
contribution_refs | nonempty:r@contribution-delta | At least one assessed, provisional or blocked knowledge delta. | 至少一条已评估、候选或阻塞的知识变化。
non_implications | nonempty:text | Explicit boundaries of package completion. | 包完成的明确边界。
''')
record('release-audit','ReleaseAudit','论文审计','Independent paper-level review of the exact candidate and its scope.','对精确候选及范围的独立论文级审阅。','P6.2','''
manifest_ref | r@release-manifest | Exact fixed candidate under audit. | 审计的精确固定候选。
review | ReviewContext | Actual independent paper auditor. | 实际独立论文审计者。
ordered_target_refs | nonempty:RecordRef | Targets audited in dependency order. | 按依赖顺序审计的目标。
assessment_refs | nonempty:r@axis-assessment | Exact assessments selected without changing them. | 未被改写的精确所选评估。
frontier_refs | list:r@frontier-item | Complete retained frontier. | 完整保留前沿。
recommendation | enum:DO_NOT_RELEASE,RECOMMEND_PROFILE_RELEASE | Profile-scoped recommendation, not paper truth. | 相对标准的建议，不是论文真假。
findings | nonempty:text | Public audit findings and limits. | 公开审计发现与限制。
''')
record('release-certificate','ReleaseCertificate','机械认证','Mechanical binding of the exact candidate, audit and authority policy.','对精确候选、审计和权限政策的机械绑定。','P6.3','''
manifest_ref | r@release-manifest | Exact candidate certified or rejected. | 被认证或拒绝的精确候选。
audit_ref | r@release-audit | Exact independent audit. | 精确独立审计。
checks | nonempty:short | Mechanical checks actually performed. | 实际执行的机械检查。
outcome | enum:REJECTED,CERTIFIED | Mechanical result only. | 仅机械认证结果。
failed_checks | list:text | Every failed required check. | 所有失败的必需检查。
''')
record('paper-release','PaperAgentRelease','论文发布包','Immutable aggregate created after manifest, audit and certificate.','清单、审计和认证之后创建的不可变聚合包。','P6.1,P6.4','''
manifest_ref | r@release-manifest | Exact content manifest. | 精确内容清单。
audit_ref | r@release-audit | Exact paper audit. | 精确论文审计。
certificate_ref | r@release-certificate | Exact successful certificate. | 精确成功认证。
release_name | short | Human-readable publication version. | 可读发布版本。
publication_uri | nullable(uri) | Actual public release location, null for local unpublished packages. | 实际公开发布位置；本地未公开包为空。
''')
record('archive-receipt','ArchiveReceipt','归档回执','Actual persistence receipt independent of knowledge admission.','独立于知识准入的实际持久化回执。','P6.4','''
release_ref | r@paper-release | Exact package archived. | 精确归档包。
objects | nonempty:ArtifactRef | Bytes whose persistence was checked. | 已检查持久化的字节。
checkpoint_ref | nullable(r@event-checkpoint) | Independent history anchor if available. | 可用时的独立历史锚点。
assurance | enum:LOCAL_PERSISTENCE,INDEPENDENTLY_ANCHORED | Actual archive integrity boundary. | 实际归档完整性边界。
location | uri | Actual archive location. | 实际归档位置。
''')
record('admission-decision','AdmissionDecision','逐条准入决定','Independent disposition of an exact candidate set for one domain snapshot.','对一个领域快照的精确候选集合做独立处置。','P6.5','''
release_ref | r@paper-release | Exact source package. | 精确来源包。
before_ref | r@knowledge-snapshot | Exact intended transaction input snapshot. | 精确事务输入快照。
review | ReviewContext | Independent admission review. | 独立准入审阅。
items | nonempty:AdmissionItem | Total disjoint dispositions of the proposed candidates. | 候选的完整互斥处置。
domain | text | Scientific reuse domain. | 科学复用领域。
''')
record('knowledge-snapshot','KnowledgeSnapshot','知识快照','Immutable domain knowledge retaining exact records, relationships and conflicts.','保留精确记录、关系和冲突的不可变领域知识。','P6.6,P6.7','''
domain | text | Domain and interpretation scope. | 领域和解释范围。
predecessor_ref | nullable(r@knowledge-snapshot) | Previous immutable snapshot; null for genesis. | 旧不可变快照；初始快照为空。
entry_refs | list:RecordRef | Admitted source, evidence, theorem or frontier records. | 获准入库的来源、证据、定理或前沿记录。
relation_refs | list:r@relation-assessment | Assessed relations, including conflicts. | 包括冲突的已评估关系。
release_refs | list:r@paper-release | Exact backing paper packages. | 精确支持论文包。
admission_refs | list:r@admission-decision | Decisions authorizing additions. | 授权新增的决定。
''')
record('ingestion-receipt','KnowledgeIngestionReceipt','知识入库回执','Atomic before/after transaction with a total candidate partition.','完整候选划分的原子前后快照事务。','P6.6','''
before_ref | r@knowledge-snapshot | Exact snapshot compared before mutation. | 修改前比较的精确快照。
after_ref | r@knowledge-snapshot | Exact resulting snapshot, identical on abort. | 结果快照；中止时必须相同。
decision_ref | r@admission-decision | Exact accepted/rejected/blocked partition. | 精确接受、拒绝、阻塞划分。
candidate_refs | nonempty:RecordRef | Complete transaction candidate universe. | 完整事务候选全集。
accepted_refs | list:RecordRef | All and only authorized additions. | 全部且仅授权新增条目。
rejected_refs | list:RecordRef | Rejected candidates. | 被拒绝候选。
blocked_refs | list:RecordRef | Candidates still blocked. | 仍被阻塞候选。
outcome | enum:ABORTED,COMMITTED | Actual atomic transaction result. | 实际原子事务结果。
''')
record('event','EventRecord','事件记录','Append-only state transition with exact actor and previous-event binding.','绑定实际主体和上一事件的追加状态变更。','P3.4,P6.4','''
stream_id | id | Exact event stream. | 精确事件流。
sequence | positive | Monotonic contiguous stream position. | 连续递增流位置。
previous_ref | nullable(r@event) | Exact predecessor; null only for first event. | 精确前一事件；仅首事件为空。
operation | short | Attributed state transition. | 可归属状态变更。
target_refs | list:RecordRef | Exact affected records. | 精确受影响记录。
receipt_artifacts | list:ArtifactRef | Actual external execution evidence. | 实际外部执行证据。
''')
record('event-checkpoint','EventCheckpoint','事件检查点','Separately held history anchor with explicit assurance limitations.','单独保存且明确可信边界的历史锚点。','P6.4','''
event_ref | r@event | Exact anchored event. | 精确被锚定事件。
anchor_artifact | ArtifactRef | Actual checkpoint or signed attestation bytes. | 实际检查点或签名证明字节。
holder_principal_id | id | Principal retaining the checkpoint outside the worker. | 在工作者之外保管检查点的主体。
assurance | enum:LOCAL_COPY,INDEPENDENTLY_HELD,SIGNATURE_VERIFIED | Observed anchoring assurance, not inferred from hashes. | 实测锚定可信性，不从哈希推断。
verification_method | text | How the anchor was independently checked. | 如何独立检查锚点。
''')
record('impact-analysis','ImpactAnalysis','影响分析','Typed dependency impact without silently rewriting historical assessments.','类型化依赖影响，不改写历史评估。','P7.2','''
trigger_refs | nonempty:RecordRef | New source, evidence, policy or adopted version triggering review. | 触发复核的新来源、证据、政策或采用版本。
dependency_refs | list:r@dependency-binding | Complete graph inputs used in impact traversal. | 影响遍历使用的完整图输入。
affected | list:ImpactTarget | Precisely affected targets and axes. | 精确受影响目标与轴。
unaffected_proof_plan_refs | list:r@proof-plan | Independent routes explicitly retained. | 明确保留的独立路线。
algorithm | short | Versioned deterministic traversal. | 版本化确定性遍历算法。
''')
record('revision-record','RevisionRecord','修订记录','Explicit semantic or representational change with preserved old identity.','保留旧身份的明确语义或表示变化。','P2.5,P7.3','''
old_ref | RecordRef | Exact preceding object. | 精确旧对象。
new_ref | RecordRef | Exact replacement or derived object. | 精确新版本或派生对象。
change_kind | enum:REPRESENTATION_CORRECTION,NEW_PROPOSITION,SCOPE_EXTENSION,ENVIRONMENT_CHANGE,ASSESSMENT_UPDATE | Semantic type of change. | 变化语义类型。
reason | text | Public difference and why identity was retained or changed. | 公开差异及保留或改变身份的理由。
impact_ref | nullable(r@impact-analysis) | Exact affected-set analysis. | 精确影响集合分析。
review | ReviewContext | Independent identity and scope review. | 独立身份和范围审阅。
''')
record('legacy-binding','LegacyBinding','旧版绑定','Exact legacy evidence without fabricated history or stronger V3 status.','不伪造历史或升级 V3 状态的精确旧版证据。','P8.1','''
legacy_contract | short | Original V1/V2 or research contract identity. | 原 V1、V2 或研究契约身份。
legacy_artifact | ArtifactRef | Unmodified legacy bytes. | 未修改的旧版字节。
original_identity | text | Original IDs, revisions and bound authority. | 原身份、修订和权威范围。
original_status | text | Original meaning preserved literally with context. | 原状态含义及上下文。
v3_target_ref | nullable(RecordRef) | Optional separately evaluated V3 object. | 单独评估的 V3 对象。
missing_information | nonempty:text | Missing identity, review, axes or events. | 缺失身份、审阅、核查轴或事件。
non_promotion | const:LEGACY_STATUS_PRESERVED | No automatic status upgrade. | 不自动升级状态。
''')
record('query-receipt','QueryReceipt','查询回执','Read-only answer over exact knowledge with visible relevant conflict.','基于精确知识的只读回答，保留相关冲突。','P7.4,P7.6','''
query | text | User request used for retrieval, not canonical mutation. | 用于检索的用户请求，不修改正式记录。
knowledge_ref | r@knowledge-snapshot | Exact queried knowledge snapshot. | 精确查询知识快照。
mode | enum:PACKAGE_BACKED,PROVISIONAL | Authority boundary of the response. | 回答权威边界。
returned_refs | list:RecordRef | Exact returned records. | 精确返回记录。
relation_refs | list:r@relation-assessment | Relevant returned relations including opposing endpoints. | 相关返回关系及反方端点。
assertions | list:QueryAssertion | Public text with exact supporting records. | 有精确支持记录的公开文字。
frontier_refs | list:r@frontier-item | Relevant unresolved issues. | 相关未解问题。
work_request_ref | nullable(r@agentization-plan) | A separately authorized work plan, if triggered. | 触发时单独授权的工作计划。
canonical_mutation | const:FORBIDDEN | A query cannot change authoritative knowledge. | 查询不能修改权威知识。
''')
record('evaluation-report','EvaluationReport','效果评估报告','Measured comparisons under fixed tasks, profiles and resource boundaries.','固定任务、标准与资源边界下的实测比较。','P8.3,P8.4','''
corpus | ArtifactRef | Exact fixed evaluation set. | 精确冻结评估集合。
profile_ref | r@processing-profile | Identical work standard used for comparison. | 比较使用的同一工作标准。
methods | nonempty:text | Compared processing methods. | 对比的处理方法。
attempt_refs | nonempty:r@work-attempt | Actual runs providing measurements. | 提供测量的实际执行。
metrics | nonempty:Metric | Measured outcomes with denominators. | 带分母的实测结果。
limitations | nonempty:text | Missing controls and uncertainty preventing stronger claims. | 限制更强结论的对照缺失与不确定性。
''')

record('source-request','SourceRequest','来源请求','A bibliographic acquisition request that exists before any source bytes are available.','在取得任何来源字节前即可建立的文献请求。','P2.1','''
paper_id | short | Requested exact work identity. | 所请求的精确作品身份。
paper_version | short | Explicit version, never a latest alias. | 明确版本，不允许最新版本别名。
source_uri | uri | Requested source location. | 请求的来源位置。
allowed_hosts | nonempty:short | Explicit acquisition host allowlist. | 明确允许的取得主机。
max_bytes | positive | Maximum response bytes. | 响应字节上限。
timeout_seconds | positive | Maximum request duration. | 请求时长上限。
''')
record('source-acquisition','SourceAcquisition','来源取得报告','Observed acquisition success or failure, including failures before a snapshot exists.','实际取得成功或失败，包括尚无来源快照时的失败。','P2.1','''
request_ref | r@source-request | Exact request and acquisition policy. | 精确请求与取得政策。
outcome | enum:FAILED,BLOCKED,ACQUIRED | Actual acquisition outcome, not source fidelity. | 实际取得结果，不是来源忠实性。
started_at | date | Actual request start. | 实际请求开始时间。
finished_at | date | Actual request completion. | 实际请求结束时间。
artifacts | list:ArtifactRef | Actual returned source bytes. | 实际返回来源字节。
final_uri | nullable(uri) | Final observed URL, null if unavailable. | 实际最终地址；未知为空。
transport_evidence | list:ArtifactRef | Retained transport evidence. | 保留的传输证据。
reason | text | Failure or success conditions and limitations. | 成败条件与限制。
''')
record('evidence-protocol','EvidenceProtocol','预先固定证据协议','Evidence targets, inputs and comparison rules frozen before execution.','执行前固定的证据目标、输入及比较规则。','P4.7,P8.3','''
scope_ref | r@frozen-scope | Exact work obligation denominator. | 精确工作义务分母。
obligation_ids | nonempty:id | Evidence work obligations under this protocol. | 本协议的证据工作义务。
target_refs | nonempty:RecordRef | Exact claims or evidence targets. | 精确主张或证据目标。
method | enum:COMPUTATION,EMPIRICAL_ANALYSIS,CONTROLLED_COMPARISON | Evidence production method. | 证据生产方法。
inputs | nonempty:ArtifactRef | Data, code and configuration fixed before execution. | 执行前固定的数据、代码与配置。
environment | ArtifactRef | Frozen execution environment. | 冻结执行环境。
comparison_rule | text | Predetermined tolerance or statistical decision rule. | 预先规定的容差或统计决定规则。
required_outcome | enum:ACCOUNT_FOR,SUCCESS_REQUIRED | Required evidence obligation. | 所需证据义务。
''')
record('work-completion','WorkCompletion','工作完成回执','Post-execution reference to results that themselves refer to the attempt.','执行之后引用反向绑定尝试的结果，避免循环身份。','P3.5,P4.3','''
attempt_ref | r@work-attempt | Exact earlier execution record. | 精确先前执行记录。
result_refs | nonempty:RecordRef | Later created results referring to that execution. | 后来产生且引用该执行的结果。
limitations | list:text | Remaining production or evidence limitations. | 剩余产物或证据限制。
''')
record('counterexample','CounterexampleRecord','反例记录','A concrete counterexample against one exact quantified proposition.','针对一个精确量化命题的具体反例。','P3.5,P4.8','''
target_ref | r@scientific-claim+derived-claim+math-claim+argument-node | Exact proposition challenged. | 被质疑的精确命题。
construction | text | Explicit mathematical instance or scientific observation. | 明确数学实例或科学观测。
premise_checks | nonempty:ParameterComparison | Why the instance satisfies the target premises and domain. | 实例满足目标前提及范围的理由。
violated_conclusion | text | Exact target conclusion contradicted by the instance. | 被实例反对的精确目标结论。
evidence_refs | nonempty:RecordRef | Derivation, checked calculation or observational support. | 推导、检查计算或观测支持。
limitations | list:text | Conditions still needing independent review. | 仍需独立审阅的条件。
''')


def clean(value):
    if isinstance(value, dict):
        return {k: clean(v) for k, v in value.items() if not k.startswith('_')}
    if isinstance(value, list):
        return [clean(v) for v in value]
    return value


def envelope(name: str, item: dict) -> dict:
    body = fields('''
record_type | short | Registered record type and exact contract version. | 注册的记录类型与精确契约版本。
record_id | id | Stable identity; semantic changes may require a new lineage. | 稳定身份；语义变化可能需要新谱系。
revision | positive | Exact immutable version within the lineage. | 谱系内精确不可变版本。
created_at | date | Attributable creation time in UTC. | 可归属的 UTC 创建时间。
data_class | enum:RESEARCH,OBSERVED,SYNTHETIC | Evidence origin, not an authority status. | 证据来源类别，不是权威状态。
schema_bundle_hash | digest | Exact manifest hash of the schema bundle. | schema 包清单精确哈希。
producer | Producer | Actual attributed producer and execution boundary. | 实际可归属生产者及执行边界。
policy_ref | nullable(r@authority-policy) | Exact authority policy; null only for bootstrap policy records. | 精确权限政策；仅自举政策记录可为空。
input_refs | list:RecordRef | Explicit exact inputs used to construct this record. | 构建记录使用的显式精确输入。
content_hash | digest | Canonical record hash excluding this one field only. | 仅排除此字段后的记录规范化哈希。
''')
    body['properties']['record_type'] = {'const': 'agtxiv.v3.' + name + '/0.0.0', 'description': 'Exact record discriminator.'}
    body['properties']['payload'] = item['payload']
    body['required'].append('payload')
    if name != 'authority-policy':
        body['properties']['policy_ref'] = {**schema_type('r@authority-policy'), 'description': 'Exact authority policy binding.', '_zh': '精确权限政策绑定。'}
    return {'$schema': DRAFT, '$id': BASE + name + '.schema.json', 'title': item['title'],
            'description': item['purpose'], **body}


def impose_rules(schemas: dict[str, dict]) -> None:
    def payload_rule(name, condition, then):
        schemas[name].setdefault('allOf', []).append({
            'if': {'properties': {'payload': condition}},
            'then': {'properties': {'payload': then}}})
    def equals(**values):
        return {'properties': {k: {'const': v} for k, v in values.items()}}
    payload_rule('authority-policy', equals(charter_state='PROPOSED'), equals(ratification_commit=None))
    payload_rule('authority-policy', equals(charter_state='ADOPTED'), {'properties': {'ratification_commit': schema_type('commit')}})
    for locator_kind in ['RAW_TEXT_BYTES','TRANSFORMED_TEXT']:
        payload_rule('source-span', equals(locator_kind=locator_kind), {'properties': {
            'byte_start': schema_type('int'), 'byte_end': schema_type('positive'),
            'span_sha256': schema_type('digest'), 'pdf_region': {'const':None}}})
    payload_rule('source-span', equals(locator_kind='RAW_TEXT_BYTES'), equals(transformation_ref=None))
    payload_rule('source-span', equals(locator_kind='TRANSFORMED_TEXT'), {'properties': {'transformation_ref':schema_type('r@source-transformation')}})
    payload_rule('source-span', equals(locator_kind='PDF_REGION'), {'properties': {
        'byte_start':{'const':None},'byte_end':{'const':None},'span_sha256':{'const':None},
        'pdf_region':ref('PdfRegion'), 'transformation_ref':{'const':None},
        'artifact':{'properties':{'media_type':{'const':'application/pdf'}}}}})
    payload_rule('axis-assessment', equals(applicability='NOT_APPLICABLE'), equals(result='NOT_ASSESSED'))
    payload_rule('axis-assessment', {'properties': {'result': {'enum': ['SUPPORTED', 'PARTIALLY_SUPPORTED']}}},
                 {'properties': {'support_refs': {'minItems': 1}, 'execution': {'const': 'COMPLETED'}, 'applicability': {'const': 'APPLICABLE'}}})
    payload_rule('axis-assessment', equals(result='COUNTEREVIDENCE'),
                 {'properties': {'counterevidence_refs': {'minItems': 1}, 'execution': {'const': 'COMPLETED'}, 'applicability': {'const': 'APPLICABLE'}}})
    payload_rule('axis-assessment', equals(method='UNASSESSED'), equals(result='NOT_ASSESSED'))
    for method,axis in {'SOURCE_REVIEW':'source_fidelity','ARGUMENT_REVIEW':'mathematical_correctness',
                       'KERNEL_AND_ALIGNMENT':'mathematical_correctness','FORMAL_ALIGNMENT':'formal_alignment',
                       'SEMANTIC_REVIEW':'semantic_applicability','EMPIRICAL_REVIEW':'empirical_support',
                       'REPRODUCTION_REVIEW':'computational_reproducibility'}.items():
        payload_rule('axis-assessment', equals(method=method), equals(axis=axis))
    payload_rule('formal-check', equals(outcome='KERNEL_CHECKED'), {
        'properties': {'built_declarations': {'minItems': 1, 'items': {'properties': {'is_axiom': {'const': False}}}},
                       'placeholder_findings': {'maxItems': 0}, 'exit_code': {'const': 0}}})
    payload_rule('release-certificate', equals(outcome='CERTIFIED'), {'properties': {'failed_checks': {'maxItems': 0}}})
    payload_rule('release-certificate', equals(outcome='REJECTED'), {'properties': {'failed_checks': {'minItems': 1}}})
    payload_rule('challenge-disposition', equals(outcome='SUPERSEDED'), {'properties': {'replacement_ref': schema_type('r@challenge')}})
    payload_rule('argument-review', equals(outcome='SUPPORTED'), {'properties': {'open_obligation_ids': {'maxItems': 0}, 'open_challenge_refs': {'maxItems': 0}}})
    payload_rule('relation-assessment', equals(outcome='ACCEPTED'), {'properties': {'witness_refs': {'minItems': 1}}})
    payload_rule('contribution-delta', equals(outcome='SUPPORTED'), {'properties': {'relation_refs': {'minItems': 1}}})
    payload_rule('upstream-import', equals(outcome='STRUCTURALLY_IMPORTED'), {'properties': {
        'missing_items': {'maxItems':0}, 'ledger':ref('ArtifactRef'),'graph':ref('ArtifactRef'),
        'identity_map':ref('ArtifactRef'),'reported_states':ref('ArtifactRef'),'context_artifacts':{'minItems':1}}})
    payload_rule('upstream-import', equals(outcome='INCOMPLETE'), {'properties': {'missing_items': {'minItems':1}}})
    payload_rule('source-acquisition', equals(outcome='ACQUIRED'), {'properties': {'artifacts':{'minItems':1},'final_uri':schema_type('uri')}})
    payload_rule('frontier-item', {'properties': {'state': {'enum': ['RESOLVED','SUPERSEDED']}}}, {'properties': {'resolution_refs': {'minItems': 1}}})
    profile=schemas['processing-profile']['properties']['payload']['properties']
    profile['required_axes'].update({'minItems':6,'maxItems':6,'uniqueItems':True})
    for profile_name,required in {
        'V3_SOURCE_MAP':['SOURCE','INVENTORY','CLAIM'],
        'V3_ARGUMENT_AUDIT':['SOURCE','INVENTORY','CLAIM','ARGUMENT','ALIGNMENT','SEMANTICS'],
        'V3_FORMAL_SUPPORT':['SOURCE','INVENTORY','CLAIM','ARGUMENT','FORMAL','ALIGNMENT','SEMANTICS'],
    }.items():
        payload_rule('processing-profile',equals(name=profile_name), {'properties': {
            'required_stages':{'allOf':[{'contains':{'const':s}} for s in required]},
            'success_required_stages':{'allOf':[{'contains':{'const':s}} for s in (
                ['SOURCE','INVENTORY','CLAIM','FORMAL','ALIGNMENT'] if profile_name=='V3_FORMAL_SUPPORT'
                else ['SOURCE','INVENTORY','CLAIM'])]}}})
    DEFINITIONS['Metric']['allOf']=[
        {'if':equals(measurement_status='NOT_MEASURED'),'then':equals(numerator=None,denominator=None)},
        {'if':equals(measurement_status='MEASURED'),'then':{'properties':{'numerator':schema_type('int'),'denominator':schema_type('positive')}}},
        {'if':equals(measurement_status='UNDEFINED'),'then':{'properties':{'numerator':schema_type('int'),'denominator':{'const':0}}}},
    ]
    p=schemas['status-view']['properties']['payload']['properties']['axes']
    p.update({'minItems': 6, 'maxItems': 6, 'uniqueItems': True})


def type_label(value: dict) -> str:
    if '$ref' in value:
        return value['$ref'].split('/')[-1]
    if 'const' in value:
        return '`' + str(value['const']) + '`'
    if 'enum' in value:
        return ' / '.join('`' + str(v) + '`' for v in value['enum'])
    if 'allOf' in value:
        enum = value['allOf'][1]['properties']['record_type']['enum']
        return 'RecordRef → ' + ', '.join(x.split('.')[2].split('/')[0] for x in enum)
    if 'anyOf' in value:
        return 'nullable ' + type_label(value['anyOf'][0])
    if value.get('type') == 'array':
        return 'array<' + type_label(value['items']) + '>'
    return value.get('type','object')


def field_table(shape: dict, zh=False) -> list[str]:
    lines = ['| 字段 | 类型 / 值 | 必填 | 含义 |' if zh else '| Field | Type / values | Required | Meaning |', '|---|---|---|---|']
    for key, value in shape['properties'].items():
        meaning = value.get('_zh',value.get('description','')) if zh else value.get('description','')
        required = ('是' if zh else 'yes') if key in shape['required'] else ('否' if zh else 'no')
        lines.append(f'| `{key}` | {type_label(value)} | {required} | {meaning.replace(chr(10), " ").replace("|", " / ")} |')
    return lines


EN_INTRO = '''# AgtXIv V3 schema v0.0 — complete contract reference

Status: experimental contract **0.0.0**, implementing the **V3 architecture**. The folder name is the user-selected `schema v0.0`; it is not a historical V0 architecture. JSON Schema dialect: Draft 2020-12. Schema titles, fields, enumerations and descriptions are English. The field-complete Chinese companion is [SCHEMA.zh-CN.md](SCHEMA.zh-CN.md).

Read the model as: exact paper → source claims and scientific context → revisable mathematical argument and fixed MathClaimIR → optional profile-required formal checking → six distinct evidence assessments → baseline-relative contributions and use-specific reuse → independently audited release → individually admitted knowledge → read-only queries and incremental review.

Schema validity establishes **shape only**. Exact bytes, references, complete frozen obligations, scope discharge, review independence, scientific alignment, real execution, conflict preservation and atomic transactions require cross-record validation or independent evidence. Every implementation report must distinguish contract coverage, tested mechanism, and scientific/operational acceptance. No fixture is a scientific approval.

## Shared envelope and identity

All records use a closed envelope and closed payload. Unknown properties and unknown record types are rejected; extension requires a new schema version. `record_id` identifies a lineage, `revision` fixes its version, and `content_hash` binds the complete record except that field. Reused canonicalization is NFC/LF normalized, integer-only JSON with exact safe-integer bounds, duplicate-key rejection and sorted keys. Floating-point scientific quantities are represented as exact strings with explicit units and interpretation. Raw source bytes are never normalized before artifact hashing.

The record discriminator selects an exact schema from the offline bundle manifest. `schema_bundle_hash` binds that manifest; `policy_ref` binds a supplied immutable AuthorityPolicy, except its explicit bootstrap case. Schema lookup never fetches the network. `input_refs` and all payload references form a supplied immutable record graph; unresolved or mismatched identities cannot be substituted by names or paths.

`data_class` records evidence origin: SYNTHETIC examples, RESEARCH experimental material or OBSERVED real input/run records. OBSERVED does not mean scientifically accepted. Actor identity fields are assertions until independently checked against a trusted runtime context. Local role separation is not institutional independence.

## Six independent questions

1. source_fidelity — whether the representation matches the exact source assertion;
2. mathematical_correctness — whether the exact conclusion follows from its explicit mathematical premises;
3. formal_alignment — whether the formal statement preserves the intended target;
4. semantic_applicability — whether objects, models, approximations and observables correspond to the intended scientific system;
5. empirical_support — what observations support or oppose the scientific assertion;
6. computational_reproducibility — whether the specified load-bearing computation can be regenerated.

Applicability, assessed result, and execution disposition are separate. An unsuccessful program is not a mathematical counterexample. An unattempted check is not automatically inapplicable. A passed formal statement does not itself support a source claim without explicit alignment. Conflicting assessments remain independently available.

## Public record dependency order

SourceSnapshot → SourceSpan / PaperStructure → ScientificClaim / SemanticContext / MathClaimIR → argument nodes, contexts and inferences → ArgumentSnapshot → review and FormalizationPacket → evidence and assessments → baseline-relative relations, contribution and reuse → release manifest → audit → certificate → release → admission decision → new knowledge snapshot → ingestion receipt.

A baseline may point to an earlier knowledge snapshot. A new snapshot points only to already-created admission decisions. Decisions bind the prior snapshot, never their unknown future snapshot. This avoids circular identity hashing. Later challenges, revised assessments and impact records append new records; they do not rewrite their targets.

## Common value structures
'''
ZH_INTRO = '''# AgtXIv V3 schema v0.0：完整中文契约说明

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
'''


def generate() -> dict[Path, bytes]:
    schemas = {name: envelope(name,item) for name,item in RECORDS.items()}
    impose_rules(schemas)
    DEFINITIONS['RecordRef']['properties']['record_type']['enum'] = ['agtxiv.v3.'+n+'/0.0.0' for n in RECORDS]
    common_schema = {'$schema': DRAFT, '$id': BASE+'common.schema.json', 'title': 'AgtXIv shared value types',
                     'description': 'Closed shared structures; no common value independently grants authority.', '$defs': DEFINITIONS}
    def encode(obj):
        return (json.dumps(clean(obj), ensure_ascii=True, indent=2)+'\n').encode()
    outputs={OUT/'common.schema.json':encode(common_schema)}
    for name,schema in schemas.items():
        outputs[OUT/(name+'.schema.json')]=encode(schema)
    outputs[OUT/'record.schema.json']=encode({'$schema':DRAFT,'$id':BASE+'record.schema.json',
        'title':'Any registered AgtXIv V3 record','description':'Closed union of all version 0.0.0 record families.',
        'oneOf':[{'$ref':BASE+n+'.schema.json'} for n in RECORDS]})
    manifest={'architecture_version':'V3','contract_version':'0.0.0','status':'EXPERIMENTAL',
        'canonicalization_profile':'agtxiv.record-canonical-json/2.0.0-candidate.1',
        'schemas':[{'path':p.name,'uri':json.loads(raw)['$id'],'sha256':'sha256:'+hashlib.sha256(raw).hexdigest(),
                    'record_type':('agtxiv.v3.'+p.name[:-12]+'/0.0.0') if p.name[:-12] in RECORDS else None}
                   for p,raw in sorted(outputs.items())],
        'record_count':len(RECORDS),'axes':AXES,
        'non_implications':['Schema validity is structural only.','No scientific, release or admission authority is granted.']}
    outputs[OUT/'manifest.json']=encode(manifest)
    en,zh=[EN_INTRO],[ZH_INTRO]
    for name,shape in DEFINITIONS.items():
        en.extend(['\n### '+name+'\n',shape['description']+'\n',*field_table(shape)])
        zh.extend(['\n### '+name+'\n',shape['_zh']+'\n',*field_table(shape,True)])
    common_envelope=schemas['scientific-claim'].copy()
    common_envelope['properties']=dict(common_envelope['properties'])
    common_envelope['properties']['record_type']={'type':'string','description':'Exact discriminator of the selected record family.', '_zh':'所选对象族的精确类型标识。'}
    common_envelope['properties']['payload']={'type':'object','description':'Closed family-specific fields documented below.', '_zh':'下文列出的对象专属封闭字段集合。'}
    common_envelope['properties']['policy_ref']={**schema_type('nullable(r@authority-policy)'), 'description':'Exact authority policy; null only for its bootstrap record.', '_zh':'精确权限政策；仅其自举记录可为空。'}
    en.extend(['\n## Record envelope\n',*field_table(common_envelope)])
    zh.extend(['\n## 记录通用封套\n',*field_table(common_envelope,True)])
    index=[]
    for n,item in RECORDS.items():
        index.append({'record_type':'agtxiv.v3.'+n+'/0.0.0','schema':n+'.schema.json','title':item['title'],'roadmap_tasks':item['tasks']})
        en.extend([f'\n## {item["title"]}\n',item['purpose']+'\n',f'Schema: [{n}.schema.json]({n}.schema.json). Roadmap: '+', '.join(item['tasks'])+'.\n',*field_table(item['payload'])])
        zh.extend([f'\n## {item["zh"]}（{item["title"]}）\n',item['zh_purpose']+'\n',f'Schema：[{n}.schema.json]({n}.schema.json)。对应任务：'+', '.join(item['tasks'])+'。\n',*field_table(item['payload'],True)])
    en.append('\n## Cross-record validation and implementation evidence\n\nSee [INVARIANTS.md](INVARIANTS.md) for checks that shape validation cannot perform, [README.md](README.md) for commands, and [the execution status](../docs/roadmaps/v3-execution-status.md) for evidence-backed implementation progress. The contract directory is a versioned experimental package; do not interpret schemas as already operationalized services.\n')
    zh.append('\n## 跨记录校验与实现证据\n\n参见 [INVARIANTS.md](INVARIANTS.md) 区分形状检查与完整语义/运行检查，[README.md](README.md) 查看命令，[执行状态](../docs/roadmaps/v3-execution-status.md) 查看有证据的进展。契约目录是版本化实验包，不代表这些服务已经全部实现。\n')
    outputs[OUT/'SCHEMA.md']=('\n'.join(en)+'\n').encode()
    outputs[OUT/'SCHEMA.zh-CN.md']=('\n'.join(zh)+'\n').encode()
    outputs[OUT/'catalog.json']=encode({'contract_version':'0.0.0','records':index})
    return outputs


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check',action='store_true',help='Fail if generated files differ; do not modify files.')
    args=parser.parse_args()
    outputs=generate()
    stale=[]
    for p,raw in outputs.items():
        if args.check:
            if not p.exists() or p.read_bytes()!=raw:
                stale.append(str(p.relative_to(ROOT)))
        else:
            p.parent.mkdir(parents=True,exist_ok=True)
            p.write_bytes(raw)
    if stale:
        parser.exit(1,'Generated files are stale:\n'+'\n'.join(stale)+'\n')
    print(f'{len(RECORDS)} record schemas; {len(DEFINITIONS)} shared structures; {len(outputs)} generated files '+('verified' if args.check else 'written'))


if __name__=='__main__':
    main()
