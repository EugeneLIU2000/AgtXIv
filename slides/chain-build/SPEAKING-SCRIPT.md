# chain-build.html — 逐帧讲解与完整演讲稿
> **索引已于 2026-09-21 重新编号。** 本稿原为 41 帧的版本所写；其后在最前面插入了
> `Slide_001.pptx` 的 27 帧与 1 帧过渡帧，因此全部帧号已整体 +28。当前成品为 69 帧，
> 本稿覆盖帧 28–68；帧 0–27 为导入的开场，不在本稿的时间预算内。


**准备日期：** 2026-09-21（讲座前一天）
**对象：** `slides/chain-build/chain-build.html`，69 帧，7 段（帧 0–27 为导入的 Slide_001.pptx + 过渡帧；本稿覆盖帧 56–68）
**数字口径：** 本文每一个数字都在 2026-09-21 对 `schema v0.3/` 的实际产物复核过。核对结果见 §5。
**语言：** 讲解用中文；**讲稿正文是英文**，因为幻灯片上的 meter、图注和 deck 内置 speaker notes 全是英文，听众是物理/数学同行。需要中文稿可以再说。

---

## 0. 这份稿子怎么用

deck 里已经有 speaker notes（写在 `motivation.py`、`pipeline.py`、`deck.js`、`closing.py` 的 `NOTE` 数组里）。本文做三件那些 notes 没做的事：

1. **串成一篇连续可讲的稿**，补上五段之间的转场——notes 是按帧写的，帧与帧之间没有话。
2. **给每帧标出 v0.3 出处**，这样被追问"这个数哪来的"时，你能直接报文件名。
3. **标出时间预算和哪几句必须说**——69 帧不可能每帧都讲一分钟。

**三条贯穿全场的规矩**（deck 自己定的，讲的时候别破）：

- **一个例子，永不离开**：arXiv:2607.26154v1。
- **暖色 `#8C4A2F` 只有一个意思：NOT FROM THIS PAPER。** 不要在口头上让它兼任"坏的"或"待办的"，一旦兼任，听众就读不懂这个颜色了。
- **虚线环 = root，下面什么都没有；实心 = 形式化顺序能到达。** 同理，别临时赋予第二重含义。

---

## 1. 全局结构与时间预算

| 段 | 帧 | 内容 | 建议时长 | 节奏 |
|---|---|---|---:|---|
| **A 动机** | 28–35 | 为什么一篇论文需要依赖图 | 11 min | 慢，每帧一个论点 |
| **B 流水线** | 36–42 | 整套系统五个盒子 | 5 min | 快，40 秒一帧 |
| **C 记录与图** | 43–49 | 单条记录长什么样 → 抽取图 → 人写的 DAG | 9 min | 中 |
| **D 链条构建** | 50–60 | 29 条 claim 一层层长出来 | 8 min | 22–29 极快（动画），30–32 慢 |
| **E 结尾** | 61–68 | 三个愿望 + 一个测量 | 10 min | 慢，35–38 是全场技术高点 |
| Q&A | — | | 4 min | |
| | | | **47 min** | |

**如果超时，砍这几帧**：34（library）、52、54、55（链条中段三帧纯动画）。**绝不要砍**：31（46 of 54 conditional）、47（9 of 9）、20（change of object）、37（redundancy trap）、32（CHAIN_INCOMPLETE）。

---

## 2. A 段 · 动机（帧 28–35，11 分钟）

### 帧 28 — ONE RESULT · AND THE SPACE UNDERNEATH IT

**屏幕：** 画面正中一个大菱形（theorem），下方一条浅灰横线，线上标 "where it came from"。中间大片空白。

**出处：** 无数字。这是全场的姿态帧。

> I am not here to tell you the machine is wrong. Take the diamond as given — it arrived, it is probably right, and arguing with it is not my talk.
>
> Everything I am going to say is about the space underneath it, and about that grey line at the bottom, which is where it came from. When a result arrives with nothing between it and its sources, there is nothing for a reader to do except believe it or not. That is a new situation for us. It is not that the answer is suspect. It is that the answer is the only thing we were handed.
>
> Hold that empty region in mind. The rest of the talk is an attempt to put something in it.

⏱ 45 秒。**说完停两秒再翻页。**

---

### 帧 29 — 6 LINES OF ANSWER · 7,765 LINES OF GROUND

**屏幕：** 左框 "6 lines / one model call / 21 seconds" 加六条短线；右框 "7,765 lines / written by hand, so that six citations could be used" 加一个实心黑块。

**出处：** 左 = `runs/proof-worker-normalization-attempt02-20260919/`（1 次模型调用，21.4 秒）。右 = `formal/AgtXIvRootMath`，55 个文件 7,765 行。

> The inversion, and it is the most surprising thing I found in my own logs.
>
> On the left: the one piece of Lean in this project that a model wrote and a kernel accepted. Six lines. One model call, twenty-one point four seconds. You will see that proof itself later, with its caveats attached — for now only its size matters.
>
> On the right: seven thousand seven hundred and sixty-five lines of Lean, written so that six citations in one paper could be used at all. Definitions, bridges, the statements of things the paper simply cites.
>
> The drawing is not to scale. The true ratio is about thirteen hundred to one.
>
> Note what that means for the usual worry. The worry is "who will check the ten thousand lines the AI wrote". In this project the AI wrote six. The ten thousand lines are the theory-building that had to happen first — and that is the work nobody gets credit for, because it is not an answer to anything.

