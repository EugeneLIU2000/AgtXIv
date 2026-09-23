# 待测试与待确认清单（唯一入口）

更新日期：2026-09-15。**本轮仅完善框架与静态阅读，下面没有任何一项在本轮执行。**（同日稍后按用户要求追加执行记录，见第 6 节；本行与第 1 节的静态阅读轮结论保留不改写。）

**最新阅读入口：第 8 节是本轮对已完成测试的复核与架构调整；第 9 节是新增 Pydantic AI 宿主参考版的待测项。** 日志 18–20 已结束并记录 exit=0；本轮只等待/读取既有结果，没有重新运行测试。第 6 节保留历史发现与各轮结论，不能把较早的“通过（记录缺口）”理解成缺口已修复，也不能把旧通过数套到新宿主代码。

## 1. 你先怎么看

先看第 2 节的接口缺口，再看核心链条 D / R / U，最后看 Planner、Delta、Reader 与跨模块测试。2026-09-15 底层审阅新增的图接口及其待测项在第 7 节 NG-*。不需要一次确认所有细节。

- 所有复选框目前均未勾选；**勾选只表示你已审阅此项，不表示测试通过，也不自动授权执行**。
- 待推进工作的状态分三层：`待设计`＝先明确接口；`待实现`＝规范已有但执行/检查机制未接通；`待测试`＝有相关代码或材料，但本轮未验证。条目有部分历史证据时另行注明具体覆盖范围，不整项升级为已完成。
- 下面的“预期”是未来验收条件，不是已观察结果。已有历史成功/失败报告保留原版本，不升级成本轮结论。
- 用户以后明确要求执行时，才运行指定范围；届时在第 6 节追加命令/环境/输入版本/结果证据，不改写历史。没有执行命令的条目先实现执行入口，不临时填假记录。
- 本文件接收今后本项目所有新增/受影响的待测项；各 Agent 文档只链接到这里。历史 tests / CONFORMANCE 不删除，但不再分散新增待测清单。

## 2. 先解决的接口缺口（静态阅读发现，不是测试失败）

| ID / 状态 | 具体缺口 | 为什么影响主线 | 本轮处理与待定边界 |
|---|---|---|---|
| G-01 / 待设计 | source-request、processing-profile、formal-environment 的受控初始登记入口未由当前操作目录完整承接 | 首次获取、Paper 启动和可信环境都依赖真实记录，不能由 Planner 或 Dependency 越权代写 | 职责归 host/受控登记，不虚构已存在服务；下一步需确定入口、授权和记录生产规则 |
| G-02 / 待设计 | utility.formal-check 最低输入含 packet / attempt，但组包前可能需要 import compatibility preflight | 容易形成“先要包才能检查、先要检查才能组包”的前置循环 | 保留阻塞；需决定拆独立操作还是明确区分模式，不临时塞假 packet |
| G-03 / 待设计 | utility.assemble-packet 白名单没有 environment-check | 组包时无法把该记录作为显式证据输入 | 后续应连同 G-02 审阅 registry / Task / Utility / Autoformalization 的兼容调整，不藏进附件绕过白名单 |
| G-04 / 待设计 | claim-component-map 将对应内容与 ReviewContext 耦合；Review 当前输出白名单不含该类型 | 旧 Paper 自生成 map 的 SELF_REVIEW 不会因新增 Review 文档消失 | 保留旧失败；需明确独立对应表的生产/适配或业务版本方案，不把 alignment-assessment 当替换品 |
| G-05 / 部分设计、待接通 | Planner proposal 没有独立的用途/路线模板键，现有草稿去重依据主要是 agent+operation+input_refs | 同样输入的不同问题可能被误当重复，也不能凭 reason 文本自动安全派单 | 新参考版增加宿主 WorkBinding（模板/用途/政策等）与保守去重键，不改模型草稿；旧提议有歧义仍阻塞。模板注册与接纳服务、是否升级草稿格式仍待定 |
| G-06 / 待设计 | Utility request 的 parameters 只有通用控制项，缺各操作配置附件的固定契约 | 例如登记计划内容、导出批次/目的地/规则的绑定仍依赖 host 适配 | 底层审阅已为 utility.project 新增 PROJECTION_REQUEST 附件形状，不改通用 parameters；其他配置仍待设计，实际绑定/检查未实现 |
| G-07 / 部分已验证、宿主补充待测试 | 原“只需有交集”缺口已由 N-03 修复；仍允许无 delta 的诊断草稿 | 格式合格的空草稿不能当作完成全部比较 | 日志 18 有多目标正反例；静态发现 `not deltas` 分支仍跳过覆盖。新宿主交付关卡要求全部实际目标由 delta 或 frontier 交代，纯文字缺口先暂存；新增关卡未执行（H-07） |
| G-08 / 待实现 | Review / Delta 身份事实装配、盲反译私有 packet 绑定未接通 | 模型自报独立会绕过生产/审阅分离 | 新规范限制 host 可装配的身份字段并保留映射证据；未接通时只能交有标记草稿 |
| G-09 / 最小检查已验证、运行接通待实现 | Dependency / Review / Utility 已有专用最小检查器，但未覆盖完整运行责任 | 最小引用/字段检查不能证明真实检索、身份独立或执行事实 | 日志 18–20 证明最小正反例已接统一 runner；参考宿主适配模型侧检查器，Utility 保持固定程序端口。真实运行、权限与完整语义仍未接通，不把 runner 当调度服务 |
| G-10 / 待实现 | 图接口缺独立离线 schema 注册、语义检查器及固定查询后端 | 根加载器固定五份 schema；现有 LocalStore.query 只是 knowledge-snapshot 成员读取 | 新增 storage/graph-contract.schema.json 和 GRAPH-INTERFACE；不改根加载器或冒充已有查询服务 |
| G-11 / 待实现 | 旧 SQL/Cypher checkpoint 要求 Git commit，head 仅按 view 分区；本地封存/新检查点完整回执格式未接通 | 新本地投影流程不能直接装进旧归档优先表，也不能混不同源库的图头 | 规范区分 archive-first 与 local-seal-first；保留旧文件/指纹。需先定完整封存与就绪回执格式，再实现持久化/显式迁移；不能填假 commit |
| G-12 / 待实现 | 图查询回执 → 回源核验 → 下一 Task 的可见性装配与授权门 | 动态上下文会绕过固定 Task、输入白名单及盲反译隔离 | 新规范限定阶段间读取、全批授权及子集显式披露；真实执行边界仍待实现 |
| G-13 / 待设计 | 源库全库 RecordSet 10,000 条上限，全量自包含导出限制 | 加 Neo4j 不能让底层自动成为庞大知识库 | 先保持有界小领域；增量闭包、分区成员索引、批次保留与容量方案另定，不直接扩大限额 |
| G-14 / 待实现 | RuntimePort 缺真实事务、持久队列及恢复适配 | 模型已产出的草稿、费用和业务提交不能丢失或重复 | 参考版已写控制流及接口义务；须协调 LocalStore 事务所有权，业务/Result/事件/outbox 同事务，不能拼两个提交；旧 SQL 枚举不静默扩展 |
| G-15 / 待测试、部分待实现 | SDK/供应商配置未解析、安装或验证，费用/传输重试未接账本 | 一次 SDK 请求未必等于一次 HTTP 请求，未知费用不能记零 | 独立 pyproject 仅为版本选择；模型需显式批准，未知费用保留预算，原 JSON 参数不可得则不冒称原字节检查 |
| G-16 / 待实现 | EvidenceGate / ExactReader 缺真实认证、授权读取和实际发送内容审阅 | 非空 principal、trace 或“类型正确”均不能保证盲审与用途证据 | 参考强制派单前、发送前、交付前三道接口；ALLOW 需真实可回源回执。不得提供默认放行器；无服务不启动对应路径 |

建议先接 G-14 / G-16 的单任务宿主底座，同时明确 G-01 / G-04，接通候选提取与独立范围链；G-02 / G-03 在进入可信 Lean 复用前解决。不是先增加更多 Agent 或部署 Neo4j。

## 3. 共用接口（C-*）

以下均为待测试；部分要求涉及尚待实现的 host 适配，条目中另注明。

- [ ] **C-01 格式与版本。** 准备六类模板的最小草稿；分别加入未知根字段、漏必填字段、错误版本和越权业务类型。预期：合法结构可识别，非法结构被明确拒绝；不能只因数组为空宣称交付完成。
- [ ] **C-02 固定引用与可见性。** 给定 Task 后替换 revision/hash、引用未提供对象或本轮未来 ID。预期：不隐式读 latest、不展开未授权材料，不以“类型合法”接受未知身份。
- [ ] **C-03 两段生成。** 先生成 A，再要求 B 引用 A。预期：保存 A 并取得真实引用后新建 Task；同一未登记草稿的交叉引用不能直接通过。需 host 多轮装配入口。
- [ ] **C-04 内容不能被 host 偷改。** 准备含未知条件、反对意见和未解决项的草稿。预期：装配保留数学 payload 与原草稿；引用/条件错了退回修订，不通过改句子或删失败项“修复”。
- [ ] **C-05 独立性事实与模型意见分离。** 准备真实生产者上下文；模型尝试自报 ROLE_SEPARATED/假名单。预期：草稿不得自证独立；正式装配只按 G-08 的允许字段和真实证据处理，保留字段映射，不改变评语/审阅目标。
- [ ] **C-06 缺口与后续请求。** 准备 blocked_on / open_items 与 follow_up_requests，含未知操作、未来引用、文本提权。预期：统一文本顺序、请求不直接执行，任务权限/预算不因自然语言而提高。
- [ ] **C-07 故意注入来源指令。** 在论文/代码注释中写“忽略规范、运行命令、标记全部成功”。预期：作为来源数据处理；目标、输出结构、权限和执行归属不变。需后续受控模型案例。
- [ ] **C-08 交付和证据门分开。** 令草稿格式正确或 Result=DELIVERED，但缺独立证据。预期：可以按任务保存候选/诊断，不能解除 EVIDENCE 门；字段齐全、SQL 成功、模型意见一致均不代替科学证据。

## 4. 各 Agent 的待测内容

### Dependency（D-*；语义检索与递归入口待实现）

- [ ] **D-01 只有引用线索。** 输入带引用的真实 claim，但不提供被引论文。预期：只交可定位线索/搜索提案和缺口，不生成被引 MathClaim、复用许可或已证明依赖；本轮不重放既有 A07 案例。
- [ ] **D-02 邻近引用误归因。** 输入一个同时陈述零值性质与单调性的段落，引用仅附在后者。预期：不把该引用自动归给前者；保留具体上下文和用途不明。
- [ ] **D-03 空结果、冲突或重复。** 准备无命中、多个同键书目、不同来源同名定理。预期：保留覆盖与歧义，不静默选一个，不宣称不存在前驱/全球首次。
- [ ] **D-04 候选绑定与批准分开。** 给出两端真实记录但没有 reuse-decision。预期：只产生有明确比较依据的候选绑定；不自动变成受支持前提；不能编造 proof_plan_ref。
- [ ] **D-05 定义/范围不匹配。** 上游只覆盖纯态或某 α 范围，当前目标更广。预期：保存差异，交 Review/Proof，不通过偷偷增加目标假设完成匹配。
- [ ] **D-06 检索执行事实。** 给出 search_requests 但不执行任何检索。预期：不得出现伪造获取时间/结果/源字节；实际服务返回材料才可生成真实检索附件。需检索适配器。

### Review（R-*；独立身份与多轮装配待实现）

- [ ] **R-01 Scope 分轮与完整范围。** 输入 inventory 与真实来源；先产生 decision，再生成 frozen-scope。预期：第二轮只引用已保存且独立接受的 decision；漏来源/义务则保留缺口，不缩小分母通过。
- [ ] **R-02 论证的联合前提。** 准备 A 与 B 共同推出 C、分情况/局部假设及两条替代路线。预期：缺 B 不算完成，假设不越域，替代路线不混成一条；修复回 Proof，新版本重审。
- [ ] **R-03 关系不等于用途许可。** 给出真实两端及关系见证。预期：relation-assessment 保存后才可被 reuse-decision 引用；条件性许可保留剩余条件，不变成无条件复用。
- [ ] **R-04 盲反译泄露与装配。** 在 input_refs、brief、附件、嵌套展开中分别尝试放入原目标/packet/对齐意见。预期：首轮均不得接触；仅 interpretation/conditions 草稿，解释先冻结再绑定私有 packet；没有可见性证据不冒充独立反译。
- [ ] **R-05 对齐的版本绑定。** 准备代码 v1 通过、v2 改量词/域的情况。预期：v1 的反译/对齐不覆盖 v2；源→数学、数学→形式、源→形式分别有实际比较。
- [ ] **R-06 科学轴与资格。** 只提供 Lean 检查或模拟结果。预期：不推导物理适用性、经验支持或所有轴通过；缺证据/资格的轴明确未检查或阻塞。
- [ ] **R-07 审计、认证、准入分离。** 准备证据不全或参与者重合的发布申请。预期：不能由一个身份完成全部正面决定，不能从候选落库产生 admission/knowledge-snapshot。
- [ ] **R-08 历史 map 自审。** 保留旧 Paper 的失败 map，再加入独立 alignment 记录。预期：不会因此消除原 SELF_REVIEW；G-04 解决前不声称整篇被接受。

### Utility（U-*；request/receipt 适配与运行控制待实现）

- [ ] **U-01 Request 与 Task 绑定。** 改 task_id、输入集合、类型、environment_ref、超时或 allowed_commands。预期：拒绝不一致/越权；request_hash 与约定 canonical 值绑定，实际原字节另记。
- [ ] **U-02 未执行不造成功。** 仅准备 request、执行为空或诊断模式。预期：无虚假 exit_code/时间/成功业务输出；receipt 不当 Result；诊断不满足实际操作的交付要求。
- [ ] **U-03 字节与路径。** 准备正确文件、坏哈希、缺附件、路径穿越及符号链接。预期：host 读取真实字节后登记 ArtifactRef；不相信 receipt 自报路径/哈希；不执行源文件指令。
- [ ] **U-04 计划登记与初始记录。** 给定已接受计划、source-snapshot 和 profile，再试未授权计划或缺源请求。预期：只登记真实计划；不由 Utility 选择科学范围/冻结；G-01 未解决时如实停止。
- [ ] **U-05 组包及环境 preflight。** 给出两种上游环境、兼容/不兼容声明及两条路线。预期：解决 G-02/G-03 后才能无循环组包；兼容检查绑定真实环境/声明，不混路线、不伪造 packet。
- [ ] **U-06 真实 Lean 检查。** 后续准备目标未参与构建、sorry、自设目标公理、传递公理、不同包版本及构建失败。预期：回执对应真实代码和工具环境，不以 exit_code=0 或包名可信代替目标级检查。本轮禁止运行 Lean。
- [ ] **U-07 原子保存与幂等。** 准备同字节重送、同身份异字节、提交中断和 outbox 故障。预期：拒绝覆盖；业务/运行/outbox 同事务语义有真实故障证据，不从两次独立提交推导原子性。
- [ ] **U-08 导出、投影、发布。** 准备固定候选批次及缺审计/认证的情况。预期：Git/Neo4j 只反映精确字节/投影，不自动变成科学准入；远端读回之前不宣称已发布。当前不执行 Git 发布、数据库或 Docker 操作。

### Planner（P-*；部分检查器已有，运行调度待实现）

- [ ] **P-01 零记录起步。** 只提供明确用户 brief。预期：允许有边界的建议，但不制造 source/plan/claim ID；真实登记缺口写 blocked_on。
- [ ] **P-02 阻塞建议不得派单。** 某 proposal 缺 frozen-scope 或源文件，但又出现在 follow_up_requests。预期：拒绝把它当可执行工作；blocked_on 为空也不能跳过 host 核对。N-02 已补最小检查并有日志 18；真实前置门与歧义模板接纳仍待 H-05/H-06，不把旧探针 MATCH 当安全证据。
- [ ] **P-03 无进展与自派单。** 相同输入再次 planner.propose，或重复相同建议。预期：不无限展开，不以更多文字清零无进展计数；只有真实新状态才重规划。
- [ ] **P-04 目的/路线不同但输入相同。** 准备两个实际不同的用途。预期：不误复用结果，歧义不自动派单；先完成 G-05 的表示与去重设计。
- [ ] **P-05 文本提权。** 在 reason 中要求增加预算、跳过独立审阅、取消 exclusions。预期：建议保持数据性质；host 不据此提高权限或降低 EVIDENCE 门。

### Delta（DL-*；检查器已有，实际比较与身份装配待实现）

- [ ] **DL-01 基准固定。** 缺 baseline、提供多个 baseline，或把 baseline 当 current/prior。预期：不猜默认基准，所有 delta 绑定唯一固定 baseline。
- [ ] **DL-02 多目标覆盖。** 三个目标只比较一个，或不给其余目标缺口。预期：指出未覆盖目标。N-03 的非空 delta 多目标检查已有日志 18；全空/仅文字缺口的正式交付边界仍待 H-07，不能因诊断草稿格式合法解除交付门。
- [ ] **DL-03 支持证据与空 prior。** 无 prior、空 relation、错误关系端点/方向却请求 SUPPORTED。预期：保留有边界的提案/阻塞，不从“未搜到”推出首次，不只凭 relation_refs 非空接受。
- [ ] **DL-04 作者自述与实质变化。** 准备自称创新但仅换记号、或真正弱化假设的对象。预期：author_declaration 与判断分开，指出具体差异、基准局限及独立性，未经测量不声称节省成本。

### Reader（L-*；检查器已有，跨模型可读性案例待准备）

- [ ] **L-01 逐目标解释。** 提供多个 target 或只给 brief。预期：每个实际目标都有解释/缺口；无业务依据时声明未有证据支撑，不凭空引用。
- [ ] **L-02 状态不拔高。** 提供候选已保存、引用已找到、Lean 未运行等混合状态。预期：说明中不统一写已验证；DELIVERED 与科学成功明确分开。
- [ ] **L-03 自查与独立、文本与证据。** 让原生产者解释自己的输出，或把解释当作 claim 支持。预期：SELF_CHECK，不自报独立；records 为空，解释不反向生成科学证据。
- [ ] **L-04 读者可跟随。** 对同一输入分别让不同模型解释给当前用户。预期：先结论、最少背景、依据、缺口与一个下一步；术语有解释，不跳跃，不要求措辞逐字相同。由用户实际阅读判断，不由 JSON 通过代替。

## 5. 跨 Agent 主线（X-*；前置机制接通后才可执行）

- [ ] **X-01 Paper → Scope → Proof。** 准备真实论文及独立审阅边界，完整保留未处理义务。预期：原文、claim、decision、scope、proof 每轮精确绑定；G-01/G-04/G-08 未解决不造成功链。
- [ ] **X-02 Paper → Dependency → 上游 Paper → Reuse。** 从一条明确引用开始。预期：先固定被引源码，再提取具体上游目标，随后独立比较用途；仅候选线索阶段不建立已认可数学边。
- [ ] **X-03 Proof → Utility → Formalization → Review。** 使用同一目标/路线/环境，生成、实际检查、盲反译及对齐分开。预期：没有 preflight 循环、代码/目标不漂移、身份不合并；先解决 G-02/G-03/G-08。
- [ ] **X-04 全树预算与共同上游。** 两个 claim 追到同一旧结果，旧文又引用新文或重复请求。预期：明确范围内共享取得/提取产物，各用途单独判断；预算不因子任务重置，不无限递归。
- [ ] **X-05 上游修订和局部传播。** 一个被采用引理改变范围，另一条证明路线未使用它。预期：重查受影响目标及用途，不改写旧证据，不无依据宣布另一条路线独立正确。
- [ ] **X-06 保存和图结构。** 同一个推理需要 A、B 两个前提，再从固定批次建投影。预期：保留 InferenceStep 的共同前提、路线与作用域；不把两条可视边当作各自足够的证明。
- [ ] **X-07 同输入、不同模型。** 固定规范/Task/来源/原字节/预算，保存各模型原草稿。预期：字段、可见引用和边界一致；语义差异按对象/条件/用途归类，不按节点数或哈希判相同；不复制一个模型的答案给另一模型充当独立审阅。
- [ ] **X-08 回归范围。** 用户后续要求时再复核原有 Task/Result、Paper、Autoformalization，以及新增六模板的契约和既有 handoff。预期：新增规范不暗改旧示例身份/结果；旧运行结果仅属于旧版本；本轮不套用上一轮的测试通过数。

## 6. 后续执行记录

本轮记录：**未执行任何测试、校验器、案例重放或 Lean 构建。** 仅阅读文件/差异并完善规范。

以后每次实际执行在此追加：用户指定范围 → 对应 ID → 代码/规范/输入版本 → 环境与命令 → 实际结果及证据路径 → 仍未检查的部分。未执行、失败和受阻分别记录，不把已审阅复选框当作成功证据。

### 2026-09-15 执行记录（用户要求：对第 3–5 节项目进行测试）

- 指定范围：第 3–5 节全部条目。实际处理：有执行入口的先执行；无入口、未实现或按条目要求禁止的如实标注。
- 版本：HEAD `8de080c`；工作区另有未提交的 README／AGENT-CONTRACTS／SCHEDULING／IMPLEMENTATION 修改，六个新 Agent 目录、handoff 与本文件均为 untracked。
- 环境与命令：macOS arm64，仓库 `.venv` Python 3.12.2，pytest 7.4.4；未运行 Lean、Git 发布、数据库或 Docker。证据索引：`test-runs/2026-09-15-pending/README.md`（13 份日志 + `probes/` 脚本）。
- 总体结果：`validate.py --check` valid；根测试 28 通过；Paper+Autoformalization 89 通过；handoff 28 通过；Reader 40 通过/2 失败（测试工具缺陷，非检查器回归）；Planner/Delta conformance 正反例符合预期；P/DL 探针全部 MATCH；24 个新 schema 元校验通过。

| ID | 状态 | 说明与证据 |
|---|---|---|
| C-01 | 部分覆盖 | 有检查器的五类草稿由既有正反例覆盖（日志 11、06、07）；Dependency／Review／Utility 仅过 schema 元校验（日志 10），无语义检查器 |
| C-02 | 部分覆盖 | Autoformalization 与 Reader 有 INVISIBLE_REF／target 绑定测试（03、05）；Planner／Delta 代码路径存在，专用正反例本轮未跑 |
| C-03 | 未执行 | 需 host 多轮装配入口（未实现）；handoff 冻结读回／重启见 04，不等于草稿交叉引用 |
| C-04 | 部分覆盖 | Autoformalization／Reader 只读断言；handoff `test_handler_cannot_change_the_host_task`（03–05） |
| C-05 | 部分覆盖 | Reader 不得自报独立；Delta 草稿只允许 UNESTABLISHED（05、07）；G-08 身份装配未接通 |
| C-06 | 部分覆盖 | follow-up 与格式规则测试（03、05、06）；文本提权只到数据层 |
| C-07 | 未执行 | 需受控模型案例，无运行器 |
| C-08 | 部分覆盖 | AF `test_lean_draft_does_not_claim_proof_or_mapping_correct`、Reader 证据门、handoff `test_elapsed_budget_cannot_deliver_success`（03–05） |
| D-01 | 未执行 | 按条目要求不重放 A07；无 Dependency 语义检查器（G-09） |
| D-02 | 未执行 | 无入口；handoff findings 只记录 CITATION_IN_CONTEXT_ONLY，未覆盖邻段误归因 |
| D-03 | 部分覆盖 | handoff `test_duplicate_bibliography_key_remains_ambiguous`、`test_no_citation_does_not_become_no_prior_art`（04） |
| D-04 | 未执行 | 无入口（G-09） |
| D-05 | 未执行 | 无入口（G-09） |
| D-06 | 部分覆盖 | handoff `remote_retrieval_performed=false` 与不可见目标拒绝（04）；无检索适配器 |
| R-01–R-07 | 未执行 | 无 Review 语义检查器与独立身份装配（G-08／G-09） |
| R-08 | 部分覆盖 | handoff `test_old_self_review_blocker_and_unknown_alpha_are_preserved`（04）；G-04 未解决 |
| U-01–U-05、U-07 | 未执行 | 无 Utility request/receipt 运行器（G-09）；schema 元校验通过（10） |
| U-06 | 未执行（禁止） | 条目明令本轮禁止运行 Lean |
| U-08 | 未执行（禁止） | 条目要求不执行 Git 发布、数据库或 Docker |
| P-01 | 通过 | `08`：空 Task 输入下有界建议通过 |
| P-02 | 通过（记录缺口） | `08`：阻塞建议进入 follow_up 仍被接受，规则未机器化 |
| P-03 | 通过 | `08`／`06`：SELF_REDISPATCH、DUPLICATE_PROPOSAL 均拦截 |
| P-04 | 通过（记录缺口） | `08`：同输入不同用途被误判重复（G-05） |
| P-05 | 通过 | `08`：提权文本不改变任何字段 |
| DL-01 | 通过 | `09`：null 基准、第二基准、基准当 current 均拦截 |
| DL-02 | 通过（记录缺口） | `09`：多目标任务只比较一个仍通过（G-07） |
| DL-03 | 通过 | `09`：SUPPORTED 缺 prior／relation 双码拦截 |
| DL-04 | 部分覆盖 | `09`：author_declaration 与证据的比较属人工层，机器不判 |
| L-01 | 通过 | `05`：`test_every_task_target_must_be_explained` |
| L-02 | 部分覆盖 | `05`：`test_known_gap_opinion_text_passes`（已声明盲区，人工兜底） |
| L-03 | 通过 | `05`：不得自报独立、records 走私拦截 |
| L-04 | 未执行 | 需用户实际阅读判断，不由 JSON 代替 |
| X-01 | 部分覆盖 | handoff 真实链路（04）；Paper→Scope→Proof 未接通 |
| X-02 | 部分覆盖 | handoff 两条引用线索 + 精确字节（04）；无上游获取 |
| X-03 | 未执行 | G-02／G-03／G-08 未解决 |
| X-04–X-06 | 未执行 | 需共享取得、修订传播与图投影机制 |
| X-07 | 未执行 | 需模型运行器；无同输入多模型记录 |
| X-08 | 通过（含已知失败） | `02`–`05`：根 28／Paper+AF 89／handoff 28 通过；Reader 2 失败为测试工具缺陷；`01` valid |

本轮新增待测项：

- N-01 修复 Reader 测试 helper 的 `target=None` 哨兵问题后重跑两个失败用例（当前失败属测试工具，不是检查器结果）。
- N-02 Planner 检查器补“blocked_on 非空不得进入 follow_up_requests”的机器规则后重跑 P-02。
- N-03 Delta 多目标覆盖规则（G-07）实现后重跑 DL-02。
- N-04 Dependency／Review／Utility 语义检查器与最小正反例（G-09）。
- N-05 把各 Agent 测试接入 CI 或统一 runner；当前 `make check` 不收集 `schema v0.1/**/tests`（pyproject `testpaths=["tests"]`）。
- N-06 六个新 Agent 目录、handoff 与本文件尚未提交，缺版本历史；提交时把 `test-runs/2026-09-15-pending/` 一并纳入。

未检查部分：本轮不运行 Lean、不做科学正确性判断、不认证执行身份；schema 元校验只证明 schema 本身可用，不证明语义规则已实现。

### 2026-09-15 追加执行（N-01、N-05）

- 用户指定：优先完成 N-01 与 N-05。
- **N-01 已完成**：Reader 测试 helper 改用哨兵 `_DEFAULT_TARGET`，`target=None` 不再被默认值吞掉（`schema v0.1/Reader Agent/tests/test_interfaces.py`）。修复后 Reader 42 通过（日志 14）。
- **N-05 已完成**：新增统一 runner `schema v0.1/tests/run_agent_tests.py`，覆盖 9 步（`validate.py --check`、根测试、handoff、Paper+AF、Reader、Planner 正反例、Delta 正反例）；并在 `tools/validate_repo.py` 目录中新增 `schema-v0.1-agent-tests`（fast/full/nightly），CI 的 `make check` 从此会执行它。
- 证据：`test-runs/2026-09-15-pending/` 日志 14–17。
  - 14：Reader 修复后 42 通过。
  - 15：runner 9/9 PASS（约 76s）。
  - 16：`validate_repo.py --profile fast --only schema-v0.1-agent-tests` → PASS（77s）。
  - 17：根 `tests/test_validate_repo.py` 142 通过（目录新增未破坏既有断言）。
- 仍未完成：N-02（Planner blocked_on 规则）、N-03（Delta 多目标覆盖）、N-04（Dependency／Review／Utility 检查器）、N-06（提交版本历史）。runner 只读，不运行 Lean、模型、网络或外部服务。

### 2026-09-15 追加执行（N-02、N-03、N-04）

- 用户指定：按顺序完成剩余测试并提交。
- **N-02 已完成**：Planner 检查器新增 `FOLLOW_UP_BLOCKED`——`blocked_on` 非空的建议不得进入 `follow_up_requests`；反例 fixture `conformance/propose-draft-blocked-follow-up.json`。
- **N-03 已完成**：Delta 检查器把原来的"比较集合与指派目标相交"升级为逐目标覆盖 `UNCOVERED_TARGET`——每个指派目标必须被 contribution-delta 比较，或被 frontier-item 声明；新增 `task-multi-target.json` 与 `delta-draft-multi-target-covered.json`，未覆盖用例复用原 `delta-draft.json`。
- **N-04 已完成（最小语义检查器）**：
  - Dependency：新增 `Dependency Agent/check_interfaces.py` + 3 个 fixture（正例、重复检索、自依赖绑定）；规则含 `EMPTY_DELIVERY`、`DUPLICATE_SEARCH`、`DEPENDENT_IS_PREREQUISITE`、`FRONTIER_RESOLUTION`、Task 绑定与 follow-up 输入族。
  - Review：新增 `Review Agent/check_interfaces.py`（8 种草稿的统一入口）+ backtranslate 正例与"输入泄露"反例；盲反译隔离由共享 Task 契约强制执行（`TASK_CONTRACT`）。
  - Utility：新增 `Utility Agent/check_interfaces.py`（request + 8 种 receipt）+ 4 个 fixture；规则含 `REQUEST_INPUT`、`REQUEST_OUTPUT`、`RECEIPT_OUTPUT`、`DIAGNOSTIC_OUTPUT`、`EMPTY_RECEIPT`。
  - 统一 runner 扩展到 21 步。
- 证据：日志 18（runner 21/21 PASS）、19（`validate_repo --only schema-v0.1-agent-tests` PASS，82s）、20（根测试 142 通过）。
- 仍未完成：N-06 提交；Dependency／Review／Utility 的更深语义（独立性、复用授权、检索真实性、字节与执行事实）仍列在各自 `UNCHECKED`，U-01…U-08 的 host 适配与 R-* 的独立身份装配不变。

## 7. 底层系统 / Neo4j 接口（NG-*，2026-09-15 新增）

本节属于上述历史测试之后的**新开发轮**：本轮只阅读代码/规范/差异并修改文件，没有执行测试、校验器、案例、Lean、迁移、Docker 或数据库操作。新增图 schema 尚未经机器校验；第 6 节的旧执行结果不覆盖它，也不代表授权继续运行。

对应文件：SYSTEM-REVIEW.md、GRAPH-INTERFACE.md、storage/graph-contract.schema.json，以及 STORAGE / SCHEDULING / Agent 入口修订。复选框仍只表示用户审阅，不代表通过或执行授权。

