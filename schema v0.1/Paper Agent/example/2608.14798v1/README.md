# Paper Agent 实例：arXiv 2608.14798v1

论文：[Stabilizer Statistical Mechanics: A Framework for Efficient Quantification and Classification of Magic States](https://arxiv.org/abs/2608.14798v1)。处理日期：2026-09-13。

**已完成真实取源、分段阅读、候选提取和本地装配；没有严格通过当前 AGENT.md 的 S0–S5。** 你的 AGENT.md 和旧 schema 均未修改。

## 先看这三个文件

1. [主张阅读版](output/claims.md)：逐项查看作者主张、条件、数学表达、原文位置和缺口。
2. [机器记录](output/records.json)：241 条现有 v0.0 格式记录；包括未获接受的候选对应关系，不可当作已准入知识导入。
3. [接口检查](spec-review.md)：规范哪些地方阻止严格执行，以及本次如何保留真实结果而不补造批准。

## 得到了什么

| 产物 | 数量 | 状态 |
|---|---:|---|
| 作者主张 ScientificClaim | 33 | 分段阅读后提取的候选，部分仍合并了相关子主张，不是全文原子化主张总数 |
| 数学目标 MathClaim | 9 | 有结构化量词与条件；未证明、未形式化 |
| 定义 Definition | 5 | Pauli 谱、nullity、稳定子熵、配分函数、核心配分函数；不是全部定义 |
| 语义背景 SemanticContext | 33 | 保留公式、适用条件、解释和未解决范围 |
| 原文定位 SourceSpan | 89 | 对实际 TeX 字节范围及指纹绑定 |
| 对应关系 ClaimComponentMap | 33 | 全部 PARTIAL/RESIDUAL；完整包校验拒绝其生产者自审归属 |
| 开放问题 FrontierItem | 33 | 未解决；不是对论文的正式否定结论 |
| 来源文件 | 16 | 全部保留；图像、数值、外部引用未被验证 |

其余 24 项不强行生成 MathClaim，表达保留在语义记录和种子文件中。原因包括量词尚未细化、一个候选合并多个结论、系综与单态混用、参数端点未定义等。种子中的 `math_extractable=true` 只是分段执行者提出的可数学化建议，不保证最终已经生成 MathClaim；实际状态以 `output/handoff-requests.json` 的 `math_ref` 为准。

## 实际校验结果

- 241 条记录各自的 JSON Schema 格式通过。
- **完整 RecordSet 未通过**：33 条对应关系触发 `SELF_REVIEW`。虽然标了 `UNESTABLISHED`，现有校验器仍要求不同审阅主体。本次没有换一个假的 reviewer ID 来消除错误。
- 明确移除未审阅对应关系后的 **208 条诊断子集**通过引用与字节检查。它不替代完整 Paper 输出，也不代表科学有效。
- 精简 Plan 对旧 schema 的校验失败；失败原因保存在 [Plan 校验](output/plan-compatibility-check.json)。完整旧格式 Plan 仅是未签名、未采用的兼容性试样，不是悄悄替换你的规范。
- 候选清单包含 16 项文件阅读义务及 33 项主张审阅义务，共 49 项；全部保留开放状态，**没有冻结分母**。

详见 [validation.json](output/validation.json) 和 [manifest.json](output/manifest.json)。`diagnostics/initial-validation-run/` 保留第一次装配的失败输出；已修复其中的可见引用登记错误，未绕过自审限制。

## 这篇论文暴露出的有用边界

以下是值得后续审阅的问题，不是本轮已经证伪的结论：

- 作者明确 SPF 打包的是 Clifford 不变的偶数统计量，不能将它说成保留完整带标签的有符号 Pauli 谱。
- 摘要的高温极限表述与正文“leading-order function of M2”的强度不同；应保留差异，不自动统一。
- Bell 采样结果需要区分归一化对象、固定截断阶、beta、截断余项以及实际状态拷贝资源。
- 可压缩系综的平均值公式不能无条件当作任意单个掺杂态的精确公式。
- 稳定子功在 beta=0 的比值端点、纯态协议与一般混态操作的区别需要单独处理。

本次仅记录引用线索；没有获取或审查所引历史论文，也没有生成已验证的数学依赖边。

## 输入和执行证据

- [下载记录](acquisition.json)：固定 `2608.14798v1`，包括源压缩包和 16 个文件的 SHA-256。
- 原始压缩包与 TeX 在仓库 `Reference/Stabilizer Statistical Mechanics - A Framework for Efficient Quantification and Classification of Magic States/` 下。源文件没有编译或执行。
- [前部主张种子](claims-foundations.json)、[系综部分种子](claims-ensembles.json)、[功／应用／附录种子](claims-work-applications.json)：本次真实 agent 阅读后的提取输入，不是合成论文结果。
- 主执行者阅读前部正文；分段 agent Rawls 阅读 731–1174 行及必要前置定义；Plato 阅读 1175–2723 行。Leibniz 对接口冲突和结果表述进行独立检查。它们不是独立的数学证明核验或正式签名。
- 运行中没有实施可信身份认证、外部模型 API 计费测量或实际预算调度。旧格式 Plan 的零费用字段不表示本次消耗为零。

## 怎样复运行

在仓库根目录运行保存结果的回读检查：

```bash
.venv/bin/python 'schema v0.1/Paper Agent/example/2608.14798v1/validate_example.py'
```

退出 0 表示预期的成功项和阻塞项均复现，不表示完整包通过。

重新装配到一个不存在的新目录：

```bash
.venv/bin/python 'schema v0.1/Paper Agent/example/2608.14798v1/build_example.py' \
  --output 'schema v0.1/Paper Agent/example/2608.14798v1/replay-01'
```

当前预期退出 2，并保留全部输出和 33 个自审错误。**这个命令不调用模型：它重放本次已保存的提取结果，不是对新论文自动提取，也不是再次独立读论文。** 不覆盖旧目录；每次装配使用不同运行身份段，避免内容变化覆盖旧记录。

正式的 Proof／Dependency 配对任务、Result 执行回执、FrozenScope 和发布清单均未伪造；本次保存的是 [后续请求](output/handoff-requests.json)，其中 `formal_tasks_created=false`。下一步应先决定如何协调精简 Plan、义务与主张的区别，以及候选对应关系与独立审阅的责任边界。
