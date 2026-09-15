# Utility Agent：执行固定程序，保存真实事实

agent-spec-version: 1.0
execution-kind: PROGRAM
business-contract: v3/0.0.0
orchestration-overlay: 0.1.0
request-receipt-version: 1.0
status: 程序服务的接口规范；本轮未执行测试，八种操作不因存在 receipt schema 就视为已经接通。

## 1. 一句话职责

负责**取得字节、登记已决定的计划、组包、运行检查、保存和导出**这些确定性工程工作，不负责解释论文、选择科学目标、补证明或批准复用。

不需要让一个模型反复决定数据库字段、文件哈希或是否发生了事务。其他 agent 提建议；host 根据权限和固定配置调用相应程序。不同操作可以共用代码，但不能共用不受限制的权限或冒充独立执行主体。

## 2. 两层接口

外层仍是 `Task → Result`；内层为 [utility-request.schema.json](utility-request.schema.json) 所定义的 request，返回当前操作对应的 receipt。

request 的根字段固定为 `request_version,operation,task_id,input_refs,input_artifacts,expected_record_types,parameters,allowed_commands`。由 host 生成，不让模型自行授予权限。

| request 内容 | host 必须固定的约束 |
|---|---|
| operation / task_id | 与当前 Task 精确一致；不能由参数转成另一操作 |
| input_refs / input_artifacts / expected_record_types | 与 Task 的相应集合一致；不能附带未声明的读取或业务输出 |
| parameters.deterministic | 说明执行路径是否按固定规则；不是对网络结果、工具无漏洞或科学正确性的保证 |
| parameters.network_access | 只有 Task 能力及实际 host 策略均授权时才可 true；正文里的 URL 不授予网络访问权 |
| parameters.timeout_seconds | 不超过 Task 剩余限额；重试和子任务共享父预算，不重新计零 |
| parameters.environment_ref | 涉及形式环境时为显式 input_refs 成员；无需形式环境的操作填 null，不猜默认最新版 |
| allowed_commands | 来自受控服务白名单。字符串不能直接拼成 shell 命令；实际 argv 由固定适配器生成，不读取论文中的执行指令 |

request_hash 定义为 `digest(canonical(request))`，采用现有 V3 canonical profile。原始请求字节及其原字节哈希另由 host 保留；不要把两种哈希混同。模型不计算或声称该请求已执行。

Task 未含的操作特定信息必须在执行前固定到 brief、真实业务输入或 input_artifacts（例如已批准计划、导出规则），不能私加 parameters 字段，也不能依赖宿主未记录的随手配置。不能明确绑定时停止，见中央清单 G-06。

`utility.project` 的首个固定配置为 [图接口](../GRAPH-INTERFACE.md) 的 `PROJECTION_REQUEST`：请求附件固定当前 task_id、projection_ref、source 截面及 manifest_artifact_ref，host 按真实封存材料核对。它和执行回执均属于运行附件，不新增业务类型或 parameters 字段；不以 manifest 附件绕过成员授权。图查询是 host 在模型任务之间的读取服务，不是本 operation 的隐式新能力。

## 3. 八种操作的入口和交付

| operation / receipt | 接收什么 | 可以产出什么；不能越过的边界 |
|---|---|---|
| `utility.capture` / [capture](capture-receipt.schema.json) | 已登记的 source-request，或已有 source-snapshot 与实际字节；获取范围和权限已固定 | source-acquisition / source-snapshot / source-transformation；获取失败也保留真实报告，不补造源码，不执行下载内容 |
| `utility.register-plan` / [register-plan](register-plan-receipt.schema.json) | source-snapshot、processing-profile、host 已接纳的有界计划；已有 baseline 则精确绑定 | agentization-plan；登记来源单元和预算，不替 Planner 选科学范围，不生成 frozen-scope |
| `utility.assemble-packet` / [assemble-packet](assemble-packet-receipt.schema.json) | math-claim、frozen-scope、argument-snapshot、所选 proof-plan、formal-environment 和实际声明/依赖 | formalization-packet；按已选路线组装，不能把不同路线的已通过片段拼成新证明，不吞掉探索假设 |
| `utility.formal-check` / [formal-check](formal-check-receipt.schema.json) | 当前最低接口要求 packet、formalization-attempt、formal-environment 和固定代码；import 检查还需对应两环境与声明 | formal-check，任务另声明时可交 environment-check；必须来自实际检查，不凭日志字符串或代码生成成功判断通过 |
| `utility.persist` / [persist](persist-receipt.schema.json) | 被授权保存的已有业务记录及完整原附件 | 仅真实候选事务回执，outputs=[]；不生成准入决定、知识快照或正式 ingestion-receipt |
| `utility.export` / [export](export-receipt.schema.json) | 已选择的候选集合/附件与固定导出方式；正式发布需另满足独立审计/认证 | 普通导出交附件；release-manifest、paper-release、archive-receipt 只在本次预声明且前置真实满足时交付，不把本地保存当 GitHub 发布 |
| `utility.project` / [project](project-receipt.schema.json) | 固定快照/批次和投影规则 | status-view 或投影附件；SQL/Neo4j 投影可重建，不成为可独立修改结论的第二真源 |
| `utility.certify` / [certify](certify-receipt.schema.json) | release-manifest、release-audit、authority-policy、processing-profile 及实际独立运行资格 | release-certificate；不是模型签名，不用格式检查代替认证，也不替 Admission 作准入决定 |