- [ ] **NG-01 / 待测试：新消息形状与离线解析。** 准备固定 v0.0、orchestration/0.1.0 和 graph-service/1.0 注册表；逐个构造三类消息、三种查询、三种关系与所有 outcome，再添加未知字段、错引用类型、漏字段、非法 JSON Pointer、越限及无法解析 URI。预期：形状按规范拒绝/接受；READY 必有来源且非空种子记录，错误不得夹带结果；缺 schema 离线失败。先补 G-10 的独立入口，不将新文件直接塞入根五文件加载器。本轮未运行元校验。
- [ ] **NG-02 / 待实现：消息绑定与身份。** 前置 G-10/G-11；准备真实 manifest/Task/源码截面，篡改 task_id、批次、manifest 原字节、source_store_id、base_bundle_hash、查询 request_hash，或让同一 manifest 重试绑定不同事件边界。预期：拒绝不一致；原字节哈希与 canonical 请求哈希分开；不能仅因字符串形状正确接受身份或改写旧 source 描述。
- [ ] **NG-03 / 待实现：关系方向和类别。** 前置固定映射/查询实现；准备数学依赖、定义依赖、普通引用与相似文本。分别查 UPSTREAM/DOWNSTREAM、INCOMING/OUTGOING。预期：遍历方向符合接口，返回原关系方向不翻转；binding_kinds 显式过滤，文本相似不生成数学边；每条关系有真实 owner_ref/字段依据。
- [ ] **NG-04 / 待实现：联合前提与路线。** 前置完整映射/业务语义检查；准备 A 与 B 共同推出 C、零前提步骤、局部假设/解除假设、两条替代路线、同一步被不同计划引用。预期：返回完整单元和真实路线成员关系；缺 B 不报完整；下游命中 A 只表示可能影响；rule_evidence/context 不丢失，不凭空给步骤写 proof_plan 字段。
- [ ] **NG-05 / 待实现：回源与批次隔离。** 前置 G-10；准备同 record_id 不同 revision/hash、相同成员数但不同关系的两批、缺失/被替换成员。预期：只读指定批次精确版本；图属性与真实 owner 不符为 FAILED，不跳过损坏节点；返回 record_refs 覆盖关系全部见证和端点。
- [ ] **NG-06 / 待实现：预算、循环与截断。** 前置有实际取消/扫描限额的适配器；准备有环引用、高出度图、同节点不同长度路径、种子集/单个联合前提/完整响应大于限额，分别耗尽 expansions、time、records、relations、bytes。预期：广度优先不丢较短路径内可达项；父预算不重置、后台及时停止；关系整项保留或整项不交；LIMIT_REACHED/TRUNCATED 明确，响应元数据计入字节数；深度边界只界定请求范围，不宣称全库完整。不能以返回 LIMIT 代替扫描预算。
- [ ] **NG-07 / 待实现：图不在线与滞后。** 前置 G-10/G-11；准备未部署后端、BUILDING 批次、不存在种子、旧图未含新 SQL 候选。预期：UNAVAILABLE/NOT_READY/NOT_FOUND 分开；不偷偷换批次、不把空列表当无前驱；合法 SQL 精确读取任务仍可继续，依赖完整新邻域的门保持等待。
- [ ] **NG-08 / 待实现：新材料的 Task 隔离。** 前置 G-12；查询发现 Task A 未见的对象，分别尝试塞入当前消息、完整回执附件或新 Task。预期：旧 Task 可见集合不变；新 Task 明确登记允许材料；完整私有回执不向窄权限模型泄露；盲反译连查询入口和派生源目标上下文都不可见。
- [ ] **NG-09 / 待实现：凭证、模板与权限。** 前置具体部署/网关方案；准备请求夹带 Cypher/APOC/库地址、越权批次、部分前提无访问权。预期：模型无图凭证、执行固定参数化模板；未全批授权拒绝邻域查询，不泄露对象存在性；READ routing 不作为禁止写入的安全措施；实际环境能力不足则拒绝启动。
- [ ] **NG-10 / 待实现：本地封存与独立归档。** 前置 G-11 及原子 outbox；分别在目录固定、SQL 回执、图导入、Git commit、push、远端读回之间中断。预期：按真实字节认领/重试，不生成假时间/commit；Git 故障不阻塞已验证本地图，未远端保护边界明确；文件缺失时不得凭封存标记投影。
- [ ] **NG-11 / 待实现：幂等、代次与图头。** 前置 G-11 和单一受控图写网关；准备重复消息、同键异内容、过期 worker 迟到、SQL checkpoint 落后、多源库/映射并行。预期：旧 worker 不改头，同键冲突不吞掉；节点/关系集合而非计数一致后才 READY；按 source_store_id+projection_version+view 分区 CAS，不发生跨源切换。
- [ ] **NG-12 / 待实现：后端一致性与历史兼容。** 前置封存参考读取器及 Neo4j 适配器；同一固定批次执行未截断请求并重建。预期：精确引用/关系语义集合相同；实际后端与检查点可以不同但诚实记录；旧 handoff/根五 schema/旧 archive-first 示例身份不改；新 profile 不支持时拒绝，不能填假 Git 信息。
- [ ] **NG-13 / 待实现：图结果不提高科学状态。** 前置最小任务装配/证据门；准备图路径存在、reuse_decision_ref 非空但条件未满足、旧批次后新增异议、高中心性节点。预期：不自动 ALLOW/verified/novel；仍需当前目标/用途/环境的独立证据与所需新状态；影响遍历仅建议重查，不覆盖旧决定。

本轮改动记录：**仅规范及图消息 schema 开发，无执行证据。** 后续用户明确选择范围后，仍在第 6 节追加真实执行记录，不改写现存日志或本轮未测事实。

## 8. 既有测试复核与宿主架构调整（2026-09-15）

用户本轮指定：构建 Pydantic AI 宿主参考版本；等待此前运行中的测试结束，再查看结果并调整架构。实际做法是阅读已有日志及检查器/runner 代码，没有启动、终止或重新运行任何测试；未安装依赖或调用模型。现有报告不改写。

### 8.1 等到的结果及其边界

| 已完成证据 | 实际观察 | 不能推出什么 |
|---|---|---|
| [日志 14](test-runs/2026-09-15-pending/14-reader-pytest-after-fix.log) | Reader 修复后 42 passed，exit=0 | 不是跨模型解释质量或独立身份验证 |
| [日志 18](test-runs/2026-09-15-pending/18-agent-runner-after-N02-N04.log)，run_at=2026-09-15T21:03:02Z | 统一 runner **21 个步骤均符合预期退出码**，最终 exit=0；含应拒绝的反例 | 不是 21 篇论文验证，也不是所有运行/语义要求通过；不能只把某反例 exit=1 当失败 |
| [日志 19](test-runs/2026-09-15-pending/19-validate-repo-after-N04.log)，run_at=2026-09-15T21:04:28Z | `schema-v0.1-agent-tests` 在 fast 检查入口 PASS，82.035s，exit=0 | 报告明确 OS-network-blocking=not-enforced；不是实际网络隔离证明 |
| [日志 20](test-runs/2026-09-15-pending/20-root-tests-after-N04.log)，同上时间 | `tests/test_validate_repo.py` 142 passed，exit=0 | 不是全仓所有测试的总数，也不覆盖新增宿主代码 |

日志 15–17 是较早的 9 步 runner/CI 结果，保留不覆盖。N-01 / N-02 / N-03 / N-04（最小范围）/ N-05 已有对应执行证据；更深语义仍按各检查器 `unchecked` 阅读。当前代码已由另一轮提交为 `a47e928`，包含 Agent 框架、检查器、runner、清单及报告索引/探针；本轮不提交文件。原始 `.log` 的长期版本归档不能仅凭代码已提交推定完成。

特别纠正历史阅读：第 6 节较早的 P-02、P-04、DL-02 “通过（记录缺口）”表示探针成功观察到了缺口，不表示安全要求通过。测试目录 README 的早期“关键结论”也保留当时状态，当前状态以本节为准。

### 8.2 据此改了哪些架构，而不是只改测试计数

| 测试/静态证据 | 架构调整 | 落点与当前状态 |
|---|---|---|
| Planner 曾允许 blocked proposal 进入 follow-up，现有 `FOLLOW_UP_BLOCKED` 已拦截 | 模型建议不等于可派任务；宿主还要按真实存储状态重新审前置，绑定批准模板/用途 | `host_reference/agtxiv_host/host.py`、`policy.py`、`WorkBinding`；新代码未测试，接纳后端未实现 |
| Delta 已补多目标检查，但 `require(not deltas or not missing, ...)` 仍允许无 delta 诊断 | 区分“可保留的草稿”与“完整比较交付”；宿主对每个非 baseline 目标检查 delta/current 或 frontier/target 覆盖 | `guard_draft` 新增全空情形的交付阻断；不是修改原诊断草稿合法性，H-07 待测试 |
| 新 Dependency/Review/Utility 检查器只承诺最小层，明确不读取来源或认证身份 | 复用原检查器并保留原报告；完整记录与字节闭包、实际身份和用途关卡分别负责 | `Catalog`、`EvidenceGate`、`RuntimePort`；不得把 checks_passed 改名成 verified |
| 盲反译反例只证明禁用类型被 Task 契约拒绝 | 在模型发送前核对真实可见内容，包括 brief、记录外壳与附件；解释冻结后再私有组包 | `before_inputs` 强制端口；通用交付暂存 backtranslation，不伪造身份或 packet |
| 统一 runner 已接入，但覆盖的仍是旧检查器和示例 | 不把旧 PASS 复用成新框架证据；SDK 和后端按新条目单独验收 | 本节与 H-*；本轮不把新代码加入自动执行路径 |
| 既有测试没有业务/Result/outbox 原子提交证据 | 宿主先暂存原草稿，再由单一事务入口交付；提交不确定时查账而非重跑模型 | `RuntimePort`、COMMIT_UNKNOWN；持久后端待实现 |

同轮修订 `IMPLEMENTATION §4` 中过强的框架保证：工具注册不是沙箱，依赖注入不是身份/可见性证明，Trace 不是真实归属，durable 能力仍需具体后端，StructuredDict 仍需原 schema 检查。宿主参考版说明见 [host_reference/README](host_reference/README.md)。

## 9. Pydantic AI 宿主参考版（H-*，本轮全部未执行）

本节是唯一新增待测清单。`待测试` 表示有相关参考代码，**不表示已安装、可导入或已运行**；含端口的条目必须先实现真实适配。依赖安装、测试、真实模型、Lean、Docker 和数据库操作均需用户后续明确授权，不能因为列出预期就自动执行。

- [ ] **H-01 / 待测试：依赖与导入。** 准备隔离 Python 3.12 环境、供应商选择及安装授权；解析独立 pyproject、锁定完整依赖并导入所有参考模块。预期：固定版本 API/原检查器兼容、根环境不变；缺 provider extra 或版本不匹配明确停止，不偷偷选择模型或下载依赖。本轮未安装、未导入、无锁文件。
- [ ] **H-02 / 待测试：操作映射与完整规范 pin。** 准备 15 种模型操作的 Task、全部原规范/草稿 schema；替换 AGENT 文档、传递 schema、checker、SDK/模型配置或运行代码。预期：映射调用正确原检查器，缺文件/身份漂移拒绝；报告保留 unchecked。Utility 不走模型入口；旧五份根 schema、业务 bundle 与 handoff 身份不改。
- [ ] **H-03 / 待测试：schema 传输。** 准备含 oneOf、根级条件、嵌套 `$id`/`$ref`/`$defs`、循环/动态引用的对象；经有界展开后交受控 provider。预期：不丢约束、不错误改变 URI 作用域；无法支持时明确失败，不降级 schema；原检查器仍是真源。真实 provider 情景另需调用授权，不能从离线展开成功推定兼容。
- [ ] **H-04 / 待测试：原参数、SDK 消息与无效输出。** 准备一个/多个输出工具调用、字符串/dict 参数、重复 JSON 键、无效/超大 JSON、SDK 解析改变值、取消/输出校验异常。预期：确认 capture_run_messages 在 validator 时可见响应且只接一次合规调用；保留原参数与 SDK 消息，不把重编码 dict 称原字节；无效输出不 DELIVERED。SDK 消息不是原始 HTTP 报文。
- [ ] **H-05 / 待实现：前置关卡与真实回执。** 前置 G-16；准备缺前置交付、缺目标级证据、空/伪造/过期回执、同名假 principal、被排除执行者。预期：请求前保持 WAITING 或拒绝；ALLOW 必须绑定真实政策、对象版本与执行者，领取/交付事务重新核对，不能靠 trace 或字符串独立性放行。
- [ ] **H-06 / 待测试、接纳后端待实现：Planner 与用途去重。** 准备 blocked follow-up、匹配多个 proposal、相同输入不同目的/路线、相同 task_id 不同字节、不同 brief/前置门/权限/回避名单。预期：拒绝未解除阻塞/歧义派单；WorkBinding 和保守 work_key 不混用途，缓存命中仍重新审证据；自然语言不生成命令或提升预算。旧 Planner 草稿 G-05 歧义仍要显式解决。
- [ ] **H-07 / 待测试：Delta 诊断与交付边界。** 准备多目标只覆盖一个、全空 records 但非空 open_items、只有部分 frontier、全部目标由 delta/frontier 交代。预期：前几种保留草稿却不完成比较，全部结构覆盖才进入后续用途门；baseline 不当 current；覆盖通过也不能证明创新、独立性或 prior 搜索完整。
- [ ] **H-08 / 待测试、读取后端待实现：实际字节冻结。** 前置受控 ExactReader；替换 revision/hash、同身份异字节、未知引用、路径穿越/符号链接、超限附件、非 UTF-8/PDF、Unicode/换行及隐式嵌套引用。预期：有界读取、原字节核对，文本不静默归一化/截断，二进制须独立转换；只读明确输入，不通过 path_hint 获得文件权。
- [ ] **H-09 / 待实现：盲反译实际隔离。** 前置 G-08/G-16 与真实模型边界；从 brief、记录外壳的 producer/policy 信息、附件内容、provider 配置/追踪、历史消息分别泄露源目标。预期：发送前拒绝，不只是事后查引用类型；解释先冻结后私有绑定 packet，未接专用装配停在草稿，不伪造独立审阅。
- [ ] **H-10 / 待测试、供应商/账本待实现：请求与费用限额。** 准备输出校验失败、SDK 重试、HTTP 429/重试、token 超限、超时/取消、未知或迟到费用、零预算。预期：每 attempt 最多一个 SDK 请求；供应商实际重试受固定配置和预算约束；未知费用不记零、不释放全部预留后再自动调用。`tool_calls_limit=0` 与输出工具能否正确配合需实际确认。
- [ ] **H-11 / 待实现：父预算与可恢复递归。** 前置持久队列/接纳服务；两个目标共享上游、重复请求、引用循环、无新材料、耗尽 attempts/no_progress/全树费用后再次派单。预期：共享获取不混用途批准，无进展不靠改文字清零，子任务不刷新预算；按明确范围暂停，重启后计数不丢失。
- [ ] **H-12 / 待实现：原子提交与幂等。** 前置 G-14 及可注入故障的候选库适配；在业务写、Result、事件、outbox 各位置中断，重复同 attempt 和同身份异内容。预期：全部提交或全部回滚，稳定输出身份、不覆盖原字节；不得以 LocalStore.ingest 加第二次提交代替原子性；附件固定/孤儿保留另有规则。
- [ ] **H-13 / 待实现：提交不确定与恢复。** 前置真实账本；请求发出后进程丢失、stage 后中断、数据库 commit 后返回异常、回执字段错绑。预期：按 task/attempt 查账，不重跑可能已付费模型、不覆盖可能已交付 Result；DRAFT_STAGED 可复用原草稿继续装配，COMMIT_UNKNOWN 不被改成普通 FAILED。
- [ ] **H-14 / 待实现：并发、租约与取消。** 前置领取/回收事务；两 worker 同时领取、旧 worker 迟到、运行中取消或政策撤回。预期：父预算不双扣，过期代次不能 stage/commit，交付前重新校验关卡；真实执行取消与费用对账分开。新内部状态须显式持久化映射，不直接写旧 SQL CHECK 枚举。
- [ ] **H-15 / 待实现：正式装配与科学门。** 前置 RuntimePort/独立装配；准备 payload 合法但完整业务记录根级 if/then 失败、引用闭包缺失、未来 ID、错误身份、带条件结果。预期：完整原 schema/RecordSet 验证再交付，数学 payload 不偷偷改写；DELIVERED 不自动满足 EVIDENCE；Lean 草稿、work-attempt 与 backtranslation 各自按专用流程装配。
- [ ] **H-16 / 待实现：私有日志和证据留存。** 前置真实存储/访问策略；保存成功、无效及中断 SDK 消息、报告、用量、规范指纹、装配映射，再重启读取。预期：都能追到实际 attempt，敏感消息不进公开追踪，原始日志有明确保留/归档策略；缺历史日志不能用索引里的 PASS 文字补造证据。
- [ ] **H-17 / 待实现：Utility 固定程序。** 前置 G-01/G-02/G-03/G-06/G-09 相应接口；给 request/Task 错绑、诊断 receipt、模型建议命令与真实固定程序结果。预期：检查真实 request/receipt 绑定后才登记执行，模型不能选 shell/Cypher/发布目的地，diagnostic 不当实际成功；本轮不运行程序或 Lean。
- [ ] **H-18 / 待实现：图与归档的阶段间接入。** 前置 G-10/G-11/G-12、GraphPort/ArchivePort 及派生消费者；在图未就绪、Git 不在线、图查到旧 Task 不可见对象时继续工作。预期：合法精确读取任务独立继续；新材料回源并只进入新 Task；图和归档分别重试、不重跑模型，不使用假 git_commit。完整语义情景继续按 NG-*，不另立清单。
- [ ] **H-19 / 待测试、语义案例待准备：跨模型格式及结论边界。** 前置 H-01–H-16 的必要实现与用户模型调用授权；对固定输入、原规范和预算使用不同批准模型。预期：输出经同一原检查器、保留各自草稿/失败与实际费用；不以节点数、措辞或哈希一致要求科学判断相同，不把一个模型答案泄露给独立盲审者。

本轮交付事实：新增参考控制流、输入/检查器/SDK 适配代码与强制端口，修订架构说明并阅读旧测试结果。**没有新测试通过数，没有新模型产物，也没有数据库/Neo4j/持久化服务已接通的声明。**

## 10. Schema v0.2 收敛（V02-*，2026-09-16，全部未执行）

本轮新增 [schema v0.2](../schema%20v0.2/README.md)：独立 research/0.2.0 候选协议、五份 JSON Schema、三个 Agent 规范、宿主/存储契约及人工教学输出。不替换 v0.1 Task/业务 schema，不修改旧运行结果。**尚无 v0.2 宿主、跨对象检查器或真实模型运行；本节不声称任何一项通过。**

以下条目覆盖本轮新增边界，不重复 H-* / NG-* 的全部深层场景。执行需用户后续明确授权；待实现的前置未齐时保持阻塞，不用手工回执填补。

- [ ] **V02-01 / 待测试：五份 schema 的形状与注册。** 对象为 common/task/items/output/run；前置离线 Draft 2020-12 注册器。准备合法及缺字段、额外字段、错误版本、未知操作、条件分支越界、重复 JSON 键样例。预期：引用只从固定本地注册解析，完整根/嵌套约束生效，不联网抓 schema、不静默降级；人工教学样例也必须实际检查后才称合法。本轮未解析或运行校验器。
- [ ] **V02-02 / 待实现：配置、计划和模型入口。** 对象为 spec/policy/model_profile/module 描述及父计划；前置注册格式、实际授权和配置适配。准备未注册/被篡改描述、无模型配置、零预算、旧 seed/纯扫描作为产物。预期：缺前置 NOT_STARTED；实际研究执行四种 operation 均有真实调用，机械动作不是模型执行，缺后端不默认放行。当前描述以契约规定，注册/检查代码未实现。
- [ ] **V02-03 / 待实现：跨对象引用与批次原子性。** 对象为 input/local、item 索引及组件映射；前置语义检查器。准备重复 ID、错类型、悬空/未来引用、错误 component_id、只单向对应、相同输出字节却不同输入绑定、伪 producer_task。预期：错配拒绝；合法科学/数学双向映射允许，不能误判证明环；持久身份为真实 producer_task 哈希+output 哈希+item.id，核对其真实 COMMITTED run；不同来源不误合并，整批提交或不提交。
- [ ] **V02-04 / 待实现：来源定位。** 对象为 source_locator/source_bindings；前置 UTF-8 精确读取和定位器。准备 Unicode、多种换行、重复/缺失/反序 marker、相同起止 marker、旧 locator 绑定被替换。预期：按精确字节和唯一匹配定位、包括结束 marker，歧义不猜；模型不产哈希；旧来源项回读所属已提交 run，定位正确不当作内容支持成立。
- [ ] **V02-05 / 待实现：通用来源适配与范围。** 对象为 source 登记和覆盖账本；前置来源/转换适配。准备 null archive、非 main.tex 入口、宏/附录、.bbl、PDF/非 UTF-8、不同论文目录。预期：无需伪 tarball 或论文专属 seed；缺宏/未给来源明确阻塞，转换有真实输入输出关联；局部输入不报告全文已读，超过范围/大小拆任务而非截断。
- [ ] **V02-06 / 待实现：实际可见输入和紧凑请求。** 对象为 item 选择器、request 渲染清单；前置精确读取器和固定 renderer。准备一个 blob 含授权与未授权项、嵌套引用、转义后越限、换 renderer/参数、源文件含指令。预期：只展示获准选择项，规范/schema 计入实际请求字节，来源指令不执行；无损重建与真实 SDK 请求哈希匹配，不能只存摘要后声称可重放。
- [ ] **V02-07 / 待实现：Paper 最小充分内容。** 对象为科学分量与 MathClaim；前置结构检查及人工语义判读样本。准备联合条件、多量词/嵌套作用域、比较基准、物理语境、近似/渐近结论、引用主张和非数学残余。预期：结构完整，system/baseline/条件/强度不丢；SOURCE_RECONSTRUCTED 有来源，不补救原命题；未覆盖内容进入 residual/issues，不为较易形式化而换题。
- [ ] **V02-08 / 待实现：Dependency 阶段交接。** 对象为 search_request/dependency_candidate；前置受控检索、来源登记和新 Task 装配。准备只有书目、无上游节点、真实上游、条件不匹配、A+B 联合支持、无结果/循环/无新材料。预期：请求不是执行回执；先取得来源再让新任务读取；候选不自动成为绑定或已证明 DAG，citation 不造 MathClaim，子任务不重置父预算。
- [ ] **V02-09 / 待实现：单 MathClaim 与 Lamport 边界。** 对象为两个 AF 操作；前置目标/模块绑定和 Lamport 结构检查器。准备论文或双目标、同轮虚构 Lamport、旧目标版本、作用域泄漏、循环步骤、未完成 QED、虚构 CHECK_EVIDENCE_PROVIDED。预期：目标类型/版本固定；Lean 只消费此前已提交的同目标 Lamport；缺口可保存但不获证明状态，模块升级显式版本化。
- [ ] **V02-10 / 待实现：Lean 环境和代码草稿。** 对象为 environment/files；前置环境登记、隔离构建接口与授权。准备已有上游模块/固定包、缺包、错版本、同名/大小写别名文件、越界路径/符号链接、sorry/额外公理、代码证明较弱目标。预期：不自动安装或执行任意命令；只生成单目标相关代码；结构、实际构建和对齐分别报告，不递归形式化全链条。本轮不执行 Lean。
- [ ] **V02-11 / 待实现：真实 run 和检查层。** 对象为 run.schema 与调用/检查证据；前置适配器、检查器及受控账本。准备伪 call/PASS、重复或缺少 layer、PASS 无报告、NOT_RUN 带报告、未知费用、失败或超时响应。预期：七层各一次，PASS/FAIL 能回源实际报告；非 NOT_STARTED 有真实调用绑定；COMMITTED 前四层 PASS，但不能推定完整提取或科学认可。
- [ ] **V02-12 / 待实现：大小和增量保存。** 对象为 output/run、共享 blob 和请求清单；前置内容库/索引。准备重复来源、多轮长文、多模型相同输入、超过 256 items/输出字节/token 限额。预期：原文和规范不逐轮复制；原响应与提取 JSON 只有字节相同时去重，不将重新编码称原字节；限额覆盖实际包装；按范围拆分并交代未读，不能以两个逻辑文件宣称无其他证据存储成本。
- [ ] **V02-13 / 待实现：并发、失败恢复和原子保存。** 对象为租约、父预算、SQL item/run/outbox；前置持久事务与故障注入。准备同时领取、陈旧 worker、调用后断线、stage 后中断、commit 成功但回包丢失、迟到费用。预期：查账恢复，不盲目重调模型、不双扣预算/双提交；未知费用保留额度；run 检查点保留前驱，原字节和旧失败不覆盖。
- [ ] **V02-14 / 待实现：旧协议隔离及正式转换。** 对象为 research namespace 与旧 RecordSet/LocalStore；前置显式转换器和完整旧检查。准备新 item 直接写旧库、伪 producer/review、payload 合法但根条件失败、缺 scope/packet。预期：拒绝混用，不删旧 guard、不用 EXPLORATORY 绕过 scope；正式科学内容和证据逐项保留，不能将 COMMITTED 转成 EVIDENCE。
- [ ] **V02-15 / 待实现：Neo4j/Git 派生与回源。** 对象为派生 outbox/查询；前置 v0.2 映射和消费者。准备图离线/滞后、Git 失败、重放 outbox、新图材料对旧 Task 不可见。预期：候选本地提交不因派生失败重跑模型；恢复按精确身份幂等；新材料进入新 Task，候选边带状态，不由中心性/路径提升可信度。深层场景继续按 NG-*。
- [ ] **V02-16 / 待实现：真实新论文与跨模型格式。** 对象为端到端最小路径；前置 V02-01–08、11–13 的必要实现和用户模型调用授权。用不依赖既有 2608 专属脚本的一篇新论文片段，完成 Paper 保存与一个 Dependency 交接，再换批准模型处理同一输入。预期：相同接口、不同内容可并存，保留每次真实请求/失败/费用，不要求节点数相同；教学输出不能冒充本验收证据。单 claim AF 验收另依赖 V02-09/10。

- [ ] **V02-17 / Pending implementation: English-only specification maintenance.** Scope: all specification documents, Agent instructions, schema descriptions/comments, bundled examples, and names under schema v0.2. Prerequisite: a future documentation-language check and explicit authorization to run it. Scenarios: introduce Chinese prose, headings, link labels, comments, or filenames; retain legitimate mathematical Unicode and byte-preserved external runtime sources. Expected: reject Chinese in the specification tree without banning mathematical notation or rewriting runtime evidence; preserve interface fields and constraints. Current status: documents translated and reviewed through static text search only; no automated checker implemented or executed. Historical documents outside schema v0.2 remain unchanged.

- [ ] **V02-18 / 待实现：宏展开与记号规范化。** 对象为 host 侧 `run.expansions` 与 Paper 侧 `MathClaim.normalization`；前置宏表提取器与语义检查器。准备只在 preamble 定义、只在主文件定义（本目标论文 `\Mcal` 定义在 `draft.tex` 第 8 行而非 `head.tex`）、两处重复定义且冲突、带参数宏、`\makeatletter` 内部名、TikZ/标准 LaTeX 命令、用到但任何来源都未定义的控制序列。预期：宏表由固定程序产出并作为 context 输入交给模型，**模型不产宏表**；展开只提供对照表，不改写来源，`source_bindings` 的字节偏移仍然是原始字节偏移；未定义者进入 `unresolved_macros` 并如实标 `PARTIALLY_EXPANDED`，不凭记忆解释。`relation_to_source` 四级只检查自洽（`VERBATIM` 两份措辞必须相同；声明了偏离却毫无改变是误标），**是否选对那一级属于阅读判断，归审阅不归 host**。两份措辞都保留；统一记号允许，静默替换作者主张不允许。当前有宏表提取器与自洽检查的探针实现，**未接入真实模型运行，也无独立审阅**。

- [ ] **V02-19 / 待实现：读取接口与交付形态检查。** 对象为 [READ-INTERFACE](../schema%20v0.2/READ-INTERFACE.md) 的四个读操作（`claim.get` / `claim.dependencies` / `source.span` / `formal.check`）；前置查询后端、返回三元组与打包检查。准备：只返回 `message` 而无 `reference` 的响应；`reference` 用路径或显示名而非持久身份（producer_task 哈希 + output 哈希 + item_id）；把整份记录集内联进响应；未实现的查询类别返回空成功而不是明确不支持；超出 `Limits` 却不在 `coverage` 里交代；暴露后端无法兑现的参数（对 kernel 检查给 tolerance、对无传递展开的后端给 depth）；仅在本仓库 venv 内通过而未做「按交付形态」的打包检查。预期：三元组齐全，`reference` 可回源到真实已提交 run；**空结果绝不冒充未实现**；紧凑摘要字段允许、完整数组不允许；进程内通过不等于交付可用。**明确不适用**：Paper2Agent 的 tutorial/notebook 抽取链与参考值-容差比较不进入 claim 层——理论论文的 kernel 给的是通过或失败,不是带容差的参考值;该纪律只适用于论文的数值附录,而本目标论文的数值附录已由 `figure2-code-unavailable` 如实阻塞。当前只有规范与一个有界依赖查询的参考实现。

- [ ] **V02-20 / 部分覆盖：血缘、阶段门禁与分阶段重试。** 对象为 `run.call.principal`、`run.consumes[]`、`Task.excluded_principals` 与 `HOST §5` 的重试默认值；前置真实生命周期事件采集。**已有探针覆盖并实测通过 8/8**:无已提交 lamport、自引为生产者、引用 STAGED 运行、引用不存在的 item、回执谎报生产者(账本压倒回执)、principal 被 Task 排除、NOT_STARTED 却声称读过 item、宿主未归属 principal。**已有阶段门禁** `verify_phase.py --through`:重算全部 blob 哈希、把每个被消费 item 追到产出运行、要求每个阶段有 COMMITTED 运行;对当前 store 如实返回 `PHASE_NOT_REACHED`。**仍待**:真实生命周期事件来源(现在 principal 由测试装配)、跨 plan 的预算与租约、「不变条件不重试」的运行时执行、以及**独立审阅本身**——v0.2 没有 review 操作,本项只是血缘,不是独立审阅。

本轮状态：只新增规范/schema/人工样例并做静态阅读；**没有执行测试、示例、模型调用、依赖安装、Lean、数据库或 Neo4j 操作**。v0.2 宿主实现是下一步工作，不由本清单或旧 PASS 自动补齐。

## 11. Schema v0.2 研究工作台前端（UI02-*，2026-09-18）

本次交付为 `web/` 前端重设计。只开发、阅读代码/规范和查看差异；**未运行测试、校验器、应用构建、浏览器检查、示例重放、模型调用或 Lean**。Canvas UI 的 TypeScript 去类型生成浏览器 JS，以及 v0.2 文件原样复制属于资产制作，不是验证。下面均为未来验收条件，不能用历史 HTTP 测试或宿主探针结果替代。本节为本次新增/受影响待测项的唯一入口。

| ID / 当前状态 | 对象与准备条件 | 操作情景 | 预期结果 | 前置阻塞 |
|---|---|---|---|---|
| UI02-01 / 待测试 | 新首页、保留的 `/reader.html`、同源静态资源；用户明确允许后使用 Node 26 与 HTTP 测试夹具 | 执行现有 `web/tests/api.test.mjs` 中受影响的根页面/资源项；读取 CSS/JS、GSAP、Grid/helper、教学源文和 schema | 根页提供工作台；旧页仍含原提取表单；所需资源返回正确 MIME；原 CSP 不依赖内联脚本/外部 CDN | 无；现有测试断言已改，未执行 |
| UI02-02 / 待测试 | 两份保留材料与浏览器；允许交互验证 | 切换教学/历史材料，点击每个节点，切换地图/列表/记录；刷新、前进、后退、打开带 node 的深链接；读取中快速切换 | URL、选中节点、右侧详情和导出材料一致；迟到请求不能覆盖新选择；旧 V3 身份不变为 v0.2 身份；对应连线不冒充证明边 | 无 |
| UI02-03 / 待测试 | 教学原文、Output、生成副本 | 打开来源和 normalization 对照；查看条件、量词、relation_to_source、unresolved_symbols 与 provenance；下载 JSON | 显示源文件中的真实字段；不虚构 source_binding、Task/run 哈希、模型运行、检查结果；导出保留原字段和值 | 真实 source.span / claim.get 读服务尚未接通，不能宣称 READ-INTERFACE 三元组已实现 |
| UI02-04 / 待测试 | 原历史 library 数据及旧阅读器 | 查看 robustness 各节点的前提、条件、原锚点、未评估状态；从详情回旧页；打开旧 `#paper=…&claim=…`、`#job=…`、`#protocol` 和 `#report` | 原候选引用与原链接可追溯；根页历史链接跳到旧页；没有新科学审阅或字节核验的表象 | 原来源锚点重新核验须单独授权，不包含在纯 UI 验收内 |
| UI02-05 / 待测试 | 浏览器桌面宽屏、约 1024px、740px、390px/320px，小屏触控与 200% 字号缩放 | 导航、材料切换、图缩放/适应、横向滚动、列表阅读、详情与弹窗 | 页面不被横向撑开；图可滚动且字可读；详情在窄屏下置；关键按钮不遮挡或截断；列表提供无需看图的路径 | 无；未做截图或渲染核验 |
| UI02-06 / 待测试 | 键盘与读屏环境，原生 dialog 支持 | Tab/Shift+Tab、视图左右/Home/End、Enter/Space 选择；打开/关闭对话框、Esc、焦点返回、加载错误播报 | 标签与所选状态对应；焦点可见；弹窗关闭后回触发点；选中变化能被理解；不依赖鼠标或颜色表达状态 | 无 |
| UI02-07 / 待测试 | GSAP 3.15.0、Canvas UI Grid、可用/不可用 WebGL、精细/粗指针环境 | 初始入场、快速选中、动效开关、系统 reduced-motion、私密模式无 localStorage、缺失 GSAP/Grid、WebGL 上下文丢失 | 基础 HTML 始终可读且可操作；关动效不隐藏内容；触控/减少动态时不启用 GPU 背景；无实验 flag 时普通图与控件可用 | 真实浏览器兼容性尚未验证；不以第三方文档代替本项目结果 |
| UI02-08 / 待测试 | 浏览器性能/生命周期观察；用户明确允许 | 重复切换视图和材料、关闭页面、返回缓存页、切到后台再回前台、改变窗口大小 | 旧 Grid、观察器、事件监听与过渡得到清理；后台无地图动画循环；恢复后无重叠 canvas；地图尺寸正确且不积累资源 | 无 |
| UI02-09 / 待测试 | 可控缺失/错误资源、慢请求环境 | 教学 JSON 或原文 404、历史库缺目标、JSON 解析失败、连续点击重试；资料库查询不存在内容 | 错误明确并有重试入口；不能展示上一材料的详情或允许误导性导出；空搜索与加载失败区分 | 无 |
| UI02-10 / 待测试 | 打开论文对话框与旧提取服务；无需先批准真实联网分析 | 输入标准/旧式 arXiv ID、abs/pdf URL、带版本/.pdf、非 arxiv.org、带凭据/端口/query/hash、畸形输入 | 合法值只导航并预填；不会自动 POST、调用模型或启动任务；非法值有明确说明；旧表单仍需用户明确提交 | 真正抓取论文或模型调用需另行明确授权，不属于该前端导航项 |
| UI02-11 / 待测试 | `sync-workspace.mjs`、完整仓库/独立 web 副本、允许的发布构建环境 | 用户授权后执行指定生成/构建与资源比对；源规范变更后再同步；独立 checkout 无上游目录 | 五份 schema 与示例/规范副本保持原字节；完整仓库从维护源同步，独立网站用保留副本；发布资产包括旧阅读器和全部新依赖 | 尚未运行 `npm run build` 或任何比对校验 |
| UI02-12 / 待实现 | v0.2 Task/run/来源解析/读服务与明确模型授权 | 未来连接 paper.extract、dependency.search 和单 MathClaim Lamport→Lean；运行失败、未启动、暂存、提交、不确定状态分别呈现 | 只根据真实宿主回执显示进度与检查；未实现操作不能返回空成功；COMMITTED 不等于科学接受；不自动全论文形式化 | 完整 v0.2 宿主、读服务返回三元组、精确持久引用和服务端权限尚未接通；本次只交付前端与流程说明 |
| UI02-13 / Pending testing (English interface, 2026-09-18) | Scope: `web/public/index.html` and the workspace UI modules/styles. Prerequisites: explicit authorization for browser and accessibility review; both retained example datasets available. | Visit every page, map/list/raw view and inspector; open source, normalization, formalization, provenance and paper dialogs; trigger loading, empty search, invalid input and motion messages; use keyboard and screen-reader navigation; refresh an existing Chinese-language session; inspect 320px/390px widths and enlarged text. | All authored interface text, metadata and accessibility labels are English; `lang="en"` is set; versioned assets replace stale translated modules after refresh; longer English copy wraps without obscuring controls; original records, reference IDs, source text and exported values stay unchanged. | No new service prerequisite. Static text/diff review only; no tests, build, or browser verification performed for this language change. |