**如果被追问 "written by hand" 的含义**：authored rather than model-generated。这个包里有文件被后面 32 条 source adaptation 中的 25 条动过，所以不是"没人碰过"，是"不是自动形式化出来的"。

⏱ 1 min 30 s。

---

### 帧 30 — 213 SUPPORT GROUPS · 0 REVIEWED BY A PERSON

**屏幕：** 213 根细竖线排成一道横向的场；下方一个巨大的 "0"。

**出处：** `runs/research-terra-continuation-20260920/summary.json`：`support_groups: 213`、`accepted_support_edges: 0`、`all_judgements_unreviewed: true`。71 分钟来自全部 ledger 的 `elapsed_seconds` 合计（4,277.5 s）。

> The asymmetry — measured, and measured on my own work rather than asserted about the field, because I cannot measure the field and neither can anyone who has tried.
>
> Seventy-one minutes of model time produced this: six hundred and thirteen claim nodes and two hundred and thirteen support groups, extracted from one paper. Each of those two hundred and thirteen is a proposal that some set of claims, taken together, discharges another claim.
>
> The number underneath is the point. `accepted_support_edges: 0`. `all_judgements_unreviewed: true`. Not one of them has been looked at by a person.
>
> That is the shape of the whole problem, in two numbers from one repository. Producing candidate structure is now minutes of machine time. Reviewing it is unchanged — it is a person reading, at the speed a person reads. Nothing in this project makes review faster, and I want to be honest that it does not. What it changes is that the unreviewed thing is now a small, enumerable, addressable list instead of a paragraph of prose.

⏱ 1 min 30 s。**这是 A 段最重要的一帧。**

---

### 帧 31 — 54 KERNEL-CHECKED THEOREMS · 46 OF THEM CONDITIONAL

**屏幕：** 54 个小菱形排成一行，前 46 个各垂一条短线向下。

**出处：** `runs/lean-evidence-20260919/lean-audit.json`，`coverage[2]`。64 条 kernel-checked（54 theorem / 9 definition / 1 inductive），公理只有 `propext`、`Classical.choice`、`Quot.sound`。`PREMISE_NONVACUITY_UNKNOWN` = 46 / 54。

> What a kernel-checked "yes" actually means.
>
> This project has sixty-four kernel-checked declarations — fifty-four theorems, nine definitions, one inductive — resting on exactly three axioms, and no axiom the project introduced. That part is real, and it is machine-verified.
>
> Now the honest part. The audit's own metric, `PREMISE_NONVACUITY_UNKNOWN`, is forty-six of fifty-four. Forty-six of those theorems carry at least one hypothesis whose inhabitation Lean does not establish. The kernel confirms the implication. It does not confirm that the premise can ever be met — and a vacuously true theorem looks identical to a useful one from the outside.
>
> I want to be careful here: this is not a flaw in Lean, and it is not fraud. It is what "verified" means, stated precisely.

⏱ 1 min 15 s。**不要砍这一帧**——这是全场对"形式化验证"最诚实的一句话，也是你后面所有 caveat 的信用来源。

---

### 帧 32 — 82 OF 82 MODULES COMPILE · THE ANSWER IS STILL EMPTY

**屏幕：** 顶部一个空框，标 "the answer"；下方 82 个小实心条排成网格。

**出处：** `epoch-migration/runs/20260919-full-case/full-case-audit.json`：82/82 模块在 `leanprover/lean4:v4.33.0` 下编译通过，74 条声明审计，44 条 composition witness，`query_chain_complete: false`，`query_declaration: null`。32 条 adaptation 来自 `epoch-migration/runs/*/adaptations/`（32 个 `.diff`）。

> Concern one, in its sharpest form.
>
> The largest single verification event in this project is the common-epoch migration. Eighty-two modules, and all eighty-two compile. Seventy-four declarations audited, forty-four composition witnesses recorded.
>
> And the same file records `query_chain_complete: false` and `query_declaration: null`. Eighty-two modules compile, and compose into no answer. The empty box at the top is not a rhetorical device. It is a null in a JSON file.
>
> That is what an isolated proof is. Not a wrong proof — a proof with no socket on either end. Getting those modules to compile also took thirty-two recorded source adaptations, each one a machine edit to somebody's proof, each stamped `AGENT_NORMALIZED_UNREVIEWED`.

⏱ 1 min 15 s。

---

### 帧 33 — TOKENS, CALLS AND SECONDS ARE RECORDED · DOLLARS ARE NOT

**屏幕：** 四个框：`7.6M tokens` / `74 model calls` / `71 minutes` / 第四个框**空着**，标 "dollars"。

**出处：** 全部 ledger 聚合（本次复核）：73 条不同调用，input 7,591,305、output 97,677、合计 4,277.5 秒。全部 `cost_microusd` 为 null，`cost_basis: CHATGPT_ACCOUNT_QUOTA_NOT_DOLLAR_METERED`。

