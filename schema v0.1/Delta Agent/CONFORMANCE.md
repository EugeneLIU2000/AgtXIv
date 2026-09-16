# 判定规则与正反例

本文件是 [AGENT.md](AGENT.md) 的规范性附件，与 [Paper Agent](<../Paper Agent/CONFORMANCE.md>)、[Autoformalization Agent](<../Autoformalization Agent/CONFORMANCE.md>) 的同名文件同构。例子是人工教学材料，不是任何论文的验证结果。文中「机器」**只**指 [check_interfaces.py](check_interfaces.py) 当前实际执行的规则；它比较的是引用身份，从不解析被引用的记录，因此看不出基准覆盖什么、prior 是否真的存在、关系是否真的见证这次比较。不要把它读成保障。

## 1. 冲突时的固定优先级

固定基准的实际覆盖 → 两端对象的精确身份 → 数学内容变化与仅记号变化之分 → 关系证据的独立性与见证 → `outcome` 强度。

前一项没确定时不得靠后一项补救：基准覆盖不明就不选更强的 `outcome`，两端身份不精确就不用"看起来同一个定理"合并。确实决定不了时，保留有边界的 `PROPOSED`／`BLOCKED`，把未决部分写成 `frontier-item` 与 `open_items`，并按 [INTERFACE §1](INTERFACE.md) 提 `follow_up_requests`；不自由选一个更方便的版本，也不改基准。

比较逐目标进行，每个目标逐维度交代：定义、假设与量词、结论、误差与适用范围、证明或证据方式。`contribution-delta` 的条数、新增节点数与 `relation_refs` 的条数都不是质量指标。

## 2. `outcome` 的固定判定顺序

从上到下选第一个符合者。枚举值取自[业务 schema](<../../schema v0.0/SCHEMA.md>) 的 `contribution-delta.payload.outcome`，不新造值。

| 优先级 | 值 | 什么时候选 | 不表示什么 |
|---|---|---|---|
| 1 | `BLOCKED` | 比较本身无法完成：基准覆盖不足以定位可比对象、必需的对应对象或关系证据缺失 | 不表示贡献为零；证据不足不写零贡献 |
| 2 | `REJECTED` | 实际比较已完成，且证据表明所声称的变化不成立（例如与基准内已有结论等价） | 不表示论文其余部分有误，也不表示该方向被否定 |
| 3 | `DISPUTED` | 实际比较已完成，但独立结论之间冲突未决 | 不表示已判定哪一方正确 |
| 4 | `SUPPORTED` | 有实际比较过的 prior，且有独立接受并见证该关系的 `relation-assessment` | 不表示优先权、全球首次、重要性或科学成立；交付语义见 [AGENT-CONTRACTS §2.1](../AGENT-CONTRACTS.md) |
| 5 | `PROPOSED` | 以上都不成立时的默认：有边界的提案 | 不表示"暂定通过"，也不是待升级的中间状态 |

`operation` 的 13 个值描述**变化类型**，不是强度分数：`INTRODUCES` 只表示在这一固定基准的覆盖范围内没有找到对应 prior，不是全球首次；`GENERALIZES`／`WEAKENS_ASSUMPTIONS`／`CORRECTS` 必须对应可指出的定义、假设或结论差异，不能由记号或表述差异充当。

## 3. 最小正反例

### E01 基准不是一个精确固定点

情形：Task 的 `input_refs` 里有两条 `baseline-snapshot`；或草稿根 `baseline_ref` 与 Task 里的唯一基准不是同一条；或某条 `contribution-delta` 挂了另一条基准。

- 应发生：一次比较只绑定一个精确基准；没有基准时先请 `dependency.search` 固定有边界的基准。
- 禁止：写 `null`、写"历史知识库"、按"最新一条"自选；同一草稿内各 delta 各挂各的基准。
- 拦截：机器（`TARGET_BASELINE`，需 `--task`；`BASELINE_MISMATCH`，无 Task 也生效）。基准里究竟覆盖了什么不解析（`unchecked.baseline_content`）。