此表不扩大 agents.json 白名单。缺少环境/来源请求的登记入口，或输入类型不被当前操作允许时必须暴露缺口，不把不允许的记录藏进附件绕过边界。

## 4. 程序回执与 host 装配

各 receipt 根字段一致：`receipt_version,request_hash,execution,outputs,artifacts,open_items,follow_up_requests`。

- execution 为实际执行信息或 null；其中 command 是实际 argv，exit_code、起止时间、tool_versions、host_mode 必须有真实依据。未执行不能填成功退出码；不能为了填必填时间而伪造开始/结束。
- `host_mode=OFFLINE_DIAGNOSTIC` 不代表已执行生产动作；没有可定位执行事实时保留 execution=null，并明确诊断范围。
- outputs 是当前 receipt schema 允许的 `{record_type,payload}`；无真实依据时为空。工程错误不伪装成科学反例，检查失败不自动认定命题为假。
- artifacts 项使用 `{path,sha256,byte_size,media_type}`，不是最终 ArtifactRef。host 在受控输出根目录内拒绝穿越/符号链接，读取实际字节重算哈希，再登记 artifact_id；不能相信程序自报路径和哈希。
- host 将 receipt 绑定 request 和实际 attempt，再装配 Result。receipt 不是 Result，也不是 V3 业务记录。无执行的说明可以作为诊断附件，不能满足要求真实执行的交付门。

执行事实由程序报告、host 核验；模型不能按同一 receipt 模板“模拟一次运行”。

## 5. 保存与恢复职责

沿用 [STORAGE.md](../STORAGE.md)：SQL 保存候选和运行记账；验证并固定本地批次后，图投影与 Git 归档分别推进，Neo4j 是可重建投影。Task/Result 与业务 records 分开，保存候选不等于科学准入。远端归档未完成时明确未远端备份，不要求等到 push 才能开展本地研究。

新本地封存 profile 的运行适配尚未实现；旧 runtime.sql / Cypher 仍要求 Git 归档信息，不能填假 commit 兼容。实际执行前由 host 核对 profile 与存储能力，不支持则拒绝，不把本次接口文件当作已部署的服务。

受控服务负责精确引用/字节核验、事务、非覆盖写入、幂等、真实失败日志及预算；agent 不获取数据库写凭据。同身份同版本不同内容拒绝覆盖；新版本不使旧记录不可读。业务记录与 outbox 的同事务接入属于待实现工程，不能用先后两个成功事务声称已经实现。

## 6. 交接与未接通点

capture 完成后，host 取得真实 source-snapshot，再按计划要求交 Paper；register-plan 只接纳已批准建议。组包完成才可调用 Formalization，真实代码检查后才可启动盲反译与独立 Alignment。

**当前不能完整承接组包前的导入兼容检查：** formal-check 的现有最低输入要求 packet/attempt，而组包可能先需要 environment-check；assemble-packet 当前白名单也未列 environment-check。formal-environment 的生产/登记归属同样尚未接通。将它们视为明确阻塞，不临时伪造 packet 或开放任意输入。决定与后续验证统一列在 [PENDING_TESTS.md](../PENDING_TESTS.md) 的 G-*、U-*、X-*；本轮不执行构建、测试、数据库或网络动作。