> Concern two — and I have to be careful here, because this is the concern my own repository can say the least about.
>
> What it does record: seventy-four model receipts, seven and a half million input tokens, ninety-seven thousand output tokens, four thousand two hundred and eighty seconds. Seventy-one minutes of model time for the entire project, on an ordinary personal account quota. No cluster, no allocation, no scheduler.
>
> What it refuses to record is the fourth box. Every `cost_microusd` field is null; every receipt carries `cost_basis: CHATGPT_ACCOUNT_QUOTA_NOT_DOLLAR_METERED`. I did not leave the price out to be coy. A token count stays true and a price does not, so the deck records the thing that will still be checkable in a year.
>
> And say the caveat out loud: seventy-one minutes is an argument from smallness, not a measured comparison against anybody's large-compute baseline. I have no such comparison, and as far as I can tell neither does anyone else. "Theory will become a capital game" is itself an unmeasured claim.

⏱ 1 min 20 s。

---

### 帧 34 — 8.6 GB OF LIBRARY · 137 SECONDS OF CHECKING

**屏幕：** 左大框 `8.6 GB / 87,659 objects`；右框 `137 s`。

**出处：** `runs/proof-worker-normalization-attempt02-20260919/audit-proof-walk-attempt05.json`，`scope_notes[0]`：`object_count: 87659`、`recorded_byte_size: 8,603,024,240`、`full_base_object_bytes_rehashed: false`。**137 秒来自另一个文件**：`runs/lean-evidence-20260919/lean-audit.json` 的四条 receipt，6.76 + 37.19 + 44.14 + 48.59 = **136.68 s**。（deck 的 note 把两个数都归给了 attempt05，那是 8.6 GB 的出处，不是 137 秒的；见 §5。）

> Concern two again — and this is the one place where I think there is a real answer rather than a caveat.
>
> The expensive object in this picture is not the model time. It is the checker: the Lean library the proofs are checked against. Eighty-seven thousand objects, eight point six gigabytes. That is the fixed capital of the whole enterprise.
>
> And it is a download. Not an allocation, not a quota, not a queue. Everybody who works this way gets the identical one, and a proof the kernel accepts against it is accepted for everybody. Checking this project's entire audited chain took one hundred and thirty-seven seconds, across four receipts, on one laptop.
>
> So if the worry is that theoretical research becomes a competition in who can afford the compute — the most useful property of a proof kernel is that it is cheap, shared, and the same for everyone. That is not a refutation of the worry; the generation side may well concentrate. It is the one counterexample in this repository that I can put a number on.

**如果被追问 8.6 GB 的可信度**：审计自己记了 `full_base_object_bytes_rehashed: false` —— 这个数来自一份哈希已核对的清单，审计没有重新逐字节哈希那 8.6 GB。

⏱ 1 min 20 s。**超时可砍。**

---

### 帧 35 — THE SAME STATEMENT, TWICE · ONCE WITH ITS INTERMEDIATES

**屏幕：** 两条等长横线。上面一条从一个 external-contract 记号出发，经过 11 个 definition 记号，到一个 theorem 记号；下面一条两端相同，中间**什么都没有**。

**出处：** 29 条 closure 中有 11 条是 definition（`runs/2607-full-candidate-20260919/closed-form-branch.json`）。

> Two routes to the same statement, drawn at the same height because they end in the same place. The lower one is what an answer looks like when it arrives alone. The upper one is the same result, with the things it passed through still attached.
>
> Concretely, from this project: the closure of one theorem is twenty-nine claims, and eleven of them are definitions. More than a third of what the headline result rests on is not a result at all. It is vocabulary.
>
> That is the part that transfers to the next problem. And it is exactly the part a good answer throws away.

**转场到 B 段（必须说）：**

> So for the rest of the talk the question is: what would have to come back, instead of a single mark?

⏱ 1 min。

---

## 3. B 段 · 流水线（帧 36–42，5 分钟）

**整段节奏：快。** 每帧 40 秒。这一段只是把词汇铺好，真正的内容在 C 和 D。开头先给一句框架：

> Six boxes. No product name, no version number, no field names — none of that has been introduced yet, and the boxes are the part that generalises beyond my project.

| 帧 | meter | 讲稿要点 |
|---|---|---|
| **36** | ONE PAPER · FROZEN | *A paper, frozen. Every downstream pointer is a byte offset into these exact bytes, so nothing can drift underneath the record while the work is going on. This is the cheapest and least glamorous idea in the system, and it is the one that makes everything else auditable.* |
| **37** | EVERY STATEMENT BECOMES ONE CLAIM RECORD | *Every statement becomes one record carrying three things: what it says, where in the source it came from, and a fingerprint. "Where" is a byte range, not a page number. "A fingerprint" is a hash — so re-wording produces a different record rather than silently editing the old one.* |
| **38** | THE CLAIMS POINT AT EACH OTHER · A DEPENDENCY GRAPH | *The records point at each other. This premise discharges that conclusion. Do that for every record and you no longer have a list, you have a network. This sketch is a cartoon; two slides from now you see the real one.* |
| **11** ⚠️暖 | AND SOME POINT OUTSIDE THE PAPER | *Some records point outside the paper, at work it leans on that nobody has fetched.* **在这里把颜色约定讲死：** *Warm means exactly one thing in every frame of this deck — not from this paper. This box is where most of the honest difficulty lives. A paper's citations are promises, and until somebody resolves one it is a promise the machine cannot check.* |
| **40** | THE CORE CLAIMS · ONLY WHAT THE RESULT RESTS ON | *Choose one result and keep only what it rests on. Everything else goes faint — not deleted, just not part of this question. This is the single most useful operation in the system, and it is also the answer to "why are there so many claims?" There are that many because nobody asked a question yet. Ask one, and the graph collapses to the part that answers it.* |
| **41** | EVERY REMAINING STEP GOES TO AUTO-FORMALIZATION | *Every surviving step goes to a checker that cannot be argued with. It does not negotiate, it does not get tired on the fortieth lemma, and it does not care who wrote the step. That is the entire reason for the machinery in front of it.* |
| **42** | IT HOLDS · OR WHAT IS MISSING GOES BACK IN | *Two exits, and that is the point of the design. It holds — every step accepted. Or it does not, and the system names what is missing. The second exit is the valuable one: a "no" that comes with a specific unmet obligation is a research to-do list; a "no" without one is just a failure. What it never does is the third thing — return something that looks like a proof because the prose around it was fluent.* |

