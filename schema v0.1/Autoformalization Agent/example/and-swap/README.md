# 从一句话，到分步证明，再到 Lean 4

这是人为构造的教学例子，不是论文提取结果，也不是已登记的正式证明包。

## 1. 输入：同一个数学问题

示例原句：“P 和 Q 都成立，那么交换顺序，Q 和 P 也都成立。”

数学目标：对任意命题 P、Q，证明 `P ∧ Q → Q ∧ P`。没有增加其他假设。直觉是：从装有两份证明的盒子中各取一份，再按相反顺序装回去；没有凭空制造新证据。这里是逻辑命题，没有额外的物理模型。

原句没有写详细证明，下面拆分的步骤标为 `RECONSTRUCTED`，不能冒充作者原文。P、Q 是任意参数；`h : P ∧ Q` 是为了证明蕴含而临时引入的假设，不回写成 Paper Agent 新增的适用条件。

## 2. 接口 A：Lamport 风格的分层证明

```text
1. GOAL：对任意 P、Q，证明 P ∧ Q → Q ∧ P。
   1.1 GOAL：在局部假设 h : P ∧ Q 下，证明 Q ∧ P。
       1.1.1 ASSUME：h : P ∧ Q。
       1.1.2 STEP：Q。BY 1.1.1，取合取的右分量。
       1.1.3 STEP：P。BY 1.1.1，取合取的左分量。
       1.1.4 QED：Q ∧ P。BY 1.1.2 和 1.1.3，合取引入。
   1.2 QED：P ∧ Q → Q ∧ P。解除 h；P、Q 始终任意。
```

最容易漏的是最后一行：`Q ∧ P` 只在假设 h 下成立；完成整个题目还需要解除这个假设，得到原来的蕴含。

保存时，“Q”“P”“Q ∧ P”各是一个节点；“同时使用 Q 和 P 得到 Q ∧ P”是一个推理记录。该推理的 `premise_refs` 必须同时含两个节点，不能写成“Q 单独推出 Q ∧ P”。局部假设单独放在 assumption-context；层级编号只负责阅读。

| 草稿／视图 | 演示内容 |
|---|---|
| `proof-context.draft.json` | 第一轮：提出局部假设范围 |
| `proof-nodes.draft.json` | 第二轮：提出目标、假设、Q、P、Q ∧ P 五个节点 |
| `proof-draft.json` | 第三轮：用测试占位引用模拟前轮已登记的节点，提出四条推理 |
| `lamport-view.json` | 在路线与快照登记后，给相同节点安排阅读层级 |

所有 `fixture:and-swap-*` 引用及重复的 `sha256:aaaa…` 都是明确的测试占位引用，不是真实哈希或入库凭证；实际流程须每轮保存后取得真实引用，再构造下一轮 Task。节点草稿顺序对应 target、h、q、p、qp；推理顺序对应 right、left、and-intro、discharge。这是例子中的说明，不是允许模型指定存储身份。

本例未制造源文档、MathClaim、frozen-scope、plan、snapshot、packet 的业务封套，也未制造 Task／Result；因此只能用于局部接口检查，不能通过完整 RecordSet 引用闭包或独立执行验证。

## 3. 接口 B：固定目标，生成 Lean 4

完整源码见 [AndSwap.lean](AndSwap.lean)。核心代码为：

```lean
theorem and_swap (P Q : Prop) : P ∧ Q → Q ∧ P := by
  intro h
  have hq : Q := h.right
  have hp : P := h.left
  have hqp : Q ∧ P := And.intro hq hp
  exact hqp
```

`intro h` 在蕴含证明内部引入假设；`h.right`／`h.left` 对应拆分；`And.intro hq hp` 同时消费两个前提。整个 `by` 证明最终返回原来蕴含的证明，而不是把 h 变成额外的全局要求。

`lean-draft.json` 同时保存完整源码与对应表：TARGET 对应外层目标；h、hq、hp、hqp 分别对应局部步骤。外层假设解除由整个证明项表达，不强求存在单独一行“discharge”代码。

在真实流程中，`AutoformalizationExample.and_swap` 必须在生成代码之前写入 packet.expected_declarations，而不是看代码生成了什么就接受什么。例子中的 packet_ref 仅是上述测试占位引用。

## 4. 怎样检查这个例子

在仓库根目录执行，重复 `--kind proof` 可检查前两份草稿：

```bash
.venv/bin/python -B 'schema v0.1/Autoformalization Agent/check_interfaces.py' --kind proof --input 'schema v0.1/Autoformalization Agent/example/and-swap/proof-draft.json'
.venv/bin/python -B 'schema v0.1/Autoformalization Agent/check_interfaces.py' --kind view --input 'schema v0.1/Autoformalization Agent/example/and-swap/lamport-view.json'
.venv/bin/python -B 'schema v0.1/Autoformalization Agent/check_interfaces.py' --kind lean --input 'schema v0.1/Autoformalization Agent/example/and-swap/lean-draft.json'
lean +leanprover/lean4:v4.30.0-rc2 'schema v0.1/Autoformalization Agent/example/and-swap/AndSwap.lean'
```

最后一条命令使用本机已有版本；本目录不安装或升级工具链。源码末尾打印实际声明和公理依赖。实际运行结果见 [validation-report.json](../../validation-report.json)。

格式检查通过，只说明草稿满足已实现的约束；运行 Lean 则检查这段真实代码。两者都不自动产生正式独立 formal-check，也不证明系统已经能对任意论文自动完成全过程。