### E02 基准被当成比较的一端

情形：`baseline_ref` 同时出现在 `current_refs` 或 `prior_refs` 中。

- 应发生：基准是量尺，两端是本次当前对象与实际 prior，三者互不相同。
- 禁止：用基准自身冒充 prior，制造"确实比较过"的外观。
- 拦截：机器（`BASELINE_AS_CURRENT`、`BASELINE_AS_PRIOR`）。

### E03 「本次检索未发现」写成贡献成立

情形：`prior_refs` 为空、`relation_refs` 为空，`outcome` 写 `SUPPORTED`，`author_declaration` 自称首次。[conformance/delta-draft-invalid.json](conformance/delta-draft-invalid.json) 就是这一条。

- 应发生：保留 `PROPOSED` 或 `BLOCKED`，把基准覆盖缺口写成 `qualifications` 与 `frontier-item`，并提 `dependency.search`。
- 禁止：把空集合读成"不存在"；空基准不是 `SUPPORTED` 的依据。
- 拦截：机器（`SUPPORTED_WITHOUT_PRIOR`、`SUPPORTED_WITHOUT_RELATION`）。这两条只看集合空不空（`unchecked.prior_art`）。

### E04 `relation_refs` 非空即当作已支持

情形：挂上一条端点不对、方向相反，或由被评估对象的生产者自己产出的 `relation-assessment`。

- 应发生：宿主核对关系端点、方向、见证、独立性与基准成员资格之后才采信；`relation-assessment` 只能来自独立的 `review.reuse`。
- 禁止：仅因 `relation_refs` 非空、或草稿 schema 合法就认为 `SUPPORTED` 成立。
- 拦截：人工＋宿主身份核对；机器只检查非空（`unchecked.relation_evidence`）。独立性条文见 I1（[I1–I6](<../Autoformalization Agent/AGENT.md>)）与 [AGENT-CONTRACTS §6](../AGENT-CONTRACTS.md)。

### E05 草稿自称独立

情形：`review.independence` 写 `INDEPENDENTLY_ATTESTED` 或 `ROLE_SEPARATED`；或原作者换用 Delta 模板、换个模型名后自评。

- 应发生：草稿只写 `UNESTABLISHED`，真实参与者照实填 `producer_principal_ids` 与 `conflicts`；正式归属由 host 判定。
- 禁止：把模板切换、进程切换或模型改名当作独立。
- 拦截：机器对枚举值（`DRAFT_REVIEW_UNESTABLISHED`，见 [conformance/delta-draft-invalid.json](conformance/delta-draft-invalid.json)）；真实主体是否分离**未接入**（`unchecked.execution_identity`），靠宿主与 I1。

### E06 多目标只比容易的一个

情形：Task 指派三个当前目标，草稿只给一条 `contribution-delta`，其余两个既不比较也不交代。[conformance/delta-draft.json](conformance/delta-draft.json) 配 [conformance/task-multi-target.json](conformance/task-multi-target.json) 就是这一条；[conformance/delta-draft-multi-target-covered.json](conformance/delta-draft-multi-target-covered.json) 是对应正例。

- 应发生：逐目标比较；暂时比不了的目标写进 `frontier-item.target_refs`，配 `open_items` 与 FollowUp。
- 禁止：交一个容易判断的目标就当作完成全部比较。
- 拦截：机器（`UNCOVERED_TARGET`，需 `--task`），错误信息逐个列出未覆盖的 `record_id`。**边界**：该规则的守卫是 `not deltas or not missing` —— 草稿里一条 `contribution-delta` 都没有时整条规则跳过，一份只有文字缺口的诊断草稿会通过。这一半**未接入**，对应 [PENDING_TESTS.md](../PENDING_TESTS.md) 的 G-07／DL-02，已在 [tests/test_delta_interfaces.py](tests/test_delta_interfaces.py) 固化为断言"通过"的特征测试。

### E07 同一条精确记录放在两侧