⏱ 5 min。

---

## 4. C 段 · 记录与两张图（帧 43–49，9 分钟）

### 帧 43 — ONE MATH CLAIM  ·  NORMALIZED, HASHED, ANCHORED

**屏幕：** 一条 MathClaim 记录的全貌（`frames/rec-mathclaim.svg`）。

**出处：** `Stabilizerness/MathClaimIRRegistry/claims/graph-theoretic-nonstabilizerness.jsonl`，该 paper 共 **25** 条记录，这是 headline 那条。

> How the schema turns one sentence of a paper into a claim record — and deliberately the same theorem this deck spends its last eleven frames building the chain for.
>
> Read the middle block. The paper states the closed form in a single line. The record has to say what that line actually contains: two assumptions the paper states, four quantifiers of which **three are marked source-implicit** — n, m and M are never quantified in the sentence — a local binder for Q over the cliques, and a convention that the empty clique counts as zero.
>
> And one line worth stopping on. `assumptions.source_implicit`, m greater than or equal to one, anchored to the **proof** rather than the statement. The paper uses a hypothesis in its proof that its theorem does not state.
>
> That is not a criticism of the paper. Every paper does it. It is the thing a reader has to reconstruct by hand — and it is exactly what this record exists to make mechanical.
>
> Three separate hashes, differing on purpose: re-wording the statement changes one and not the others.

**被问到 id 不一致时**：registry 的 id 是 `closed-form-equality`，链条里的是 `claim:closed-form-rom`。同一个数学，不同文件里的不同记录，不是同一条记录。

⏱ 1 min 45 s。

---

### 帧 44 — ONE LAMPORT PROOF  ·  WHAT THE MODEL RETURNED, THEN WHAT THE HOST DID

**屏幕：** 一份 Lamport 式分层编号证明（`frames/rec-lamport.svg`）。

**出处：** `runs/proof-worker-normalization-attempt02-20260919/attempts/*/lamport.json`。就是帧 29 左边那六行。

> A Lamport-style structured proof: hierarchically numbered steps, each checkable on its own, rather than a paragraph of prose.
>
> This is the real artifact from the one end-to-end run that worked. One model call, and the Lean it produced was accepted by the kernel using the audited library theorem `normalized_l1`.
>
> Note what travels with it. The alignment notes record what the formal statement does and does **not** assert — "no nonnegativity or nonempty-index assumption is added"; "does not assert primal feasibility or strong duality". The remaining-obligations field records what was still pending at that point.
>
> The proof does not arrive alone. It arrives with its own caveats attached.

**诚实补一句（建议加，deck 的 note 没有）：** 这次成功时，冻结环境里只有两条声明，其中一条就是答案。所以它演示的是管道通了，不是"模型能在真实规模的库里自己找到该用的定理"。**这句话会让你在提问环节立于不败之地**；不说而被问出来则相反。

> One qualifier I want to volunteer rather than be asked. The frozen environment for that run held two declarations, and one of them was the lemma the proof used. So this demonstrates that the plumbing works end to end. It does not yet demonstrate that a model can find the right declaration in a library of two hundred thousand.

⏱ 1 min 30 s。

---

### 帧 45 — 613 NODES  ·  634 DEPENDENCIES  ·  ONE PASS OVER ONE PAPER

**屏幕：** 整张抽取图，几百个空心记号。

**出处：** `runs/research-terra-continuation-20260920/graphs/00001-db0e3d21/graph.json`。`legacy_dag_edges_used: false`。

> This is what you get when you ask a machine to extract every mathematical claim in one paper, and every dependency between them. Six hundred and thirteen nodes, six hundred and thirty-four edges, assembled from the frozen bytes of the paper, using no hand-authored graph at all.
>
> Shape is node kind. Everything is hollow, because this version of the schema has no accepted state to fill a mark with — `accepted_support_edges` is zero.

⏱ 45 秒。

---

### 帧 46 ⚠️暖 — 240 FROM THE TARGET PAPER · 373 EVERYTHING ELSE

**出处：** 152 `external_claim_request` + 221 `unresolved_claim_occurrence` = 373。连通性由 deck 现算：80 个弱连通分量，最大 379，24 个孤立点，7 个简单环。