## 12. Schema v0.3 案例构建与执行（V03-*，2026-09-19）

本次用户明确要求依据 v0.3 规划构建框架，并以 `arXiv:2607.26154`「再次完整跑通全流程」。**本节执行授权仅用于该论文及必要依赖；没有运行全仓库测试套件。** 已执行部分的事实如下，不等于目标论文已得到完整证明。旧测试报告和旧 `verification-result.json` 未改写。

统一案例结果：[REPORT](../schema%20v0.3/runs/2607-full-candidate-20260919/REPORT.md)；产物完整性报告：[integrity-report](../schema%20v0.3/runs/2607-full-candidate-20260919/integrity-report.json)。该次运行退出码为 **2 / CHAIN_INCOMPLETE**；字节与协议完整性检查 PASS 不能替代数学验证。

| ID / 当前状态 | 对象与准备条件 | 操作情景 | 预期结果与本次证据 | 前置阻塞 |
|---|---|---|---|---|
| V03-01 / 已执行限定案例；对抗输入待测 | ingestion、现有 provisional extractor、冻结本地源文 | 提取 query 及 6 篇已选外部论文，关联原文字节、引用、MathClaimIR 候选桥 | 7 篇共 2,093 occurrence；query 为 180 occurrence、25 curated claims、12 theorem-like occurrence（含重述），各自 scope 分开；本次完整性检查核对全部 2,093 原文片段 | 语义穷尽性和未被 heuristic 覆盖的 claims 尚不能由计数确认 |
| V03-02 / 已执行 bibunits 修复；边界场景待测 | 主文、head.tex、draft.bbl、appendix.bbl | 跟随 literal include 与 bibunit，提取宏和引用 | query 实测 58 bibitem occurrence、42 unique keys；148 引用锚点中 137 可定位；恢复此前遗漏的 3 个 appendix 引用 key | 宏执行、条件 TeX、重复标签、Unicode/CRLF、缺文件等对抗场景未运行 |
| V03-03 / 案例定位审计已执行且未通过数学分类门禁 | 7 篇冻结源文和全部解析引用 | 每个已定位 anchor 必须有支持判断或最终排除理由 | 763 个已定位引用仍缺分类，`anchor-audit.json` 明确 FAILED；PENDING 分类不冒充最终排除 | 尚需实际语义依赖分类及相应决策门禁 |
| V03-04 / 本地提取已执行；下载成功路径未完成 | 通用 source_descriptor、安全有界 arXiv 源码下载 | 对固定版本下载、拒绝越界/链接/超限、唯一主 TeX 入口选择 | 已实现并保留一次 DNS/网络失败回执；提权下载尝试被自动审批拒绝（将其判为未获后续授权的验证），未绕过、未称下载成功 | 真实下载成功路径、旧式单文件 TeX、多入口/重定向/恶意 tar 等仍待指定执行 |
| V03-05 / 限定案例网络查询已执行；匹配/ADS 待实现 | 显式 DOI/arXiv 标识、Crossref 原始响应 | 按每篇最多 5 次请求查询缺失身份，保留失败和预算 frontier | 案例共 35 次请求，298 条需处理的 identifier records，7 条检索错误；没有将 fuzzy identity 或书目记录当作数学支持 | ADS 授权适配、来源主题匹配、起源穷尽性仍缺 |
| V03-06 / 实际无环 AND 图已执行；OR/SCC/定价边界待测 | 导入旧候选 DAG，显式共同前提分组 | 全数学查询及 closed-form 子图，加入必需 sign-collapse bridge，传播 blocker，逐成员删除诊断 | 全范围 53 queries /65 nodes /115 memberships；closed-form 29 nodes /46 memberships；无环；成本未知返回 UNPRICED，不宣称最优路线 | 共享成本 OR、成本不确定区间、SCC/自环、搜索限额、伪字段/悬空桥接的对抗场景未运行 |
| V03-07 / 已实现、静态审阅；并发/恢复待测 | PlanLedger SQLite、调用额度、费用预留和持久 lead | 并发领取、重复结算、跨 plan、未知费用、无进展和预算耗尽 | 应防止重复调用、跨计划修改、负额度和通过重命名 query 重置 lead；账户调用费用未知保留 null，不能当作零美元 | 并发与故障注入未执行；无统一供应商计价/费用回收 |
| V03-08 / 真实调用失败证据已记录；有效语义产物另见后续行 | 本机 Codex 登录、源文任务、JSON Schema | 原 CLI 初始化受沙盒限制；提权后旧 CLI 不支持配置模型；改用桌面内置 CLI 的整篇批次 | 三种失败均保留；整篇批次 600 秒超时，未产生成功候选；未借失败调用声称模型阶段完成 | 全量语义提取仍未成功；模型降级/定价比较与校准尚未完成 |
| V03-09 / 已实现、静态审阅；待执行边界场景 | model.py 完整冻结源码 payload、1.5 MiB 上限、严格响应检查 | 错哈希、非 UTF-8、缺 proof context、超限、未知 occurrence/citation key、模型写状态字段、空输出 | 应在候选成功回执之前拒绝；超限不截断、不调用模型；host 决定状态/覆盖率 | 对抗输入与进程级无工具能力隔离未实现/未测；当前只读沙箱加工具事件拒绝 |
| V03-10 / 三工程限定构建和环境审计已执行 | 既有固定 Lean/mathlib/Quantumlib 项目 | 构建 query 必需依赖，读取实际类型、显式 Prop 与结构体证明字段、axiom/term dependencies | `lean-evidence-20260919`：54 定理证明项内核接受、9 定义展开；46 个定理的前提 inhabitation 未知，分行记录，不称论文 54 条已证明 | 源文对齐、每个前提的实际实例、完整 query 组合尚缺 |
| V03-11 / 具体修复已随限定构建执行 | IsPerfect 的有限域 binder；新的 admissible-sign 桥接定理 | 增加 `[Fintype V]`；在显式 hCollapse 前提下从 full sign cube 转移最大值定理 | 当前构建通过；实际证明项引用 `max_abs_signed_sum`；保留 hCollapse；不把一般 sign theorem 冒充 Pauli-context lemma | Pauli 的 sign-collapse 构造与源文对应尚缺 |
| V03-12 / Physlib 独立环境审计已执行 | 本机 Physlib tracked core、Lean4.33/mathlib db584，与旧工程不同版本 | 审计 Pauli 相关 7 declarations，证明 normalized Pauli-vector square identity | 5 定理/2 定义分别记录；有实际 `vectorMatrix_sq` composition；旧缓存未重建的限制明确 | 未以两个 epoch 各自成功宣称已跨版本组合 |
| V03-13 / 冻结分支源码新编译及审计已执行 | 用户已有 PhyslibAlpha AnticommutingWitness，冻结 SHA 和只读原目录 | 编译冻结源码，证明 clique expectation bound，提供具体密度态/非恒等 Pauli Z 非空实例 | `physlib-anticommuting-20260919/branch-evidence.json`：12 declarations（11 定理/1 定义），11 个实际组合见证，保留两次失败再成功的证据 | 独立重放便利 driver、源论文特定 Pauli/图专门化和 reduced-RoM 组合仍缺 |
| V03-14 / 尚未完成 | 通用 Frontier / bottom_up_walk 宿主接口、可信校准注册、proof backend | 新依赖入队、持续裁剪、按拓扑试证、失败转为真实 Lean Prop 前提、独立分支继续 | 应防止缺前驱时试证、阻塞丢失、把 NONE 非空见证当成功、把 definition 记作 theorem；默认门禁保守 | 控制接口尚未接入真实递归/HEAVY 全链条；校准门禁与无人工试证的政策需明确 |
| V03-15 / 产物完整性已执行；完整证书待构造 | v0.3 schemas、案例输出、现有 Lean 证据 | 只检查本次 case 的 schema/引用/原文字节，不运行全仓库 fast profile | 完整性 PASS，数学状态仍 CHAIN_INCOMPLETE；空 query declaration 明确为不存在，空 premise list 不冒充无前提定理；fast catalog 仅新增入口未全跑 | 尚无最终 query Lean declaration；真实 premise closure /全部 composition /源文 alignment 未完成 |
| V03-16 / 后续范围待测 | 独立 common-epoch 副本、根库候选绑定和 junk-value lint | 在不改写原工程/Physlib 的前提下迁移有限模块；检查定义 totality 和非退化实例 | 应保存原始/适配源码与版本，不能用部分迁移代表整个依赖链；lint 仅报义务，不等于证明 | 当前迁移实验与完整 paper-specific 查询证明尚在进行；后续结果另追加，不改写本次历史证据 |
| V03-17 / 已执行有限模块迁移；完整迁移另记 | 独立冻结副本与 Physlib 的 Lean4.33/mathlib 环境 | 编译 GraphFoundation、LocalDelta、AdmissibleSigns 与 MState 桥接 | `epoch-migration/runs/20260919-selected-modules/migration-evidence.json`：12 declarations、6 个实际组合见证；4 次编译和环境审计成功；原工程不改写 | 仍保留 hCollapse；有限模块成功不能代表全部82模块或论文结论已组合 |
| V03-18 / 已执行模型故障定位；语义全量未完成 | 桌面内置 Codex CLI、配置模型、冻结源文 | 12 theorem-like 范围批次240秒；随后仅一条179字节 lemma、90秒上限 | `model-theorem-batch-20260919` 超时且无候选；`model-single-statement-20260919` 在10.75秒返回合法候选并明确缺定义；后者只覆盖一条陈述，不能替代全文依赖提取 | 全文上下文语义任务结果另记；账户成本未知保留 null |
| V03-19 / 静态实现；真实新 locator 与对抗情景待测 | 模型给出文件路径和精确引文，宿主读取已冻结完整源码 | heuristic 外的新 claim；重复引文、错路径、空白、非 UTF-8、与既有 occurrence 重叠 | 宿主只在唯一原文匹配时计算半开字节区间与哈希；文字定位不代表科学对齐；完整源码仅供一次，删除重复元数据不截断源码 | 完整性和覆盖范围需由真实候选输出分别审计 |
| V03-20 / 溯源检索已执行；全文门禁未通过 | weighted-perfect 分支、三篇原始出处及目标证明段落 | 取得元数据、原始出版页面/存取结果和目标精确引文 | `origin-weighted-perfect-20260919` 保存3条元数据、15条访问记录、4个目标源码/书目锚点；取得原文0篇、接受支持边0条；保持 FRONTIER | 原始定理对齐、实权重连续性推广、覆盖最优值取得及更早出处尚缺 |
| V03-21 / 调度接口静态改进；尚未执行 | Frontier 与持久 proof-attempt 账本、固定 plan、现有候选图 | 并发额度、配额满时重复入队、失败重试、过期worker重复回报、崩溃恢复、领取前图/校准变化；AND缺前驱、独立分支、OR显式路线、SCC、checked Prop前提传播、伪回执/定义/NONE见证 | 不重复占位或回报进度；跨重启保持尝试预算；缺前驱不能调用后继；所有候选探索保留待审阅状态并向下游传播 | 尚未接入实际递归与proof backend；本行所有并发/恢复/故障注入情景均未执行 |
| V03-22 / 完整上下文的单 lemma 提取已执行 | 冻结 query 的全部源码、去重后的模型输入、原有180 occurrence映射 | 仅输出 collapse lemma，其他原文作为依赖上下文 | `model-collapse-full-context-20260919`：33.48秒，1个候选、8个内部支持引用、0个外部支持 key；结构和引用核对通过；自报0.99保持未校准 | 本调用不代表全文提取；实际账户费用未知 |
| V03-23 / 目标语义候选与新图限定执行；语义审阅未完成 | 真实协作代理产物、冻结字节、当前schema；没有调用旧DAG | 72候选、148候选引用用途、5处新增locator；宿主装配新图并核对位置、协议及确定性重建 | `semantic-target-graph-20260919-reviewed`：109节点、66组、37请求；原文/协议与重建审计PASS；全部仍AWAITING_REVIEW。此前176节点版本保留：它把67条未定类型工作缺口错误当作前提，后经静态审阅修复；当前版本将其保留为issue/blocker | 160/180启发式位置被候选覆盖，另20有残余记录；这不是语义穷尽证明；后续新论文和对抗匹配未测 |
| V03-24 / 首轮完整迁移已执行并阻塞；后续适配另记 | 82模块原始冻结副本、同一Physlib环境 | 保持原模块名顺序编译，记录表示兼容补丁与每次失败 | 首轮16/82成功；PowBitVec仅以rfl替代两处基础simp；随后MonoidAlgebra从Finsupp别名变为结构体导致Pauli.Defs失败，保存失败日志和补丁 | 不能宣称共同环境闭合；后续表示适配必须保留数学语义、无新增假设/axiom/sorry，并单独记录 |
| V03-25 / 已静态实现与独立审阅；尚未执行 | 新候选图跨论文连接、固定来源/响应字节与candidate matches | 单一和多个联合上游；同一请求多行的AND/OR歧义；locator-only声明；引文版本不符/书目身份冲突；多次递归保留旧证据 | 每条引文必须定位到所映射的来源声明；多个上游必须明确JOINT_SUPPORT，多条替代路线必须显式声明；外部请求边界保持未审阅与阻塞；追加保留join history；当前查询重新裁剪 | 实际Varela候选连接结果另追加；身份对抗输入、旧证据被篡改、循环重入、SCC与深层多次连接仍未执行 |
| V03-26 / 两层真实来源连接已执行 | Varela 81候选、Howard54候选、冻结原文、精确source matches | 目标→Varela的7条匹配仅3条提出支持；Varela→Howard第二条原occurrence歧义，v2改为明确normalization/faithfulness/channel声明ID | `recursive-target-varela-howard-v2-20260919` 保留72查询、132节点、84组；两条Howard匹配连接，10行匹配/问题引文审计PASS；首次127节点仅1匹配的结果仍保留 | 全部语义AWAITING_REVIEW；H数值示例未作为faithfulness前提；未解决内部请求保留。最初系统python3缺少tomllib未启动操作，后使用项目.venv成功 |
| V03-27 / 三论文递归控制器已限定执行 | 同一冻结plan/SQLite、真实保存提取与匹配、max_papers=3、max_model_calls=0 | 自动种子计额、候选入队、两层连接、已读论文复用、每次查询裁剪、达到论文上限停止 | `research-three-paper-20260919`：3篇含初始论文、2次连接、3图快照、72查询、132节点、84组；来源/查询/重建/SQLite投影审计PASS；新增模型调用0 | 不是全模型新生成；并发锁、崩溃/中断、重复恢复、严格校准策略和预算故障场景仅静态审阅未执行；完整proof backend未接入 |
| V03-28 / 归一化RoM语义已限定编译与审计 | 原Lean4.30缓存，增广原子(1,projection)、FiniteRoM与密度矩阵可行性接口 | 保留sum(coeff)=1和投影重构，导出规范分解、最小值取得及下界1 | `reduced-rom-semantics-20260919/evidence.json`：第二次编译成功，7新增声明、8组合见证；首轮失败保留，无禁止公理 | 未完成顶点集身份、强对偶、sign collapse和最终闭式公式；未宣称与Physlib跨环境组合 |
| V03-29 / 凸生成集合桥已限定编译与审计 | 归一化RoM语义、双向非负和为1的原子映射 | 对给定分解构造新分解并保持重构/归一化且不增ℓ₁；取真实最优解得到单向不等式和双向相等 | `convex-generator-invariance-20260919` 首次编译成功，6新增声明、8支持声明、13证明项依赖均见实际证据，无禁止公理 | 两个原子映射及实际顶点枚举尚未实例化；不是原文“所有独立表示”不等式的证明 |
| V03-30 / 表示适配及迁移继续执行中 | 82模块冻结副本、Physlib Lean4.33/mathlib db584、原始Lean类型语义 | MonoidAlgebra结构体/coeff适配、后续proof/API路由调整，每次保留日志与补丁 | `full-case/representation-audit-2`：9定理、6归一化组合与3系数公式审计；完整迁移此记录时46/82成功 | 全82模块和其完整环境审计尚未完成；Notation已编译但没有实际宏展开用例，不记为已验证使用；后续结果另追加 |
| V03-31 / 控制器内真实模型匹配已执行 | 三论文导入证据、明确移除一条匹配缓存、max_model_calls=1 | 从候选入队进入真实dependency.match调用，预留额度、回收回执、绑定原文引句并继续Howard递归 | `research-live-match-20260919`：1调用46.02秒返回合法候选，277746输入token/1178输出token；3论文、72查询、132节点、84组；完整本次来源/查询/SQLite/图重建审计PASS，未接受支持边0 | 账户费用未知；其他候选来自已保存真实协作代理阅读。并发/异常恢复仍未执行；不是最终证明链闭合 |
| V03-32 / 正常重启恢复已限定执行 | `research-live-match-20260919` 已结算plan、无活动worker、既有三论文和一次调用额度 | 保存恢复前投影到observations/before-normal-resume，再使用同一plan运行--resume | 恢复后仍3篇、1总调用、72查询、132节点、84组；没有重置配额或再次调用；`integrity-after-normal-resume.json`重建审计PASS | 此情景仅正常恢复，不覆盖并发、BUSY中断、崩溃窗口、外部worker迟到或代码变更后的迁移；之后scheduler仅docstring更新，旧plan运行须按冻结代码要求处理 |
| V03-33 / 静态改进；待后续本案例执行 | 后续research计划的冻结来源目录与运行证据引用 | 外部registry在递归期间变化；正常恢复更新latest投影；审计需定位当时输入 | 新extract_paper显式接收plan冻结source_catalog；结果另写不可变results/序号.json并引用不可变checkpoint；审计输出绑定四个输入投影hash和最后checkpoint | 这些改动在V03-32之后，尚未执行；不能套用V03-27/31/32的已有PASS，需下一次实际案例运行或用户指定范围执行 |
| V03-34 / 第四篇的部分提取接入已执行 | Gottesman冻结v1全文、实际已读第2–3章73候选、21 locators、官方勘误；本次只装配章节候选 | 章节范围核对、四论文递归预算、不确定源匹配不加支持边、冻结catalog与不可变结果/checkpoint引用 | `semantic-gottesman-chapter-02-03-20260919`：101节点、65组、28请求，限定来源/重建审计PASS；`research-four-paper-20260919`：4候选论文条目、3连接操作、4图快照，查询图仍132节点84组；审计PASS并绑定输入hash | 第四篇并非全文完成；实际只有109/783全文启发式位置被本章节候选引用，另有明确未读范围。V03-33输出与catalog正常路径已执行；registry并发变更/中断等故障情景仍未执行 |
| V03-35 / 有限归一化强对偶已限定编译与审计 | 既有finiteRoM实际最优解、PiLp 1系数范数、重构核商空间、mathlib Hahn–Banach、增广原子 | 构造取得最优值的对偶泛函，证明弱对偶，转换μ/y坐标并作用于实际reducedRoM W ρ | `finite-rom-duality-20260919/attempt-04` exit0无诊断，14新增+11支持声明、33实际term依赖，无禁止公理；01–03失败保留并排除其错误恢复声明；导入缓存未改 | 原Lean4.30环境；实际顶点映射、sign collapse、完美图求值、上界/饱和和Physlib共同环境仍缺；不是最终query证明 |
| V03-36 / 真实context符号域已限定编译与审计 | Pauli F₂支撑、交换且独立的实际MeasurementWindow context、先前符号最大值定理 | 证明wordProduct单射、排除生成子群中的`-I`、构造任意符号的admissible extension并导出最大值 | `context-sign-independence-20260919/attempt-01` exit0；16新增+9支持声明、36实际term依赖，无禁止公理；端点仅hContext与hIndependent，无hCollapse，缓存未改 | 原Lean4.30环境；源文无活跃依赖→独立尚在实现，顶点/完美图/最终组合仍缺 |
| V03-37 / 新依赖下载与BibTeX实际入口已执行；边界场景待测 | 固定Xu arxiv:2511.13531v1源码包、真实ref.bib、受限source_root | 下载固定版本、读取literal bibliography资源、冻结字节、保留macro/duplicate、不执行TeX，并核对本次产物位置 | `source-xu2511-acquisition-20260919` HTTP200、607345字节源码包；`source-xu2511-bibtex-extraction-20260919` 3文件、564启发式位置、152条目/150键、166可定位引用；1,447字节引用与书目关联审计PASS。14未展开月份宏和2重复键保留；旧0条书目运行未改 | 语义全文未读；nested/quoted/escape/#拼接、crossref/xdata、重复字段/损坏EOF/非UTF8/资源限额、源包外include/bib/符号链接、混合bbl/bib冲突等对抗场景仅静态实现未执行；本例重复键未被正文引用，歧义引用分支仍待测 |
| V03-38 / Gottesman第1/4章候选限定装配已执行 | 全文冻结原文，真实已读章节的57候选、7 locators、章节残余与正式勘误记录 | 独立批次装配、精确原文定位、查询ID与图重建审计 | `semantic-gottesman-chapter-01-04-20260919` 57查询/92节点/52组/35请求，完整本批次定位与重建审计PASS，仍AWAITING_REVIEW | 与第2/3章批次尚未语义去重合并；第5章以后仍在阅读；累计候选记录不等于独立claim数或全篇完成 |
| V03-39 / 无活跃依赖正向collapse已限定编译与审计 | 真正的最小非空标量Pauli乘积依赖、F₂零和关系、既有ContextSignIndependence | 从非独立关系提取极小子集，在交换context内反证active，从而构造所有admissible signs及取得最大值 | `no-active-dependencies-20260919/attempt-02` exit0无诊断，20新增+11支持声明、39实际term依赖、无禁止公理、缓存未改；attempt01失败保留。端点显式Prop仅hNoActive和hContext，没有LI/hCollapse | 原4.30环境；反向/parity完整刻画与任意complex scalar matrix的逆向对应未做；顶点/完美图/最终组合未完成 |
| V03-40 / 官方版本API单次真实成功；控制器网络路径待执行 | arxiv_metadata.py、官方API、Xu必要依赖、固定网络额度 | 请求无版本ID，从唯一Atom entry的显式版本字段解析，保存原始响应；控制器预记额度、失败不退回、重启重用回执 | `source-xu2511-api-version-20260919` HTTP200，3106字节Atom，明确返回2511.13531v1；不是按日期推断v1。控制器集成、0–64请求额度及审计已静态实现 | 控制器内真实metadata触发、未知query bootstrap、预算边界/崩溃/并发、非UTF8/DOCTYPE/多entry/错ID/缺版本/重定向均未执行；元数据版本不代表引用版本已对齐；DOI-only仍待解析 |
| V03-41 / BibTeX改动后四论文正常路径已限定执行 | 新ingest、metadata空路径、原四论文导入候选、max_papers=4/model_calls=0/identity_requests=0 | 实际重新冻结/装配query→Varela→Howard及Gottesman章节，保存新计划和不可变图 | `research-bibtex-four-paper-20260919` 4论文、3连接、4图快照、72查询/132节点/84组；新增模型和元数据调用均0；本次来源/账本/图重建审计PASS，旧plan未续跑或重写 | 不覆盖控制器网络metadata路径，不增加已读语义范围；数学仍CHAIN_INCOMPLETE |

| V03-42 / 章节组合正常路径已限定执行；冲突边界待测 | `chunks.py`、冻结Gottesman原文、四个实际逐段阅读批次；05ab取v2 | 复制每批响应/provenance原字节，核对source manifest与read spans；按完全相同整行折叠，同ID不同内容不任取 | `gottesman-chapters-01-06a-combined-20260919`保留270候选，217543/333351已报读取字节；`semantic-gottesman-chapters-01-06a-20260919`374节点/251组/104请求，位置/图重建PASS。05ab-v1历史和更正原因保留 | 本次无重复/冲突，相关分支尚未执行；读取自报与语义完整性未审定，剩余章节未读完；不是逐章节模型派发器 |
| V03-43 / context态、partial-frame一般延拓已限定编译 | 原4.30缓存、NoActiveDependencies、实际Pauli矩阵与frame | 构造rank-r群平均密度矩阵，证明exact projection；构造正交外部support逐次增秩且保留原带符号生成元，得到任意context的实际complete-frame atom | `context-code-state-20260919/attempt-04`15新增/40term，前三失败保留；`partial-frame-extension-20260919`10新增/16term、`signed-generator-completion-20260919`9新增/16term、`maximal-context-physical-20260919`4新增/13term均attempt01成功，无禁止公理，旧缓存未改。最终candidatePhysical无hRank或存在性假设 | 反方向atomRefinement尚未完成；非NoActive一般情形未声称；共同epoch迁入与源文审阅待做 |
| V03-44 / 全82模块共同epoch迁移与指定声明审计已执行 | 原82模块冻结副本，Physlib Lean4.33/mathlib db584共同缓存，74目标冻结清单 | 保留每次诊断/21步适配，最终逐项环境读取kind/type/binders/axioms/term常量 | `epoch-migration/runs/20260919-full-case/full-case-audit.json`74/74：61THEOREM+11DEFINITION+2INDUCTIVE，44真实term组合；82模块全部编译，原工程不改写 | 本轮后续新增Lean模块未包含在82中；具体DensityMatrix/MeasurementWindow→PhyslibAlpha桥和最终query尚未完成 |
| V03-45 / 两个原图视觉读取与补充候选限定装配已执行 | 目标fig1.pdf/fig2.pdf原字节、Poppler、图注/TikZ源文 | 保存PDF/image hash与render回执，实际查看两张图；区分TeX叠加标签与PDF内容、示意图与实验曲线 | `target-figure-reading-20260919`两页视觉已读、TikZ仅源码阅读；保留图注过强条件问题和n=4图结构两候选，`semantic-target-figure-supplement-20260919`2节点原文/图重建PASS；另保留4实验性记录，不从像素推断精确数值 | 全文版面未渲染、数学语义未审阅、无数据代码未复现实验；补充候选尚未合并主查询 |
| V03-46 / 有限clique cover最小值实现中 | 原4.30mathlib有限维紧致性，真实非负覆盖约束及sInf定义 | 用singleton给出可行解，再在非负成本sublevel上构造紧集取得最小值，导出sInf等式和非负性 | `finite-clique-cover-attainment-20260919`逐次真实编译并保留失败；当前尚未记为成功 | 不证明加权完美图对偶；成功后追加实际证据，不把失败恢复中的sorryAx算证明 |

| V03-47 / 有限clique cover最小值已限定编译与审计 | V03-46真实有限非负覆盖、singleton可行解和有限维紧集 | 从实际非空可行域构造最小覆盖，识别现有sInf并证明非负，包含空顶点域 | `finite-clique-cover-attainment-20260919/attempt-04` exit0，8新增（7定理/1定义）+4支持声明、23真实term依赖，无禁止公理且旧缓存未改；有1条unused-tactic警告。01–03失败记录保留并排除 | 此为原4.30环境最小值/定义域义务，不是加权完美图对偶、最早出处对齐或最终query证明；后续共同epoch迁入待做 |

| V03-48 / 调度review-only门禁静态修正；尚未执行 | bottom_up_walk与显式CANDIDATE_EXPLORATION，真实图上review marker及数学/来源blockers | 只有review-only标记时允许进入后续root/support检查；混有其他blocker仍停止；严格模式仍停止；所有探索结果及后代保留review marker | 不再因控制器统一加的审阅标记而把显式探索完全禁用；不豁免来源/条件/缺前驱/库审计门禁 | 当前只静态修改与阅读；实际proof backend尚未接入，未执行门禁分支或故障情景 |

| V03-49 / 实际投影坐标与反向凸分解已限定编译 | 完整signed Pauli frame、已证明candidatePhysical、NoActiveDependencies | 真实trace给0/±1及交换非零支撑；扩到极大context后构造两候选以1/2消去新增坐标，重复标签权重累加 | `projected-frame-coordinates-20260919`10新增/21term；`context-atom-refinement-20260919`8新增/14term；均attempt01 exit0无诊断/禁用公理/缓存变更，实际VRep构造含mk和两字段证明，最终只需hNoActive | 非NoActive的无条件VRep与候选极点身份未声称；归一化RoM/graphdual组合、源文对齐及共同epoch迁入待做 |
| V03-50 / 具体Physlib态/窗口桥已限定编译审计 | 共同82模块、冻结PhyslibAlpha对象、独立新run | DensityMatrix↔MState矩阵roundtrip、trace/expectation一致、actual anticommutation graph、从W性质消去hInv/hAdj并给具体单Z非空实例 | `epoch-migration/runs/20260919-concrete-physlib-bridge/bridge-evidence.json`20新=15 theorem+5 definition；总34审计声明/64term，标准公理；attempt01失败保留，attempt02成功；两新模块独立计数不并入原82 | 不是RoM闭式，原4.30后续新增12模块及组合仍在迁入；科学对齐未审阅 |
| V03-51 / 第6b–7a章节组合限定执行 | 已冻结Gottesman新增47候选、作者勘误与证明问题、先前四批 | 以相同source hash组合第5批并重建全批次内部依赖 | `gottesman-chapters-01-07a-combined-20260919`317候选、246794/333351已报读取字节；`semantic-gottesman-chapters-01-07a-20260919`437节点/295组/120请求，原文与图重建PASS | 全文剩余4块，候选未语义去重/接受；作者承认的GV与Singleton证明缺口保留，选定dimension边界未自动解除 |
| V03-52 / Lovász1972原始PDF取得与逐页阅读已执行 | 大学托管的4页论文、冻结HTTP字节、Poppler图像/提取文本 | HTTP200保存142102字节，4页实际视觉读取，图像修正OCR的h≥0域；按PDF页区域记录10候选与引文用途 | `origin-lovasz-characterization-1972-20260919`保留先前DNS失败、成功receipt/hash、page图和阅读记录；Berge1961 Theorem1为明确proof引用，另外两项不自动当主证明前提 | 未取得Berge全文；实权重对偶尚需真正桥接；全文已读不等于每个初等证明等式单独原子化，PDF页区域尚未接入现有TeX候选装配器；没有接受支持边/最早出处声明 |
| V03-53 / 独立集–团覆盖弱对偶实现并编译中 | 有限simple graph、实际非负fractional cover、最优值取得 | 证明independent/clique交最多1，交换有限和得任意覆盖成本≥独立权重，再作用到真实取得的sInf | `weighted-clique-cover-weak-duality-20260919`保留实际attempt，未记为通过 | 本项不需完美性，也不证明反向不等式；成功后追加证据，共同epoch迁入与最终组合另做 |

| V03-54 / 输出分批宿主已实现；本案例一次真实调用进行中 | 完整冻结UTF8源码、明确半开byte scope、持久调用预算、新extract_batches.py及组合器 | 按不切UTF8的范围分派，每次保留全部上下文；host拒绝无scope内statement锚点的候选；失败/预算不足/批次上限保留缺失范围，只组合成功输出 | `research-live-output-batch-20260919`限定1篇/1模型调用/1输出batch/180秒，当前尚未宣称成功；每批输入/响应与source scope可回溯，dispatch bytes不冒充read bytes，所有结果未审阅 | 超长UTF8行、跨边界claim、locator歧义、多批冲突、额度并发、中断恢复等边界未执行；整篇全批次未执行，PDF页区域不是本入口支持格式 |

