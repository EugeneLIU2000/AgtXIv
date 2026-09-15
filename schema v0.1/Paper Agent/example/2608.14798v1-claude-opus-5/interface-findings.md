# 接口边界：本次运行在哪里停住，为什么

本文件只讲 `AGENT.md` + `schema v0.0` + `schema v0.1/validate.py` 三者在一次真实运行中相撞的地方。
每条结论都对应 [output/interface-checks.json](output/interface-checks.json) 里一次真实的校验调用，
可以用 `validate_run.py` 复现。**本文件不修改任何规范，也不建议立刻修改。**

## 1. 单主体运行必然在 S2 断链

AGENT.md S2 写得很清楚：发现者提出义务数（`inventory-discovery`），**由生产者之外的独立审阅者签署**
（`scope-decision`），然后锁定（`frozen-scope`）。schema 把这句话执行到了字面：

- `scope-decision.payload.review` 必填，`ReviewContext` 的 `reviewed_refs` 与 `producer_principal_ids`
  都至少一项，不能为空、不能为 null。
- `RecordSet._semantic`：记录自身的 `principal_id` 只要出现在 `review.producer_principal_ids` 里，
  就是 `SELF_REVIEW`。
- 同一处：`independence == 'UNESTABLISHED'` 且 `decision == 'ACCEPT'` 时，是 `INDEPENDENCE_UNESTABLISHED`。
- `frozen-scope` 要求 `decision == 'ACCEPT'`，否则 `UNACCEPTED_SCOPE`。

四个探针的实测结果（全部在真实引用闭包里跑，只筛出探针自身的问题）：

| 探针 | `principal_id` | `independence` | `decision` | 实测问题码 |
|---|---|---|---|---|
| a | 与发现者相同 | UNESTABLISHED | ACCEPT | `SELF_REVIEW`, `INDEPENDENCE_UNESTABLISHED` |
| b | 与发现者相同 | UNESTABLISHED | BLOCK | `SELF_REVIEW` |
| c | 不同主体 | UNESTABLISHED | ACCEPT | `INDEPENDENCE_UNESTABLISHED` |
| d | 不同主体 | ROLE_SEPARATED | ACCEPT | （无） |

b 行值得单独看：**连"阻塞"这个决定，发现者本人也签不了。** 一次单主体运行既拿不到 ACCEPT，
也拿不到一个合法的 BLOCK 记录，只能完全不产出 `scope-decision`——这正是本次的做法。

连锁后果，全部由 `validate.py` 的必需输入表直接给出：

- `proof.expand` 必需输入含 `frozen-scope` → 本次实测被拒：`Missing required operation input: frozen-scope`。
- `obligation-disposition.payload.scope_ref` 指向 `frozen-scope` → S5 的"每项义务恰好一个当前处置"无法开始。
- AGENT.md 第 6 节的同哈希规则要求送 Proof 与送 Dependency 的两个 Task 引用同一个 `frozen-scope` 哈希
  → 即使 `dependency.search` 单独校验通过（本次实测通过），**配对也组不起来**。

所以本次交付的是 S0、S1、S3，加上一个**提出但未冻结**的 57 项义务分母。

## 2. 对应关系的自审无法回避

AGENT.md S3 要求每项义务至少一条 `scientific-claim`，且**每条都配一个 `claim-component-map`**。
而 `claim-component-map.payload.review` 同样必填、同样不可为空。于是：

| 探针 | 与主张同主体？ | 实测问题码 |
|---|---|---|
| 同主体 | 是 | `SELF_REVIEW` |
| 不同主体 | 否 | （无） |

两个探针的记录内容**逐字节相同，只差 `producer.principal_id` 一个字段**。这说明：

- 这不是抽取质量问题，改进主张切分、补充数学目标、写更细的残留都不会让它通过；
- 唯一的机械解法是给对应关系换一个 `principal_id`。本次**没有**这么做。仓库自己的
  `AuthorityContext` 里有 `ALIASED_SELF_REVIEW`（"不同显示名解析到同一个真实生产者"）正是为了抓这种做法，
  而 `validate.py --archive` 并不提供 `AuthorityContext`，所以换个名字能骗过归档校验、骗不过设计意图。

一个可能的规范侧取舍（**本次不主张采纳**）：如果 `claim-component-map` 的 `review` 允许为 null，
表示"尚无任何审阅"，那么生产者自述的对应关系可以作为合法的未审阅候选入库，独立审阅仍然必须另起一条记录。
当前 schema 不区分"自审通过"与"尚未审阅"，两者都只能写成一个必填的 review 块。

## 3. AGENT.md 的 12 字段 Plan 与 v0.0 schema 不兼容

AGENT.md 第 3 节把 Plan 定死为 12 个字段，并明确：`created_at` 交事件日志、`data_class` 交生产者标签、
`max_seconds` 与 `max_cost_units` 直接删除（`max_steps` 足够）、`identity_evidence` 在有身份机制之前删除。

v0.0 `agentization-plan` 对这四项的要求，本次实测：

```
SCHEMA /payload: 'max_seconds' is a required property
SCHEMA /payload: 'max_cost_units' is a required property
SCHEMA /: 'created_at' is a required property
SCHEMA /: 'data_class' is a required property
```

本次采用的 Plan 因此在两个预算字段上填了声明性占位值（`max_seconds: 86400`、`max_cost_units: 0`），
并在 `trigger_note` 里写明这两个数**从未被度量也从未生效，`0` 不得读作"本次零成本"**。
AGENT.md 形状的 Plan 保存在 `output/plan-as-agent-md-specifies.INVALID.json`，只作兼容性样本，未签署、未采用。

## 4. 两个较小的表达缺口

- **Component 角色枚举没有"解释性"一档。** v0.0 `Component.role` 只有
  CONCLUSION / ASSUMPTION / DEFINITION / MODEL / APPROXIMATION / EVIDENCE / ATTRIBUTION / LIMITATION，
  而 `scientific-claim.modality` 有 `INTERPRETIVE`。本文这类"以统计力学类比重述磁性"的段落，
  在主张层可以标 INTERPRETIVE，到组件层只能落到 `MODEL`。本次一律记为 `MODEL`，此处说明其含义。
- **`required_axes` 必须恰好 6 项。** 该字段的 `minItems` 与 `maxItems` 都是 6，所以"本轮只要求来源忠实"
  这种意思无法表达；只能全列六轴，再靠 `success_required_stages` 和义务的 `requirement` 去区分强弱。
  本次即如此：六轴全列，但只有 SOURCE／INVENTORY／CLAIM 是 `SUCCESS_REQUIRED`。

## 5. 这些结论不覆盖什么

- 不涉及论文数学是否成立，也不涉及抽取是否忠实——后者恰恰需要本文件说明的那个独立审阅者。
- 不涉及运行时调度、身份认证、计费或数据库写入：本次一项都没有发生。
- 探针记录（`record_id` 以 `probe:` 开头）只为定位边界而构造，**不属于交付记录集**，不在 `records.json` 中。