> The same graph, two colours.
>
> Ink: the two hundred and forty candidate statements actually extracted from the paper's own TeX. These carry a paper id.
>
> Warm: the other three hundred and seventy-three. A hundred and fifty-two are external claim requests — anchored to a byte range in the bibliography, paper id null, nobody has fetched the source. Two hundred and twenty-one are unresolved source occurrences — a location in the paper that no candidate has yet claimed.
>
> And that is the point of the colour split. Most of this graph is not knowledge. It is the system's own record of what it has not done.
>
> For shape: eighty weakly connected components, the largest three hundred and seventy-nine nodes, twenty-four isolated, and the digraph is not acyclic — seven simple cycles.

⏱ 1 min 15 s。

---

### 帧 47 — 14 OF THE 240 LAND ON A RESULT THE PAPER DECLARES  ·  9 OF 9 HIT

**出处：** `draft.tex` 里正式环境共 **9** 个：2 theorem + 3 lemma + 3 proposition + 1 definition（本次复核逐个数过）。240 个候选中有 14 个的 source span 落在其中之一，命中 9/9。

> The reduction — and it is mechanical. No model judgement anywhere in it.
>
> The host reads the frozen TeX and takes the byte range of every theorem environment and its siblings. The paper declares **nine** formal results: two theorems, three lemmas, three propositions, one definition, each with its own label. Then it asks which of the two hundred and forty extraction candidates have a source span falling inside one.
>
> Answer: fourteen candidates, hitting nine of nine. So nothing the paper formally declares was missed.
>
> Now what this is **not**. It does not delete the other two hundred and twenty-six and it asserts nothing about them. Many are load-bearing — the curated registry holds twenty-five, not nine. It is a mechanical attribution, fully reversible, and it is the cheapest honest cut available: from two hundred and forty unreviewed candidates, to the nine results the paper itself chose to state formally.

⏱ 1 min 30 s。

---

### 帧 48 — A DIFFERENT OBJECT  ·  74 CLAIMS, AUTHORED BY HAND

**出处：** `Stabilizerness/dag/claim-dag.json`：74 节点、129 边（本次复核确认）。

**⚠️ 这是全场最容易被误解的一帧。开口第一句就要挡住误解。**

> Stop. This is a **change of object**, not a zoom.
>
> This is the paper's hand-authored dependency DAG: seventy-four claim nodes, a hundred and twenty-nine edges, one connected structure, acyclic because a person made it so.
>
> It is **not** a subgraph of the previous slide, and I do not want to imply that it is. The two graphs share zero node ids. I also tested correspondence by source location — converting the authored anchors to byte ranges and intersecting them with the extracted spans — and it is far too coarse to be an extraction: four hundred and thirty-six of four hundred and fifty-eight extracted candidates overlap some authored claim. So no clean subgraph exists.
>
> Said plainly: the machine's reading and the human's reading of the same paper are two different objects, and neither is derived from the other.

⏱ 1 min 15 s。

---

### 帧 49 — 29 OF 74  ·  THE CLOSURE OF ONE THEOREM

**出处：** `closed-form-branch.json`：29 节点。build 脚本 assert 这 29 个 id 是那 74 个的真子集。

> This extraction is real, and verified in code: the twenty-nine node ids of the closure are a strict subset of the seventy-four authored ids. The build fails if that ever stops being true.
>
> Ink is the backward closure of the main theorem. Ghosted is the other forty-five claims of the paper — which include five further external roots, the whole empirical branch behind Figure 2, three open problems and two stated limitations.
>
> So: the figure everything after this is built on covers twenty-nine of the paper's seventy-four claims. Thirty-nine percent. A closure answers "what does this theorem rest on". It does not answer "what is in this paper".

⏱ 1 min。

---

## 5. D 段 · 链条构建（帧 50–60，8 分钟）

**节奏提示：** 50–57 是一段动画，**快速连翻**，每帧 15–25 秒，只报数字和一句话。58、59、60 才是内容，各 1 分半。

**开场先定单位（重要）：**

> The unit of construction here is the **support group** — an AND-set of premises that together discharge one target — not the individual edge. That is why you will see brackets rather than arrows.

| 帧 | meter | 一句话 |
|---|---|---|
| **50** | 1 CLAIM | *Start at the theorem. Nothing under it yet.* |
| **51** | 4 CLAIMS  ·  1 AND-GROUP | *Its support group opens: three premises. Drawn as a bracket, not three arrows, because it is an AND — any one missing and the target is not discharged.* |
| **52** | 7 CLAIMS  ·  3 GROUPS | *The same question asked of each premise: what discharges this? Two more groups open.* |
| **53** | 13 CLAIMS  ·  5 GROUPS | *The relaxation branch and the antiblocker branch descend separately. From here a heavier stroke and a faint ring mark what arrived at this step.* |
| **54** | 23 CLAIMS  ·  10 GROUPS | *The widest step — ten new claims at once, and three of the roots arrive together.* |
| **55** | 26 CLAIMS  ·  16 GROUPS | *Three more, completing the reduced-polytope side.* |
| **56** | 28 CLAIMS  ·  19 GROUPS | *Two: the full robustness of magic, and the resource theory that defines it.* |
| **57** | 29 CLAIMS  ·  20 GROUPS  ·  NOTHING LEFT TO EXPAND | 见下 |

**帧 57 要说全（这里放慢）：**

> Twenty-nine claims, twenty support groups. The recursion terminates, because every remaining premise is already in the chain.
>
> And this is worth saying out loud: it terminates **because the input was a closed, hand-authored DAG**. Run the same question against the paper itself and it does not terminate. The controller stops at a budget limit, with four hundred roots — and three hundred and seventy-three of those are placeholders: a hundred and fifty-two citations nobody has fetched, two hundred and twenty-one locations no claim has yet claimed.