情形：`current_refs` 与 `prior_refs` 含同一条精确记录；或 `current_refs` 里同一条重复列两次。

- 应发生：两端是两条不同的精确记录；一个目标在一条 delta 内只列一次。
- 禁止：拿自己比自己制造"有差异"。
- 拦截：机器（`CURRENT_PRIOR_OVERLAP`、`DUPLICATE_CURRENT`）。**不覆盖**：同一 lineage 的两个不同 `revision` 分放两侧时身份不同，机器放行；这两版是否真的构成可比的前后关系属人工层。

### E08 事后换基准迎合结论

情形：先看到结果，再挑一个不含竞争工作的基准；或把旧基准换掉重开同一次比较。

- 应发生：基准开工时固定（[SCHEDULING.md](../SCHEDULING.md) §3 第 1 步）；覆盖不足就保留局限，新材料形成**新的**比较记录，旧判断保留。
- 禁止：改写旧基准，或把换基准后的结论套回旧记录。
- 拦截：**未接入**。草稿不带时间，检查器只比较引用身份，事后固定的基准与开工固定的基准在本检查器下完全一样（`unchecked.baseline_fixation_time`）。实际防线是宿主的登记时间与 `review.audit`。已固化为特征测试。

### E09 仅记号或表述变化记成内容变化

情形：换记号、换排版、重述同一命题，却记成 `GENERALIZES` 或 `INTRODUCES`。

- 应发生：先区分数学内容变化与仅记号变化；后者不算知识边界拓展，写成有边界的说明，必要时作为 `frontier-item`。
- 禁止：用 `operation` 枚举值的强弱暗示重要性。
- 拦截：**未接入**。13 个 `operation` 值只做枚举合法性校验，选哪一个从不判断（`unchecked.meaning`）。防线是人工与 `review.reuse`／`review.audit`。已固化为特征测试。

### E10 作者自述当成系统判断

情形：把 `author_declaration` 原样复制进 `qualifications`；或 `outcome` 直接跟随作者的"首次"表述；或 `qualifications` 填一句与基准覆盖无关的话。

- 应发生：作者自述原样留在 `author_declaration`（schema 不赋予它任何证据地位），系统判断分开写；`qualifications`（`minItems: 1`）写清基准覆盖范围与未解决局限。
- 禁止：用空白或套话充数；没有「无保留贡献」这种形状。
- 拦截：机器只拦全空白（`BLANK_QUALIFICATION`，见 [conformance/delta-draft-invalid.json](conformance/delta-draft-invalid.json)）。内容是否真的说明了覆盖缺口、是不是作者自述的复制件，**未接入**（`unchecked.qualification_meaning`）。已固化为特征测试。

### E11 `frontier-item` 声称已解决

情形：`state` 写 `RESOLVED` 或 `SUPERSEDED`，`resolution_refs` 为空。

- 应发生：给出精确解决证据，否则保持 `OPEN`／`BLOCKED`／`DEFERRED`；缺口不因为换了一轮就消失。
- 禁止：用状态字段代替证据。
- 拦截：机器（`FRONTIER_RESOLUTION`）。这是草稿层的**重实现**：草稿只 `$ref` v0.0 的 `properties.payload`，业务 schema 根层的 `if/then` 门不被继承（`unchecked.record_conditionals`），在本检查器之外装配的记录不受这一条保护。**不覆盖**：用一条 `OPEN` 的 `frontier-item` 一次挂上全部未比较目标即可满足 E06 的覆盖要求，这个缺口是否真实有边界，机器不判。

### E12 FollowUp 越界或引用尚不存在的对象

情形：`agent`／`operation` 不是 [agents.json](../agents.json) 里注册的配对；`input_refs` 含目标 operation 白名单外的族；同身份不同哈希；或引用一条本轮尚未落库的关系判断。