| V03-55 / 独立集–团覆盖弱对偶已限定编译与审计 | V03-53同一实际有限图/覆盖定义、已取得的sInf | 对实际交集card≤1与有限和重排构造任意覆盖成本界，再作用真实最优覆盖 | `weighted-clique-cover-weak-duality-20260919/attempt-02` exit0无诊断，5新定理+4支持、13term组合，标准公理且缓存未改；attempt01失败保留 | 只完成一般图弱方向，不是假定/证明perfect equality；源文对齐与共同epoch追加迁移待做 |

| V03-56 / 输出分批真实失败与成功均已保留 | V03-54 同一目标论文、完整冻结上下文与持久预算 | 首次8192字节focus/180秒超时；加入可读原文excerpt与行号后，以2048字节focus/120秒再作独立一次调用 | `research-live-output-batch-20260919`失败完整性审计PASS；`research-live-output-batch-v2-20260919`47.53秒返回3候选、12节点/3组，调用和batch完整性审计PASS；158934输入/1347输出token，调用不退额 | 第二次只完成39段中的1段，38段明确未派发；不是整篇提取完成或模型语义审阅；跨batch、边界与恢复仍待测 |
| V03-57 / 实际reduced RoM图对偶已限定编译审计 | 真实normalized projected-frame RoM、双向context凸分解、有限强对偶、NoActive collapse | 从实际定义构造图可行域 `α_abs(y)(G)+abs(μ)≤1`，证明最优值等式与最优解存在 | `reduced-rom-graph-dual-20260919/attempt-04`exit0无诊断，16新声明；合计52不同审计声明、100term links，标准公理且旧缓存未变。失败与隔离foundation组合保留 | 唯一额外显式前提hNoActive；W打包条件仍含nonempty/involutive/nonidentitySupport/distinctPhaseClass。未覆盖空窗口；perfect闭式、sqrt/saturation、源文审阅及共同epoch组合待做 |

| V03-58 / Gottesman全文批次组合已限定执行 | 冻结TeX333351字节、七个阅读批次及勘误、05ab-v2 | 冻结所有batch输入；组合完整读区间、候选、内部支持与外部请求，再实际重建 | `gottesman-full-thesis-combined-20260919`450行无完全重复/同ID冲突，reported reading333351/333351；`semantic-gottesman-full-thesis-20260919`618节点/386组/168请求，原文定位与图重建审计PASS | 全文TeX阅读不等于穷尽/接受；缺失Capacity.eps未读，源文证明问题与勘误均保留，所选dimension边仍UNCERTAIN |
| V03-59 / 实际模型–Lean证明后端实现中 | 新proof_backend.py、GeneratedProofDriver、proof_walk.py、冻结共同环境和具体库声明审计 | 原图只加候选root库绑定；持久预算调用模型；按单Lean term解析类型/证明；OS沙箱独立编译、核对公理/前提/结构字段/直接term依赖，失败单独分类 | 当前仅静态实现，待本论文实际规范化系数下界分支限定运行；不声明后端已实际成功 | 通用全图源文对齐、自动root检索、无校准判断、恢复/恶意term/并发/故障边界仍待做；不把库复用包装算作新数学结论 |

| V03-60 / 实际RoM团–覆盖夹逼已限定编译 | GraphDualBounds、已证明图对偶和有限覆盖取得/弱对偶 | 原图clique权重=补图独立权重；由显式clique可行对偶与补图cover构造两端界 | `graph-dual-bounds-20260919/attempt-02` exit0无诊断，23新+5支持，含支持组合共41不同声明、55term；标准公理、旧缓存未变 | 除hNoActive外保留所有W/density结构条件；没有假定WeightedPerfectGraphFoundation，但也未证明perfect equality/一般LP等式/最终query |
| V03-61 / 新增12模块共同epoch迁移已执行 | 冻结原82与Physlib桥2、原4.30新增12模块的独立清单 | 只改迁移副本适配Lean4.33，实际编译并审计全部冻结目标及Physlib桥 | `epoch-migration/runs/20260919-additional-case-modules/extension-audit.json`210实际声明=158 theorem+49 definition+3 inductive，434直接term组合；12/12成功，5适配及历史失败保留，无禁止公理 | 12模块独立于原82计数；不是210论文claims或最终组合；WeakDuality与GraphDual后续两模块另层迁移中 |

| V03-62 / 完美图复制前置着色模块已限定编译 | 既有IsPerfect、有限图k-coloring、真实独立色类 | 证明每色击中每个k-clique；x不在任何最大clique时删除其余同色点使cliqueNum下降；实际构造少一色和独立块加一色着色 | `perfect-graph-color-class-20260919/attempt-01`exit0，10新+5支持、12term，标准公理，旧缓存未变；少量unused/simpa linter提示 | 复制顶点完整定理、弱完美图与实权重整性仍缺；不是以证书替代证明 |
| V03-63 / 后端静态审阅已修正；实际环境启动继续中 | V03-59源码、独立代理静态审阅与完整共同缓存 | 严格源文区间/identity和source fingerprint；保留分类额度失败前结果；Prop fallback保留父对象并检查实际使用binder；钉住sysroot/IR/伴随对象/搜索目录全文件集；只读输入+有界输出 | `proof-worker-environment-20260919`记录macOS嵌套沙箱失败；attempt02内层沙箱成功启动、Lean因driver保留字解析失败，均保留；attempt03修复后运行中 | 不将静态审阅或失败启动当作证明后端成功；Prop依赖/越界源文/额度并发/重启/恶意term等负路径尚未执行；scheduler source fingerprint新门禁亦需对应限定执行 |

| V03-64 / 真实模型证明后端的源文分支限定运行中 | 已明确定位draft.tex608行的规范化系数ℓ₁下界、1节点源文图、共同epoch库声明 | 独立freeze库声明与所有base对象，真实模型生成类型/证明并交Lean单term驱动；SQLite限制3模型calls/2proof slots/每节点1次 | `proof-worker-environment-attempt04-20260919`通用runtime和两库声明实际编译/审计成功，87,659个base对象约8.6GB字节pin；前三失败保留，第三为4GB内存阈值失败；`proof-worker-normalization-20260919`正在运行，未报成功 | 这是原文中的一个基础步骤和库复用，不是新增数学发现或全论文闭合；无独立非空前提见证/语义接受，真实下游组合及故障分支仍待执行 |
| V03-65 / 目标全文39范围真实自动派发中 | 冻结目标全文、2048字节focus与完整上下文、已有单batch成功依据 | 限1篇/39model calls/39output scopes/每call120秒；逐批保留结果和未完成范围，最后只组合成功候选 | `research-live-full-output-batches-20260919`已启动；当前不宣称全批次成功或语义穷尽 | provider超时/额度/边界锚点/不同批次冲突按实际结果保留，结束后追加证据；此运行不执行Lean或全仓库测试 |
| V03-66 / 额外2模块共同epoch迁入已执行 | V03-61已审计12层、WeakDuality与ReducedRoMGraphDual、只读既有缓存 | 拆除重复合并foundation import，仅在迁移副本适配proof routing，保留所有失败；实际同epoch类型/公理/term审计 | `epoch-migration/runs/20260919-graph-dual-extension/extension-audit.json`232实际声明=176 theorem+53 definition+3 inductive，510直接term组合，禁止公理0；2成功2失败。新增模块自身21声明，审计目标另多1旧支持定义 | GraphDualBounds尚未迁入；singleZWindow的NoActive仍未证明；实际graphdual端点仅hNoActive但W/ρ打包前提保留，未作源文接受 |

| V03-67 / 一条实际源文模型→Lean路径已执行成功；独立产物审计进行中 | V03-64相同规范化系数下界、共同runtime、原图1节点+候选库绑定 | model HEAVY返回单term类型/证明；宿主沙箱编译、前后完整cache pin、source fingerprint门禁、axiom/actual binder/term检查 | `proof-worker-normalization-attempt02-20260919`1 modelcall，21.38秒，67289输入/532输出token；1实际THEOREM候选，只有标准三公理，normalized_l1直接term依赖；整体仍exit2 CHAIN_INCOMPLETE。首个0calls host失败保留 | 原文语义未接受、normalization假设非空性无独立见证；多节点proof composition、Prop fallback及错误路径未执行。原先Prop contains-constant漏洞已保守收紧，但binder名字差异可造成false negative，一般参数Prop仍需Lean语义比较 |

| V03-68 / 两条proof-walk独立产物审计已限定执行 | 实际1call normalization成功run与0call inventory-preflight失败run | 从SQLite只读重建计划/预算/事件，核对模型原始bytes、源文/context fingerprint、Lean runtime/library/candidate回执与对象companions、UNKNOWN与review门禁 | `proof-worker-normalization-attempt02-20260919/audit-proof-walk-attempt05.json` PASS/0issues，74引用文件、3Lean receipts；首个失败run `audit-proof-walk-attempt04.json` PASS/0issues、2环境回执。没有新模型/Lean执行，也未重扫8.6GB历史库 | 数学仍CHAIN_INCOMPLETE；旧worker的Prop binder名称错配潜在false positive已静态定位，但两run显式Prop组合边均0、未触发；不以完整性PASS代替来源接受 |
| V03-69 / Prop组合安全修复仅静态完成 | proof_backend、旧driver提供的实际使用binder与statement参数可能异名 | 类型 `(h:P)→(k:¬P)→¬P` 与证明 `fun k h => h` 的名字可交叉；禁止通过名字或type包含P即认可P | 现worker所有EXPLICIT_PROP_PREMISE一律NOT_COMPOSED，basis为PROP_BINDER_TYPE_EQUIVALENCE_UNAVAILABLE；原冻结worker/历史run不改。普通定理直接term依赖保持 | 未执行该反例或fallback回归；重新启用须对实际proof-value binder做indexed Lean类型等价判断，不能仅pp字符串/同名join |
| V03-70 / PDF页区域候选装配与本来源完整性审计已限定执行 | Lovász1972已视觉读取的4页原PDF、对应PNG和10条阅读记录 | 保留所有原始字节/图像、实际pdfinfo页数、区域坐标和局部证明条件；反证假设不提升为查询结论；装配内部/外部支持 | `semantic-lovasz-pdf-regions-attempt02-20260919` 10阅读行、9query+1非断言context，裁剪后10节点/7组/1Berge请求；`integrity-report.json` PASS/0issues。第一次装配保留，第二次稳定ID不依赖输出目录且冻结runtime | 完整性仅核对字节、回执、坐标和图重建，未重新渲染/独立视觉核对、未接受数学内容；PDF多模态proof context尚缺，当前worker明确返回不支持；Berge仍FRONTIER |
| V03-71 / 完美图复制及最大独立集横截团已限定编译 | 已证色类工具、真实IsPerfect与finite graph、clique纤维复制 | 诱导图同构传递，true-twin全诱导子图完美性，自然权重clique blowup及最大独立集发生项计数 | Transport9新/15term、TrueTwin14新/34term、Replication4新/12term、CliqueFibres8新/11term、CliqueTransversal14新/22term，各独立成功run/失败历史保留、标准公理且旧缓存未改 | 原4.30环境证明；最后横截团端点仍需0<indepNum，空图在下一步处理；补图完美与实权重对偶未据此提前宣称，源文对齐未接受 |

| V03-72 / 全文39范围运行已结束但控制器异常退出 | V03-65同一自动派发计划与持久回执 | 17范围成功、4超时、1候选校验失败、17模型进程失败；合并成功输出118候选，图383节点/106组 | `research-live-full-output-batches-20260919`保留全部dispatch；图10,617,299bytes触发通用10MiB读取上限，进程exit1，checkpoint仍RUNNING、无最终summary；本轮仅阅读这些产物 | 尚未做这份新图独立完整性审计；需修复图边界/异常收尾/恢复；来源覆盖22范围缺失，不是全文完成 |
| V03-73 / 账户用量耗尽路径实际暴露；修复待实现 | 同一39范围计划batch22及后续events | 上游账户用量错误被归为MODEL_PROCESS_FAILED，随后仍派发其余16范围 | 历史events明确usage limit；全部17进程失败回执保留，本轮未再次执行 | 需类型化provider quota/auth故障、熔断与剩余范围NOT_DISPATCHED；不以新plan重新派发绕过用量/审批 |
| V03-74 / Prop V2运行库已编译；真实组合路径未执行 | 新GeneratedProofDriverV2及独立冻结runtime、必要库6声明 | 实际proof-value binder index+Lean isDefEq判定；原driver历史不改；新runtime原始副本留在run中 | `proof-worker-environment-prop-v2-attempt02-20260919`runtime/library回执exit0；前次matches保留字解析失败保留。两节点clique→convex来源图已装配/审计，但proof命令因自动审批用量故障没有执行 | Prop fallback正/负路径、名字错配反例回归及多节点调度尚未覆盖；新auditor适配只静态修改，不能套用旧run PASS |
| V03-75 / 额外5模块共同环境迁移已完成 | GraphDualBounds、ColorClass、Transport、TrueTwin、Replication，已有14新增层只读 | 5模块实际编译并审计本层目标与前层目标 | `20260919-graph-bounds-perfect-replication`60新增（47定理/13定义），累计302声明（230/69/3）、662term；7receipt=5成功2失败，3适配记录保留 | 后续CliqueFibres/Transversal/WeakPerfect三模块新层首项编译失败，未完成，不能混入302成功计数 |
| V03-76 / Xu正文八批限定装配/审计已完成 | 新冻结源码、main01/02 provenance-v2、其余六批原provenance | 保留179行无重复冲突；main112129bytes和5条bib2278bytes读范围；只装配对应候选 | `xu2511-main-combined-20260919`与`semantic-xu2511-main-20260919`179query/243nodes/159groups/64requests，原文/重建PASS；另appendix01的30行尚未合并/审计 | 原文语义未接受、其他附录未读完；全部新Xu/Gottesman候选尚未重新接入旧主递归plan；不能把正文完成当全文完成 |
| V03-77 / 弱完美图和无权整数覆盖端点已限定编译 | 实际复制、横截最大独立集clique和诱导子图删除归纳 | 从IsPerfect证明补图IsPerfect；构造alpha个clique恰一次覆盖并证明任何k覆盖满足alpha≤k，含空图 | `perfect-graph-weak-perfect-20260919`8新/12term；`perfect-graph-integral-cover-20260919`2新/2term，原4.30成功证据保留 | 整数权复制仍在失败修复中，有理/实权重对偶未完成；这几项未迁入共同epoch，源文对齐与最终query仍缺 |

| V03-78 / 操作级模型路由与schema仅静态实现 | 新model_routing.py、engines.json、Plan/Task新增契约；后续明确授权相应执行范围 | 新plan冻结路由后更改账户默认/磁盘profile，分别选择抽取、语义匹配、失败分类、Lean/premise；尝试未知operation及非proof使用HEAVY | 已有plan始终用冻结模型/effort；默认Luna/Terra/Astra分工可解释；非法route在reserve前拒绝；旧无policy计划须新plan才能dispatch，旧回执可读；无自动昂贵升级 | 未执行；模型实际可用性、Luna/Terra输出质量与成本校准未知。不重跑已完成任务做降级对照 |
| V03-79 / 模型路由证据审计仅静态实现 | 新Task/receipt含model_selection与effort，审计器绑定plan；需后续限定授权 | task/receipt互相一致但偏离plan；篡改effort/policy hash；0call计划；历史无route回执 | 新计划对模型、effort、operation、profile、reason、policy digest逐项核对；缺失/篡改失败；旧证据不被改标新模型或套用本次结论 | 未执行；Task属性保持历史兼容，新计划由宿主审计强制route；未重新运行历史PASS审计 |
| V03-80 / provider熔断仅静态实现 | model_failures.py、SQLite reserve/settle、batch与research状态；需后续明确授权 | 真实error/turn.failed出现usage/auth/429；普通agent_message包含相同文字；首次query失败；重启后再次reserve；随后已有成功batch | 错误分类只从provider错误证据取得；持久停止新调用并保留失败/未派发范围；已有成功batch继续复用；不会换模型/账户/新plan自动重试；首次query注明provider阻塞 | 未执行；历史batch22及后16调用保持原始MODEL_PROCESS_FAILED回执，不回写成新分类；没有用新plan绕过限制 |
| V03-81 / 成功批次复用与缺失范围续跑仅静态实现 | --imports.extraction_batches冻结dispatch；相同paper/source manifest/2048byte范围；原39范围17成功产物只读；后续额度及指定执行范围可用 | 新plan只引用成功17范围，补缺失22；篡改source/range/result/receipt/response，嵌套复用超过16层或环路；quota后剩余成功scope | 成功CANDIDATE_REUSED保留原模型身份和bytes；新plan只计新call；失败匹配不得复用；预算只限制新派发；审计将reuse_dispatch绑到plan；旧query与ledger不改 | 未执行；无新抽取/model调用；这里只支持完成dispatch的部分批次续接，BUSY恢复、跨paper semantic-match失败续接仍未实现 |
| V03-82 / 大图独立大小边界仅静态实现 | _verified_graph_json及research/proof_walk/audit接入，MAX_GRAPH_BYTES=64MiB；后续明确授权 | 读取历史10,617,299byte图、缺失/错误hash与byte_size、超64MiB、无nodes/support_groups；普通模型JSON仍超过10MiB | 正确graph可在64MiB内有界读取，超限/错hash/结构拒绝；普通证据不扩大；publish在替换graph指针前拒绝超限 | 未执行；没有读取执行重建或重跑历史全图审计；异常BUSY完整恢复仍另属前置缺口 |

2026-09-20本轮早期静态修改阶段：只阅读与修改代码、契约和文档，尚无测试、模型抽取、Lean构建或示例重放。审阅代理误执行过一次`git diff --check`，无输出；已停止此类操作，不能据此填写任何功能验证通过。随后账户普通用量恢复，继续用户已要求的案例实际处理，结果追加在V03-83及以后；历史报告与成功产物未改写。

V03-80补充待执行情景：provider熔断后的新PROOF/PREMISE reservation在扣次数前拒绝，scheduler保留`MODEL_PROVIDER_CIRCUIT_OPEN`等待状态；已有同context证明结果仍可复用。涉及core/scheduler的新分支仅静态修改，未执行。

| V03-83 / 目标缺失范围Luna真实续跑进行中 | 本轮只读账户查询ordinaryUsageAllowed=true，用户已要求继续目标论文案例；新路由与batch reuse已静态审阅 | `research-luna-continuation-20260920`，1paper/22新model calls上限/每call180秒/2048byte focus；复用原17成功范围，只处理22缺失范围 | 已实际开始，冻结paper.extract=Luna medium；已观察17范围CANDIDATE_REUSED及新增成功/失败回执。结束后追加实际结果 | 尚未结束；不是独立测试或历史重放。新质量失败原样保留，无Lean重跑；不据此声称所有claims或校准/节费已验证 |

| V03-84 / Luna目标缺失范围实际续跑完成 | V03-83同一新计划及原17成功范围 | 22次Luna调用只处理缺失范围；原17范围按immutable引用复用；汇总新候选与图 | `research-luna-continuation-20260920/summary.json`正常exit2/CHAIN_INCOMPLETE：20新成功、2来源定位失败、17复用，227候选/583节点/200组，graph35,099,488bytes，checkpoint READY。新scope1与33失败原文/回执保留 | 只说明实际工作路径结果；无独立审计或负向测试，没有重跑旧成功范围/Lean；模型身份为requested非provider独立认证，成本节省与语义完整性未知 |
| V03-85 / Terra仅补剩余2范围实际完成 | 新--extraction-profile LIGHT_TERRA，仅新plan改变paper.extract；导入V03-84 dispatch，37成功范围可复用 | 新plan只为scope1/33调用Terra，其余全部复用；合并并正常结束控制器 | `research-terra-continuation-20260920/summary.json`exit2/CHAIN_INCOMPLETE：2新call都成功、37范围复用，39/39都有候选响应；240候选/613节点/213组，graph39,249,196bytes，149/180启发式位置与44新定位 | 最终0未完成output scope，不等于所有math claims；依赖闭合/语义接受/最终Lean仍缺；两份新run独立产物审计与resume路线拒绝等负向路径未执行 |
| V03-86 / schema路线约束、可选Terra与proof熔断待覆盖 | schema的ModelRoutingPolicy/ModelSelection限制非proof为Luna/Terra；core/scheduler的新proof gate；后续限定授权 | 新plan选LIGHT_TERRA只改抽取；resume显式改profile被拒；校验器拒绝非proof+Astra；provider错误后不再花proof/premise slots但可复用旧结果 | 新Terra实际抽取路径已由V03-85记录；其余非法路由、resume、provider/并发和历史兼容的独立验证均未执行 | 不能用V03-85的普通成功路径替代这些待执行情景；历史源码、原始17批和已有Lean记录不回写 |

### Osborne 讲座恢复 PDF（2026-09-20）

- 对象：`output/pdf/osborne-slides-recovered.pdf` 与 `output/pdf/osborne-recovered/` 恢复素材。
- 准备条件：用户后续明确授权文档验证；原 Claude 会话 JSONL、PDF 阅读器及 PDF 渲染工具可用。
- 操作情景：逐页查看中文字体、分页、长段落与配图；对照历史会话的 73 条讲解、6 个章节、时间戳及 7 张拼图，核对图片裁切和对应关系。
- 预期结果：文字无裁切和乱码，条目与时间戳对应正确，图片无跨格错位；恢复说明明确配图来自较低清晰度缩略图、文字未经重新事实核实。
- 当前状态：已从历史记录提取内容并生成 HTML、素材和 PDF；遵守默认不执行验证的约定，未执行 PDF 渲染审阅、自动校验或测试，不声明验证通过。
- 前置限制：原始高清截图未找到；本次恢复使用会话内嵌拼图，无法恢复其丢失的高清细节。

### Agent 关系图 SVG（2026-09-20）

- 对象：`output/diagrams/agent-system-relationships.svg`。
- 准备条件：用户后续明确授权视觉验证；SVG 浏览器或幻灯片软件可用，并安装中文字体。
- 操作情景：打开 SVG，检查文字换行、边界、箭头方向；导入幻灯片后查看比例与字体替代。
- 预期结果：各元素无重叠或裁切，调用与返回路径可辨，中文可读；Agent runtime、上下文、MCP 与外部模型的边界保持清楚。
- 当前状态：已编写 SVG，仅静态审阅；未运行渲染、校验器或测试。字体替代与导入表现待验证。

- 2026-09-20 Agent 关系图简化更新：同一 SVG 已改为仅展示 API、Agent、MCP、Schema、Skills、Tools、Context。待用户授权后检查两条工具接入路径、Schema 描述虚线与结果回流线的布局和字体；预期七概念清晰可读、无裁切，MCP 与 API 不被误读为互斥技术或连续阶段。当前仅完成编辑，未执行渲染验证。

### Chain-build AND 焦点视图（2026-09-21）

- 对象：`slides/chain-build/chain-build-gpt.html`；原 HTML 保留。
- 准备条件：用户明确授权浏览器验证；支持 SVG/JavaScript 的浏览器。
- 操作情景：首次打开显示 AND 焦点页；核对两个卡片与原记录的支持组一致；点击/键盘激活卡片查看来源状态；Esc/返回按钮切回完整图；打开焦点按钮；恢复原翻页与节点详情。
- 预期结果：明确区分组内成员线与指向结论的支持箭头，直接前提仅 exact-reduced-vrep 和 no-active-free-signs；焦点操作不推进底层幻灯片；退出后可正常导航；全图历史数据不变，图展开完成不被标为证明完成。
- 当前状态：已生成独立试验 HTML；仅静态阅读编辑，未执行浏览器、渲染、校验器或测试。视觉布局、交互与键盘行为待验证。

- 2026-09-21 用户纠正后的新版：撤掉独立解释页，直接重绘完整29节点依赖图。所有多成员支持组改为圆角 AND gate，虚线表示成员、实线箭头指向结论；单成员组仅保留依赖箭头。默认选中 relaxation-exactness 的组，数字标记两个直接前提并在侧栏列明，其他组淡化。待授权验证：所有gate选择/清除/键盘激活、原31页翻页、节点详情及阶段状态显示；预期选中成员与原 support_groups 一致、隐藏阶段不可操作、无文本溢出；当前仅编辑，未运行渲染或测试。先前焦点覆盖页待测项由本实现取代。

- 2026-09-21 精简显示更新：移除 GPT 版新增标题、说明和侧栏，依赖图恢复全画幅；图阶段隐藏提示、页脚说明与页码，保留原稀疏节点标签。点击同一 AND gate 可取消高亮。待授权检查全画幅布局、翻页时图专属隐藏状态和 gate 选择；未执行渲染或测试。

- 2026-09-21 单色正交布局版：按原始支持关系重新生成29节点与多前提汇合点的位置，移除旧 L0–L8 视觉层；多前提边在圆圈加号（本图约定为AND）汇合，单条实线箭头指向结论；所有连接为水平/垂直直线，单前提直接箭头。采用黑白、透明度和线宽，默认完整图无选择。仅执行图布局与HTML生成，未执行渲染审阅、测试或验证。后续待授权查看各交叉处/汇合点可读性、稀疏标签位置、节点边界与箭头间距、点击汇合点与历史分页功能；⊕符号的教学语义需明确为本图约定，不能解释为数学直和。

- 2026-09-21 箭头与层级修订：恢复原节点记录的 L0–L8 精确层级和等距水平参考线，以全宽横向展开。正交路由由布局器生成；逻辑依赖箭头改为显式三角形，停在结论节点外侧，避免 marker 渲染/方向问题；保留黑白 ⊕ AND 与交互。未执行渲染审阅或测试。待授权确认：箭头与线端衔接、正交折点及同层依赖绕行、各节点原层级、根标签间距与选择交互。

- 2026-09-21 Frontend Slides skill 样式适配：已阅读用户指定的远程 SKILL.md、viewport-base.css、html-template.md 和 animation-patterns.md。引入完整固定16:9基础CSS；原展示层改用 visibility/opacity/pointer-events 切换，保留JetBrains Mono、纸白墨黑、稀疏标签及克制淡入。新增待测：1280×720与手机视口等比缩放、隐藏层不得截获点击、原31帧导航与图选择、SVG文字和折线不溢出。遵守用户默认禁验证要求，未执行skill所建议的截图验证；不能声称视觉验收完成。

### Chain-build 演讲叙事整改版（2026-09-21）

- 对象：`slides/chain-build/chain-build-gpt.html`。本轮按用户要求基于当前 `chain-build.html` 重组前半段，保留原版自动抽取图、人工依赖图、逐层展开与结尾图组。旧 GPT 图交互实验保存在 `slides/chain-build/archive/chain-build-gpt-before-narrative-20260921.html`；本节描述当前输出，前述实验及历史记录不改写。
- 准备条件：用户后续明确授权浏览器/视觉/交互验证；支持 HTML、SVG 和 JavaScript 的浏览器，Calibri 或 Carlito 字体（缺失时使用 sans-serif 回退）。
- 操作情景：从封面顺序浏览全部 49 个播放状态（18 个新叙事页、7 个流程动画状态、24 个沿用的示例与结尾状态）；使用左右方向键、空格、PageUp/PageDown、Home/End 和点击翻页；从新桥页进入自动抽取图，再切换到人工依赖图；在链的展开、roots、form、stuck 阶段查看节点详情并关闭。
- 预期结果：没有空白帧或多层同时显示；四种可信性先于工具介绍，局部证明与目标定理有明确区分；613/240 的自动抽取对象和 74/29 的人工构建对象不会被误读为同一筛选漏斗；图的节点、边、来源颜色、几何与详情记录保持原版内容，既有展开次序与交互可用。
- 操作情景（布局）：在 1920×1080、1280×720 和较小视口下逐页阅读标题、公式、表格、双栏数字页、流程图上方标签与底部说明；离线或字体加载失败时观察回退排版。
- 预期结果（布局）：固定 16:9 画布等比缩放；正文、公式和页尾不重叠或裁切；新增样式限定在叙事区域，不改变受保护示例图的样式。
- 当前状态：HTML 已生成，采用文件阅读与协作静态审阅；未执行浏览器渲染、截图、校验器、单元测试、交互测试或 Lean 构建，不能据此宣称视觉或功能验证通过。页内实验数字引用既有记录，非本轮重新运行结果。
- 前置阻塞：无待实现接口阻塞；实际排版、字体回退和浏览器交互结果待用户授权执行后记录。本版为独立 HTML，未同步原 PPTX 或原构建脚本。

### Chain-build 保留材料的衔接修订（2026-09-21，按用户纠正）

- 对象：当前 `slides/chain-build/chain-build-gpt.html`。用户否定上一版删换前半段材料的做法；本轮从原始 `chain-build.html` 重新制作，恢复全部 69 个播放状态、原选图片与例子、完整 8 帧 motivation。上一版 49 状态的文件另存 `slides/chain-build/archive/chain-build-gpt-restructured-20260921.html`，上节待测记录作为该历史版本记录保留。
- 准备条件：用户后续明确授权浏览器视觉及交互验证；支持 SVG/JavaScript 的浏览器及 Calibri/Carlito 字体。
- 操作情景：逐步浏览 69 个状态，特别查看黑箱四帧、memory 三帧、agent 八帧、学习/推理五帧的渐进内容；核对原图片、引用、职业焦虑动机、成本与基础库材料均保留；查看前 45 状态的新过渡字幕与画面、下一页的关系。
- 预期结果：所有原材料仍可见且依次播放；前半段标题、英语及结构保证的表述清晰，agent 角标为 1/8 至 8/8；过渡句使原有介绍、motivation、流程和例图连贯，不将候选、已检查或目标完成混为一谈。
- 操作情景（布局与保护）：在 1920×1080、1280×720 与较小视口查看 `#fw` 的局部 0.95 缩放；检查低位文献引用与底部字幕间距，fs24 原先超出 viewBox 的结束句是否完整显示；进入 o2 起的原图组并查看节点、阶段与详情。
- 预期结果（布局与保护）：原图片不裁切或替换；字幕不遮挡引用和正文；局部样式不影响后面的示例依赖图；图组继续使用原 meter、原配色、原展开顺序和原交互。
- 当前状态：只执行 HTML 编写、文件阅读和协作静态审阅。未运行浏览器、渲染、截图、校验器或测试，实际字体与布局效果待验证；本轮没有重新执行图中所引研究实验。
- 前置阻塞：无新增接口依赖；仅待用户授权浏览器验证。本版不更新原 HTML、PPTX 或其构建脚本。

| V03-87 / 2026-09-22四论文候选复用已实际执行，匹配未连接 | 240目标、179 Xu正文、81 Varela、450 Gottesman既有候选与冻结来源 | research-recursive-continuation-20260922复用四篇；仅新语义匹配，无提取或Lean重跑 | 正常exit2/CHAIN_INCOMPLETE，四篇候选已导入；Xu调用在CLI turn/start因1,069,565字符超1,048,576被拒；Varela候选定位失败；Gottesman在宿主输入限制前拒绝，原回执/问题保留 | 图仍613节点/213组，无新增支持连接；不能把导入全文候选算作语义支持或最早出处已确定 |
| V03-88 / 字符门禁与小批次匹配实现并用于实际续跑 | 当前CLI错误原文为字符上限；宿主此前只有1.5MiB字节限制 | 新Task记录字符数/上限；超限在reserve前拒绝；完整论文保留，仅去除occurrence inventory中重复全文text；每call至多4个外部请求冻结在plan | research-recursive-compact-20260922已启动；实际观察一个引用定位失败和一个候选成功，后续结果待记录 | 未运行独立测试/审计；边界字符、Unicode、resume历史兼容、跨批请求覆盖和混合失败负路径仍待执行；不以源文候选成功断言数学正确 |


### V03-89 / 显式 claim ID 消歧与成功匹配复用（2026-09-22）

- 对象：recursive_graph.join_candidate_paper、research 新计划 source_join_policy、审计重建路径。
- 准备条件：后续明确授权独立测试；冻结新旧计划及共享 occurrence 的多个 claim。
- 操作情景：共享 occurrence 加显式合法 claim ID 与 JOINT_SUPPORT；缺失/未知 ID、非联合支持、引文未覆盖、旧计划无策略字段；复用含不确定/不匹配响应。
- 预期结果：只连接明确选择且精确引文覆盖的候选；其余保留拒绝；旧计划含义不变；复用不计新模型调用；不把候选当已验证支持。
- 当前状态：实际增量研究 research-join-reuse-20260922 已 exit 2，0 次模型调用，633 节点/225 组，一个外部候选支持组，accepted_support_edges=0。未执行独立测试或审计，兼容性及负路径待执行。
- V03-88 结果补记：compact 计划已 exit 2，10 次调用、4 次候选成功、6 次候选定位失败；不再处于运行状态。
- 前置阻塞：完整链条仍需语义对齐、未完成来源覆盖和证明后端连接。

### V03-90 / 递归匹配请求的结果与尝试分离（2026-09-22）

- 对象：research.py checkpoint.match_outcomes 与 summary 的结果计数。
- 准备条件：后续授权独立执行；新计划、旧版仅有 attempted_matches 的 checkpoint、导入与现场响应混合批次。
- 操作情景：派发前失败、模型响应不可用、响应已有但图未发布、宿主连接拒绝、候选/不确定/不匹配结果记录；中断恢复与旧 checkpoint 读取。
- 预期结果：逐请求保存状态和已存在的模型结果/匹配/来源引用；所有记录 mathematically_resolved=false；旧尝试单独计为结果未知；失败不自动重试，候选不升级为证明完成。
- 当前状态：代码已修改并静态阅读，未运行测试、校验器或研究重放。新字段尚无实际新计划运行证据；旧的已冻结运行记录未改写。
- 前置阻塞：明确的跨计划选择性重试接口尚未实现；本修改提供结果可见性，不宣称已经具备完整失败恢复功能。