---

### 帧 58 — 9 ROOTS · NOTHING BELOW THEM

**出处：** `closed-form-branch.json`：`roots` = 9。

> Nine claims have no support group at all. Nothing in the chain explains them. They are where the paper stops arguing and starts citing.
>
> Six are imported foundations. Three are the paper's own definitions that rest on nothing — which is why the DAG has nine sources rather than six.

⏱ 1 min。

---

### 帧 59 — FORMALIZATION ORDER  ·  14 OF 29

**出处：** `closed-form-branch.json`：`formalization_order` = 14 条。

> The system orders the chain for Lean, and can reach fourteen of the twenty-nine. The order begins at the MWIS definition, the Pauli window, the perfect-graph definition, and finite LP strong duality.
>
> Note the shape. Every filled mark sits in the lower-left mass. Nothing near the top is reachable.

⏱ 45 秒。

---

### 帧 60 — 15 UNREACHABLE · CHAIN_INCOMPLETE

**出处：** `closed-form-branch.json`：`conditional_nodes` = 15。分解：11 条只被 Varela 挡住、1 条只被 perfect-graph root 挡住、1 条（定理本身）被两者挡住，加上 2 个被挡的 root 自己。

**这是 D 段的落点，也是全场诚实度的顶点。慢讲。**

> The fifteen the ordering cannot reach — everything downstream of a blocked root, including the theorem itself. Not because the Lean is missing, but because a premise above it has no discharged source.
>
> The two warm rings are the cause: the only two imports outside the formalization order. Broken down, the fifteen are eleven blocked by the Varela citation alone, one by the perfect-graph root alone, one — the theorem — by both, plus the two blocked roots themselves.
>
> So resolving one citation would return eleven of the fifteen.
>
> And then the status, which I will not dress up. The chain is complete and the proof is not. `mathematical_status: CHAIN_INCOMPLETE`. `accepted_support_edges: 0`. `proof_backend: NOT_CONNECTED`.

⏱ 1 min 30 s。**说完停一拍再进结尾段。**

---

## 6. E 段 · 结尾（帧 61–68，10 分钟）

**开场定调（必须说，否则听众分不清哪些是已做的、哪些是想做的）：**

> The ending is three wishes with one measurement wedged in the middle, and I will keep saying which is which.

### 帧 61 — ONE THEOREM’S CHAIN · 29 CLAIMS, 46 DEPENDENCIES

> Start from the object the deck has been building: the closure of one theorem. Twenty-nine claims, forty-six dependencies, laid out exactly as in the chain frames — same positions, same shapes, same claims.

⏱ 30 秒。

### 帧 62 — WISH ONE · MORE PAPERS, ONE NETWORK

> **Wish one.** Do this to the next paper, and the next. The heavier lines between clusters are the point: the same claim, leaned on by two different papers. That is the moment a pile of decomposed papers becomes one network.
>
> It is also the joint I said I cannot build. Deciding that this lemma and that lemma are the **same** lemma is an identity question, and my system does not answer it. Schematic layout, no counts, nothing asserted.

⏱ 1 min。

### 帧 63 — CUT ONE CLAIM OUT · COUNT WHAT LEAVES THE CLOSURE

**出处：** `closed-form-branch.json` 的 `edge_criticality`，46 条。`gen_skeleton.py` 里有断言，重算对不上就 build 失败。

> **Not a wish.** Cut one claim out of the graph — remove every dependency into it — and recompute the backward closure of the theorem. Count what is no longer in it. Size and ink are that count.
>
> Before you trust any of this: my computation reproduces all forty-six of the omission experiments the pipeline recorded, edge for edge. The assertion is in the build script and the build fails if it ever stops matching. I am not showing you a model of the pipeline. I am showing you the pipeline's own arithmetic.
>
> The graph program carries twenty-five of the twenty-nine. The distribution has a long thin tail and one spike — and that shape is what makes the rest of this worth attempting. You do not need taste to find the load-bearing parts. You need an omission test.

⏱ 1 min 30 s。

### 帧 64 — 46 DEPENDENCIES · WEIGHTED BY WHAT REMOVING ONE COSTS

> The same question asked of every dependency rather than every claim — and this one the pipeline had already answered for itself, in all forty-six cases.
>
> Line weight is what removing that one edge costs. Most of the graph is thin. The small chart is the whole distribution, sorted. It is deliberately small: the number on any one bar does not matter. The shape does. And the shape is a cliff.

⏱ 45 秒。

### 帧 65 — 29 FREE ON THEIR OWN · TOGETHER THEY COST 14 CLAIMS

**这是全场技术上最漂亮的一帧。慢讲，并且把"我自己搞错过"讲出来——这句话的说服力比结论本身还大。**

> And here is the trap. I walked into it while building this frame, and I think it is the most useful thing on the slide.
>
> Twenty-nine of the forty-six dependencies cost nothing when you remove them. Each one, on its own, is redundant — every claim is still reachable by some other route.
>
> Take all twenty-nine away **together**, and fourteen of the twenty-nine claims fall out of the closure.
>
> Individual redundancy does not compose. Two edges can each be safe to cut because the other one is there. It is obvious once stated, and it is extremely easy to miss — I had this frame drawn the wrong way round, asserting that the twenty-nine could go and seventeen would remain, before I checked it jointly.
>
> That is precisely the kind of mistake a person makes reading a dependency structure by eye. And precisely the kind a machine does not.