- 应发生：按注册配对与输入族提请求；关系判断先由 `review.reuse` 登记，再用真实引用重开 Delta 任务。
- 禁止：为了凑齐 `relation_refs` 而引用未来身份。
- 拦截：机器（`FOLLOW_UP_OPERATION`、`FOLLOW_UP_INPUT`；`review.backtranslate` 只允许 `formal-environment`）。给了 `--task` 时越界引用另由 `INVISIBLE_REF` 拦截。**不检查**引用的记录是否真实存在，也**不检查**目标 operation 的必需输入是否齐全（后者属 scheduler）。

## 4. 一致性如何验收

三层分开报告，前一层通过不等于后一层通过：

1. **机械不变项**：草稿根字段、`records` 类型分支与 payload 引用、草稿层规则（E01、E02、E03 的空集合部分、E05 的枚举、E06 的非空 delta 部分、E07、E10 的空白部分、E11、E12）、Task 绑定（唯一基准、预声明输出、精确可见输入）。检查器只覆盖它在 `checked` 中列出的层，`unchecked` 是发布给读者的边界声明，不是待办清单。
2. **内容覆盖**：逐目标、逐维度核对定义、假设与量词、结论、误差与适用范围、证据方式；基准局限逐条落到 `qualifications`；未比较目标逐条落到 `frontier-item`。范围内未配对的目标必须单列，不被"平均覆盖率"吸收。
3. **差异处置**：措辞不同而实质相同可接受；缺 prior、换基准、把记号变化当内容变化、把作者自述当判断必须报告。多个模型给出同一结论也可能一起错，最终对照基准与原始对象。

`delta` 条数、`relation_refs` 条数、新增节点数、文本相似度都不能单独作为质量指标。

## 5. 现在可运行什么

从仓库根目录运行，全部为 2026-09-16 实际执行过的命令：

```bash
.venv/bin/python -B 'schema v0.1/Delta Agent/check_interfaces.py' --kind delta \
  --input 'schema v0.1/Delta Agent/conformance/delta-draft.json'
.venv/bin/python -B 'schema v0.1/Delta Agent/check_interfaces.py' --kind delta \
  --input 'schema v0.1/Delta Agent/conformance/delta-draft-invalid.json'
.venv/bin/python -B 'schema v0.1/Delta Agent/check_interfaces.py' --kind delta \
  --input 'schema v0.1/Delta Agent/conformance/delta-draft.json' \
  --task 'schema v0.1/Delta Agent/conformance/task-multi-target.json'
.venv/bin/python -B 'schema v0.1/Delta Agent/check_interfaces.py' --kind delta \
  --input 'schema v0.1/Delta Agent/conformance/delta-draft-multi-target-covered.json' \
  --task 'schema v0.1/Delta Agent/conformance/task-multi-target.json'
.venv/bin/python -B 'schema v0.1/tests/run_agent_tests.py'
.venv/bin/python -B -m pytest 'schema v0.1/Delta Agent/tests' -q -p no:cacheprovider
```

观测结果：第一条与第四条 exit 0；第二条 exit 1，四个错误码 `DRAFT_REVIEW_UNESTABLISHED`、`SUPPORTED_WITHOUT_RELATION`、`SUPPORTED_WITHOUT_PRIOR`、`BLANK_QUALIFICATION`；第三条 exit 1，一个 `UNCOVERED_TARGET` 并列出 `math-claim:current-2, math-claim:current-3`；第五条 exit 0，21 项全部通过（其中 4 项是上面前四条命令）；第六条 exit 0，41 项通过。逐条的真实退出码见 [validation-report.json](validation-report.json)。

跨整个包运行 pytest 需要加 `--import-mode=importlib`：`Reader Agent/tests/test_interfaces.py` 与 `Autoformalization Agent/tests/test_interfaces.py` 基名相同，而 tests 目录没有 `__init__.py`。

退出码 0 只表示**已执行的层**没有发现问题；1 表示检查发现问题；2 表示输入或检查器装载错误。0 不等于"合规"，更不等于贡献成立或基准充分。不给 `--task` 时，Task 相关的四层明确记为未执行（`unchecked.task`），不是默认通过。