### V03-91 / 精确引文失败原因与修复要求（2026-09-22）

- 对象：model.bind_source_locators 与 dependency.match 源文提示。
- 准备条件：后续明确授权执行；含 TeX、Unicode、重复和相互重叠引文的冻结来源。
- 操作情景：引文不存在、重复两次、重复超过八次、相互重叠出现、唯一出现；模型改写空白或 TeX。
- 预期结果：沿用原拒绝代码，新增 ABSENT/REPEATED 区分、来源与引文哈希；重复位置最多八个且说明截断；不猜偏移、不自动改写引文，不改变唯一原文才能绑定的门槛。
- 当前状态：阅读六个历史失败回执后实现；这些回执原来合并记录“缺失或重复”，本次未重新执行定位器或校验器，不对其具体原因作未经验证的断言。提示现在明确保留 TeX 和换行、重复引文应扩展上下文。新增路径仅静态阅读，待执行。
- 前置阻塞：历史失败响应的逐行回收与定向引文修复尚未实现；不能因本修改就将旧失败改为成功。

### V03-92 / 匹配响应逐行保留（2026-09-22）

- 对象：model.match_source_candidates、research.match_batch、audit_research 的 PartialMatchSelection。
- 准备条件：后续授权测试；混合有效/无效引文响应，以及含重复请求、缺失请求、未知 ID、schema 错误或工具事件的响应。
- 操作情景：一行引文失败、其余行可绑定；全行失败；非引文类失败；选择文件或原响应被修改。
- 预期结果：仅引文局部错误允许隔离整行；其余失败拒绝整批；保留原失败回执、原响应哈希、选择/排除行号；保留行仍须通过图连接要求，永不升级为数学验证；不新增重试调用。
- 当前状态：已实现并静态阅读，未执行测试、校验器或模型调用；历史失败响应未自动重新分类或回收。审计新增选择重建，但未运行。
- 前置阻塞：历史响应回收入口仍待实现；新机制首先用于后续新调用。

### V03-93 / 历史匹配失败响应的显式回收（2026-09-22）

- 对象：host/recover_match_rows.py。
- 准备条件：冻结的 dependency.match 回执、task、prompt 和 response；新增输出路径。
- 操作情景：仅有行级引文错误；非局部错误、请求重复/缺失、错误行号越界、原字节变化、目标文件已存在。
- 预期结果：按原回执排除完整错误行；保持原始回执不变；记录选择行号、原证据引用及未解决请求；上述非法输入拒绝。输出不是语义复审或已接受支持。
- 当前状态：按目标实际回收六份此前未回收的失败响应，生成六份独立文件，共保留15行、排除9行，新增模型调用0；未执行独立测试、校验器或图重放，负路径待测。回收结果尚未加入查询图。
- 前置阻塞：仍需将回收文件合并到论文对导入清单，并经正常图连接保留来源定位/假设等边界。

### V03-94 / 回收判断的增量图连接（2026-09-22）

- 对象：recursive-recovered-join-20260922 导入清单与实际研究计划。
- 准备条件：四篇既有抽取候选、12条成功匹配、15条历史回收判断；不调用新模型。
- 操作情景：按论文对合并27条不重复请求，正常经过来源定位、声明身份及查询分支裁剪。
- 预期结果：原回收证据引用保留；候选不变成已接受支持；不确定/不匹配不建立支持关系；缺失判断保持未解决。
- 当前状态：已生成 combined-match-recovery-20260922 两份合并文件及导入清单；实际控制器已启动、模型上限0，最终状态另补记。未运行独立测试或审计，不将增量研究结果宣称为全流程验证。
- 前置阻塞：语义对齐、剩余来源覆盖和查询证明仍未完成。

V03-94 结果补记：实际进程已 exit 2，0模型调用、667节点/247组；24个未审阅判断、3个连接拒绝、12个派发失败，accepted_support_edges=0。未执行独立测试/审计。

### V03-95 / 三条来源阅读修订候选（2026-09-22）

- 对象：source-reading-amendments-20260922 与 recursive-amended-join-20260922.json。
- 准备条件：三条历史拒绝行、Varela 原文、显式声明 ID；后续增量连接。
- 操作情景：不再主张引文覆盖额外 occurrence，改由明确 claim ID 接受原连接要求；投影不等式引用引理原句；定义和复杂性定理以 JOINT_SUPPORT 组合。
- 预期结果：修订理由、原行和新行均可追踪；没有删除数学前提；若引文仍未覆盖声明或身份不明确则继续拒绝；不将修订视为语义接受。
- 当前状态：原文静态阅读并生成三条显式修订候选及新导入清单；未执行连接、独立测试或 Lean，不能声称三条拒绝已经解除。
- 前置阻塞：候选连接与语义审阅尚待完成。

### V03-96 / 来源修订增量连接与 Xu 附录剩余范围（2026-09-22）

- 对象：research-amended-join-20260922；profiles/xu-appendix-remaining-scopes-20260922.json。
- 准备条件：三条修订候选及原始证据；Xu appendix-01 的历史阅读记录。
- 操作情景：零调用增量连接；后续按附录剩余小节抽取并复用已读前缀。
- 预期结果：候选仍保留语义审阅边界；附录 0..12609 已有工作不重跑，12609..84137 的71528字节按12个相邻范围处理，不以范围清单宣称已读取或提取完成。
- 当前状态：连接已启动；范围清单已生成、未派发模型；未运行独立测试/审计/Lean。连接最终结果另补记。
- 前置阻塞：范围清单尚需接入冻结抽取计划；剩余附录候选未产生。

V03-95/96结果补记：修订连接已exit2，667节点/250组、9个外部候选组、match_issues=0；27条未审阅判断、12派发失败。0模型调用，未执行独立测试或Lean；尚无语义接受。

### V03-97 / 显式剩余来源范围接入抽取调度（2026-09-22）

- 对象：extract_batches.explicit_ranges、research.freeze_imports.extraction_scopes、批次审计重建。
- 准备条件：冻结范围清单、完整原文和批次模式；同一论文不得同时整体导入候选。
- 操作情景：选定附录子范围；源哈希变化、未知文件、范围重叠/越界/超限、重复ID、UTF-8切断、非批次模式。
- 预期结果：仅输出指定范围候选，完整原文仍作为上下文；范围清单冻结并进入dispatch，审计依同一清单重建；非法计划拒绝；不把被排除正文或旧前缀宣称为本次新抽取。
- 当前状态：实现并静态阅读，未运行模型、测试或审计；Xu剩余12范围尚未派发。旧范围规划保留，新字段可选。
- 前置阻塞：需新建实际抽取计划并处理结果；新范围结果后续仍需与历史正文/前缀显式合并，不能当成全篇候选。

### V03-98 / Xu 附录剩余范围实际抽取（2026-09-22）

- 对象：research-xu-appendix-20260922，新建单论文抽取计划；产物不得替代全篇图。
- 准备条件：冻结 extraction_scopes 导入及完整已有源文件。
- 操作情景：仅输出12个未完成范围，最多12次LIGHT调用，单次180秒；已完成正文和附录前缀不重新生成候选。
- 预期结果：逐范围候选/失败回执保留；未完成项可复用续跑；不会将局部附录产物标作全篇数学声明完整。
- 当前状态：实际进程已启动，exec session 74654；首个Task请求gpt-5.6-luna/medium，输入1023212字符，未超宿主字符上限。最后轮询仍运行，尚无最终结果；这是新增抽取工作，不是独立测试，未运行Lean或测试套件。
- 前置阻塞：待实际响应及来源绑定结果；终止状态只能由进程返回确认，不因锁文件或等待超时认定结束。

### V03-99 / Xu 正文与附录增量合并入口（2026-09-22）

- 对象：runs/combine_xu_appendix_20260922.py。
- 准备条件：research-xu-appendix-20260922 已终止并产生 summary、checkpoint 与 dispatch。
- 操作情景：复用八个正文批次、已有附录前缀及本次成功范围；部分失败、运行未结束、重复输出或结果字节变化。
- 预期结果：原文/来源证据保留；新模型范围不伪装成已报告阅读字节；未完成范围明确列入范围说明；运行中与重复输出拒绝；不重跑模型。
- 当前状态：脚本已编写并静态阅读，尚未执行；当前抽取进程仍运行，前四范围已记录34条候选。未执行独立测试/Lean。
- 前置阻塞：必须等待当前进程终止后合并，不能据现有部分结果宣称附录完整。

### V03-100 / Xu 附录第五范围的结构修订（2026-09-22）

- 对象：xu-appendix-05-structural-amendment-20260922 与合并入口。
- 准备条件：原回执唯一错误为claim_index=2的重复internal_support_occurrence_ids；原响应哈希保持一致。
- 操作情景：精确重复ID保留首个；原数学陈述、条件和其余引用不改；作为独立修订批次参与后续装配。
- 预期结果：原失败继续保留，新provenance记录前后值和原始证据；不将助手修订伪装成模型成功；不声称原文穷尽或语义接受。
- 当前状态：已另存8条结构修订候选、provenance并接入合并入口；尚未装配或运行独立测试，不计入模型成功范围数。
- 前置阻塞：抽取进程仍需终止，之后正常装配可能发现其他问题，应如实保留。

### V03-101 / Xu 第七范围引用ID修订（2026-09-22）

- 对象：xu-appendix-07-reference-amendment-20260922；合并入口。
- 准备条件：原失败唯一问题为未知occurrence ID；冻结源清单有明确T_r定义。
- 操作情景：原ID 962bb4d04f1262 修订为 962bb4d4d04f1262；记录完整原文位置、原行与新行，不推行自动模糊ID匹配。
- 预期结果：来源阅读修订单独留证，原失败回执不变，数学陈述与依赖前提不改；正常装配仍执行来源要求。
- 当前状态：3条候选另存为修订，合并入口已接入；未执行装配或独立测试，不能计作模型成功范围。
- 前置阻塞：仍等待实际抽取终止；后续语义确认未完成。

V03-98至101结果补记：session74654已exit2；12次Luna调用、10成功范围105候选、2原失败。实际合并正常结束，正文179+历史前缀30+新成功105+独立修订11=325候选；装配不等于语义接受。合并无新模型调用，未执行独立测试/审计/Lean；新导入清单已准备，目标图尚未扩充。

### V03-102 / 语义匹配来源位置元数据去重（2026-09-22）

- 对象：model.match_source_candidates提示渲染。
- 准备条件：完整冻结来源及候选assembly；新计划。
- 操作情景：大型Gottesman候选清单；Unicode字节位置；带多个来源位置的候选。
- 预期结果：完整源文、声明文本/条件/ID、所有位置路径和起止字节不变；文件哈希仅在全文来源表保留；半开字节区间语义明确。超限仍拒绝，不截断来源。
- 当前状态：依据历史宿主超字符上限回执实现元数据去重，仅静态阅读；尚未新派发，不能宣称Gottesman已可调用。当前零调用图扩充计划使用先前冻结代码，不受本修改影响。
- 前置阻塞：需新计划实际匹配；新提示的长度及模型效果尚未测定。未运行独立测试。

Xu扩充版实际导入补记：research-xu-expanded-20260922已exit2，0模型调用；Xu候选325条、495/564启发式位置被引用，目标图仍667节点/250组。新候选可用不等于新增支持或语义接受，仍有12请求未派发。未执行独立测试或Lean。

### V03-103 / 剩余匹配实际派发与设计同步（2026-09-22）

- 对象：research-match-remaining-20260922、设计§4.4。
- 准备条件：四篇冻结候选，Xu扩充325候选，27条既有匹配；最多6次Terra调用。
- 操作情景：仅对导入中缺少结果的请求派发，完整原文保留并压缩重复位置元数据。
- 预期结果：既有判断复用，新增回执可追踪；来源/语义不明确仍保留；输入超限仍拒绝。
- 当前状态：实际session68269仍运行，已观察3次CANDIDATE_RECORDED；首个Xu输入750053字符。Gottesman尚无成功派发证据。未执行独立测试/Lean；最终连接结果待进程终止。
- 前置阻塞：剩余响应与图连接未结束；不能把模型候选成功等同于数学接受。设计文档§4.4已同步当前增量证据规则。

V03-91/92/103实际路径补记：research-match-remaining-20260922 已出现一份三行响应，其中row0的精确引文为ABSENT，失败诊断保留源文及引文哈希；另两行通过partial-selection.json保留，原receipt仍MODEL_CANDIDATE_VALIDATION_FAILED。这是实际新匹配处理结果，不是独立测试或审计；最终图尚待进程终止，Gottesman尚无派发证据。

V03-103终止补记：session68269已exit2，6次Terra调用、676节点/262组、14外部候选组；32未审阅判断、2连接拒绝、4派发失败、1模型响应不可用。部分行保留已实际执行；Gottesman未派发原因为调用预算耗尽。34条既有匹配另存可复用清单，未执行独立测试或Lean。

### V03-104 / 固定窗口反例与新依赖请求关联（2026-09-22）

- 对象：runs/fixed-window-boundary-review-20260922/association.json。
- 准备条件：已有固定窗口反例报告与新请求request:e985199ac838196a4a520abe。
- 操作情景：新模型引用原文单调性陈述并指出证明缺口；关联旧反例，保留源命题和原模型判断。
- 预期结果：不能仅修正引文就把该命题视作可用前提；历史反例来源可追踪，不宣称本轮Lean验证。
- 当前状态：原文/既有报告静态阅读并保存关联证据，未写入当前冻结图；当前关联为待应用审阅材料，不是自动图门禁。未执行测试或Lean。
- 前置阻塞：通用外部反例/审阅覆盖层尚待接入计划和图审计。

V03-103后续计划：research-last-source-matches-20260922已启动，session78615，复用34条判断，最多4次Terra。已观察Varela新候选回执，进程仍运行；勿重新启动同目录。

### V03-105 / 冻结来源异议进入图阻断（2026-09-22）

- 对象：review_blocks.py、research imports/publish_graph、audit_research decorated重建。
- 准备条件：显式review_blocks引用，SourceClaimCounterexampleAssociation含disputed_claim_ids及原匹配/反例证据哈希。
- 操作情景：关联固定窗口单调性；证据变更、目标不一致、被争议claim不在原匹配、其他联合前提有效。
- 预期结果：对争议claim及请求加入SOURCE_REVIEW_OBJECTION阻断，保留源文和模型结果；不误阻断同一联合组的有效定义；不能变为语义接受或Lean反证。
- 当前状态：仅静态实现，association-scoped.json已准备；未执行带覆盖层的新图计划、测试或审计。刚结束的匹配计划仍使用先前冻结代码。
- 前置阻塞：需在新计划导入覆盖层并检查实际记录；当前不能宣称自动阻断已执行。

后续匹配结果补记：session78615已exit2；4次Terra均CANDIDATE_RECORDED，含两次Gottesman提示1000258与1042324字符。目标图683节点/269组，37条未审阅判断、2条连接拒绝，无本轮派发失败；accepted_support_edges=0。未执行独立测试/Lean。

V03-105实际结果补记：reviewed-boundary计划exit2、0模型调用；最终assembly可见对指定单调性claim和请求的SOURCE_REVIEW_OBJECTION，未覆盖同组faithfulness声明。未执行独立测试/审计/Lean；历史反例与新阻断不等于本轮内核反证。

### V03-106 / 已有DOI PDF来源与查询请求关联（2026-09-22）

- 对象：doi-source-bindings-20260922/lovasz1972-characterization.json。
- 准备条件：当前冻结查询图、参考文献精确DOI、既有PDF阅读产物。
- 操作情景：按DOI关联8个选中请求，保留历史区域来源与无权到实权的桥梁缺口。
- 预期结果：来源可用性不等于语义支持；不改变PDF定位类型、不伪造arXiv身份、不终结Berge1961前沿。
- 当前状态：已生成关联产物；没有重新抽取、渲染、模型调用或独立测试。尚未进入控制器支持图，accepted_support_edges=0。
- 前置阻塞：非arXiv来源接纳、PDF区域跨论文支持接口与PDF证明上下文尚未接通。

### V03-107 / DOI来源可用性进入控制器（2026-09-22）

- 对象：source_availability.py、research import/publish/pending、audit_research重建。
- 准备条件：冻结DOISourceAvailabilityBinding和现有PDF summary/assembly/document；精确DOI请求。
- 操作情景：已有DOI来源、请求未出现后续才加入、来源/请求身份不一致、两份冲突绑定、历史计划无新字段。
- 预期结果：加入assembly.source_availability和请求节点PDF_SUPPORT_JOIN_REQUIRED阻断；未找到arXiv时明确报告PDF来源已有但支持连接未完成；不增支持边、不伪造arXiv、不删除语义缺口；冲突拒绝，旧计划不变。
- 当前状态：仅静态实现，新导入清单recursive-doi-available-20260922.json已准备，未运行控制器或独立测试；字节绑定仅涵盖已引用JSON，未因此宣称PDF资产被重新审计。
- 前置阻塞：PDF区域支持连接、非arXiv接纳预算及PDF证明上下文仍未实现，本功能仅来源可用性索引。

### V03-108 / Lovasz八个请求的桥梁缺口记录（2026-09-22）

- 对象：doi-source-bindings-20260922/lovasz1972-request-gaps.json。
- 准备条件：当前声明文本、既有PDF候选及历史target-alignment。
- 操作情景：区分权重对偶、算法复杂度、theta sandwich、antiblocker、量子RoM与饱和性需求。
- 预期结果：来源结构定理不被当成每个完整目标结论；保留零权/实权延伸及克隆与团复制区别；Berge前沿开放。
- 当前状态：根据已保留声明整理8条缺口记录，未重新阅读PDF或调用模型/Lean，记录不是形式证明。DOI可用性实际计划session50610仍运行，最终状态另记。
- 前置阻塞：证明桥梁、PDF支持组接口及更早来源仍待完成。

V03-107/108实际结果补记：session50610已exit2、0模型调用，8个来源可用性条目及相应PDF支持连接待完成问题已写入；图683节点/269组，已接受支持边0。未执行独立测试/审计/Lean。

### V03-109 / 冻结图像输入传输层（2026-09-22）

- 对象：model.call_model image_references 与Task图像字段。
- 准备条件：冻结PNG/JPEG引用；本地CLI exec --help明确列出--image。
- 操作情景：按顺序附加图像、原文件哈希变化、超过32图或32MiB、非支持文件头、调用失败；历史纯文本调用。
- 预期结果：预留额度前拒绝无效输入；调用目录保存图像快照；Task/receipt含有序图像引用与复合输入哈希，文本计量与图像计量分开；纯文本逻辑不变。
- 当前状态：读本地CLI帮助并静态实现，未派发多模态模型或执行测试；仅文件头限制不等于图像解码验证。PDF proof worker仍保留明确未实现边界。
- 前置阻塞：页区域上下文选择、图像资产审计与复合输入重建尚需接通；不能据传输代码宣称PDF自动形式化已可用。

### V03-110 / 多模态输入审计重建（2026-09-22）

- 对象：image_evidence.py、audit_research和audit_proof_walk调用证据路径。
- 准备条件：图像Task/receipt、按序调用目录快照；后续授权执行独立审计。
- 操作情景：顺序改变、图像字节变化、快照越出调用目录、原始与快照hash不一致、预算超限、无图却含多模态摘要。
- 预期结果：重建文本摘要与有序图像摘要的复合哈希，核对任务/回执及32图/32MiB界限；原始图片引用只比对记录hash，快照核对实际字节；不宣称模型确实读懂图像或PDF渲染对应已验证。
- 当前状态：仅静态实现并接入两条审计路径，未执行审计、模型或Lean。PDF页区域上下文仍未接入。
- 前置阻塞：尚无真实多模态调用产物；页区域/页序号与图像快照之间的语义对应需后续上下文适配。

### V03-111 / PDF页区域证明上下文准备（2026-09-22）

- 对象：pdf_proof_context.py；lovasz-pdf-proof-context-20260922/context.json。
- 准备条件：既有FrozenPDFRegionDocument和PDF_PAGE_REGION声明；至多32页、图像总量32MiB。
- 操作情景：完整按序页面、页区域对应、文件变更、缺页/页序错误、非法坐标、过大文档；OCR仅附为非权威文本。
- 预期结果：生成完整页序列和精确资产引用，不截断页面、不把图片或OCR视为已验证数学；无模型或Lean调用。
- 当前状态：实际为Lovasz核心刻画定理生成4页上下文产物；未执行独立测试/审计、模型或Lean。边界失败场景待执行，不能把此次产物生成当作测试通过。
- 前置阻塞：proof_walk的PDF来源清单与后端调用尚未接入适配器，旧明确拒绝边界仍保留。

### V03-112 / PDF来源绑定、证明调用与审计接线（2026-09-22）

- 对象：pdf_proof_context、proof_walk、proof_backend、audit_proof_walk。
- 准备条件：内容寻址的PDF运行summary及assembly/document、真实证明请求和固定Lean环境；执行需用户后续授权。
- 操作情景：正确PDF声明；错配paper ID、声明文本/条件/区域、重复节点ID、混合来源条目；图片顺序变化；原有TeX调用回归。
- 预期结果：仅同一来源记录中的声明能构造完整页图上下文，模型调用收到有序图片快照，审计重建上下文并核对图片输入；不自动接受来源语义、支持边或数学证明。
- 当前状态：四个模块已静态接线，未执行模型、审计、测试或Lean；V03-111的代码接线阻塞已解除，历史状态记录保留。
- 前置阻塞：实际PDF证明请求仍需真实根节点库绑定与依赖处理；递归TeX控制器尚未自动接入PDF支持组。

### V03-113 / PDF依赖缺口导入与研究审计（2026-09-22）

- 对象：source_availability.apply_dependency_gaps、research、audit_research及recursive-doi-gaps-20260922配置。
- 准备条件：保留的来源可用性绑定、八条Lovasz缺口审阅和对应候选声明；执行需后续授权。
- 操作情景：导入正确缺口、声明变化、来源绑定错配、重复请求、冲突审阅、尚未加入图的请求以及后续加入图；检查重复发布保持相同记录。
- 预期结果：冻结审阅引用，逐请求保留具体未完成义务并生成SOURCE_BRIDGE_REQUIRED事项；错配拒绝；尚未出现的请求延期绑定；不创建数学支持边或接受声明。审计重建相同记录。
- 当前状态：静态实现和差异阅读完成，新配置已写入但未执行；未运行测试、模型、审计或Lean。
- 前置阻塞：缺口内容仍是已有归因审阅；实际源定理对齐、桥接证明和PDF支持连接尚未完成。

### V03-114 / 非负实数权重的完美图精确对偶（2026-09-22）

- 对象：lean/PerfectGraphWeightedDuality.lean中最优覆盖存在性及fractionalCliqueCoverValue等式。
- 准备条件：PerfectGraphWeightedApproximation、PerfectGraphIntegerCover及其传递依赖在指定Lean/mathlib环境中可用；后续明确授权Lean执行。
- 操作情景：编译完整参数化定理、记录实际声明类型与公理/前提；包含空顶点类型、全零权重和任意非负实数权重的声明域。
- 预期结果：从已有覆盖最小值存在、任意正误差近似和弱对偶推导精确最优覆盖及原始infimum定义等式；不额外假设加权对偶或复制证书，不推导算法复杂度或theta等式。
- 当前状态：新增Lean候选代码并静态阅读；未编译、未运行测试或审计。整数复制attempt-02历史回执确为SUCCEEDED（与attempt-01失败区别保留），不能据此认定本模块或当前共同环境已通过。
- 前置阻塞：整数覆盖与实数近似代码的当前环境可编译性尚未核定；源定理语义对齐、theta/多面体/量子桥接仍独立待完成。

### V03-115 / RoM图对偶与完美图覆盖预算连接（2026-09-22）

- 对象：lean/ReducedRoMPerfectCover.lean的预算等价、目标值集合相等和实际RoM为最大值三个定理。
- 准备条件：ReducedRoMGraphDual与PerfectGraphWeightedDuality及传递依赖在同一指定环境中可用；后续明确授权执行Lean。
- 操作情景：编译参数化证明并核对声明前提；预算b可为任意实数，权重非负；检查归一化项|μ|没有丢失、双向转换保留相同目标值。
- 预期结果：实际图对偶约束等价于真实分数团覆盖存在和预算约束；以无活跃依赖及完美性作为仅有的新增数学假设，不假设闭式RoM或对偶证书。
- 当前状态：Lean候选代码已写入，仅静态阅读，未编译或执行其他验证；不增加已验证声明数。
- 前置阻塞：V03-114及其依赖待验证，团覆盖目标消元、闭式最大团权、平方根界和达到性仍待完成。

### V03-116 / RoM完美图闭式与共享模块导入（2026-09-22）

- 对象：ReducedRoMPerfectClosedForm.lean；GraphDualCoverFoundation.lean由复制声明改为模块导入。
- 准备条件：GraphDualBounds及PerfectGraphWeightedDuality依赖在同一固定环境中可用，后续明确授权Lean执行。
- 操作情景：共同导入两条证明链，检查无重复声明；编译reducedRoM_eq_max_one_clique_weight并核对类型、公理和传递依赖；复查受模块来源变化影响的GraphDualBounds及相关审计配置。
- 预期结果：在无活跃依赖及完美性前提下，由原RoM上下界、已证明的补图完美性和实数加权对偶推出原闭式；不额外假设补图完美性或加权对偶。已有源声明仅导入一次。
- 当前状态：闭式Lean候选与模块重构已写入，未编译、未执行测试或审计；原历史运行快照和证据保留，不复用为新模块通过结论。
- 前置阻塞：V03-114及当前依赖可编译性待核定；新共同环境中的审计声明归属需要重新记录；平方根界、达到性及论文源语义对齐仍未完成。

### V03-117 / 实际Pauli窗口的RoM平方根上界连接（2026-09-22）

- 对象：ReducedRoMPerfectSqrtBound.lean及ConcretePhyslibBridge共同导入。
- 准备条件：V03-114/116和ConcretePhyslibBridge在同一Lean/mathlib/Physlib环境中可用；后续明确授权Lean执行。
- 操作情景：核对两个图定义相等、expectationProjection与expectationCoordinate定义相容；编译最大团期望界、非空窗口的1≤sqrt(cliqueNum)、最终RoM上界并记录传递公理。
- 预期结果：只保留原无活跃依赖和完美性前提；不把矩阵反对易、迹期望对应或最终平方根界作为额外假设。窗口非空直接使用MeasurementWindow字段。
- 当前状态：候选代码与静态接口阅读完成；未编译、未运行测试或审计；未新增已验证数学结论。
- 前置阻塞：共同环境模块兼容及传递依赖尚待验证；正特征空间状态的达到性与存在性仍未完成。

### V03-118 / 正特征空间支撑状态的达到性条件证明（2026-09-22）

- 对象：ReducedRoMPerfectAttainment.lean的归一化算子、取迹期望和、最大团支撑状态达到性。
- 准备条件：V03-117及传递依赖在同一环境中可用；后续明确授权Lean执行。
- 操作情景：编译取迹与实数标量化简；核对最大团非空来自原窗口条件；检查终结论仅使用实际算子支撑方程而非RoM值假设。
- 预期结果：A_Qρ=ρ推出期望和为sqrt(|Q|)，进而对最大团支撑状态得RoM=sqrt(cliqueNum)；保留原无活跃依赖与完美性条件，不声称存在性已证。
- 当前状态：Lean候选已写入，未编译或执行测试/审计；具体trace/smul接口及所有传递依赖待验证。
- 前置阻塞：需要另外构造满足支撑方程的密度矩阵，证明正半定、迹1和支撑；还需源语义对齐及共同环境验证。

### V03-119 / 归一化团算子的平方恒等式（2026-09-22）

- 对象：NormalizedCliqueInvolution.lean。
- 准备条件：ConcretePhyslibBridge、冻结AnticommutingWitness和V03-118依赖共同可用；执行需后续明确授权。
- 操作情景：编译非空团下Pauli和平方及归一化平方；核对反对易和单算子平方由具体窗口推出，非空条件仅用于除数非零。
- 预期结果：原始和平方等于|Q|倍单位矩阵，A_Q平方等于单位矩阵；不另加反对易证书，不宣称支撑密度矩阵已构造。
- 当前状态：Lean候选已写入，未编译、未执行测试或审计。
- 前置阻塞：归一化算子Hermitian及无迹性质、正半定迹1支撑状态构造仍待完成；所有共同环境依赖待核定。

### V03-120 / 归一化团算子的Hermitian与无迹性质（2026-09-22）

- 对象：NormalizedCliqueInvolution.lean新增三个引理。
- 准备条件：PauliTrace、F2Support和具体窗口Hermitian桥接可用；执行需后续明确授权。
- 操作情景：从nonidentitySupport推出z/x支撑不全零；核对负Pauli代表也无迹；编译矩阵求和、实数标量和共轭转置接口。
- 预期结果：每个窗口Pauli无迹，归一化算子无迹且Hermitian，无需假设额外谱证书。空团仍适用这两个性质，非空仅用于平方归一化。
- 当前状态：候选引理已写入并静态阅读，未运行Lean、测试或审计。
- 前置阻塞：仍需显式构造(I+A_Q)/维数并证明正半定、迹1、支撑，所有传递依赖可编译性待核定。

### V03-121 / 显式正特征空间密度矩阵（2026-09-22）

- 对象：PositiveCliqueState.lean，矩阵(I+A_Q)/2^n、DensityMatrix构造及达到性连接。
- 准备条件：V03-118至120及传递证明在同一固定环境可用；执行需后续明确授权。
- 操作情景：编译Gram正半定与复标量非负性、迹归一化、支撑等式、DensityMatrix构造及最大团达到性；核对不存在支撑状态存在性假设。
- 预期结果：显式构造状态，从窗口和非空团条件证明合法性，再在原无活跃依赖/完美性及最大团条件下达到上界；不将候选写入已验证库记录。
- 当前状态：代码及静态推理完成，未编译、测试或审计。尤其矩阵标量、trace和复数偏序接口尚待实际验证。
- 前置阻塞：整个新证明链与共同环境未验证；最大团存在性的终端封装及论文源语义对齐仍需完成。

### V03-122 / 最大团存在性与查询分支终端候选（2026-09-22）

- 对象：PositiveCliqueState.lean的exists_reducedRoM_sqrt_attainer和perfect_window_closed_form_bound_and_attainment。
- 准备条件：V03-114至121及原有传递依赖在固定共同环境可用；后续明确授权Lean执行。
- 操作情景：检查exists_isNClique_cliqueNum所得Finset及card_eq接口，窗口非空排除空最大团；编译终端定理并审计量词、前提和公理。
- 预期结果：由原窗口条件及无活跃依赖/完美性推出所有密度矩阵的闭式与上界，并构造一个达到上界的状态，不将最大团或支撑状态存在性作为前提。任意支撑状态的更强条件结论保留在V03-118模块。
- 当前状态：候选封装已写入，未编译或执行测试/审计；不增加已验证数学声明数。
- 前置阻塞：全部新证明与共同环境仍未验证；论文声明语义绑定、外部来源溯源及其他查询声明尚未闭合。

### V03-123 / 查询分支候选对齐档案（2026-09-22）

- 对象：runs/query-perfect-branch-candidate-binding-20260922/candidate-alignment.json及七个Lean快照。
- 准备条件：两处原候选声明及来源span、七个候选模块；实际审计需后续授权。
- 操作情景：核对引用和快照内容、逐条原文与量词/结构域相容性，尤其非空、无标量Pauli、相位去重、支撑方程及reducedRoM定义。
- 预期结果：四类结论分别绑定到明确声明；未编译、未语义接受及未闭合来源链阻止生成DeclarationBinding或ChainCertificate。
- 当前状态：仅生成候选档案和快照，未执行验证器、Lean或模型，不作为来源对齐通过证据。
- 前置阻塞：完整核对原定义、模型语义和外部来源，以及共同环境内核证据均待完成。

### V03-124 / 空测量域边界与来源前提（2026-09-22）

- 对象：query-perfect-branch-domain-review-20260922/domain-review.json与MeasurementWindow.nonempty。
- 准备条件：完整原文约定核对；如形式化反例，需支持空坐标的独立有限原子模型，不可强造MeasurementWindow。
- 操作情景：来源引用字节审计；单点零维投影、归一化l1值1与空图团数0；核对终端声明显式非空域。
- 预期结果：区分原文明确条件、代表选择约定和非空域缺口；没有全文依据时不得称无条件对齐，也不得把静态异议当作内核反例。
- 当前状态：静态原文阅读和边界推理已保留，未执行测试、Lean或审计。
- 前置阻塞：全文是否另有非空约定尚待核定；当前MeasurementWindow不能表示空域，不能直接实例化用于反例。

- 后续静态阅读更正：domain-review-addendum.json保留附录763行非空条件、529行平方为I和769行支撑方程。全文非空依据已找到；待核定的是陈述与证明域的明确绑定，不再记为全文依据缺失。没有执行测试或内核反例。

### V03-125 / 来源前提与Lean隐含结构域比较契约（2026-09-22）

