# 判定规则与正反例

本文件是 [AGENT.md](AGENT.md) 的规范性附件，与 Paper Agent、Autoformalization Agent 的 CONFORMANCE 同构。例子是人工教学材料，不是验证结果。文中"机器"只指 [check_interfaces.py](check_interfaces.py) 当前实际执行的规则；它一行解释文本都不读，不要把它读成内容保障。每条反例都注明哪一层拦得住：机器拦得住的给错误码，拦不住的写"人工"或"未接入"。

## 1. 冲突时的固定优先级

记录实际说了什么 → 这些记录把证据推到了哪一层 → 读者这次问的是什么 → 表达顺序与可读性。

前一项没定下来，不能用后一项补。读者听不懂不是把结论说得更肯定的理由；问题问得含糊不是替读者选一个更好回答的版本的理由。确实决定不了时，保留两种读法并在 `gaps` 写明歧义，不自行挑一个更方便的；宁可交一条"这里无法判断"的解释，也不交一条读起来顺但越过了记录的解释。

顺序只约束解释怎么组织，不改变记录本身。把一条记录读得更强、更弱或更窄，都是改写，不是解释。

## 2. `attribution` 的固定判定顺序

从上到下选第一个符合者。取值只有两个，`explanation-draft.schema.json` 的枚举里**没有任何表示独立的值**。

| 优先级 | 值 | 什么时候选 | 不表示什么 |
|---|---|---|---|
| 1 | `SELF_CHECK` | 本次解释的主体与被解释材料的生产者是同一个 | 不表示这次自查质量更低或更高；也不表示宿主已核对过主体身份 |
| 2 | `UNESTABLISHED` | 其余全部情形，包括自认为独立、以及不知道生产者是谁 | **不表示独立**。独立只能由宿主按 [I1–I6](<../Autoformalization Agent/AGENT.md>) 的 I1 与 [AGENT-CONTRACTS.md](../AGENT-CONTRACTS.md) §6 确立；即便确立了，独立 Reader 也不获得科学批准权 |

不确定属于哪一种时选 `UNESTABLISHED`，并在 `gaps` 写明"本次解释者与生产者的关系未经核对"。换一个模型名、换一次会话、换一台机器都不构成独立。

## 3. 最小正反例

### E01 业务记录直接放进 `records`

情形：解释过程中顺手把"读者版本的陈述"写成 `{"record_type": "agtxiv.v3.derived-claim/0.0.0", "payload": {...}}`，塞进 `records`，想和被解释对象一起保存。

- 应发生：拒绝。`reader.explain` 的 `output_record_types` 是空数组，读者版本的陈述只能留在 `text` 里。
- 禁止：把"顺手保存"当作便利；一条业务记录一旦落库就会被后续任务当作既有事实引用。
- 拦截：**机器（`SMUGGLED_RECORD` ×2 + `SCHEMA` ×2，exit 1）**。反夹带扫描在 schema 之前执行，因此它先被命名为夹带，再被报告为形状错误。固定在 [conformance/explanation-draft-smuggled.json](conformance/explanation-draft-smuggled.json)。

### E02 业务记录伪装成引用

情形：`basis_refs` 里放 `{"record_type": "agtxiv.v3.math-claim/0.0.0", "statement": "…"}`，或在一个合法 RecordRef 上多挂一个 `payload` 键。

- 应发生：拒绝。只有键集合恰好等于 `{record_type, record_id, revision, content_hash}` 的对象才是引用。
- 禁止：用"它看起来像引用"绕过空输出白名单；引用携带内容就不再是引用。
- 拦截：**机器（`SMUGGLED_RECORD`）**。扫描逐节点判定：任何 dict 含 `payload` 键即失败；任何 dict 含 `record_type` 而键集合不等于 `REF_KEYS` 即失败。测试见 `tests/test_interfaces.py` 的 `test_payload_anywhere_is_smuggling`、`test_record_type_outside_an_exact_ref_is_smuggling`。

### E03 自造字段承载结论

情形：草稿加一个顶层 `verdict: "SUPPORTED"`，或给某条 explanation 加 `confidence: 0.9`。