⏱ 1 min 45 s。

### 帧 66 — THE SKELETON · 28 DEPENDENCIES, NOTHING LOST

> So the skeleton has to be computed properly: remove one dependency, recheck the whole closure, and only then try the next. Greedily, to exhaustion.
>
> Eighteen can go. Twenty-eight remain, and all twenty-nine claims are still reachable.
>
> That is what I mean by the skeleton of a theory. Not a summary, and not "the important bits" as judged by anybody — the subgraph you cannot cut any further without losing something, arrived at by an operation with no opinion in it.
>
> Two honest caveats. It is a statement about the graph **as recorded**: if the extraction missed a route, an edge looks more necessary than it is. And twenty-nine claims is small enough that a careful person could have done this by hand — slowly, and as the previous frame shows, probably wrongly.

⏱ 1 min 15 s。

### 帧 67 — WISH TWO · A CLAIM IN A GAP THE STRUCTURE NAMES

> **Wish two.** If you can compute where the load sits, you can also see where the structure is thin — a place where several load-bearing claims converge and nothing has been written.
>
> The diamond is a claim nobody has stated, proposed because the shape of the network says something belongs there.
>
> And note that the junction is drawn exactly like every other junction in this deck. A proposed claim gets no special status. Same AND-junction, same premises, same arrow, same kernel. Accepted, it is knowledge. Refused, the system names what was missing — and that becomes the next thing to read.

⏱ 1 min。

### 帧 68 — WISH THREE · A NEW PAPER INHERITS WHAT IS ALREADY CHECKED

**全场落点。**

> **Wish three**, and this is the one I would most like to be true.
>
> Along the bottom: what has already been checked, and stays checked. A proof the kernel accepted does not need re-accepting next year.
>
> Above: a new paper. Most of what it rests on is already down there — the same foundations, the same definitions, the same handful of load-bearing claims every paper in the area leans on. Those edges cost nothing new. Only three things in it are actually new, and only those three need a junction and a check.
>
> That is what the apparatus is **for**. Not to verify a paper — to make the **next** paper cheap, by making verification something you inherit instead of something you repeat. Today, reading a paper properly means reconstructing its dependencies from scratch. Every reader. Every time. This is the version where you do not.

**然后停下来，报状态收尾（不要省略）：**

> And the status, so I end where I started. Twenty-nine claims. Fourteen reachable. `accepted_support_edges`: zero. `CHAIN_INCOMPLETE`.
>
> Three wishes, and one measurement.

⏱ 1 min 45 s。

---

## 7. 本次数字复核结果（2026-09-21）

deck 的自述是 *"EVERY NUMBER ON THESE FRAMES IS READ OUT OF THIS REPOSITORY"*。这条自述本身就是讲座的论点之一，所以我把每个能核的数都核了。

### 7.1 已核对一致

| 数字 | 出处 | 结果 |
|---|---|---|
| 613 节点 / 634 边 / 213 组 / 240 + 373 | `graphs/00001-db0e3d21/graph.json` | ✅ |
| `accepted_support_edges: 0`、`all_judgements_unreviewed: true` | `summary.json` | ✅ |
| 7,591,305 input / 97,677 output token | 全部 ledger 聚合 | ✅ **逐位一致** |
| 4,280 秒 ≈ 71 分钟 | 同上（73 条不同调用，实测 4,277.5 s） | ✅ |
| 全部 `cost_microusd` null，`CHATGPT_ACCOUNT_QUOTA_NOT_DOLLAR_METERED` | 同上 | ✅ |
| 87,659 objects / 8,603,024,240 B = 8.6 GB | `audit-proof-walk-attempt05.json` `scope_notes[0]` | ✅ |
| `full_base_object_bytes_rehashed: false`（那条 caveat） | 同上 | ✅ |
| 64 kernel-checked = 54 thm + 9 def + 1 ind；46/54 `PREMISE_NONVACUITY_UNKNOWN` | `lean-evidence-20260919/lean-audit.json` | ✅ |
| 82/82 编译、74 声明、44 composition witness、`query_declaration: null` | `full-case-audit.json` | ✅ |
| 32 条 source adaptation | `epoch-migration/runs/*/adaptations/`（32 个 `.diff`） | ✅ |
| 7,765 行 | `formal/AgtXIvRootMath`（55 文件） | ✅ |
| 六行证明 / 1 次调用 / 21.4 秒 | `proof-worker-normalization-attempt02-20260919` | ✅ |
| 人写 DAG 74 节点 / 129 边 | `Stabilizerness/dag/claim-dag.json` | ✅ |
| registry 25 条 | `MathClaimIRRegistry/.../graph-theoretic-nonstabilizerness.jsonl` | ✅ |
| 论文正式结果 9 个 = 2 thm + 3 lem + 3 prop + 1 def | `draft.tex` 逐个数 | ✅ |
| 闭包：29 节点 / 46 边 / 20 组 / 9 roots / 14 formalization_order / 15 conditional / 46 criticality / **0 SCC** | `closed-form-branch.json` | ✅ **八项全中** |