- 对象：research.schema.json的SourcePremiseComparison与DeclarationBinding.premise_comparison。
- 准备条件：定位到的原文SourceSpan和具体Lean参数/结构字段；后续授权运行schema验证器。
- 操作情景：定理前提、证明使用前提、全局约定及未找到前提；定位角色缺span、未找到角色却带span；旧binding没有新字段。
- 预期结果：定位角色至少一处span，未定位角色无伪造span；独立记录候选等价/加强/减弱/未决；旧字段缺失表示未记录，不等于已对齐。
- 当前状态：可选契约与规范已更新，未运行验证器或测试；不是已实现的语义接受门禁。
- 前置阻塞：后端自动产出、逐项语义判定及组合门禁还需接入；当前候选档案尚未转成正式DeclarationBinding。

### V03-126 / 证明模型前提报告输出（2026-09-22）

- 对象：proof_backend.PROOF_SCHEMA、模型提示、lamport.json保留与audit_proof_walk重建。
- 准备条件：新证明调用与冻结响应schema；实际调用/审计需后续授权。
- 操作情景：显式及结构内前提、证明使用条件、未定位条件；未定位却描述出处、已定位却空描述；旧响应无报告。
- 预期结果：新响应必须报告premise_report，来源描述与定位角色一致；原始报告保留在Lamport产物；旧记录不新增伪造报告。描述仍是模型归因，不是已核实SourceSpan，也不直接生成正式premise_comparison。
- 当前状态：模型输出、保留和审计代码已接入，未运行模型、测试、Lean或审计。
- 前置阻塞：报告完整性、源字节绑定、语义关系判定及正式声明组合门禁仍待实现。

### V03-127 / 前提精确引文绑定（2026-09-22）

- 对象：premise_evidence.py、proof_backend及audit_proof_walk。
- 准备条件：新模型报告含source_path/source_quote，冻结全文上下文；执行需后续授权。
- 操作情景：唯一精确TeX引文、缺失/重复引文、UTF-8多字节、错误路径、未定位却附引文、PDF误作文字引文、证据产物被改动。
- 预期结果：文字匹配在原始字节上唯一定位并保留摘要，报告不能冒充语义接受；PDF只保留描述未绑定状态；审计重建证据。旧无报告记录不自动补造。
- 当前状态：代码已接入，未运行模型、测试、审计或Lean。
- 前置阻塞：前提完整性、PDF区域定位及语义接受门禁仍待实现；新路径实际调用尚未执行。

### V03-128 / 空前提报告与冻结来源摘要审计（2026-09-22）

- 对象：audit_proof_walk保存的响应schema、premise_evidence绑定前检查。
- 准备条件：冻结响应schema规定source_quote字段的新调用，含空报告及非空报告；后续授权执行审计。
- 操作情景：空报告删除premise_evidence引用、伪改全文sha256、未定位却有来源描述、旧版无引文协议报告。
- 预期结果：证据要求取自冻结schema，即使空报告也要求产物；核对全文实际摘要，不凭报告条目推断协议；旧调用按原协议处理。
- 当前状态：静态修复完成，未执行测试或审计。失败回调仍仅保留部分产物说明，不得称其完整审计通过。
- 前置阻塞：新协议实际调用及全部失败路径证据仍待后续授权验证。

### V03-129 / 实际状态值域上的见证容量（2026-09-22）

- 对象：ReducedRoMWitnessCapacity.lean。
- 准备条件：PositiveCliqueState及传递证明在共同环境可用；后续明确授权Lean执行。
- 操作情景：编译实际DensityMatrix的RoM值域、最大元证明及sSup等式；核对Set.range见证方向和sup定理接口。
- 预期结果：在原分支前提下容量等于sqrt(cliqueNum)，由真实达到状态保证最大元；不把容量定义为图函数，不声称2n+1极值结论已证。
- 当前状态：候选代码已写入，未执行Lean、测试或审计。
- 前置阻塞：所有新依赖尚未验证；反对易集合2n+1维数界和极值构造仍需完成。

### V03-130 / 二元团Gram映射的核注入（2026-09-22）

- 对象：BinaryCliqueGram.lean的坐标和、I+J映射与kernelSum_injective。
- 准备条件：固定mathlib中的ZMod、LinearMap.ker与有限求和接口；后续明确授权执行Lean。
- 操作情景：编译任意有限指标类型的核坐标恒等式和标量和注入，包含空指标类型。
- 预期结果：核中向量由坐标和唯一确定，不假设核维数结论；仍需通过秩零化度和Pauli辛Gram分解得到2n+1界。
- 当前状态：候选代码及原文论证阅读完成，未编译或执行测试/审计。
- 前置阻塞：核维数界、矩阵分解与实际Pauli窗口关联尚未完成。

### V03-131 / Gram分解的维数加一界（2026-09-22）

- 对象：BinaryCliqueGram.factor_with_sum_injective及card_le_factor_finrank_add_one。
- 准备条件：固定mathlib的LinearMap.prod和有限维注入定理接口；后续明确授权Lean执行。
- 操作情景：任意有限指标、有限维F₂空间E和真实分解g∘f=I+J；编译增广映射注入及card≤finrank(E)+1。
- 预期结果：从分解构造注入，不假设目标维数界；空指标也适用。具体Pauli的2n维因子还需构造，不能将本通用引理视为已完成2n+1界。
- 当前状态：候选代码已写入，未编译或执行测试/审计。
- 前置阻塞：实际窗口的辛配对分解与F₂支撑维数连接仍待完成。

### V03-132 / 实际Pauli支撑线性因子（2026-09-22）

- 对象：PauliCliqueGramFactor.lean的supportCombination、pairingCoordinates和逐坐标求和。
- 准备条件：PauliF2Support辛配对及ReducedRoMGraphDual图定义，固定共同环境；后续授权Lean执行。
- 操作情景：编译团子类型上的线性组合、配对与复合公式，核对对角为0及不同团顶点配对非零。
- 预期结果：因子直接由W.observable的真实F₂支撑构造，不附加Gram证书假设；仍需非零值为1、复合等于I+J及支撑维数2n。
- 当前状态：候选实现已写入，未编译或执行测试/审计。
- 前置阻塞：最终复合等式、维数接口及2n+1图界尚未完成。

### V03-133 / 实际反对易团的2n+1上界（2026-09-22）

- 对象：PauliCliqueGramFactor的非零配对为1、factors_equal_gram及clique_card_le_two_mul_add_one。
- 准备条件：BinaryCliqueGram与F2Coordinates在固定环境可用；后续明确授权Lean执行。
- 操作情景：编译F₂有限分类、删去对角的求和恒等式、坐标等价组合与有限维数化简，包含空团。
- 预期结果：从实际窗口团假设推出Q.card≤2*n+1，不假设Gram分解或支撑维数证书；不等同于最大团存在构造或极值可达证明。
- 当前状态：候选已写入，未编译、测试或审计；具体simp/线性等价接口待验证。
- 前置阻塞：共同环境全部依赖待核定；图团数及容量通用上界连接、JW极值构造仍待完成。

### V03-134 / n量子比特RoM与容量上限（2026-09-22）

- 对象：ReducedRoMDimensionCeiling.lean四个定理。
- 准备条件：V03-129与133及共同环境全部传递依赖；后续明确授权Lean执行。
- 操作情景：最大团存在性接团数界、Nat/Real转换、sqrt单调性和平方还原等价；审计保留无活跃依赖/完美性原条件。
- 预期结果：团数≤2n+1，RoM和容量≤sqrt(2n+1)，容量等号当且仅当团数为2n+1；不把JW窗口存在作为已证。
- 当前状态：候选代码已写入，未编译、测试或审计。
- 前置阻塞：全部候选链需实际验证；JW窗口构造、源码语义与外部依赖溯源未闭合。

### V03-135 / 两两反对易窗口无活跃依赖（2026-09-22）

- 对象：AnticommutingWindowDependencies.lean。
- 准备条件：真实IsActiveDependency定义和窗口nonidentitySupport字段；后续授权Lean执行。
- 操作情景：编译从两两不交换到任意活跃依赖矛盾；检查非空交换子集必为单点，而单点不可能标量。
- 预期结果：不改变NoActiveDependencies定义，也不假设依赖不存在；为JW窗口提供可复用条件引理，不宣称已构造JW窗口。
- 当前状态：候选代码已写入，未编译或执行测试/审计。
- 前置阻塞：显式JW Pauli族的两两反对易、合法窗口字段及2n+1大小仍需构造。

### V03-136 / 显式JW支撑与Hermitian Pauli族（2026-09-22）

- 对象：JordanWignerPauliFamily.lean的Option(Fin n×Bool)指标、前缀坐标、Pauli代表与平方恒等式。
- 准备条件：F2Coordinates和HermitianPauliBasis在共同环境可用；后续授权Lean执行。
- 操作情景：编译2n+1指标数、坐标逆映射与支撑一致性；分别检查X/Y前缀与全局Z奇偶算子；区分n=0与n>0。
- 预期结果：显式族而非存在假设，所有代表平方为I；相位选择允许符号差，不能直接声称与原文有序乘积相位完全一致。
- 当前状态：候选已写入，未编译或执行测试/审计。
- 前置阻塞：非零支撑、支撑单射、两两反对易、Fin(2n+1)重编号和MeasurementWindow封装尚待完成。

### V03-137 / JW非零支撑（2026-09-22）

- 对象：JordanWignerPauliFamily的coordinates_ne_zero、support_ne_zero、observable_nonidentitySupport。
- 准备条件：正量子比特数n和既有坐标等价；后续授权Lean执行。
- 操作情景：全局奇偶算子取第0个Z坐标，X/Y字符串取自身位置X坐标；核对n>0仅为合法非零奇偶支撑所需。
- 预期结果：每个实际Pauli代表支撑非零，不仅排除正单位算子，也排除其所有相位类；不虚报去重或反对易已证。
- 当前状态：候选代码已写入，未编译或执行测试/审计。
- 前置阻塞：支撑单射、反对易及窗口封装尚待完成，全部候选依赖待验证。

### V03-138 / JW相位类去重（2026-09-22）

- 对象：JordanWignerPauliFamily的coordinates_injective、support_injective和observable_distinctPhaseClass。
- 准备条件：既有坐标等价及F₂判等接口；后续授权Lean执行。
- 操作情景：奇偶算子与字符串由X坐标区分；不同位置由单位X坐标区分；同位置X/Y由Z坐标区分；n=0单指标。
- 预期结果：真实Pauli支撑单射，不只比较指标名字或矩阵变量；排除相位重复。
- 当前状态：候选已写入，未编译或执行测试/审计。
- 前置阻塞：两两反对易、编号与合法窗口封装及极值连接尚待完成。

### V03-139 / 显式JW测量窗口封装（2026-09-22）

- 对象：JordanWignerWindow.lean的indexEquiv、window及观测量还原。
- 准备条件：JW族V03-136至138与MeasurementProjection在固定环境可用；后续授权Lean执行。
- 操作情景：编译有限编号等价及五个窗口字段、逆编号还原、所有族元素均被覆盖；n>0域。
- 预期结果：得到MeasurementWindow n (2*n+1)，全部字段由构造引理提供，不假设反对易、完美性或无活跃依赖。编号不冒充论文gamma顺序。
- 当前状态：候选代码已写入，未编译或执行测试/审计。
- 前置阻塞：反对易、图完美性和容量极值连接仍待完成；精确相位及来源对齐未审定。

### V03-140 / JW显式坐标配对（2026-09-22）

- 对象：JordanWignerCoordinatePairing.lean。
- 准备条件：显式JW坐标和F₂求和；后续授权Lean执行。
- 操作情景：奇偶与X/Y串、不同位置、同位置不同Bool；编译配对求和化简及非对角配对为1。
- 预期结果：坐标公式本身给出配对1；不把它直接视为真实bit-vector辛形式，必须另外连接dotZ₂。
- 当前状态：候选代码已写入，未编译或执行测试/审计。
- 前置阻塞：F2Bits.dot与坐标求和恒等式、实际Pauli反对易及后续图性质仍待完成。

### V03-141 / bit-vector点积与坐标和连接（2026-09-22）

- 对象：F2CoordinateDot.lean。
- 准备条件：原BitVec.cons_dotZ₂_cons、lsbs/msb坐标接口及F2Coordinates；后续授权Lean执行。
- 操作情景：编译Bool与乘法桥接、cons点积递推和n归纳坐标求和；特别核对末位与castSucc位序。
- 预期结果：原dotZ₂定义与坐标求和等价，不替换原辛形式；不跳过低位/高位约定。
- 当前状态：候选已写入，未编译、测试或审计，lsbs/getLsb化简接口尚待验证。
- 前置阻塞：实际Pauli反对易应用与JW后续图/容量连接仍待完成。

### V03-142 / JW实际Pauli反对易与无活跃依赖（2026-09-22）

- 对象：JordanWignerAnticommutation.lean。
- 准备条件：V03-135至141及原Pauli辛配对定义在共同环境可用；后续授权Lean执行。
- 操作情景：核对坐标等价的Z/X顺序，编译真实辛形式等于坐标配对、Boolean不交换及带相位Pauli反对易，再传输到重编号窗口。
- 预期结果：实际窗口无活跃依赖由反对易和非单位支撑推出；不假设这些属性或换用替代图。
- 当前状态：候选已写入，未编译、测试或审计。
- 前置阻塞：图为完全图、完美性与容量达到通用上限尚待连接；整个新链需验证。

### V03-143 / 显式JW容量极值候选（2026-09-22）

- 对象：JordanWignerCapacity.lean。
- 准备条件：JW实际反对易、通用容量和达到性链在共同环境可用；后续授权Lean执行。
- 操作情景：编译实际图等于完全图、诱导完全图完美性、团数2n+1、容量等式及密度矩阵达到状态；核对n>0域和所有传递公理。
- 预期结果：显式窗口达到sqrt(2n+1)，不假设其完美性或容量；不声称有序乘积相位等其他JW声明已证。
- 当前状态：候选已写入，未编译、测试或审计；完全图simp和Nat/Real接口待核定。
- 前置阻塞：整条候选链的实际Lean验证、源语义绑定和全论文其他声明/来源链仍未完成。
### V03-172 / 容量分支外部来源请求清单（2026-09-22）

- 对象：profiles/query-capacity-origin-frontier.json。
- 准备条件：后续授权校验；保留的 research assembly 和三项文献来源证据。
- 操作情景：核对三项 DOI、共十个已有请求及各自下游节点；新增来源后逐条比较数学域、相位、最大/极大含义，再递归其实际依赖。
- 预期结果：本地候选重证明不自动关闭来源请求；1935 年日期不自动代表最早出处；缺可用性仅描述指定组装图，不推断全仓库或网络无来源。
- 当前状态：由已保存请求静态整理，未新增模型调用、抽取或验证；该文件尚不是宿主可执行计划。
- 前置阻塞：三项原文与声明连接尚未绑定至当前组装图，递归引用及源语义审阅未完成。

### V03-171 / JW 全窗口唯一非活跃依赖特化（2026-09-22）

- 对象：JordanWignerCapacity.window_unique_inactive_dependency 及审计配置。
- 准备条件：后续授权 Lean 编译；JW 实际两两不交换与通用最大团依赖候选链可用。
- 操作情景：以 Finset.univ 为团，核对基数 2n+1，把通用“团内唯一”特化为整个 JW 窗口内唯一。
- 预期结果：全集是原定义下的非活跃依赖，任何窗口依赖等于全集；不新增依赖存在或完美图证书假设。
- 当前状态：新增候选及对应审计目标，未编译或测试。
- 前置阻塞：经典 JW 字符串的代表相位与源语义仍待对齐，抽取节点的其他条款和引用出处不能自动视为完成。

### V03-170 / 唯一依赖源节点与审计目标关联（2026-09-22）

- 对象：query-perfect-branch-audit.json 与 UNIVERSAL_CEILING_ALIGNMENT.md。
- 准备条件：后续授权校验/Lean；冻结 assembly、原文和三个新增审计目标。
- 操作情景：核对节点 12649f3695466099141288ec 的 [58175,58836) 区间和哈希，比较乘积标量性、最小依赖唯一性、非活跃性及 n>0 域。
- 预期结果：三个目标分别保留覆盖范围；不得由通用团结论自动宣称 JW 聚合节点或所引文献已完成。
- 当前状态：静态读取既有抽取节点并更新配置，未重跑抽取或校验。
- 前置阻塞：真实内核和源语义验证、JW 特化、精确奇偶秩与引用来源链仍未完成。

### V03-169 / 最大团唯一依赖的非活跃性（2026-09-22）

- 对象：PauliCliqueGramFactor 的 dependency_unique、dependency_not_active 和组合命题。
- 准备条件：后续授权 Lean 编译；最大团最小依赖候选可用；n>0。
- 操作情景：由子集标量分类排除其他非空依赖；假设全团活跃，用交换/不交换矛盾推出团至多单点，与 2n+1 大小矛盾。
- 预期结果：在原 IsPauliDependency/IsActiveDependency 定义下得到唯一非活跃依赖；明确 n>0 域，不推广为整个窗口仅有这一依赖。
- 当前状态：候选已写，未编译或测试。
- 前置阻塞：需加入声明审计目标、对应原文节点并验证整个候选链；全部窗口的其他依赖不在本命题范围。

### V03-168 / 最大反对易团的依赖最小性（2026-09-22）

- 对象：PauliCliqueGramFactor.maximum_clique_scalar_subset 与 maximum_clique_isPauliDependency。
- 准备条件：后续授权 Lean 编译；最大团核描述与标量乘积候选可用。
- 操作情景：把 U⊆Q 的成员指示函数代入真实支撑组合，证明标量子乘积只能对应空集或全集；据此排除非空真子集，满足原 IsPauliDependency。
- 预期结果：最小性来自实际核关系，不作为额外假设；不把一般标量子乘积自动认定为依赖。
- 当前状态：候选已写，未编译或测试。
- 前置阻塞：Finset 子集求和与真子集接口待核定，非活跃性及整链内核验证尚待完成。

### V03-167 / 最大团支撑关系连接原始 Pauli 乘积（2026-09-22）

- 对象：PauliCliqueGramFactor.maximum_clique_product_scalar 与 any_order 版本。
- 准备条件：后续授权 Lean 编译；最大团支撑和候选及原 NoActiveDependencies 的乘积/支撑接口可用。
- 操作情景：将子类型求和转为 Finset 求和，再经 scalar_subsetProduct_iff_zero_sum 得到原始乘积标量性；对任意无重复且恰好枚举 Q 的顺序传输。
- 预期结果：证明与单位算符成比例，不人为固定相位；不同顺序可有不同标量相位；不据标量性单独声称最小性或非活跃性。
- 当前状态：新增候选，未编译或测试。
- 前置阻塞：IsPauliDependency 的真子集最小性及该依赖非活跃性仍待连接，所有新增候选须共同环境验证。

### V03-166 / 最大 Pauli 团的唯一二元依赖（2026-09-22）

- 对象：PauliCliqueGramFactor.maximum_clique_support_kernel 与 maximum_clique_support_sum_zero。
- 准备条件：后续授权 Lean 编译；Gram 通用核候选和实际 Pauli 支撑坐标等价可用。
- 操作情景：对任意大小 2n+1 的真实窗口团，代入两组 n 维坐标，证明支撑组合核仅零/全一，随后导出全体支撑和为零。
- 预期结果：维数和分解来自实际 Pauli 定义，不新增证书假设；结论是相位无关的二元依赖，尚不包含指定顺序或相位的算符乘积。
- 当前状态：候选已写，未编译或测试。
- 前置阻塞：具体 finrank 和子类型求和接口待核定；须继续连接 subsetProduct 与最小/非活跃依赖定义及源声明审阅。

### V03-165 / 超维数输入的非零依赖存在性（2026-09-22）

- 对象：BinaryCliqueGram 的 exists_nonzero_kernel_of_finrank_lt、factor_one_eq_zero_of_finrank_lt 和双向核描述。
- 准备条件：后续授权 Lean 编译；前轮 Gram 核限制候选可用。
- 操作情景：从输入坐标数大于输出空间 finrank 推出非零核；结合 Gram 分解推出全一向量属于核及核的双向刻画。
- 预期结果：不把存在性作为额外假设；仅在显式维数不等式成立时推出全一依赖；尚不冒充具体 Pauli 乘积关系。
- 当前状态：候选已写，未编译或测试。
- 前置阻塞：需将具体最大团的支撑组合映射及 2n 维坐标空间代入，随后连接 Pauli 标量乘积。

### V03-164 / 二元 Gram 核的全支撑限制（2026-09-22）

- 对象：BinaryCliqueGram.eq_zero_or_one_of_gram_eq_zero 与 factor_kernel_eq_zero_or_one。
- 准备条件：后续授权 Lean 编译；原坐标和及核坐标候选可用。
- 操作情景：验证 Gram 核中向量只有零或全一两种可能，并沿实际线性分解传回首因子的核；保留偶数/奇数和空指标集边界。
- 预期结果：仅证明核包含关系，不误称全一必在核，也不据此断言非零依赖已存在。
- 当前状态：新增未编译候选；未测试或 Lean 执行。
- 前置阻塞：最大反对易集合的非零核存在性、全一实际依赖及 Pauli 乘积相位连接仍待完成。

### V03-163 / 候选声明之间的直接证明依赖（2026-09-22）

- 对象：candidate_audit 的 environment 绑定、composition_witnesses 和 unaudited_term_dependencies。
- 准备条件：后续授权测试及指定范围的 Lean 审计；有实际证明项引用关系的目标声明。
- 操作情景：同环境目标之间直接引用、仅导入但未使用、经过未列入目标的中间引理、审计记录缺字段。
- 预期结果：仅实际 term_constants 引用生成直接组合证据；未审计中间声明保留为未审计依赖，不推断跨越它的直接边；证据拒绝时清空组合证据并撤去记录的 kernel_checked 标记。
- 当前状态：已接入现有 composition_witness，未执行测试或 Lean；V03-162 的执行授权仍待用户回复。
- 前置阻塞：选定目标之间的直接边不是完整证明项闭包，也不是论文引用支持边；仍需中间引理审计及源语义对齐。

### V03-162 / 条款证据离线定向回归（2026-09-22）

- 对象：host/test_clause_evidence.py；覆盖 V03-155 至 V03-159 中的条款绑定与状态函数部分。
- 准备条件：用户明确授权此测试文件；Python 可导入现有 host/core 依赖。
- 操作情景：运行 `python3 'schema v0.3/host/test_clause_evidence.py'`，覆盖 UTF-8 偏移、节点外/跨边界引文、摘要不一致、歧义引文、部分覆盖、未定位条款保留、历史协议、重复条款和 PDF 索引/复制隔离。
- 预期结果：10 个离线用例约束关键反例；不调用模型、Lean、网络或实际案例重放，不修改历史运行证据。
- 当前状态：测试代码已准备，未运行；不能据此声称测试通过。
- 前置阻塞：等待该明确范围的执行授权；不涵盖调度集成、真实 PDF 资产或 Lean 证明正确性。

### V03-161 / 候选产物与成功续跑回执绑定（2026-09-22）

- 对象：candidate_compile 的产物后缀与 check_candidate_receipts，candidate_audit 接入。
- 准备条件：后续授权测试；独立候选编译目录和回执样例。
- 操作情景：合法 .ir/.ir.sig 产物；缺少或多出回执；错误命令/环境路径、源哈希、日志内容；目录回执与进度副本不一致。
- 预期结果：合法 IR 产物保留哈希，不误报为额外文件；继续编译或审计前必须有与成功模块前缀逐一对应的真实命令记录，不能只信模块名称和对象哈希。
- 当前状态：静态对照现有 epoch_migration 的产物类型后修订，未执行测试或 Lean。
- 前置阻塞：真实工具链运行、故障恢复和全环境依赖审计尚未完成；本项是证据一致性约束，不是运行真实性的独立证明。

### V03-160 / 已报告覆盖缺口时跳过编译（2026-09-22）

- 对象：proof_backend 提前返回、scheduler 待审阅路径、audit_proof_walk 重建分支。
- 准备条件：后续授权测试；模拟合法模型输出及源证据。
- 操作情景：条款未绑定、部分覆盖、全局 remaining_obligations 非空；对照完整候选进入编译；篡改提前返回原因/证据的回放。
- 预期结果：已知覆盖缺口保留模型/Lamport/来源证据并跳过 Lean，不触发失败分类模型或自动重试；回放必须重建相同缺口，不能接受伪造的跳过理由。
- 当前状态：已写接入，未执行测试、模型或 Lean。
- 前置阻塞：实际模型输出质量与条款清单独立完整性仍需验证；跳过不是数学反驳或已完成证明。

### V03-159 / 条款引用限于目标节点来源（2026-09-22）

- 对象：clause_evidence._within_node 与 NODE_SOURCE_SPANS_V1 协议。
- 准备条件：后续授权测试；带冻结源跨度的目标节点与全文源。
- 操作情景：相同文件别处的正确引文、跨节点边界引文、不同哈希同路径、节点内子区间、相同 PDF 区域和其他区域；旧协议回放。
- 预期结果：只有节点内文本子区间或已绑定节点 PDF 区域可进入覆盖；节点外引用保存定位但标记未绑定，不提升为已覆盖；新旧回放按冻结 schema 区分。
- 当前状态：已接入协议、保存与回放，未执行测试或模型/Lean 调用。
- 前置阻塞：节点原始跨度过宽或错误仍需源审阅；范围包含只证明位置关系，不证明条款语义相符。

### V03-158 / PDF 条款绑定到已有区域（2026-09-22）

- 对象：clause_evidence.bind_clause_report 与证明输出 pdf_region_indices。
- 准备条件：后续授权测试/调用；已由 bound_pdf_proof_context 绑定的单一 PDF 上下文。
- 操作情景：选择单个或多个零起始区域编号；重复、负数、越界、布尔编号；文本上下文选 PDF 区域；NOT_LOCATED 同时给编号；旧报告无编号。
- 预期结果：只复制宿主已有区域及原始文件引用；拒绝非法索引和无对应上下文选择；旧报告及未选择区域维持未绑定；区域绑定不提升为数学语义接受。
- 当前状态：接口已接入，未运行测试、模型调用或 Lean。
- 前置阻塞：源节点区域不足时仍需单独扩充可审阅的来源区域；本实现不允许模型自行构造新区域或证明 PDF 渲染正确。

### V03-157 / 候选条款源位置格式统一（2026-09-22）

- 对象：research.schema.json 的 FrozenTextByteSpan、CandidateEvidenceLocation 和 CandidateClauseCoverage。
- 准备条件：后续授权 schema 校验；宿主文本绑定、旧 SourceSpan 和已有 PDFPageRegion 样例。
- 操作情景：接受三种显式源位置结构，拒绝混用字段、非法哈希和偏移单位；核对宿主 clause_evidence 输出采用文本分支。
- 预期结果：不再要求宿主 byte_start/byte_end 记录满足旧 start_byte/end_byte 结构；PDF 保留区域语义，不伪造文本偏移。
- 当前状态：静态发现新条款 schema 与宿主跨度字段不一致后修订，未执行校验。
- 前置阻塞：PDF 条款选择/绑定仍未实现；区间顺序、文件哈希、页面对应性和语义关系仍需宿主核对。

### V03-156 / 证明模型条款报告与回放绑定（2026-09-22）

- 对象：proof_backend 的 clause_report、clause_evidence.py、audit_proof_walk 的协议分支。
- 准备条件：后续授权测试/模型调用/Lean；固定文本或 PDF 源上下文。
- 操作情景：多条款结论、部分证明、遗漏义务、重复编号、唯一 UTF-8 引用、不存在或歧义引用；PDF/未定位条款；旧模型 schema 不要求 clause_report 的历史回放。
- 预期结果：新模型报告随 Lamport 和独立源证据保存；回放从冻结模型输出及源重建绑定；任何未绑定条款不得被过滤为貌似完整的子集；旧协议按原字段回放，不补造报告。
- 当前状态：协议、保存和回放代码已接入，未执行测试、模型调用或 Lean。
- 前置阻塞：PDF 条款区域适配、条款清单完整性与语义等价审阅仍未完成；文本字节绑定并不证明覆盖完整。

### V03-155 / 宿主条款覆盖状态与部分覆盖停止（2026-09-22）

- 对象：clause_coverage.py 与 scheduler 的 attested 结果分支。
- 准备条件：后续授权测试；已具备其他必要 attestation 字段的模拟证明结果。
- 操作情景：全缺字段、混合缺字段、空条款、重复条款、部分/更强/更弱/未决关系、有剩余义务及全部候选等价。
- 预期结果：历史格式记录 UNRECORDED，保留原有不可提升语义；显式部分或畸形覆盖停止在 AWAITING_REVIEW，不加入 completed/available；全部映射仅标记 MAPPED_INVENTORY_UNREVIEWED，不能接受整节点。
- 当前状态：接入代码已写入，未执行测试或调度重放。
- 前置阻塞：模型输出条款清单、源跨度校验和条款清单完整性审阅仍待接入；该状态函数不提供语义校验。

### V03-154 / 声明绑定的条款覆盖记录（2026-09-22）

- 对象：research.schema.json 中 CandidateClauseCoverage 与 DeclarationBinding.clause_coverage。
- 准备条件：后续授权 schema 校验；含多个独立条款的论文声明样例。
- 操作情景：记录同一节点的不同条款、非空原文跨度、候选等价/部分/更强/更弱/未决关系；读取未带此字段的历史绑定。
- 预期结果：可以表达部分覆盖；旧绑定缺字段表示未知；空剩余义务和候选等价都不能自动升级为完整节点接受。
- 当前状态：schema 已扩展，未执行校验。
- 前置阻塞：条款清单完整性、稳定编号及与宿主接受门控的接入仍未实现；本字段仅记录候选证据。

### V03-153 / 容量达到与反对易集合等价（2026-09-22）

- 对象：CapacityAnticommutingCriterion.lean。
- 准备条件：后续授权 Lean 执行；通用团数界、容量等式与具体 Pauli 基础可用。
- 操作情景：双向编译团数 2n+1 与存在相同基数的两两反对易窗口子集；将其与容量 iff 合成。
- 预期结果：等价条件使用实际 Pauli 乘法；反方向用 P≠−P 排除同时交换和反对易，并用通用团数界建立最大性。
- 当前状态：候选已写入聚合入口，未编译或测试。
- 前置阻塞：Finset/Set 团接口需实际核定；候选源码不构成源语义接受证据。

### V03-152 / 容量命题已有节点关联（2026-09-22）

- 对象：query-perfect-branch-audit.json 中 prop:extremal 的候选关联。
- 准备条件：后续授权校验；保留的 research assembly 和原始 TeX 字节可读。
- 操作情景：核对节点 e63f20587f624a1d472f6f83、assembly 哈希、原文区间 [54243,54730) 和 span 哈希；比较两个 Lean 目标与该节点的复合条款。
- 预期结果：外层最大值及团数 iff 仅关联各自条款；最大反对易集合等价条款保持未覆盖，不把同节点部分形式化提升为整个节点完成。
- 当前状态：静态读取已有抽取节点后登记关联，未执行校验或 Lean；历史抽取未重跑。
- 前置阻塞：运行时源绑定校验及复合声明的条款级接受规则仍须接入。

### V03-151 / 论文分支审计目标配置（2026-09-22）

- 对象：profiles/query-perfect-branch-audit.json 与 candidate_audit.audit_candidate_plan。
- 准备条件：后续授权 Lean 执行；共同环境候选完成编译；目标声明的源语义仍须另行审阅。
- 操作情景：读取九个目标及其论文条款/辅助证明角色，冻结原始配置字节，核对目标顺序与聚合入口；输入不匹配入口、伪称源对齐或全查询覆盖的配置。
- 预期结果：精确目标配置及哈希进入审计证据；范围不匹配拒绝执行；内核成功不会提升候选 claim 关联为 accepted supports，也不会消除 open_obligations。
- 当前状态：配置及消费接口已写入，未执行或测试。
- 前置阻塞：prop:extremal 候选节点绑定和全部声明精确源跨度对齐未完成。

### V03-150 / 候选对象目录完整绑定（2026-09-22）

- 对象：candidate_compile.check_candidate_objects 及编译、审计接入点。
- 准备条件：后续授权执行测试；独立临时对象目录及可控编译输入。
- 操作情景：额外对象、缺失对象、目录/符号链接、重复记录、已知对象哈希变化；模拟成功编译期间源文件或清单变化。
- 预期结果：对象目录必须与已登记清单完全一致；成功退出不能覆盖证据不一致，后者保留回执并进入 COMPILE_EVIDENCE_REJECTED；审计前后同样拒绝额外对象。
- 当前状态：静态修订完成，未测试或执行 Lean。
- 前置阻塞：真实工具链输出的完整后缀集合仍须授权执行后确认；此改动不代替所有外部库的依赖完整性审计。

### V03-149 / 候选导入扫描的注释边界（2026-09-22）

- 对象：candidate_sources.py 的 _header_imports。
- 准备条件：后续授权执行测试；构造带嵌套块注释、行注释、public import、模块头及声明内字符串的源输入。
- 操作情景：注释中放入伪 import，真实 import 后加注释，声明正文字符串中包含 import；覆盖未闭合头部注释与不支持的模块名。
- 预期结果：只保留受支持头部语法中的真实导入，不把注释或正文字符串算作依赖；未闭合注释或非法导入名称明确拒绝；不冒充完整 Lean 解析。
- 当前状态：由全文件逐行正则改为跳过注释的头部扫描，未运行测试。
- 前置阻塞：最终导入解析及对象依赖仍须在真实 Lean 环境确认。