- 应发生：拒绝。草稿根字段恰好六项，explanation 项恰好五项，两层都是 `additionalProperties: false`。
- 禁止：用新字段给解释赋予判定语义；本模块没有、也不应该有任何结论字段。
- 拦截：**机器（`SCHEMA`）**。同理，模型自填 `record_id` / `revision` / `created_at` / `producer` / `content_hash` 也一律被拒——这些归宿主（I2）。

### E04 自报独立

情形：`attribution` 写成 `INDEPENDENTLY_ATTESTED` 或 `INDEPENDENT`；或原说明的生产者解释自己的输出却写 `UNESTABLISHED`，读者据此以为经过了第二双眼睛。

- 应发生：前者拒绝；后者应写 `SELF_CHECK`，并在文本里说明这是自查。
- 禁止：靠换模型名、换会话冒充独立；靠留白让读者自行推断独立。
- 拦截：前半**机器（`SCHEMA`，枚举里没有独立取值）**；后半**未接入**——检查器把声明值原样接受，`unchecked.attribution` 明写"是否同一主体产出被解释材料不检查"。真实防线是宿主身份核对，规则本体见 I1 与 [AGENT-CONTRACTS.md](../AGENT-CONTRACTS.md) §6。

### E05 把业务记录写成散文夹带

情形：结构上什么都没加，但 `text` 里逐字写进一条完整的 `{"record_type": …, "payload": …}`，或把一段新的数学陈述写成"读者版记录"，指望下游把它抄成记录。

- 应发生：解释只复述被解释记录说了什么；需要一条新记录时提 `follow_up_requests`，由有该输出白名单的 agent 产出。
- 禁止：用自然语言绕开空输出白名单；把"我在文本里写过"当作"系统里有这条记录"。
- 拦截：**未接入**。实测：把一条完整记录序列化成字符串放进 `text`，检查器 `checks_passed: true`。扫描只遍历 JSON 结构中的 dict，字符串内部不解析；`unchecked.explanation_quality` 已声明文本从不被读取。人工防线是下游装配只从 `records.json` 取记录，以及 [PENDING_TESTS.md](../PENDING_TESTS.md) 的 L-03。

### E06 通用讲解冒充项目事实

情形：还没有任何业务记录，交付一段"这类稳健度量一般不小于 1，所以本项目的结果也应当成立"的介绍：`target_ref` 为 `null`、`basis_refs` 为空、`gaps` 也为空。

- 应发生：拒绝。没有目标也没有依据时，必须在 `gaps` 里声明该说明未有业务证据支撑。
- 禁止：把一般性教学写成项目结论；用"读者需要背景"当作不声明缺口的理由。
- 拦截：**机器（`UNGROUNDED_EXPLANATION`，exit 1）**。空白字符串不算声明——`gaps: ["  "]` 同样被拒。固定在 [conformance/explanation-draft-ungrounded.json](conformance/explanation-draft-ungrounded.json)。

### E07 读者意见当成证据

情形：`text` 写"我读过这段论证，看上去是对的，可以当作已验证的结果使用"，`gaps` 清空。后续有人把这句话当作支持该 claim 的依据引用。

- 应发生：解释只能说证据到了哪一层（原文主张／数学候选已保存／论证快照已保存／机器检查已执行／独立审阅已完成），以及下一步缺什么。"看上去对"不是其中任何一层。
- 禁止：把可读性判断写成验证结论；把解释附件反向当作 claim 的支持证据。可读性通过不授予科学认可，也不解除证据依赖（[AGENT-CONTRACTS.md](../AGENT-CONTRACTS.md) §2.1）。
- 拦截：**未接入**。实测：该草稿在带 Task 的完整八层检查下 `checks_passed: true`。草稿没有判定字段，但没有任何机制阻止一句意见被写成散文后被人引用。`unchecked.opinion_as_support` 逐字声明了这一点，`tests/test_interfaces.py::test_known_gap_opinion_text_passes` 把它断言成"通过"，将来补上覆盖时该测试会响亮失败。实际防线是人工（L-03）与宿主只把独立审阅记录当证据。

### E08 只解释容易的目标

情形：Task 给了 `math-claim` 与 `definition` 两个目标，草稿只解释了前者。

