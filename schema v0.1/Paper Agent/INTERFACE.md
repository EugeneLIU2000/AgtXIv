# Paper Agent 1.1：模型草稿与宿主接口

这是 AGENT.md 的规范性附件。这里只新增 **Paper 内部的模型草稿载体**，外部 Task/Result、业务记录与权限不变。草稿不是可以直接放进数据库业务表的记录。

## 1. 唯一模型返回形状

```json
{
  "draft_version": "1.1",
  "records": [],
  "open_items": [],
  "follow_up_requests": []
}
```

这是空形状示意，不是提取完成示例。没有可交付内容时必须解释原因；模型拒绝、响应截断、无效 JSON 或缺输入也不能被宿主转换为“成功的空提取”。真实的人工教学样例见 [conformance/claim-draft.json](conformance/claim-draft.json)。

- records 每项严格为 `record_type` 与 `payload`，类型使用完整 v0.0 标识。九个 schema 分支逐类绑定，不能混用一种类型的名字和另一种 payload。
- payload 的唯一字段来源是对应 v0.0 schema 的 `properties.payload`，本目录不复制它。字段名、枚举和必填规则优先于自然语言摘要；新增业务字段须单独版本迁移。
- open_items 沿用现有字符串数组。每项采用固定文本顺序：`target=<已有引用ID/组件ID/原文位置>; missing=<缺什么>; checked=<查过哪里>; next=<需要什么>`。它是公开缺口摘要，不要求记录模型内部思考。
- follow_up_requests 复用现有四字段 `agent`、`operation`、`input_refs`、`reason`；reason 使用 `target=...; need=...; purpose=...`。例如查引理时注明原文引用位置、待查命题及预期用途，不仅写“search references”。
- 空数组仅表示该集合确实为空；未知或未处理另有 open_items。语义不适用时只用原 schema 允许的空值，不能加入自拟 `UNKNOWN`、null 或省略必填字段。

## 2. 引用与多轮：先保存，再交给下一轮

每轮都必须是单独固定的 Task。宿主的引用目录是 **该 Task.input_refs 的展示**，而非可以另外访问的隐含输入。所需原文字节和规范附件固定在 Task.input_artifacts；相关身份与实际可见性由宿主记录。

不同模型使用同一段任务指令，具体目标、范围和预期类型从固定 Task 读取，不按模型品牌另写提取标准。最小指令为：“按所附 Paper Agent 1.1 规范处理本工作单；仅使用提供的来源、上下文与精确引用。遵循原文断言边界、量词和条件范围；无法确定时保留缺口。只返回符合所附 extraction-draft schema 的 JSON，不补造未提供的事实或引用。”不同厂商的消息角色适配可以不同，但实际提供的规范和任务内容须留痕且等价。

1. 模型使用已有输入，提取原文位置、结构、定义或主张的 payload。
2. 宿主检查草稿，生成完整记录并保存。新记录须校验；保存候选不等于独立认可。
3. 调度程序创建新的 Task，把确需使用的已保存记录列入 input_refs，把实际字节列入 input_artifacts，再运行下一轮数学目标／对应提取。

同一草稿中的记录尚没有正式身份，不能互相引用；FollowUp 也不能引用它们的未来身份。无正式目标时在 reason 中描述原文位置和所缺产物，调度程序在保存后依据固定规则选择，不能靠“取最新记录”解决歧义。component_ids 等局部编号必须属于所引用主张；它们不是全库身份。

现有 Task.input_refs 与 Result.execution.visible_input_refs 必须匹配；输入新增、目标变化或重试规则变化要新建工作单，不能回写旧任务。多轮顺序由实际引用依赖决定，不要求每篇固定五次模型调用。

## 3. 模型与宿主各写什么

| 内容 | 所有者 | 约束 |
|---|---|---|
| 主张、条件、对象、量词、结论、语义、引用线索、缺口 | Paper 模型 | 按 AGENT 的 R1–R8 填写 |
| 编号、修订、时间、data_class、schema_bundle_hash、producer、policy_ref、input_refs、content_hash | 宿主 | 来自真实输入与执行；不能让模型虚构 |
| source-span 的字节偏移、片段哈希与附件绑定 | 模型提位置，宿主核对 | 优先使用宿主预计算的定位；按实际字节验证，不靠模型心算偏移／哈希 |
| payload 中的 review 归属 | 宿主提供真实上下文，Paper 如实描述未审阅状态 | Paper 不能自报 INDEPENDENT；`UNESTABLISHED` 也不解除现有 SELF_REVIEW 检查 |
| Result 的 outcome、execution、output_refs 与 artifacts | 宿主 | 来自运行事实、预声明任务与校验；open_items 非空不自动等于 BLOCKED |
| 下游 Task、独立审阅、冻结范围 | 调度程序及相应角色 | 不由模型草稿直接创建或批准 |

装配前后 payload 的 JSON 值必须相等。程序可以计算封套并拒绝非法内容，但不得悄悄清空来源、统一 ASSERTED、复制全部定义、改变公式或添加适用条件。位置校核发现错误时退回修订，不静默“修好”学术内容。序列化不能改变量词或组件的有意义顺序。

修订另一个记录时，Task.target_refs 明确旧目标；若批量修订无法唯一确定草稿项与旧记录的对应，拆成单目标任务或停止请求澄清，不以文本相似度覆盖记录。运行身份与科学对象身份分开；不同模型不得相互覆盖历史产物。