**结论：没有发现任何一个编造或对不上的数字。** 对一份 69 帧、数字密度这么高的 deck，这个结果本身值得你在被质疑时直接说出来。

### 7.2 三处建议在开口前收紧的措辞

都不是错，是**可能被追问到卡壳**的地方。

**（1）"137 秒"的出处写错了文件。**

`motivation.py` 的 note 把 8.6 GB 和 136.68 s 都归给了 `audit-proof-walk-attempt05.json`。8.6 GB 确实在那里；**136.68 秒不在**——全仓库检索不到这个字面量。它是一个**加总**：`runs/lean-evidence-20260919/lean-audit.json` 里的四条 receipt，6.76 + 37.19 + 44.14 + 48.59 = 136.68。

"across four receipts" 完全正确。只要把引用的文件名换成 `lean-evidence-20260919/lean-audit.json` 即可。**如果有人问"这个数在哪个文件里"，照 attempt05 去翻会翻不到。**

**（2）"74 model receipts" 与 token 总数的口径不同。**

磁盘上有 74 个 `call-*` 目录；ledger 里是 **73 条不同的 call id**（有一条在两个 ledger 里各出现一次，另有一条失败调用没有 ledger 记录）。7,591,305 / 97,677 / 4,277.5 这三个数是**按 73 条去重后**算的。

建议口头说成 *"seventy-four receipts on disk, seventy-three of them ledgered"*，或者干脆都说 73。现在这样说不算错，但两个数并列时会被细心的人抓住。

**（3）帧 46 的 "373 unfetched requests" 不够准确。**

373 = **152** 条未取的外部引用 + **221** 条本文内尚未被认领的位置。只有那 152 条是 "unfetched"。稿子里我已经改成分开报，照着念就行。

### 7.3 一处建议主动补充的话

帧 44 的 Lamport 证明：**主动说出那次成功时冻结环境里只有两条声明、其中一条就是答案。** 理由是这一条是整个 deck 里最容易被内行一句话拆掉的地方（"所以模型只是把你给它的引理包了一层？"）。你自己先说，它是诚实；被问出来，它是被抓。稿子帧 44 末尾已经写好了这句话。

---

## 8. Q&A 备弹

| 问题 | 回答 |
|---|---|
| **"613 里有多少是真的数学内容？"** | 634 条支持边里 261 条（41.2%）落到本文另一条 claim 上；其余 221 条是未解析的内部位置、152 条是未取的外部引用。613 里只有 14 个是 theorem/lemma/proposition。 |
| **"为什么不直接在抽取图上做形式化？"** | 因为它的 `formalization_order` 是空的——613 个节点全部带 `CANDIDATE_EXPLORATION_REVIEW_REQUIRED` 阻塞标记，调度器一个都不会尝试。今天能走链条的那 29 条，是人写的 DAG。**这一句必须照实说。** |
| **"抽取图和人写的 DAG 能合并吗？"** | 目前不能机械合并。候选 id 是 `(paper_id, sources, statement, conditions)` 的内容哈希，两套 id 交集为零。 |
| **"Lean 里有 `sorry` 吗？"** | 没有。35 个 `.lean` 文件里零 `sorry`、零 `admit`、零自定义 `axiom`、零 `native_decide`；302 条审计记录只用 `propext`、`Classical.choice`、`Quot.sound`。 |
| **"递归到最早出处做到哪一步了？"** | 没做到，而且我认为它作为自动判据不可判定。判据写在 `graph.py` 里（`ORIGIN` 需要 `search_status: SEARCH_EXHAUSTED`），但**没有任何代码生产那个证据**，历史上零个节点被标成 ORIGIN。实际撞上 Berge 1961 时——一篇 1961 年 Halle 大学学报的德文摘要——五轮检索后拿不到原文。这 152 条外部请求里 40.8% 指向 1935–1988 年的文献。 |
| **"成本？"** | 我只报 token、调用数和秒数，不报美元。全部 `cost_microusd` 是 null，因为走的是账户额度不是计量计费。token 数一年后还是真的，价格不是。 |
| **"这个能用在别人的论文上吗？"** | 还不能。今天展示的链条依赖一份人手搭的 DAG 和一张 7 条硬编码的根绑定表，两者都是为这一篇写的。自动库检索（在 mathlib 里找对应声明）目前是零行代码——那是最大的一块缺口。 |
| **"下一步？"** | 一个约 12 美元、一小时的测量实验：拿三个已经有人写好 Lean 的节点，把参照 Lean 藏起来只当评分器，让模型从 claim 文本自己写，测 def 和 theorem 各自需要几次尝试才编译通过。这是唯一能回答"这条路走不走得通"的实验，我还没跑。 |

---

## 9. 最后 30 秒清单（讲前过一遍）

- [ ] 暖色只说 "not from this paper"，不说 "bad" / "pending"
- [ ] 帧 48 开口第一句就是 "this is a change of object, not a zoom"
- [ ] 帧 44 主动交代"当时库里只有两条声明"
- [ ] 帧 46 把 373 拆成 152 + 221
- [ ] 帧 65 把"我自己画反过"讲出来
- [ ] 帧 60 和帧 68 都以 `CHAIN_INCOMPLETE` 收尾——这是全场的诚实锚点，两次都别省
- [ ] 有人问 137 秒出自哪个文件：`runs/lean-evidence-20260919/lean-audit.json`，四条 receipt 相加