- 应发生：拒绝。每个 `Task.target_ref` 至少对应一条 explanation；解释不了的目标也要绑定它，用 `text` 说明原因、用 `gaps` 列缺失依据。
- 禁止：跳过难的目标；把"没解释"留给读者自己发现。
- 拦截：**机器（`UNEXPLAINED_TARGET`，exit 1，需 `--task`）**。不给 Task 时这一层整层不执行，检查器在 `unchecked.task` 里说明。固定在 [conformance/task-unexplained-target.json](conformance/task-unexplained-target.json)。

### E09 引用 Task 没给的记录

情形：解释里把一条 `formal-check` 列进 `basis_refs`，声称"形式检查已经通过"，但这条记录本轮 Task 根本没提供。

- 应发生：拒绝。草稿里每个精确 RecordRef 都必须是 `Task.input_refs` 的成员。没拿到的记录只能写进 `gaps`。
- 禁止：为了让解释完整而补造引用；把"我知道有这么一条"当作"本轮可以引用"。
- 拦截：**机器（`INVISIBLE_REF`，需 `--task`）**。两个边界要说清：不给 `--task` 时同一份草稿 `checks_passed: true`；即便给了 Task，检查器也只核对"是否是本轮输入的精确成员"，**不核对这些记录是否真实存在**。同一身份同修订出现两个 `content_hash` 另由 `INCONSISTENT_REF` 拦截，那一层不需要 Task。

### E10 用后续请求提权或越界

情形：`follow_up_requests` 里加 `capabilities: ["records.write"]`；或写 `agent: "reader", operation: "review.argument"` 这种不存在的配对；或对 `review.backtranslate` 递交 `math-claim` 作为输入。

- 应发生：全部拒绝。后续请求只有 `agent` / `operation` / `input_refs` / `reason` 四个键，并且必须是 [agents.json](../agents.json) 注册的配对，输入族不得超出该 operation 的 `input_record_types` ∪ 上下文类型。
- 禁止：用自然语言在 `reason` 里要求提高预算、去掉回避或放行 EVIDENCE；scheduler 按既定规则接纳建议，不因措辞让步。
- 拦截：**机器**，三个码分工不同：提权字段判 `SCHEMA`（schema 里根本没有这些键）；配对不存在判 `FOLLOW_UP_OPERATION`；输入族越界或同身份两哈希判 `FOLLOW_UP_INPUT`。`review.backtranslate` 是唯一特例，只接受 `formal-environment`。检查器**不**核对目标 operation 的必需输入是否齐全，也不核对这些记录是否存在——那是 scheduler 的事。

### E11 把未知解释成否定或成功

情形：`text` 写"本轮没有搜索到反例，因此该命题成立"，或把"Lean 文件已生成"写成"已通过检查"。

- 应发生：分别说清作者声称、数学候选已保存、论证已快照、机器检查已执行、独立审阅已完成各到哪一步；未搜索到不是不存在，文件生成不是检查器接受。
- 禁止：用一个统一的"已验证"标签盖住混合状态；把 `DELIVERED` 读成科学成立（[AGENT-CONTRACTS.md](../AGENT-CONTRACTS.md) §2.1）。
- 拦截：**未接入**。实测该草稿 `checks_passed: true`。这是 [AGENT.md](AGENT.md) §5 五组状态的机器盲区，人工防线是 L-02。

### E12 悄悄丢掉已知缺口

情形：被解释记录自带三条未决事项，解释只写了最容易的一条，`gaps` 看起来是满的。

- 应发生：把已知缺口原样带到读者面前；解释是把缺口讲清楚，不是把它磨平。
- 禁止：为了让说明读起来完整而删缺口；把"读者不关心"当作删的理由。
- 拦截：**未接入**。`unchecked.gap_fidelity` 逐字声明：`gaps` 只被数数，从不与被解释记录的未决事项比对。实测：把两条真实缺口换成一条无意义的 `missing=nothing` 仍然 `checks_passed: true`。人工防线是 L-01 与宿主对照原记录。

### E13 在 Reader 任务上挂科学门

情形：Task 写 `acceptance: "EVIDENCE"`，或 `expected_record_types: ["frontier-item"]`，想让一次可读性检查充当证据关。