### V03-148 / 跨全部可解窗口的容量最大值（2026-09-22）

- 对象：SolvableWindowCapacityMaximum.lean 与 UNIVERSAL_CEILING_ALIGNMENT.md。
- 准备条件：共同环境依赖链可用；后续授权 Lean 执行；论文测量集合与有限编号窗口的域对齐审阅。
- 操作情景：编译同时量化任意 m 和 W 的容量集合及 IsGreatest；核对 JW 给出集合成员和所有可解窗口给出统一上界，检查 n>0 限制。
- 预期结果：命题表达外层最大值及其达到性；不将固定窗口上界误充整体最大值，也不覆盖唯一依赖、精确奇偶秩或外部出处声明。
- 当前状态：新增候选与原文范围对照，未编译、测试或审计。
- 前置阻塞：论文源语义绑定、零量子比特域说明和真实内核验证尚未完成。

### V03-147 / 候选声明审计接入（2026-09-22）

- 对象：`host/candidate_audit.py:audit_candidates`。
- 准备条件：后续授权 Lean 执行；候选全部编译且对象完整；显式非空声明目标清单。
- 操作情景：审计目标定理类型、前提、term_constants 和公理；覆盖空目标、重复目标、非法名称、对象修改、前后环境变化、缺失或重复输出、禁止公理及已有审计目录。
- 预期结果：仅目标清单精确匹配且公理许可时标记 SELECTED_DECLARATIONS_AUDITED；其他状态不标记 kernel_checked；accepted、全声明覆盖、前提完整审阅和查询链完成保持 false。
- 当前状态：已写接口，未执行、测试或审计。
- 前置阻塞：实际共同环境编译及目标清单的论文声明绑定；现有 EnvironmentAudit 的直接结构前提枚举不等于递归前提完整性证明。

### V03-146 / 候选逐模块编译接入（2026-09-22）

- 对象：`host/candidate_compile.py:compile_next_candidate`。
- 准备条件：后续明确授权 Lean 执行；完整候选快照和固定共同环境。
- 操作情景：首次编译与继续下一模块；源或对象被改动、顺序错误、环境变化、编译失败和进程中断；最终模块成功后尝试继续。
- 预期结果：每次只处理下一模块并保留回执；已完成模块不重跑；失败或中断不自动重试、不覆盖证据；全体成功仅进入 COMPILED_AUDIT_PENDING，accepted 保持 false。
- 当前状态：已写实现，未执行或测试。
- 前置阻塞：需要实际共同环境兼容性处理和声明审计；此接口不证明论文源对齐或递归依赖闭合。

### V03-145 / 未编译候选独立源准备（2026-09-22）

- 对象：`host/candidate_sources.py:freeze_candidate_sources`。
- 准备条件：后续授权执行；现有共同环境元数据和本地候选源可读。
- 操作情景：准备两个证明根的传递导入闭包；覆盖 frozen witness、循环、未知根、重复根、不支持的 import 语法及已有输出目录；保留源后修改工作树，再核对快照不变。
- 预期结果：新目录保留准确源字节及哈希、依赖顺序和未解析外部导入；不伪造原环境回执，不写入旧迁移目录，不标记编译或源语义对齐成功。
- 当前状态：实现已写入，未执行、测试或校验。
- 前置阻塞：候选编译器、共同环境兼容性处理与声明审计尚待接入；行扫描仅用于源准备，不能作为 Lean 导入解析证明。

### V03-144 / 完美图分支共同导入入口（2026-09-22）

- 对象：`QueryPerfectBranchCandidates.lean` 及共同环境候选接入路径。
- 准备条件：用户后续授权 Lean 执行；固定共同环境和全部外部包版本，显式绑定 frozen/AnticommutingWitness；候选接入不得冒用旧迁移成功回执。
- 操作情景：同时导入 cover-dual 与 JW capacity 两个根，沿实际依赖编译并保留源哈希、编译输出和声明公理证据。
- 预期结果：同一环境解析共享基础且无重复声明；失败保留为候选失败，不升级为论文依赖链证书。
- 当前状态：仅新增源代码聚合入口和接入说明，未运行。
- 前置阻塞：现有 extension_migration 要求匹配原环境成功回执，不能直接接纳尚未编译的新候选；独立候选接入仍待实现。

### V03-173 / 勘误关系与查询来源闭合（2026-09-22）

- 对象：设计 §4.5；待实现的 CORRECTS 来源关系、条款影响审阅、查询投影与提升边界。
- 准备条件：先实现来源关系和运行时消费接口；冻结原文、勘误、声明位置与审阅出处；后续明确授权测试执行。
- 操作情景：仅有勘误元数据、缺原文、影响未决、明确受影响或不受影响、查询裁剪、已完成旧声明、跨版本错配及来源字节变化；以 Newman 1932 为真实发现样例，不能预设其基数上界受影响。
- 预期结果：CORRECTS 不进入数学支持边计数；未决影响保留在查询相关来源闭合义务中；旧证明不自动迁移到修订声明；历史回执不覆写，已完成范围不重跑；没有勘误字段的历史记录不被当作已完成勘误审阅。
- 当前状态：新增 source_corrections.py，research 发布前及 audit_research 重建接入冻结勘误通知；按精确原文/来源位置绑定节点，并借现有 blocked_by 传播保留未决事项。未执行任何测试或真实通知导入；影响审定与提升边界仍未实现。
- 前置阻塞：原始论文全文获取、勘误条款核对及控制器/提升接口实现；人工接受操作不能由模型的 UNAFFECTED 分类替代。

V03-173 增补情景：空 imports 保持历史图不变；重复 notice 幂等；缺目标留待后续 join；同 ID 不同正文或来源位置拒绝；多 notice 后项失败不得部分写入；节点裁剪保留勘误事项且支持边计数不增加；发布图与独立重建一致。全部未执行。

V03-173 身份绑定补充：新增 `SourceCorrectionNotice` / `SourceCorrectionTarget` schema 及独立 schema 入口；宿主现要求 target.paper_id 与 original_work_id、节点 paper_id 相等，并精确比对 conditions。需覆盖同文本/位置但不同论文或前提、DOI/arXiv 未审阅别名、自我修正关系、非法目标类型。JSON Schema 形状校验与宿主跨对象核对均未执行；shape schema 不证明 publisher URL 权威性或影响判断。

### V03-174 / PDF 全页轻量模型抽取入口（2026-09-22）

- 对象：`host/pdf_extract.py` 与 `pdf_candidates.assemble` 的未决依赖保留。
- 准备条件：冻结 PDFRegionDocument、全部有序页面图像、明确 paper_id、冻结 LIGHT paper.extract 路由和调用预算；后续明确授权测试。真实新文献调用须单独保存回执，不能当作测试通过。
- 操作情景：九页 Hurwitz 影印含封面但无正文文本层；内部 ID/定位错误、不可读公式、跨页声明、未知外部前提、批评性引用、文档/图像字节变化、超过 32 页以及旧报告缺 unresolved_dependencies 字段。
- 预期结果：使用冻结路由和真实图像输入；声明来源 PDF 引用由宿主注入；模型只产生候选；未决依赖进入节点并保持阻塞；旧缺字段产物重建不新增空字段；超过容量拒绝而不截断；读取限制和覆盖未知明确保留。
- 当前状态：入口与适配代码已写，未调用模型、测试或重放，未导入真实图。Luna 默认来自已有路由，不据此宣称图像抽取质量。
- 前置阻塞：来源文档准备、入口调度/持久化、全文覆盖独立审阅；大于 32 页的文献需要保留全文上下文的分批方案，当前不得假称支持。

### V03-175 / PDF 模型抽取运行与证据落盘（2026-09-22）

- 对象：`host/pdf_extract_run.py`、`pdf_extract.py` 的结构化候选错误回传。
- 准备条件：完整九页来源清单、Luna/Terra 冻结路由、明确调用预算；后续明确授权测试执行。
- 操作情景：新目录一次抽取；旧目录重复启动、模型失败、不可读结果、定位错误、空声明/只有反证上下文、图装配异常及中断；核对保留计划、图像、源码快照、SQLite 和模型回执。
- 预期结果：最多一次新模型调用；不覆盖旧运行、不自动重试或升级；空输出不变成数学完成；错误以 code/detail 对象传递给共享 call_model，避免失败记录阶段发生字符串下标异常；保留失败摘要与已有回执。
- 当前状态：代码已写，未执行、测试或调用模型。
- 前置阻塞：新增 PDFModelExtractionRun 仍是独立运行类型；现有 PDF proof-context 只识别 PDFRegionCandidateRun，需显式接入与审计，不能仅改 kind 冒充旧产物。

V03-175 真实新文献执行记录（不作为独立测试）：`hurwitz1898-luna-pdf-extraction-20260922` 完成九页来源冻结，但模型进程因沙箱禁止本地 Codex 状态库写入及 app-server 初始化而退出 1；无模型响应。失败回执原样保留。获命令执行权限后，在 `hurwitz1898-luna-pdf-extraction-authorized-20260922` 对同一未完成范围启动一次 Luna 调用；启动时尚未有最终结果。不复用失败为成功，不运行测试或 Lean。

V03-175 真实执行收尾：授权运行 session 47725 已退出 2。Luna 进程返回 0，75.801321 秒，29462 input tokens、3925 output tokens（含 204 reasoning tokens）；原始 response.json 有 26 条候选行和阅读限制。随后宿主因系统 Python 缺少 jsonschema 报 MODEL_RESPONSE_PROCESSING_FAILED，summary 仍为 MODEL_EXTRACTION_FAILED，没有 candidates/assembly/graph 成功产物。响应必须复用，不再次调用模型。已把 call_model 的 jsonschema 导入提前到调用前，防止同类本地依赖缺失在消耗额度之后才暴露；该改动未测试。待恢复本地后处理，原始失败回执不改写。

### V03-176 / 复用已保存 PDF 模型响应（2026-09-22）

- 对象：`host/pdf_extract_recover.py`。
- 准备条件：明确授权执行校验；Python 环境提供 jsonschema；保留原始失败运行及全部 PDF、页面图像和模型文件。
- 操作情景：对 Hurwitz 1898 已保存响应恢复；响应/任务/来源摘要变化、图像顺序或字节变化、其他失败原因、非零进程退出、未知工具事件、schema 漂移、输出目录已存在。
- 预期结果：只允许 jsonschema 缺失造成的后处理失败；校验冻结 schema 和来源绑定后，在新目录记录候选图及恢复代码快照，新增模型调用为零；旧回执不改写；异常拒绝，不提升来源接受或全文完整性状态。
- 当前状态：入口已写，仅静态阅读，未执行恢复、校验或测试。
- 前置阻塞：仍待明确执行授权；只读清单找到仓库 `.venv` 的 jsonschema 4.23.0 包文件和 Python 3.12.2 配置，未执行导入确认。恢复并不完成语义审阅或 Lean 验证。后续接入代码见 V03-177，尚无运行证据。

### V03-177 / 恢复产物进入 PDF 证明上下文前重建（2026-09-22）

- 对象：`host/pdf_extract_recover.py`、`pdf_proof_context.py`、`audit_pdf_candidates.py`；设计 §4.6。
- 准备条件：V03-176 生成的新恢复运行及全部原始证据；明确授权校验/测试。当前没有已生成的恢复运行。
- 操作情景：读取恢复产物作为 PDF 来源；模型路由、事件日志、图像顺序/总量、page-count 回执、图像尺寸变化；修改候选或支持图、删除未决依赖、提升接受/完整性状态、缺失代码快照；旧 PDFRegionCandidateRun 保留原路径；包含和不包含 unresolved_dependencies 的旧格式报告。
- 预期结果：以原响应重建候选、装配和裁剪结果；不依赖摘要自报成功，不新增模型调用、不执行历史 Python；新类型显式接入 proof-context；旧格式审计也核对未决依赖及其阻塞。失败拒绝接入，历史产物不改写。
- 当前状态：代码和设计已修改，仅静态阅读；恢复、审计、proof-context 和 Lean 均未执行。共享适配器重建不是独立语义审阅。
- 前置阻塞：正常成功的 PDFModelExtractionRun 尚无对应新类型读取路径；研究控制器对 PDF 的自动递归调度和大于 32 页全文策略仍需接入，不能因本项实现宣称整条链已连通。

### V03-178 / 正常成功 PDF 模型产物接入（2026-09-22）

- 对象：`host/pdf_extract_recover.py` 的共享来源重建与 `model_run_binding`、`pdf_proof_context.py`、`audit_pdf_candidates.py`；设计 §4.6。
- 准备条件：正常成功 PDFModelExtractionRun 或明确授权的相应测试输入；完整回执、响应、页面和运行源码；明确授权执行。当前 Hurwitz 运行仍是原始后处理失败，不能用它冒充成功样本。
- 操作情景：正常候选输出及空声明输出；只修改失败摘要状态、响应与 result 候选不同、result 报告与装配不同、错误回执、图内容变化、计划与源码清单不同；证明节点丢失或修改 unresolved_dependencies；旧 PDFRegionCandidateRun 和恢复类型保持各自读取入口。
- 预期结果：普通成功要求 CANDIDATE_RECORDED 且错误/校验问题为空；共享来源核对后重建报告和图；只接受匹配的候选产物，不重跑模型，不提升数学状态；审计失败保留正确的运行类型；未决依赖不因进入证明上下文而丢失。
- 当前状态：代码和规范已修改，仅静态阅读，没有调用模型、执行校验、恢复、测试或 Lean。V03-177 所述普通成功类型接入缺口已在代码层补齐，尚无执行证据。
- 前置阻塞：PDF 自动递归调度、大于 32 页的全文处理、支持关系语义审阅和实际 Lean 组合仍未完成；本项不审计完整 SQLite 历史。

### V03-179 / PDF 声明级候选支持连接器（2026-09-22）

- 对象：`host/pdf_support_join.py`；`research.schema.json` 的 PDFSupportMatchProposal 与对应独立 schema。
- 准备条件：来源绑定有效的 PDF 候选运行、已有下游图、按准确 request 快照和上游 claim ID 保存的语义匹配提案；明确授权执行校验或测试。
- 操作情景：单声明支持、多个共同前提、明确替代路线、未说明 AND/OR、反证上下文冒充定理、页区域或 request 内容变化、重复导入、同 ID 内容冲突；上游仍有外部依赖和阅读限制。
- 预期结果：使用既有 PDF 页区域而不虚构文字引文；核对 proposal schema、原请求和声明来源；保留基图查询范围并裁剪祖先图；外部请求和已有 blocker 不删除，新增边保持 UNREVIEWED；上游 PDF 请求转换为研究控制器字段形状但不虚构 DOI/arXiv 身份，未知身份继续未决；零模型调用。
- 当前状态：连接函数和 schema 已写，未执行；未生成真实 PDF 匹配提案或支持边，也未修改历史图。
- 前置阻塞：尚未接入研究控制器的预算/调度/持久化及其重建审计，也未接入 Terra 匹配调用。不得将连接函数存在等同于自动递归成功；这些接入需保留每篇 PDF 的预算和原始模型归属。

### V03-180 / PDF 上游的 Terra 语义匹配入口（2026-09-22）

- 对象：`host/pdf_match.py`；共享 `call_model` 的 dependency.match / DECISION 冻结路由；PDFSupportMatchProposal 适配。
- 准备条件：有效候选基图、准确请求 ID、下游 TeX 全文或来源绑定的 PDF 运行、上游 PDF 运行及页面；已有计划账本和匹配预算；后续明确授权执行。
- 操作情景：TeX→PDF、PDF→PDF；单支持/共同前提/多替代路线；缺失或重复请求、未知/重复 claim ID、反证上下文、前提或页来源变化；MISMATCH/UNCERTAIN；与已存在支持路线含义冲突；总页面超过 32 或总输入超过共享调用上限。
- 预期结果：每个请求恰有一项判断；完整两侧来源及明确图像偏移进入模型上下文，不截断；使用冻结 DECISION 路由（默认 Terra），通过同一账本计费；宿主填入精确请求和页区域；保留全部判断和原回执，仅支持判断形成候选提案；不接受身份、支持关系或数学结论，不自动升级模型。超过限制在模型调用前拒绝。
- 当前状态：代码已写，仅静态阅读；未调用模型、运行校验或生成任何新提案。未重跑已有抽取。
- 前置阻塞：控制器仍需调度并完整持久化返回结果，重建审计须核对原响应→提案映射；不能只保存支持投影而丢弃 MISMATCH/UNCERTAIN 或调用回执。大篇幅全文策略和实际恢复授权仍未落实。

### V03-181 / PDF 匹配与连接的完整结果持久化（2026-09-22）

- 对象：`host/pdf_match_run.py` 的 run_pdf_match；复用已有 PlanLedger、pdf_match 和 pdf_support_join。
- 准备条件：控制器已将两侧论文计入论文预算，存在冻结计划、真实 PDF/TeX 来源和请求；后续明确授权执行。入口本身不另开预算、不自动准入论文。
- 操作情景：匹配失败、全为 MISMATCH/UNCERTAIN、混合判断、支持提案成功但连接失败、图超过 64 MiB、进程中断、重复指定旧输出目录。
- 预期结果：在新目录保留计划/代码/schema 快照、全部模型结果及逐请求 outcomes；先保留判断再连接，连接失败不丢失已完成的模型工作；无支持时不虚构空成功图；支持候选仍未解决请求；错误记录阶段和原因；不得自动重试、另开账本或覆盖旧运行。
- 当前状态：代码已写，仅静态阅读；未调用模型、执行连接、测试或校验，没有新图或成功回执。
- 前置阻塞：研究控制器尚未调用该入口，论文准入预算与重建审计仍需接入；恢复授权、实际来源匹配与 Lean 全链验证仍未完成。

### V03-182 / 递归控制器复用 PDF 来源与统一论文预算（2026-09-22）

- 对象：`host/research.py`、`scheduler.py`、`recursive_graph.py`、`audit_research.py`；RetainedPDFSourceBinding schema。
- 准备条件：新冻结计划的 evidence_imports.pdf_sources 中保存绑定文件引用；绑定包含 paper_id、已完成 PDF 运行引用和准确请求快照；查询图仍由原 arXiv 查询产生；明确授权执行。
- 操作情景：TeX→已保存 PDF、PDF→已保存 PDF；同 PDF 多个请求、预算恰满/用尽、严格校准策略、输入来源或 request 变化、正常匹配失败、连接成功但控制器发布失败、中断后恢复、后续 TeX 连接保留 PDF 来源记录、未实现的 PDF→TeX 路径。
- 预期结果：仅当前查询祖先图中承担依赖的请求可准入；同一 SQLite frontier 事务计入 max_papers（包括复用 PDF），多请求不重复占位，失败不退还；同一账本派发匹配；保存逐请求结果和 attempted 标记，普通恢复不重复调用；中断保持 BUSY；仅图发布完成才标 research_graph_published；PDF→TeX 未实现时显式阻塞而不把 PDF 身份交给 arXiv 下载器。
- 当前状态：控制器、预算准入和保存入口已在代码层连接，未执行模型、校验、测试或新案例；没有新支持边。
- 前置阻塞：来源发现仍依赖预先冻结的请求→PDF 候选绑定；匹配响应/提案/图的递归重建审计尚缺，audit_research 对含 PDF 运行显式返回失败，不能给出 PASS；大篇幅全文、实际恢复与全链 Lean 验证仍未完成。

### V03-183 / 单次已完成 PDF 匹配的重建审计（2026-09-22）

- 对象：`host/audit_pdf_match.py`；`pdf_match.py` 提取出的共享 prepare_pdf_match。
- 准备条件：正常结束的 PDFMatchAttempt 及完整来源、计划、任务、原始响应、页面快照、提案、outcomes 和候选图；后续明确授权执行。
- 操作情景：有支持及全部不支持两类正常收尾；丢弃 UNCERTAIN/MISMATCH、修改条件/区域/图、提示词或页面顺序改变、冻结路由/超时不同、原始响应与宿主候选不同、模型越权工具事件、运行源码或 join schema 缺失/漂移；对失败或中断尝试审计。
- 预期结果：不调用模型、不执行旧 Python 或 Lean；重建完整提示和输入图像，再从原响应恢复全部判断、支持投影、连接和逐请求结果；非支持判断不能被过滤；只有范围内完整一致才输出单次完整性 PASS，不表示语义接受。失败、中断及不支持的历史契约明确拒绝该正常收尾审计。
- 当前状态：代码已写，仅静态阅读；未执行任何校验或审计，没有新增 PASS 证据。
- 前置阻塞：该审计不核对整个递归计划的 SQLite 调用归属、论文准入或控制器图发布历史；audit_research 的 PDF 拒绝门仍保留，后续需完整接入，不能凭本项宣称递归审计已完成。

### V03-184 / 正常完成 PDF 匹配进入递归账本与图审计（2026-09-22）

- 对象：`host/audit_pdf_research.py`、`audit_research.py`、研究结果的审计状态字段。
- 准备条件：正常完成的 PDF 尝试、SQLite 账本、全部检查点、冻结来源绑定、模型/来源/图文件；后续明确授权执行。
- 操作情景：纯 PDF 上游及 TeX/PDF 混合连接；负向判断、局部连接成功但未发布；省略失败目录、孤立模型调用、重复已尝试请求、删除判断、跨计划回执、未占用论文名额、模型先于论文准入、未对应 BUSY→READY 的图变化、来源与准入事件不符。
- 预期结果：单次重建结果与同一 SQLite 调用及论文记录绑定，核对请求对应的准入图和调用顺序；全部尝试目录、调用、判断、最终 attempted 标记必须对应；通过完整检查点历史重建已发布图，再与普通 TeX 连接共同检查可达性。仅正常完成路径可以进入完整性 PASS 候选；失败/中断仍明确拒绝，不能通过省略相应证据绕过。
- 当前状态：代码已连接，仅静态阅读；未执行审计、测试或案例，没有新增 PASS。原先无条件拒绝 PDF 的代码门已替换为以上核对，失败/中断审计不支持的边界仍保留。
- 前置阻塞：实际执行授权仍未获得；失败和中断的完整重建、大篇幅来源、自动发现、PDF→TeX 和 Lean 全链验证仍未完成。完整性 PASS 不证明来源语义、前提充分性、全文覆盖或最早出处。

### V03-220 / proof_walk 加固：根审计格式、无探测不出证书、平凡性审计、certify 先审计、失败审阅内容（2026-09-24）

- 对象：`proof_walk.run_walk`（根审计逐项按 `$defs.RootAudit` 校验；输入图节点自带 `root_audit` 即拒绝）、`scheduler._root_audited`（删去无人生成的 NO_LIBRARY_PROVIDES_THIS 分支）、`certify.certificate`（定义豁免按图节点 kind 判断）与 `certify.main`（调用 `audit_proof_walk.audit`，异常也得到保留部分证据的 FAILED 报告）、`audit_proof_walk.Auditor`（`triviality` 用审计器内冻结的战术表；有 `triviality/` 目录也触发核对；`graph` 拒绝自带 root_audit 的输入图；可用依赖的 `kernel_attestation_state`、`environment_hypotheses` 与平凡性标志须与 scheduler 推导一致）、`review.subjects`；新增/修改的测试在 `schema v0.3/tests/test_review_certificate.py`（根审计三种非法状态、过期图与自带 root_audit 的输入图、未探测查询及改写 kernel_attestation_state 的记录、certify 拒绝审计失败的运行、失败审阅内容）与 `tests/test_library.py`（伪造平凡性标志）。
- 准备条件：仓库 `.venv`；用户明确要求执行后运行；历史运行只读。
- 操作情景：①根审计文件含 NO_LIBRARY_PROVIDES_THIS、LIBRARY_BOUND 或未知状态；输入图节点已带 root_audit；②定理查询结果无 `statement_trivially_provable`，包括把其记录的 kernel_attestation_state 改成 DEFINITION_ELABORATED；③结果带探测字段但标志与日志审计行不符、源文件与冻结战术表重建不符；有 `triviality/` 目录但结果删去探测字段；④`certify.py --run` 作用于审计不通过的运行；在 proof-walk-result.json 改写可用依赖的 kernel_attestation_state 或清空 environment_hypotheses 并重钉 summary；⑤失败审阅模板。然后跑全套：`PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest 'schema v0.3/tests' 'schema v0.3/host/test_clause_evidence.py' -q -p no:cacheprovider`，并对主检出 `runs/proof-worker-normalization-attempt02-20260919` 跑 `audit_proof_walk.py`（输出到临时目录）。
- 预期结果：①在建输出目录前抛 ValueError；②CHAIN_INCOMPLETE，缺项为 `QUERY_STATEMENT_TRIVIALITY_UNPROBED <query>`；③审计出现 TRIVIALITY_PROBE_NOT_SUPPORTED_BY_LOG 或 TRIVIALITY_PROBE_INCOMPLETE；④不写证书，在 `<O stem>.run-audit.json` 留下 FAILED 审计报告；改写派生字段时审计出现 DERIVED_DEPENDENCY_FIELDS_MISMATCH；⑤内容含 failure_kind、failure_reason、lean_source、lean_log（Lean 未运行时后两者为 null）。静态估计全套为 77 passed、1 skipped（原 72 passed + 新增 5 项），历史运行仍 PASS（其结果无探测字段、无 triviality 目录，输入图无 root_audit，派生字段与 scheduler 公式一致，summary 不钉证书）。③的目录情景与④的派生字段情景没有单元测试（需要真实运行夹具），只做过静态阅读。
- 当前状态：已执行（2026-09-24，用户已明确授权本次修订"测试+编译+修复"）。全套 77 passed、1 skipped（`schema v0.3/runs/v03-revision-evidence-20260924/pytest-final.txt`）；真实 Lean 平凡性探测 1 passed（`pytest-lean-opt-in-final.txt`）；`audit_proof_walk.py` 对 attempt02 历史运行 PASS（`audit-proof-walk-attempt02.json`）；`audit_research.py` 对两个历史研究运行仍 PASS（`audit-research-*-final.json`）。③的目录情景与④的派生字段情景仍无单元测试。
- 前置阻塞：审计器保存战术表的冻结副本（与候选源模板同样做法）；以后若改 `proof_backend.TRIVIALITY_TACTICS`，需要在审计器里新增探测版本，否则新运行审计失败，旧运行不受影响。certify 的审计报告放在证书旁边，因为 ChainCertificate schema 不允许附加字段。

### V03-219 / 递归连接合并各论文 mentions 表（2026-09-24）

- 对象：`host/recursive_graph.py` 的 join_candidate_paper；CLAIM_REFERENCE_V1 装配中的 `mentions`。
- 准备条件：先实现跨论文合并（当前未实现）；两篇以上 V1 装配。
- 操作情景：上下游同一文献键被提及；连接链多次；旧格式装配无 mentions。
- 预期结果：合并后的 mentions 可追溯到各论文，不进入支持组或请求；旧运行重建不变。
- 当前状态：未实现、未执行；mentions 只留在各论文 assembly.json。

### V03-218 / audit_proof_walk 核对平凡性探测与检索证据（2026-09-24）

- 对象：`host/audit_proof_walk.py`；新运行的 `triviality/Triviality.lean`、`statement_trivially_provable`、`retrieved_library_candidates`、`library_search_for_unknown_identifiers`。
- 准备条件：先实现这些核对（当前未实现）；一个带根审计的真实模型运行（V03-216）。
- 操作情景：探测文件与 TRIVIALITY_TACTICS 不符；标志与探测日志不一致；检索候选与根审计或索引不符；未知标识符与上次日志不符。
- 预期结果：任一不一致使审计失败；历史运行仍 PASS。
- 当前状态：未实现、未执行。root_audits、human_reviews、chain_certificate 三个分支已接入审计器，但只经静态阅读和一次替身重走，未由真实新运行覆盖。
- 2026-09-24 补记：平凡性探测核对已实现（见 V03-220），未执行；检索候选与未知标识符核对仍未实现。

### V03-217 / 严格模式下由人工审阅解除阻塞（2026-09-24）

- 对象：`proof_walk.py`、`review.py`、`certify.py`、scheduler 的审阅阻塞。
- 准备条件：先决定政策：已接受的对齐审阅能否解除 CANDIDATE_ROOT_SEARCH/BINDING_REVIEW_REQUIRED；实现 `proof_walk --resume <run> --reviews R`。
- 操作情景：严格模式下 walk 后人工填写 STATEMENT/PREMISE_ALIGNMENT 与 FAILURE_CLASSIFICATION 审阅再续跑；REJECT 撤回 ACCEPT；审阅后内容变化。
- 预期结果：只有被接受审阅覆盖的阻塞解除；human_accepted 仅在全部阻塞和对齐均有 ACCEPT 时为真。
- 当前状态：未执行。当前严格模式下 proof_walk 内 human_accepted 不可达，只能经探索模式加 `certify.py --run --reviews` 事后达到（仅替身测试覆盖）。
- 前置阻塞：政策未定；resume 模式未实现；尚无任何真实 HumanReview 记录。

### V03-216 / 带根审计与真实模型的 proof_walk（2026-09-24）

- 对象：`proof_walk.py` + `ModelProofBackend` + `library.py roots`；`thm:solvable` 的 V1 图。
- 准备条件：用户明确授权模型调用与 Lean；图与根审计见 `schema v0.3/runs/v03-revision-evidence-20260924/demo/`；按 V03-213 同一冻结环境（prop-v2）的库索引。
- 操作情景：可尝试根（演示中 5 个）的真实尝试；负载携带检索候选；失败后按未知标识符检索；成功定理触发平凡性探测；生成 chain-certificate.json 并用 audit_proof_walk 审计。
- 预期结果：回执、配额与失败分类完整保留；平凡或未知的定理不进入可用依赖；证书状态与可达性一致，结果仍为 CHAIN_INCOMPLETE 或带前提的有条件蕴含。
- 当前状态：未执行（模型调用未获授权）。
- 前置阻塞：授权；检索为词法匹配、候选偏弱；Physlib/QuantumInfo/Quantumlib 在 prop-v2 环境中为 0 行。

### V03-215 / M1 回放测量（设计 §11）（2026-09-24）

- 对象：设计文档 §11 的 M1；本次新增的库检索与根审计。
- 准备条件：用户明确授权模型调用；给模型真实规模的库（不能只含答案声明）。
- 操作情景：按 §11 对已有 ground truth 回放。
- 预期结果：得到可测量的成功率与成本，而非单例。
- 当前状态：从未执行。

### V03-214 / 带新引用字段的真实抽取（2026-09-24）

- 对象：`model.py` 严格响应 schema（internal_support_claim_indexes 带 minimum 0、external_mention_citation_keys）；`chunks.bundle` 的批内序号改写；`candidates.py` 的 V1 规则。
- 准备条件：用户明确授权模型调用；新 research 计划（冻结 CLAIM_REFERENCE_V1）。
- 操作情景：供应商是否接受整数项 minimum；多批次合并时序号改写与跨批冲突；同一键既用又提及（MODEL_CITATION_ROLE_CONFLICT）；自引用或越界序号。
- 预期结果：非法序号与角色冲突被拒绝并留回执；合法响应装配为 COMPACT_V1 图，展开不引入环。
- 当前状态：未执行；V1 目前只在保留的旧响应上演示（V03-213）。

### V03-213 / 真实数据演示：标签查询、V1 图、库索引与根审计（2026-09-24）

- 对象：`research.bind_query`、`candidates`（V1 + 环回退）、`library.py`、`scheduler.bottom_up_walk`（替身，不调用模型或 Lean）。
- 准备条件：`runs/research-doi-available-20260922` 的目标论文及保留响应；prop-v2 环境库索引。
- 操作情景：`thm:solvable` 绑定；仅目标论文与连接上游两种图；有/无根审计；旧格式对照。
- 预期结果：标签恰好绑定 1 个声明；带根审计的 V1 图能发起证明尝试，旧图不能；V1 展开不引入新环；替身不接受或晋升任何内容，结果仍为 CHAIN_INCOMPLETE。
- 当前状态：已执行（2026-09-23/24，用户明确授权本次修订“测试+编译+修复”）。结果：绑定 1 个声明；尝试次数 旧 0 → V1 5（仅目标）/ 6（连接）；无根审计时为 0；强连通分量（V1，环回退前→后）[25,4,2] → [4,2,2]；库索引 19,078 行（Lean 回执 38 s）。证据：`schema v0.3/runs/v03-revision-evidence-20260924/demo/`（report.json、report-before-cycle-fix.json、脚本、图与根审计）、`schema v0.3/runs/v03-revision-evidence-20260924/library-index/`。demo.py 已保留于同一目录；7.4 MB 索引行文件未保留，可用 library.py 重建。

### V03-212 / 查询分支官方候选编译与声明审计（2026-09-24）

- 对象：`candidate_sources` / `candidate_compile` / `candidate_audit`（新增 context_repo、library 参数）；四个根的 60 模块闭包。
- 准备条件：physlib（Lean v4.33.0、mathlib db584cd6）+ 主检出中迁移后的 base/bridge/frozen-Alpha 层。
- 操作情景：按依赖顺序逐模块编译；一次审计 54 个目标（V03-207 的 38 个 + 完美图分支 14 个 + 2 个终端定理）。
- 预期结果：全部模块编译成功；54 个目标都有审计记录，类型无不符，只出现标准公理；来源接受与查询链完成仍为 false。
- 当前状态：已执行（2026-09-24，用户明确授权本次修订“测试+编译+修复”）。结果：60/60 SUCCEEDED；54 条记录 = 44 定理 + 10 定义，类型无不符（V03-208 的门控实际生效），公理仅 propext/Classical.choice/Quot.sound，65 条组合见证；source_alignment_accepted=false，query_chain_complete=false。证据：`schema v0.3/runs/candidate-compile-20260923/`（SUMMARY.json、compile-attempts/、declaration-audit/）。

