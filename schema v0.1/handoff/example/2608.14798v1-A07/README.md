# 真实案例：A07 从 Paper 候选交给 Dependency

## 结果

2026-09-15 实际完成一次本地交接，状态为 **DELIVERED**。意思是“本次引用扫描及其产物已交付”，不是“论文通过”或“命题得到证明”。

输入：论文 *Stabilizer Statistical Mechanics: A Framework for Efficient Quantification and Classification of Magic States*，`2608.14798v1`；来自已有 Claude Opus 5 v1.1 提取结果的 `A07-conclusion-1`。本轮没有重新调用 Claude 或其他模型。

目标：原文声称，对纯态有 **Mα(ψ)=0 当且仅当 ψ 是稳定子态**。原提取记录未明确此性质适用的 α 范围；本次没有更改该记录，也没有补造假设。

## 按这个顺序看

1. **[task.json](task.json)**：host 给 Dependency 的工作单。精确固定 7 条输入记录和 3 个可见文本附件。
2. **[findings.json](findings.json)**：下游实际完成的本地搜索。两个原文片段分别出现 2022 年 SRE 定义论文、2024 年 SRE 单调性论文的引用；两个键均在论文自带书目中找到一个匹配。每条保留原文与书目字节位置和哈希。
3. **[search-draft.json](search-draft.json)**：按 Dependency 现有接口输出的后续搜索提案。`records=[]`；尚无依据生成数学依赖记录。提案本身不表示远程搜索已运行。
4. **[result.json](result.json)**：真实执行回执，绑定上述两个产物的原字节哈希。实际执行时间为 `2026-09-15T18:19:34.933572Z` 至 `2026-09-15T18:19:34.950412Z`；这仅是 handler 扫描与输出检查时间，不包括准备、原文提取或完整验证耗时。
5. **[status.json](status.json)**：`READY → RUNNING → DELIVERED`，一次 attempt。另起进程重放后回执完全相同，attempt 数仍为 1。
6. **[manifest.json](manifest.json)**：固定输入及实现哈希，保留完整旧案例失败和本次局部成功的不同范围。

2024 年引用在原文中对应**单调性**，不能直接判定为本次“为零当且仅当”性质的数学前驱。2022 年定义论文是后续优先检查的线索，而不是已经批准复用的节点。

## 哪些保留问题仍然存在

- 原 Paper 全集 433 条记录仍有 **82 个 SELF_REVIEW** 错误，本次没有使整篇交付通过。
- 本次选择的 7 条记录及其 17 个源附件通过了结构、引用闭包和源字节检查。这不认证提取是否忠实，也不认证数学正确性。
- 没有被引论文原文获取、上游 claim 提取、独立适用性审阅、dependency-binding、Lamport proof 或 Lean 4 代码。
- 没有模型 API 调用。执行者为本地程序 `local-citations/1.0`，身份为自报的本地服务，不冒充已认证身份或独立审稿人。

## 验证记录

本轮最终版本实际运行：

| 检查 | 结果 |
|---|---|
| 新增交接测试 | 28 项通过 |
| 原有 orchestration 契约测试 | 28 项通过 |
| 原有 Paper Agent 接口测试 | 25 项通过 |
| 原有 Autoformalization Agent 接口测试 | 64 项通过 |
| `validate.py --check` | 通过；仍是离线契约检查 |
| 本例 Task/Result 的独立契约检查 | 通过 |
| 本例源记录/原始字节重新验证、结果附件哈希读回 | 通过 |
| 另一个进程读取已完成任务 | 同一 Result、同一 attempt，无重复扫描 |

合计 **145 项相关测试通过**，不是整个仓库所有测试或科学验证通过。测试里的故障注入全部位于临时目录，不修改本例、原 Paper 记录或源码。

## 继续运行

本目录的 `handoff.sqlite` 是本地运行库，约 16.2 MB，保存输入记录、17 个原附件、工作单、事件和输出。它被本目录上层的 `.gitignore` 排除，不是已提交的 Git 数据批次；这里的 JSON 也是本次运行的检查出口，不是符合 `archive-batch` 的完整封存包。

在仓库根目录：

```bash
.venv/bin/python -B 'schema v0.1/handoff/handoff.py' status --run-dir 'schema v0.1/handoff/example/2608.14798v1-A07'
.venv/bin/python -B 'schema v0.1/handoff/handoff.py' run --run-dir 'schema v0.1/handoff/example/2608.14798v1-A07'
```

若运行库不在当前机器，或代码/接口已经改变，请按[交接说明](../../README.md)在新目录重建运行，不覆盖本例的旧回执。

下一步只需继续一条线：**获取 2022 年被引论文 → 找出对应的真实上游 claim → 独立比较定义和 α 范围 → 决定能否建立依赖**。