- 应发生：拒绝。可读性通过不构成证据；Reader 任务用 `DELIVERY`，业务输出预声明必须为空。
- 禁止：用"解释也是一种检查"把 Reader 放进证据链；用 Reader 的交付去满足别人的 EVIDENCE 门。
- 拦截：**机器**，且两层各自独立成立：本模块判 `EVIDENCE_GATE_ON_READER` / `NONEMPTY_EXPECTED_TYPES`，`../validate.py` 的 `Contracts.task` 另判 `TASK_CONTRACT`（EVIDENCE 任务必须指名业务输出，而 Reader 的输出白名单为空）。能力越权同样在 `TASK_CONTRACT` 一层被拒。

## 4. 一致性如何验收

三层分开报告，前一项通过不等于后一项通过。

1. **机械不变项**：草稿根字段固定、`records` 为空、无夹带、引用在本轮 Task 中、每个目标都有解释、后续请求的配对与输入族合法。检查器只覆盖它在 `checked` 里列出的层，`unchecked` 里的九项一概没查。
2. **内容覆盖**：逐目标比对解释与被解释记录——结论是否与记录一致、证据层级是否说对、被解释记录的未决事项是否全部出现在 `gaps` 里。范围内未覆盖的目标必须逐条列出。
3. **读者可跟随**：由真实读者按 [AGENT.md](AGENT.md) §4 的顺序阅读并回答"哪份来源、什么前提、检查到哪里、还缺什么"。这一层只能由人做（L-04）。

不用字数、术语命中率、JSON 文本相似度或"多个模型说法一致"当质量指标。多个模型可以一起把候选说成定理。

## 5. 现在可运行什么

以下命令在 2026-09-16 于仓库根目录实际执行，退出码为观测值。完整记录见 [validation-report.json](validation-report.json)。

```bash
R='schema v0.1/Reader Agent'
# 正例，不给 Task：exit 0，checked 5 层，unchecked 10 键（含动态追加的 task）
.venv/bin/python -B "$R/check_interfaces.py" --kind explanation --input "$R/conformance/explanation-draft.json"
# 正例，给 Task：exit 0，checked 8 层，unchecked 9 键
.venv/bin/python -B "$R/check_interfaces.py" --kind explanation --input "$R/conformance/explanation-draft.json" --task "$R/conformance/task.json"
# E01 夹带：exit 1
.venv/bin/python -B "$R/check_interfaces.py" --kind explanation --input "$R/conformance/explanation-draft-smuggled.json"
# E06 无依据：exit 1
.venv/bin/python -B "$R/check_interfaces.py" --kind explanation --input "$R/conformance/explanation-draft-ungrounded.json"
# E08 目标未覆盖：exit 1
.venv/bin/python -B "$R/check_interfaces.py" --kind explanation --input "$R/conformance/explanation-draft.json" --task "$R/conformance/task-unexplained-target.json"
# 输入不可读：exit 2
.venv/bin/python -B "$R/check_interfaces.py" --kind explanation --input "$R/AGENT.md"
# 本模块回归：exit 0，42 passed
.venv/bin/python -B -m pytest "$R/tests" -q -p no:cacheprovider
# 全包统一入口：exit 0，21 步全过（其中 reader-pytest 一步）
.venv/bin/python -B 'schema v0.1/tests/run_agent_tests.py'
```

退出码含义：0 表示**已执行的层**没发现问题，不表示合规、正确或可交付；1 表示在已执行的层里发现问题；2 表示输入不可读或检查器自身装载失败（例如草稿 schema 与 [agents.json](../agents.json) 的空输出白名单漂移），那是检查器／注册表的问题，不是被检查草稿的问题。

`../tests/run_agent_tests.py` 目前只把本模块的 pytest 套件接进去，上面六条 conformance 命令尚未接入统一入口；接入由该文件的所有者决定。跨整包直接跑 pytest 需要 `--import-mode=importlib`：本模块与 Autoformalization Agent 的测试文件同名为 `test_interfaces.py`，且两个 `tests/` 目录都没有 `__init__.py`，不加该参数会在收集阶段报 `import file mismatch` 并以 exit 2 中断。
