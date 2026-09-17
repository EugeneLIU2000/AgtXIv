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

本轮状态：只新增规范/schema/人工样例并做静态阅读；**没有执行测试、示例、模型调用、依赖安装、Lean、数据库或 Neo4j 操作**。v0.2 宿主实现是下一步工作，不由本清单或旧 PASS 自动补齐。