## 4. 文件交付约定

新运行统一使用下表名称；这些是运行附件，不新增业务类型。所有路径相对于独立的运行目录。旧 example 保持原样，不作为新接口可接受别名。

| 路径 | 内容 |
|---|---|
| `draft.json` | 本轮原始模型 JSON；无效原始输出另存 `diagnostics/model-output.txt` |
| `task.json` | 实际固定工作单；仅在确实存在时保存 |
| `records.json` | 已装配业务记录数组；不混入 Task、Result、manifest 或被拒绝的草稿；即使是候选也需声明检查边界 |
| `result.json` | 真实执行产生的现有 Result；没有足够运行事实时不造回执 |
| `manifest.json` | 宿主的运行索引，字段约定如下 |
| `validation.json` | 草稿、任务限制、引用、单条记录、完整记录集检查分别报告 |
| `diagnostics/` | 被拒绝草稿、校验错误和尚待迁移的问题；不能作为正式业务输出的替代通道 |
| `README.md` | 面向人的可读说明，不代替机器结果 |

manifest 固定字段：`manifest_version`（`paper-agent/1.1`）、`run_id`、`mode`（`EXECUTED` 或 `OFFLINE_DIAGNOSTIC`）、`source_refs`、`spec_files`、`schema_bundle_hash`、`model`、`files`、`record_counts`。

- spec_files 是 `{path, sha256}` 列表，包含实际加载的本目录规范与草稿 schema；哈希统一为 `sha256:` 加 64 位小写十六进制。
- model 为 `{provider, model_id, settings}`；不可取得的 provider/model_id 为 null，settings 只列真实使用的非敏感设置，未知不编造。模型名字不证明执行身份。
- files 是 `{path, sha256, byte_size}` 列表，不包括 manifest 自身，避免自引用；record_counts 按完整业务 record_type 从 records.json 计算，不能手填。
- OFFLINE_DIAGNOSTIC 不宣称正式 Task 已运行或 Result 已交付。正式 EXECUTED 交付必须具有真实 task.json/result.json；缺身份或回执事实不填零费用、假时间、假签名。

本轮实现了草稿 schema 和离线检查器；**完整共享装配器、manifest 写入器、候选对应与审阅分离、实际模型调用和调度适配尚未实现**。文件约定是下一步实现的契约，不是这些服务已经存在的声明。候选持久化、Git 封存、SQL/Neo4j 投影继续服从上层 STORAGE。

## 5. 与旧契约的已知兼容边界

- 不再使用 1.0 文档中的“12 字段精简 Plan”。真实计划保留 v0.0 所有必填字段，包括预算、时间和身份归属；没有真实依据就报告缺失，不伪造凭据。
- 当前 RecordSet 要求计划 source_unit_ids 与对应快照的来源单元集合一致。局部批次只是工作安排，不把计划清单擅自缩为子集。来源文件清单、段落定位、处理义务和 claim 数量不是同一件事。
- 当前 claim-component-map 把对应内容与 review 绑定；Paper 自生成对应表会受到 SELF_REVIEW 限制。草稿合法不表示完整记录集合法。
- 若 Task 预期 map 而其无法通过检查，Result 保持 BLOCKED，已通过的其他预声明记录可以部分保留，失败 map 不进入正式 output_refs；原始失败草稿可以保存诊断，但不能绕过输出白名单或满足交付数量。
- 后续新 Task 可事先不要求 map，原 Task 不得事后删要求获得 DELIVERED。真正分离候选对应与独立审阅需要新的业务版本或明确适配设计，不能在本目录偷偷实现。
- 旧示例校验器把规范哈希与当前 AGENT.md 比较；升级后该检查会有意失败。旧版本原文已保存于 history/AGENT-1.0.md，原始输出、manifest 和校验脚本不重写，不能重新标成 1.1 运行。

## 6. 运行时与跨模型的一致性要求

同一次比较固定来源字节、规范文件哈希、处理标准、阅读顺序、输出语言、上下文窗口切分、工具可见性及装配器版本。记录每个模型的实际设置；不同模型设置不必假装数值等价。评估前不得先把另一个模型答案喂给待测模型。

为减少收录范围漂移，宿主应按同一版本的源文解析规则提供结构位置清单：有编号的断言、公式、段落、图表和附录位置。它只是阅读索引，不提前断定每处都是 claim，也不等于独立冻结范围。没有自动解析器时，可先固定同一份人工位置清单并明确其来源；不能让两模型各自选择不同片段后称为同条件比较。每个已提供位置的提取、重复引用、非主张或未处理原因应在清点记录及缺口中可追踪。

若调用渠道支持约束式 JSON 输出，使用其可支持的 schema；本 schema 引用了外部定义，不能未经适配就假定任何厂商 API 能直接接收。适配器应解析本地引用并测试所支持子集，不另手写一套字段。拒绝、截断和不支持 schema 的情况单独处理；无此功能时仍必须本地校验、按固定预算修复，不能忽略错误。

依据 [OpenAI 官方 Structured Outputs 说明](https://developers.openai.com/api/docs/guides/structured-outputs)，结构化输出仍可能有内容错误。因此本规范把格式检查与来源／语义审阅分开，用统一正反例降低误读，不承诺不同模型或重复运行逐字一致。