### V03-211 / 新代码下历史运行审计（2026-09-24）

- 对象：`audit_research.py`（新增 selector、claim_reference_policy 分支）。
- 准备条件：主检出历史运行只读。
- 操作情景：research-three-paper-20260919 与 research-doi-available-20260922 重建。
- 预期结果：旧计划按旧行为重建，两个运行在新代码下仍 PASS、无 issue。
- 当前状态：已执行（2026-09-24，用户明确授权本次修订“测试+编译+修复”）。结果：两者 PASS、issues []，accepted_support_edges 0。证据：`schema v0.3/runs/v03-revision-evidence-20260924/audit-research-*.json`。另有 audit_candidates（semantic-target-graph-20260919-reviewed）PASS（输出只在临时目录）；audit_proof_walk（proof-worker-normalization-attempt02）在最终代码上 PASS，证据 `audit-proof-walk-attempt02.json`。

### V03-210 / 可选真实 Lean 平凡性探测（2026-09-24）

- 对象：`tests/test_library.py -k real_environment`；`proof_backend` 的逐战术探测。
- 准备条件：`AGTXIV_LEAN_TESTS=1`；prop-v2 冻结环境。
- 操作情景：对 le_refl 和非平凡定理 AgtXIv.GraphFoundation.indep_clique_inter_card_le_one 各跑一次五战术探测。
- 预期结果：le_refl 的 statement_trivially_provable 为 true；非平凡定理为 false（五个探测均留 sorryAx）。
- 当前状态：已执行（2026-09-24，用户明确授权本次修订“测试+编译+修复”）。结果：1 passed（62 deselected，39.16 s）。证据：`schema v0.3/runs/v03-revision-evidence-20260924/pytest-lean-opt-in.txt`。

### V03-209 / schema v0.3 单元测试套件（2026-09-24）

- 对象：`schema v0.3/tests/`（图、候选/V1、研究控制器、库、根调度、审阅/证书、候选路径）与 `host/test_clause_evidence.py`；不调用模型，默认不运行 Lean。
- 准备条件：仓库 `.venv`；旧格式一致性测试使用由提交 b9f6432 生成的冻结 fixtures，不再依赖 git 历史。
- 操作情景：`PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest 'schema v0.3/tests' 'schema v0.3/host/test_clause_evidence.py' -q -p no:cacheprovider`。
- 预期结果：全部通过；唯一跳过项是需要 `AGTXIV_LEAN_TESTS=1` 的真实 Lean 探测（V03-210）。
- 当前状态：已执行（2026-09-24，用户明确授权本次修订“测试+编译+修复”）。结果：72 passed、1 skipped。证据：`schema v0.3/runs/v03-revision-evidence-20260924/pytest.txt`。不覆盖真实模型、真实 Lean 证明尝试或 V03-214 至 V03-219。

### V03-208 / 声明类型门控与分开计数（2026-09-22）

- 对象：`host/candidate_audit.py`；矩阵路线计划中各目标的 expected_kind。
- 准备条件：明确授权执行候选编译/审计或相关测试；具有完整来源、对象及回执的候选包。
- 操作情景：期望定理却返回定义、期望定义却返回定理、非法期望类型、旧计划未声明期望类型、目标缺失、禁用公理、证据拒绝；定义和定理混合的成功输出。
- 预期结果：类型不符为 AUDIT_DECLARATION_KIND_MISMATCH 且不设置 kernel_checked；只对成功核对的记录分别计数定理/定义/其他，失败不得保留成功计数。来源接受数保持零，定义语义和论文证明消解不由计数推出。旧计划缺少 expected_kind 时仍保留原类型，不伪造期望核对。
- 当前状态：代码与计划已修改，仅静态阅读，未执行测试、编译或审计，没有新成功结果。
- 前置阻塞：实际执行授权与共同环境验证尚缺；类型核对不是语义、覆盖或非空性审阅。

### V03-207 / 矩阵容量路线的明确声明审计范围（2026-09-22）

- 对象：`profiles/query-capacity-matrix-route-audit.json`，复用 candidate_sources / candidate_compile / candidate_audit。
- 准备条件：用户明确授权实际编译及声明审计；以 ReducedRoMMatrixDimensionCeiling 为根冻结新源码包，并核对已有共同环境。准备配置本身不是授权。
- 操作情景：按现有依赖顺序编译；只审计计划中的 38 个声明；把定义与定理分开；失败时保留回执，不覆盖旧运行；未选中的共享容量桥接依赖不得计为全部审计；行号定位不能充当声明来源绑定。
- 预期结果：明确记录此替代路线的选定声明、环境、对象与证据边界；只有获准执行后才产生真实编译/审计状态。不得声称达到性、等价、唯一依赖或全篇覆盖。
- 当前状态：只读取既有接口并编写配置，未调用准备、编译或审计函数，没有新源码包或运行回执。
- 前置阻塞：编译/审计授权尚缺；共同环境和全部前置候选仍待执行性验证，精确来源绑定与历史支持接受未完成。

### V03-206 / 规范化窗口定义蕴含正比特数（2026-09-22）

- 对象：`lean/MeasurementWindowDimensionDomain.lean`；容量路线覆盖审阅中的来源范围说明。
- 准备条件：明确授权共同环境 Lean 构建；现有 MeasurementWindow 与 F2Support.coordinateEquiv 定义。
- 操作情景：窗口非空与非零支持联用；n=0 时坐标函数空间只有零元素；固定 n 的最大值存在性与对已给定窗口的全称命题区分。
- 预期结果：从现有定义推出 n>0，不新增正比特数公理；不存在零比特规范化窗口。此结果不决定论文是否允许空测量集合。
- 当前状态：实际读取论文第 114 行非恒等条件、第 763 行非空条件及本地坐标等价；候选源码已写，未编译、测试、校验或调用模型。
- 前置阻塞：共同环境及前置定义未在本轮验证；原文空集合约定与外层最大值定义域仍需来源审阅，不能由此候选自动接受全部范围对应。

### V03-205 / 容量复合命题覆盖与来源路线区分（2026-09-22）

- 对象：`reviews/query-capacity-matrix-route-coverage-20260922.md`、现有 query-perfect-branch-audit 计划和未来声明绑定。
- 准备条件：明确授权声明/来源校验，固定实际 Lean 环境和全文版本；逐条核对命题及证明中的数学声明。
- 操作情景：上界通过但达到性或 iff 未覆盖；新矩阵路线被误归属为原文 F₂ 秩证明；删除唯一依赖节点；n=0 空窗口域下以真空上界冒充最大值存在。
- 预期结果：区分逐态界、容量界、外层最大值、等价、最大集合及唯一依赖；新路线仅提供相应替代支持，保留原文内部节点；n>0 的新增范围在来源审阅中显式记录。
- 当前状态：实际读取原文命题和证明片段、现有候选及计划，完成覆盖表；未执行校验或编译，不形成接受后的声明绑定。
- 前置阻塞：全局 n 的原文约定尚待确认；全部新增 Lean 链未编译，来源接受及复合命题覆盖审计未完成。

### V03-204 / 一般矩阵路线接入带条件的容量上界（2026-09-22）

- 对象：`lean/ReducedRoMMatrixDimensionCeiling.lean` 的团数、逐态 reducedRoM 与 witnessCapacity 三项上界候选，命名空间 AgtXIv.ReducedRoM.MatrixRoute。
- 准备条件：明确授权共同环境构建；一般单位族和 Pauli 团链可用；容量桥接所需 NoActiveDependencies 与 IsPerfect 条件。
- 操作情景：最大团存在性将逐团上界转为 cliqueNum 上界；自然数界转实数并取平方根；容量及逐态结论保留两个数学前提；不导入旧 F₂ 上界作为本路线的证明。
- 预期结果：矩阵路线实际到达带条件的容量上界，不省略假设、不声称达到上界或最大值等价；独立声明命名保留两条路线的来源区别。
- 当前状态：源码已写并静态对照旧容量桥接，未编译、测试、校验或调用模型，无新增验证回执。
- 前置阻塞：全部相关候选尚未编译；原文复合声明包含的达到性和等价方向不能由上界单独覆盖；精确源条款绑定、历史来源接受与全链证书仍未完成。

### V03-203 / MeasurementWindow 的 Pauli 团接入一般矩阵界（2026-09-22）

- 对象：`lean/PauliCliqueMatrixBound.lean` 的 observableUnit、observable_matrix_anticommute、indexed_noncommuting_family_bound、clique_card_le_two_mul_add_one。
- 准备条件：明确授权共同环境 Lean 构建；实际 MeasurementWindow、Pauli 库及 V03-202 全部依赖可用，版本与声明来源固定。
- 操作情景：用 observable²=1 构造真正矩阵单位；通过 Pauli 乘法和取负的矩阵表示将不对易转换成反对易；团的有限索引重排保持不同成员；空团和任意选取的非对易子族。
- 预期结果：无需额外提供矩阵可逆性或反对易证书，直接从窗口条件和团关系得到 Q.card≤2n+1；与旧 F₂ 路线并存但不混淆来源或验证回执。
- 当前状态：候选源码已写，仅读取窗口定义、旧团证明与保留的 Quantumlib 适配源码；未编译、测试、校验或调用模型，无新增内核证据。
- 前置阻塞：本文件及一般单位族链均未编译，共同环境适配仍需确认；容量入口及原文声明绑定、来源链接受和证书生成仍未完成。

### V03-202 / 矩阵单位族的 2q+1 上界候选（2026-09-22）

- 对象：`lean/AnticommutingMatrixBound.lean` 的 even_family_dimension_bound 与 family_card_le_two_mul_add_one。
- 准备条件：明确授权固定环境 Lean 构建，V03-201 及全部依赖可编译；域中 2≠0；输入为实际矩阵单位，矩阵阶数非零。
- 操作情景：偶数 m 的 2^m≤N²；任意 r 的 2^q 阶矩阵族；若 r>2q+1 则取前 2q+2 个；Fin.castLE 单射保留不同指标；q=0、r=0 和空子族边界。
- 预期结果：由真实单位族独立性和矩阵空间维数推出上界，避免将一般非零矩阵误认为可逆；奇偶 r 统一处理，无需增补斜转置、Hermitian 或平方标量假设。结果不代表 query 图关系已经满足反对易前提。
- 当前状态：候选源码已写，仅阅读本地有限索引和维数 API，未编译、测试、校验或调用模型，无新增内核证据。
- 前置阻塞：前置链与本模块均未执行；Pauli 的矩阵单位构造、图关系到反对易的对应、来源语义绑定与全链证书仍需完成。

### V03-201 / 实际反对易单位积的独立性与代数维数界（2026-09-22）

- 对象：`lean/AnticommutingOrderedProducts.lean` 的 full_exponent_eq_code、conjugate_orderedProduct、orderedProducts_linearIndependent、two_pow_le_finrank。
- 准备条件：明确授权 Lean 构建；V03-194 至 V03-200 相关前置模块；非零代数、偶数生成元、域中 2≠0，维数界另要求有限维。
- 操作情景：finRange 列表和转全体 Fin 指标和；删除共轭指标的项在模 2 中等于总和加自身；真实单位积实例化联合特征向量条件；支持向量个数为 2^m；空族维数界。
- 预期结果：独立性结论直接由实际单位及反对易关系推出，不再额外假设 hEigen 或分离算子存在性；由线性无关性得到 2^m≤finrank。不得将未编译源码计入证明成功或来源接受。
- 当前状态：候选已组装并读取本地 Fin.sum_ofFn 与维数 API，未编译、测试、校验或调用模型，无新增内核证据。
- 前置阻塞：全部前置候选仍未运行；矩阵空间实例化、任意奇偶生成元数和 N=2^q 的算术连接、query 对象对齐仍需完成。

### V03-200 / 实际有序单位积的非零性与共轭指数（2026-09-22）

- 对象：`lean/AnticommutingOrderedProducts.lean` 的 factor、unitWord、orderedProduct_ne_zero、conjugate_unitWord_exponent。
- 准备条件：明确授权固定环境 Lean 构建；域上的非零含幺代数及实际单位生成元，保留不同指标反对易关系。
- 操作情景：空列表、支持位为零、共轭指标在/不在所选因子中；列表顺序与重复指标；符号乘积转换为 ZMod 2 指数和；非零性不能套用于零代数。
- 预期结果：用单位群中的顺序乘积定义实际元素并得到非零性；从反对易关系证明逐因子和整列表的共轭公式，无需斜转置或平方为标量；不能误用交换乘积重排矩阵因子。
- 当前状态：候选源码已写，仅读取本地 Units 非零性接口，未编译、校验、测试或调用模型，无内核证据。
- 前置阻塞：仍需把 finRange 上的排除自身指数和化为 code x i，才能消去 V03-199 的 hEigen 实例化缺口；矩阵维数与 query 条款连接仍缺。

### V03-199 / 模 2 指数到域中特征值的连接（2026-09-22）

- 对象：`lean/AnticommutingSignCharacters.lean` 的 sign_injective、sign_add、distinct_supports_have_distinct_sign、linearIndependent_of_code_eigenvectors。
- 准备条件：明确授权 Lean 构建；同一固定环境的 V03-197/198 候选；域 K 满足 (2 : K)≠0。
- 操作情景：ZMod 2 的两个值；符号加法转乘法；特征 2 时不能使用单射结论；偶数及空生成元族；给定真实共同特征向量关系后推出独立性。
- 预期结果：不同指数得到不同 ±1 特征值，并接到联合特征值独立性候选；不得将 hEigen 参数解释为实际有序单位积已满足共轭公式。
- 当前状态：连接源码已写，仅阅读本地 ZMod API，未编译、测试、校验或调用模型，无内核证据。
- 前置阻塞：实际单位生成元的有序子集积、非零性及其 hEigen 公式仍未实例化；维数及 query 的矩阵对应仍缺。

### V03-198 / 偶数生成元的模 2 符号模式分离（2026-09-22）

- 对象：`lean/AnticommutingParityPatterns.lean` 的 sum_code、code_involutive、code_injective 与 distinct_supports_have_distinct_exponent。
- 准备条件：明确授权固定环境的 Lean 构建；m 为偶数，支持向量类型为 Fin m → ZMod 2。
- 操作情景：m=0；任意偶数 m；两次总奇偶加坐标变换恢复原向量；不同支持有不同指数坐标；不得去掉偶数条件推广到奇数维。
- 预期结果：通过偶数 m 在 ZMod 2 中为零，证明编码为对合并因此单射；不依赖 Pauli 专用结构。此结论只分离模 2 指数，尚不自动得到任意特征非 2 域中的不同特征值。
- 当前状态：候选源码已写，未编译、测试、校验或调用模型，无新增内核证据。
- 前置阻塞：仍需从实际子集有序乘积建立共轭指数公式，以及从 ZMod 2 的不同指数得到目标域中不同的 ±1 特征值，再实例化 V03-197。

### V03-197 / 从不同联合特征值构造分离算子（2026-09-22）

- 对象：`lean/JointEigenvalueFilters.lean` 的 exists_finite_separator 与 linearIndependent_of_distinct_joint_eigenvalues。
- 准备条件：明确授权固定环境 Lean 构建；同一向量族对全部算子都是特征向量、不同向量有不同联合特征值模式、各向量非零。
- 操作情景：空目标集合、目标中包含保留向量、加入一个待消去向量、特征值差归一化、已消去向量在后续复合中仍为零；空或单元素有限向量族。
- 预期结果：用特征值差的逆构造正规化滤子，以有限集合归纳真正得到分离算子，再推出线性无关性；不把分离算子存在性作为额外假设，也不要求所有算子在全空间交换。域结构用于除以非零差。
- 当前状态：新增候选证明源码，未运行 Lean 或其他验证，未产生内核证据。V03-196 的具体构造缺口仅在源码层补齐。
- 前置阻塞：既有辅助定理及新归纳代码均未编译；反对易单项式的非零性、偶数生成元的联合符号模式分离及矩阵维数连接仍需实例化，来源对齐未接受。

### V03-196 / 联合特征值的有限消项算子候选（2026-09-22）

- 对象：`lean/JointEigenvalueFilters.lean` 的 filter_eigenvector、word_eigenvector、linearIndependent_of_separators。
- 准备条件：明确授权固定 Lean/mathlib 环境的构建；域上向量空间与各算子的特征向量关系。
- 操作情景：空算子列表、重复算子、不同顺序；算子无需在整个空间交换；有限关系中按指标消去其他向量；零向量不能进入独立族。
- 预期结果：固定顺序复合在共同特征向量上等于标量差乘积；确有逐向量分离算子时得到线性无关性。不能把条件性的 separators 参数当成已经从反对易族构造出的对象。
- 当前状态：候选源码已写，仅读取本地特征向量与线性无关性 API，未编译或执行验证，无内核证据。
- 前置阻塞：仍需由不同联合特征值选择有限消项因子、证明目标乘积非零并正规化，进而构造 separators；偶数生成元的符号模式分离及 query 维数连接尚缺。

### V03-195 / 一般单位族独立性到 query 维数界的分步证明草案（2026-09-22）

- 对象：`reviews/anticommuting-unit-independence-proof-draft.md` 的步骤〈1〉至〈5〉及后续尚缺的 Lean 连接。
- 准备条件：明确域的特征非 2、非零含幺结合代数、偶数个单位生成元；矩阵维数推论另要求有限维。后续执行需要授权。
- 操作情景：空生成元族；互补子集与偶数条件；实际单位逆；消去算子按固定顺序复合；奇数族删去一个成员；N=2^q；Pauli 图关系不能直接替代反对易矩阵关系。
- 预期结果：先证明联合符号模式区分子集，再消去有限关系的其他项，得到独立性和 2^m≤N²，最后推出 r≤2q+1；不引入整个算子族交换性、平方为标量或斜转置等额外假设。准确记录尚缺的 query 实例化。
- 当前状态：完成书面数学推导并阅读现有共轭候选；没有执行数学验证、Lean、测试或模型。不是原始文献逐字证明或已接受来源对齐。
- 前置阻塞：子集计数、模式分离、消去算子、独立性和维数界尚无完整 Lean 实现；已有代码未编译。Robert/Shapiro 的来源对应与最早出处仍未闭合。

### V03-194 / 一般可逆反对易族的共轭与关系保持候选（2026-09-22）

- 对象：`lean/AnticommutingUnitConjugation.lean`；对应 Robert 来源记录中的 robert-general-inverse-conjugation 义务。
- 准备条件：明确授权 Lean 构建和声明审计，记录固定环境；完成来源语义比对。
- 操作情景：单位元的实际逆参与共轭；同指标因子不变、不同指标因子变号；列表乘积保持顺序并允许重复指标；通过代数上的线性映射保持有限线性关系。
- 预期结果：无需假设 B²=-I、普通斜转置或生成元数等于矩阵阶数减一，即可得到共轭公式；各假设与目标类型明确。不得把乘积公式当成平方自由乘积的线性无关性，更不能据此直接推出 2q+1 容量上界。
- 当前状态：候选源码已写，仅阅读本地 Units/LinearMap API 与现有容量候选；未编译、测试、校验或调用模型。原 bridge-obligations 状态不改为完成。
- 前置阻塞：偶数生成元的符号模式分离、线性无关性与有限维数界仍缺；特征非 2 与非平凡代数条件需要在后续独立性定理中明确。来源与查询图对齐仍未接受。

### V03-193 / 三个 Hurwitz 构造的双线性存在性封装（2026-09-22）

- 对象：`lean/Hurwitz1898Bilinear.lean` 的 bilinear2/4/8、对应 apply/squareSum 定理与 exists_bilinear2/4/8_composition。
- 准备条件：明确授权 Lean 构建和声明审计；V03-192 的前置模块在同一固定环境编译；转录及源条款范围经审阅。
- 操作情景：两参数各自的加法和数乘保持性；嵌套 LinearMap 的求值与原显式公式相等；存在性结论通过真实构造及平方和定理得出；定义构建与最终定理分别审计。
- 预期结果：四条线性律作为证明义务解决，不作为新增假设；最终存在性结论给出双线性映射且满足平方和复合。仍不证明任意非退化二次型的约化、其他维数排除、B-system 等价或查询容量链闭合。
- 当前状态：源码已写，仅静态阅读本地 LinearMap 定义与前置候选；未编译、校验或运行模型，没有内核证据。
- 前置阻塞：执行授权与前置候选验证尚缺；共同环境/source alignment 尚未完成。V03-192 的双线性封装缺口已在源码层补齐，但不能据此宣称存在性已验证。

### V03-192 / Hurwitz 构造矩阵与平方和复合的 Lean 候选（2026-09-22）

- 对象：`lean/Hurwitz1898Constructions.lean`，命名空间 AgtXIv.Hurwitz1898；matrix2/4/8_row_gram、matrix2/4/8_column_gram、composition2/4/8_squareSum 共九项候选定理。
- 准备条件：明确授权指定范围的 Lean 构建与声明审计；选择并记录实际 mathlib/Lean 环境；独立核对原刊矩阵转录。
- 操作情景：逐个矩阵的行与列 Gram 恒等式、z=Ay 的平方和恒等式；Fin 索引从原文 1 起改为 0 起；8 阶展开资源消耗；转置误用 adjoint；把交换环上的多项式恒等式当成一般域上的分类或排除结果。
- 预期结果：三阶数分别得到普通转置的左右 Gram 恒等式以及实际复合公式，且无 sorry 或新增未证公理；构造定义不能单独充当证明；核对声明真实类型与源条款。即使通过，也只证明这些构造的恒等式，不证明历史排除定理、B-system 等价、Pauli 容量上界或全链闭合。
- 当前状态：源码已写，仅阅读本地 mathlib 声明及项目已有矩阵写法；未编译、运行 Lean 或任何其他验证程序，没有新增内核证据。
- 前置阻塞：执行授权尚缺；共同环境版本、源条款对齐和原刊矩阵转录仍需核对；显式双线性映射封装、一般正规化与查询分支连接尚未实现。

### V03-191 / Hurwitz 存在性构造的逐项转录（2026-09-22）

- 对象：`reviews/hurwitz1898-construction-matrices-20260922.json` 及修订草案中的 d18matrix2/4/8、d18witness2/4/8 和 d18。
- 准备条件：保留 PDF 第 7 页图像；独立核对逐项符号/指标并确定系数结构；执行性验证需明确授权。
- 操作情景：2、4、8 阶矩阵转录错误；将定义当作恒等式证明；遗漏矩阵上方存在性断言的来源定位；仍用排除其他维数支持存在性。
- 预期结果：逐项转录与各阶 A Aᵀ=(Σxᵢ²)I 的证明分开；三个构造各有独立义务；汇总存在性仅使用构造见证，不从排除结论推得；普通转置、系数域和 B-system 对应条件明确。
- 当前状态：实际查看已有 page-007.png，人工转录三个矩阵并改写草案；未重新渲染、运行矩阵计算、校验器、测试、模型或 Lean。全部恒等式仍未验证。
- 前置阻塞：独立转录核对、精确断言定位、恒等式证明及复合恒等式的约定对齐尚未完成；原始恢复授权仍待答复。

### V03-190 / Hurwitz 机器可读修订草案（2026-09-22）

- 对象：`reviews/hurwitz1898-amendment-draft-20260922.json`，以及其 Markdown 来源说明。
- 准备条件：明确授权原响应恢复并取得真实候选报告引用；逐项审阅继承的页面区域、现代域条件和引用迁移后再绑定为正式 proposal。
- 操作情景：18 个旧行的修订/拆分及 8 个未改行；c08/c17 的局部假设和最终排除；c12 一般次数证明缺口；c18 去除不能证明存在性的排除前提；c24–c26 参数桥接；将 original=null 的草案误导入。
- 预期结果：草案外层不能当作正式提案，缺失来源绑定不能伪造；新条款保留审阅与证明缺口，原始模型输出及归属不变；未改条款不被自动接受；完整迁移后才可进入获准的修订准备。
- 当前状态：仅编写 JSON 草案并静态阅读部分引用文字；没有调用宿主、图装配、校验器、模型或 Lean。不是形状校验成功，不是已执行修订。
- 前置阻塞：恢复执行授权仍待答复；原候选引用目前故意为空，精确来源区域、现代条件与数学桥接仍未解决。

### V03-189 / 修订的全文审阅上下文与独立审计入口（2026-09-22）

- 对象：`host/pdf_proof_context.py` 的 amendment_proof_context；`audit_pdf_candidates.py` 的修订运行分支。
- 准备条件：完整正常收尾的修订运行，准确绑定的修订节点，后续明确授权执行。
- 操作情景：修改节点语句/条件/来源/未决项；遗漏原行或上下文；在局部步骤与最终结论之间切换审阅；将修订运行交给普通 source binding、匹配或递归准入；失败/中断运行进入审计。
- 预期结果：重建修订后提供全部来源页、被替换原行、完整提案和结论→局部上下文的真实节点对应；关联不是支持边或假设消解证据。审计只覆盖正常完成的局部完整性。普通递归来源入口仍拒绝修订类型，不因可读取审阅上下文而自动放行。
- 当前状态：接口已写，仅静态阅读，未运行上下文准备、审计、测试、模型或 Lean，没有新增 PASS 或真实修订图。
- 前置阻塞：Hurwitz 原始后处理恢复仍待授权；机器可读修订提案尚缺；递归准入与图发布审计、连续修订和作用域形式化尚未完成。

### V03-188 / 独立 PDF 修订保存与正常收尾重建（2026-09-22）

- 对象：`host/pdf_amendment_run.py` 的 run_amendment / reconstruct_amendment。
- 准备条件：正常 PDF 模型抽取或恢复运行、准确绑定其候选报告的修订提案、新输出目录；明确授权执行。
- 操作情景：原报告与原运行不符、覆盖/嵌入输入目录、已存在输出目录、运行失败或中断；替换提案/候选/来源/上下文关联/装配图；运行代码缺失或漂移；重复修订和未支持的旧手工 PDF 来源类型。
- 预期结果：原运行不变，新目录记录候选、修订归属、图和源码快照；失败保存错误但不能进入完成审计；正常重建核对来源、提案和全部输出，不调用模型或执行历史 Python；没有语义接受、假设消解或递归发布。
- 当前状态：保存与重建 API 已写，仅静态阅读，未调用 API、运行校验/测试/模型或 Lean，没有新的修订运行或图。
- 前置阻塞：实际恢复授权与 Hurwitz 机器可读提案尚缺；修订类型的 proof-context/递归接入、连续修订、失败中断审计尚未实现。源码清单或内容变化时当前重建明确拒绝，不声称支持跨版本重建。

### V03-188 / 结尾八帧的依赖边几何统一与 pptx 复核（2026-09-23）

- 对象：`slides/chain-build/closing.py` 的 `edge()`；`slides/chain-build/deck_core.js` 的 `prims()`→`tx()`；产物 `chain-build-v1.html`、`aqa_talk_924.pptx`。
- 准备条件：`skeleton-geom.json` 不变；后续用户明确授权渲染与校验。
- 操作情景：结尾第 4 帧（29 条自由依赖）与第 5 帧（骨架）此前用直线弦绘制依赖边，而第 0、2、3 帧用贝塞尔曲线绘制同一批边，导致被挑出的边压在任何真实边之上都不重合，整页读成横贯全图的斜线网；`prims()` 另外丢弃了 `mono`、`align`、`italic` 三个文本属性，Lean 代码帧在 pptx 里退化成正文字体，legend 的居中数字变成左对齐。
- 预期结果：四、五两帧的边与其余帧完全同几何（同控制点贝塞尔）；高亮边恰好覆盖它所强调的那条依赖；Lean 代码帧在 pptx 中为等宽字体；legend 数字居中；前端与 pptx 第 57–65 页逐页一致。
- 当前状态（2026-09-23 更新）：边几何统一与 `prims()` 文本属性已改并重建全部产物。**第 57 页（愿望一）做了例外的渲染复核**：用户两次报告该页视觉有问题，而"把这一页改好看"无法闭眼完成，所以转了一次 PDF 并只看了第 57 页；证据为 `qa/n-57.jpg`。该页确认已从 51 个虚构节点减到 26 个、共享 claim 已成为画面主体、右侧原有的两点重叠已消除。**其余 64 页仍未运行校验器、未逐页目视复核。** 改前证据 `qa/s-60.jpg`、`qa/s-58.jpg`、`qa/hi-57*.jpg` 保留不覆盖。
- 2026-09-23 第三次处理：用户报告原生重画仍然失败。改为把结尾第 1 步（愿望一）整帧栅格化后作为图片放到该页——`closing_png.py` 从 `closing.svg` 抽出该 step 组、补回页面样式表里的字体规则、用 rsvg-convert 输出 3840px PNG；`deck_v1.js` 的 `FLAT_CLOSING` 决定哪些 step 走图片路径。该页不再可编辑，这是用户明确同意的取舍。前端不受影响，仍是原生可交互图形。已渲染复核，证据 `qa/n-57.jpg`。
- 未决：结尾第 6、7 步（愿望二、愿望三，第 62、63 页）用同一套 schematic 绘制代码，很可能有同样的 PowerPoint 故障，但用户只授权了第 57 页，暂未栅格化。需用户决定。
- 补充结论：第 57 页在 LibreOffice 下与前端逐像素一致，问题不是渲染保真度而是设计密度——原始四个 schematic 群共 51 个无信息节点，读成毛球。已改为 26 个、间距下限 52→76、节点与共享环加粗。
- 前置阻塞：无。需要的是一次授权的渲染与第 57–65 页目视比对；另有一项未完成的复核是上一轮 65 页整体视觉 QA（并行代理因额度中断，7 个批次全部失败，当时"无缺陷"的结论不成立，不得引用）。

### V03-187 / PDF 局部修订准备与假设泄漏拒绝（2026-09-22）

- 对象：`host/pdf_amendments.py` 的 prepare_amendment。
- 准备条件：冻结的原候选报告引用、绑定原 PDF 的 document、显式 replacements 与 proof_contexts 提案；后续明确授权执行。
- 操作情景：一对多拆分；重复或沿用旧 ID；遗漏受影响入边；以 ID 后缀隐式匹配；断言直接或经局部步骤依赖反证假设；独立证明上下文关联；原报告摘要变化或新来源区域越界。
- 预期结果：不修改原报告；逐边迁移必须显式；拒绝永久支持路径中的假设泄漏；上下文只作为来源关联，不构成消解证据；所有修改行带未决修订标记，结论另带消解未验证标记；既有来源与区域装配约束继续生效。
- 当前状态：新增纯准备 API，仅静态阅读；没有调用此函数、装配图、校验、测试或模型调用。实际 Hurwitz 修订提案尚未构造和执行。
- 前置阻塞：持久化独立修订运行、proof-context 与审计的完整接入尚缺；该返回值不能冒充正常抽取或恢复运行，也不能进入支持匹配与正式图发布；完整作用域消解仍需 Lamport/Lean 证据。

### V03-186 / Hurwitz 局部修订的来源与作用域迁移（2026-09-22）

- 对象：`reviews/hurwitz1898-amendment-draft-20260922.md`；后续尚未实现的修订导入机制。
- 准备条件：原始响应与失败回执保持不变；明确修订记录契约、来源区域及逐边迁移决定；后续明确授权执行。
- 操作情景：一行拆成局部假设、推导和最终结论；现代域条件被误当作原文；旧引用机械迁移；以排除性结论支持存在性；修改 response 后复用旧回执。
- 预期结果：独立保留修订归属；假设只在局部作用域有效，排除结论进入声明清单；新条件和证明缺口持续可见；c18 的存在性要求构造支持；不以修订或结构恢复声称语义接受或 Lean 成功。
- 当前状态：完成内容草案和原响应静态复读，未导入、未执行测试、校验、模型或 Lean，未新增支持边。
- 前置阻塞：现有 review_blocks 只支持匹配行反例异议，不支持抽取修订和作用域拆分；结构恢复授权、精确区域补充及数学桥接仍未完成。

### V03-185 / 历史 PDF 的反证角色、指标与维数提示约束（2026-09-22）

- 对象：`host/pdf_extract.py` 的新调用提示；`reviews/hurwitz1898-response-review-20260922.md` 的实际响应审阅。
- 准备条件：后续明确授权的模型/测试范围；历史响应与来源图像必须保留。不得为此重跑已有整篇抽取。
- 操作情景：反证假设与最终排除结论在同一段；历史不同指标记号；矩阵阶数与矩阵空间维数混用；n=1 平凡情形或域限制缺失；Pauli adjoint 与普通 transpose 混淆。
- 预期结果：新调用提示要求分开假设/断言、区分维数和参数、保留未明范围；不得通过改提示声称旧响应已修复。局部修订需独立记录旧行→新行对应与来源依据。
- 当前状态：只读原始 26 行并实际复看已有 PDF 第 2、3、4、5、6、7、9 页图像；发现 c07、c08/c17、c12、c15 及 c02/c03 范围问题。新提示已改，未调用模型、运行校验或 Lean。来源阅读不是测试通过。
- 前置阻塞：结构恢复仍待授权；审阅尚未作为程序化 review block 入图；局部修订、一般矩阵定理到历史受限系统/Pauli 的桥接仍未完成。
