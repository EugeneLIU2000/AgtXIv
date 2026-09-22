# chain-build-v1.html — 逐帧讲解与完整演讲稿

> **这份稿子对应 `chain-build-v1.html`（67 帧），不是 `chain-build.html`（69 帧）。**
> v1 把同样的图重新排了顺序：测量数字那一段被拆成三块分别放进了三个不同的幕，
> 导入开场里 5 帧重复的 build step 被删掉，新增 3 帧（标题 / 铰链 / 路线图）。
> 每一段讲稿文字都是从旧稿原样搬过来的，只有帧号变了；对照表见 §2。

**对象：** `slides/chain-build/chain-build-v1.html`，67 帧，9 幕
**语言：** 讲解用中文；**讲稿正文是英文**，因为 deck 上的 meter 和 speaker notes 都是英文。

**三条贯穿全场的规矩**（deck 自己定的，讲的时候别破）：

- **一个例子，永不离开**：arXiv:2607.26154v1。
- **暖色 `#8C4A2F` 只有一个意思：NOT FROM THIS PAPER。**
- **虚线环 = root，下面什么都没有；实心 = 形式化顺序能到达。**

---

## 1. 全局结构与时间预算

| 幕 | 帧 | 内容 | 建议时长 |
|---|---|---|---:|
| **I · OPENING** | 0–1 | 2 帧 | 1 min |
| **II · WHAT THE MACHINE IS DOING** | 2–7 | 6 帧 | 4 min |
| **III · WHAT HAS TEETH** | 8–17 | 10 帧 | 6 min |
| **IV · WHAT WE ARE TRYING TO TRUST** | 18–23 | 6 帧 | 4 min |
| **V · HOW A PAPER BECOMES CLAIMS** | 24–36 | 13 帧 | 8 min |
| **VI · ONE REAL PAPER** | 37–43 | 7 帧 | 5 min |
| **VII · ONE THEOREM’S CHAIN** | 44–54 | 11 帧 | 6 min |
| **VIII · THREE WISHES** | 55–62 | 8 帧 | 5 min |
| **IX · IN CLOSING** | 63–64 | 2 帧 | 2 min |
| Q&A | — | | 4 min |
| | | | **45 min** |

这一版相对 v0 的改动，讲之前先记住：

1. **危机曲线之后只有一句话**，然后直接进 LLM 机制——旧稿里那两帧（一个孤立的定理 / 6 行对 7,765 行）开了一个此处不打算展开的论证，已删。
2. **「please help me …」三帧挪到了 trust 四象限之前**，因为 learn backwards / reason forwards 正是后面 closure 与 build 两个方向的引子。
3. **How formalization works 之后加了三帧 Lean**：一段能读的代码、kernel 接受或拒绝、以及库（Mathlib / Quantumlib / 本文 66 个文件）。**这三帧是给物理听众的，讲慢一点。**
4. **旧的测量段（213 support groups / 46 conditional / 8.6 GB …）整段删除。**这是一场关于可能性的报告，不是 schema 的技术汇报。其中最该说的那几句诚实话，现在集中在倒数第二帧「IN CLOSING」上。
5. **最后两帧是新的**：结论，然后一帧只有一个问题的讨论页。

---

## 2. 帧号对照表（v1 → v0）

| v1 | v0 | 幕 | meter |
|---:|---:|---|---|
| 0 | **新** | I | SOME THOUGHTS ABOUT LLM FOR THEORETICAL RESEARCH |
| 1 | 1 | I | THE AI CRISIS IN THEORETIC RESEARCH |
| 2 | **新** | II | WHAT IS THE MACHINE ACTUALLY DOING |
| 3 | 2 | II | WHAT IS INSIDE THE BLACK BOX OF LLM REASONING |
| 4 | 3 | II | WHAT IS INSIDE THE BLACK BOX OF LLM REASONING |
| 5 | 5 | II | WHAT IS INSIDE THE BLACK BOX OF LLM REASONING |
| 6 | 7 | II | MODEL MEMORY · THE CONTEXT WINDOW |
| 7 | 8 | II | MODEL MEMORY · WHEN THE WINDOW IS EXCEEDED |
| 8 | 9 | III | API / AGENT / MCP / SCHEMA / SKILLS |
| 9 | 10 | III | A LANGUAGE MODEL, BY ITSELF |
| 10 | 11 | III | PUT IT IN A LOOP · THAT IS AN AGENT |
| 11 | 12 | III | A SKILL IS A STRUCTURAL PROMPT DOCUMENT |
| 12 | 13 | III | MCP · MODEL CONTEXT PROTOCOL |
| 13 | 14 | III | AGENT USES TOOLS AND THE LOOP |
| 14 | 15 | III | SCHEMA · A MACHINE-CHECKED CONTRACT |
| 15 | 16 | III | SCHEMA · A RECORD THAT DOES NOT CONFORM IS REFUSED |
| 16 | 17 | III | SCHEMA · ONLY IT CAN MAKE AN ANSWER IMPOSSIBLE TO EXPRESS |
| 17 | **新** | III | A REQUEST CAN BE IGNORED · A CONSTRAINT CANNOT |
| 18 | 19 | IV | “PLEASE HELP ME …” · LEARN BACKWARDS |
| 19 | 21 | IV | “PLEASE HELP ME …” · REASONING FORWARDS |
| 20 | 22 | IV | “PLEASE HELP ME …” · OR, SOMETIMES TOGETHER |
| 21 | 23 | IV | WHAT WE ACTUALLY CARE ABOUT · AND WHAT CAN WE TRUST? |
| 22 | 27 | IV | OF THE FOUR, THIS TALK IS ABOUT THE SECOND |
| 23 | **新** | IV | THE ROUTE · WHAT IS COMING, AND WHY |
| 24 | 24 | V | IMAGING PAPER AS AN AGENT |
| 25 | 25 | V | HOW FORMALIZATION WORKS |
| 26 | **新** | V | LEAN 4 · A DEFINITION, A CLAIM, A PROOF |
| 27 | **新** | V | ACCEPTED, OR REFUSED · AND THE ONE WAY TO CHEAT |
| 28 | **新** | V | THE LIBRARIES · AND THE ONE PHYSICS DOES NOT HAVE |
| 29 | 26 | V | AUTOFORMALIZATION |
| 30 | 36 | V | ONE PAPER · FROZEN |
| 31 | 37 | V | EVERY STATEMENT BECOMES ONE CLAIM RECORD |
| 32 | 38 | V | THE CLAIMS POINT AT EACH OTHER · A DEPENDENCY GRAPH |
| 33 | 39 | V | AND SOME POINT OUTSIDE THE PAPER |
| 34 | 40 | V | THE CORE CLAIMS · ONLY WHAT THE RESULT RESTS ON |
| 35 | 41 | V | EVERY REMAINING STEP GOES TO AUTO-FORMALIZATION |
| 36 | 42 | V | IT HOLDS · OR WHAT IS MISSING GOES BACK IN |
| 37 | 43 | VI | ONE MATH CLAIM  ·  NORMALIZED, HASHED, ANCHORED |
| 38 | 44 | VI | ONE LAMPORT PROOF  ·  WHAT THE MODEL RETURNED, THEN WHAT THE HOST DID |
| 39 | 45 | VI | 613 NODES  ·  634 DEPENDENCIES  ·  ONE PASS OVER ONE PAPER |
| 40 | 46 | VI | 240 FROM THE TARGET PAPER  ·  373 EVERYTHING ELSE |
| 41 | 47 | VI | 14 OF THE 240 LAND ON A RESULT THE PAPER DECLARES  ·  9 OF 9 HIT |
| 42 | 48 | VI | A DIFFERENT OBJECT  ·  74 CLAIMS, AUTHORED BY HAND |
| 43 | 49 | VI | 29 OF 74  ·  THE CLOSURE OF ONE THEOREM |
| 44 | 50 | VII | 1 CLAIM |
| 45 | 51 | VII | 4 CLAIMS  ·  1 AND-GROUP |
| 46 | 52 | VII | 7 CLAIMS  ·  3 GROUPS |
| 47 | 53 | VII | 13 CLAIMS  ·  5 GROUPS |
| 48 | 54 | VII | 23 CLAIMS  ·  10 GROUPS |
| 49 | 55 | VII | 26 CLAIMS  ·  16 GROUPS |
| 50 | 56 | VII | 28 CLAIMS  ·  19 GROUPS |
| 51 | 57 | VII | 29 CLAIMS  ·  20 GROUPS  ·  NOTHING LEFT TO EXPAND |
| 52 | 58 | VII | 9 ROOTS  ·  NOTHING BELOW THEM |
| 53 | 59 | VII | FORMALIZATION ORDER  ·  14 OF 29 |
| 54 | 60 | VII | 15 UNREACHABLE  ·  CHAIN_INCOMPLETE |
| 55 | 61 | VIII | ONE THEOREM’S CHAIN · 29 CLAIMS, 46 DEPENDENCIES |
| 56 | 62 | VIII | WISH ONE · MORE PAPERS, ONE NETWORK |
| 57 | 63 | VIII | CUT ONE CLAIM OUT · COUNT WHAT LEAVES THE CLOSURE |
| 58 | 64 | VIII | 46 DEPENDENCIES · WEIGHTED BY WHAT REMOVING ONE COSTS |
| 59 | 65 | VIII | 29 FREE ON THEIR OWN · TOGETHER THEY COST 14 CLAIMS |
| 60 | 66 | VIII | THE SKELETON · 28 DEPENDENCIES, NOTHING LOST |
| 61 | 67 | VIII | WISH TWO · A CLAIM IN A GAP THE STRUCTURE NAMES |
| 62 | 68 | VIII | WISH THREE · A NEW PAPER INHERITS WHAT IS ALREADY CHECKED |
| 63 | **新** | IX | IN CLOSING · WHAT IS SHOWN, AND WHAT IS NOT |
| 64 | **新** | IX | DISCUSSION |

v0 里被删掉的 5 帧：**0**（源文件 slide 1，两个空占位符）、**4**（slide 5，slide 6 是同一帧多一张图）、**6**（slide 7，slide 8 是同一帧多一个 context window 框）、**18**（slide 19，slide 20 是同一帧多一张图）、**20**（slide 21，slide 22 同理）。删的都是同一张源幻灯片的重复 build step，没有删掉任何内容。

---

## I · OPENING（帧 0–1）

### 帧 0 — SOME THOUGHTS ABOUT LLM FOR THEORETICAL RESEARCH

> **新增帧。** deck 内置 speaker note：

> OPEN HERE, on almost nothing. The title is deliberately modest - these are thoughts, not results, and saying so in the first ten seconds buys the room's patience for the honest parts later.
>
> Everything that used to be printed on this frame is now yours to say: where you are, what the date is, and the sentence the talk is actually about - a paper states what it proves, and it does not state what it depends on, or who checked which part.
>
> Say that sentence here, word for word. It is the only one in the talk worth memorising.
>

### 帧 1 — THE AI CRISIS IN THEORETIC RESEARCH

*（导入开场帧，旧稿未覆盖——照着幻灯片讲即可。）*

---

## II · WHAT THE MACHINE IS DOING（帧 2–7）

### 帧 2 — WHAT IS THE MACHINE ACTUALLY DOING

> **新增帧。** deck 内置 speaker note：

> ONE SENTENCE, THEN TURN THE PAGE. Do not elaborate - the next four frames are the elaboration.
>
> The curve you just saw is about volume. This is the turn from volume to mechanism: the reason a generated result is hard to reuse is not that it is sloppy, it is that of what the machine did to produce it, nothing survives except the text.
>
> Say the second line - it is a description, not a criticism - and move on. It buys you the room's patience for four frames of mechanism.
>

### 帧 3 — WHAT IS INSIDE THE BLACK BOX OF LLM REASONING

*（导入开场帧，旧稿未覆盖——照着幻灯片讲即可。）*

### 帧 4 — WHAT IS INSIDE THE BLACK BOX OF LLM REASONING

*（导入开场帧，旧稿未覆盖——照着幻灯片讲即可。）*

### 帧 5 — WHAT IS INSIDE THE BLACK BOX OF LLM REASONING

*（导入开场帧，旧稿未覆盖——照着幻灯片讲即可。）*

### 帧 6 — MODEL MEMORY · THE CONTEXT WINDOW

*（导入开场帧，旧稿未覆盖——照着幻灯片讲即可。）*

### 帧 7 — MODEL MEMORY · WHEN THE WINDOW IS EXCEEDED

*（导入开场帧，旧稿未覆盖——照着幻灯片讲即可。）*

---

## III · WHAT HAS TEETH（帧 8–17）

### 帧 8 — API / AGENT / MCP / SCHEMA / SKILLS

*（导入开场帧，旧稿未覆盖——照着幻灯片讲即可。）*

### 帧 9 — A LANGUAGE MODEL, BY ITSELF

*（导入开场帧，旧稿未覆盖——照着幻灯片讲即可。）*

### 帧 10 — PUT IT IN A LOOP · THAT IS AN AGENT

*（导入开场帧，旧稿未覆盖——照着幻灯片讲即可。）*

### 帧 11 — A SKILL IS A STRUCTURAL PROMPT DOCUMENT

*（导入开场帧，旧稿未覆盖——照着幻灯片讲即可。）*

### 帧 12 — MCP · MODEL CONTEXT PROTOCOL

*（导入开场帧，旧稿未覆盖——照着幻灯片讲即可。）*

### 帧 13 — AGENT USES TOOLS AND THE LOOP

*（导入开场帧，旧稿未覆盖——照着幻灯片讲即可。）*

### 帧 14 — SCHEMA · A MACHINE-CHECKED CONTRACT

*（导入开场帧，旧稿未覆盖——照着幻灯片讲即可。）*

### 帧 15 — SCHEMA · A RECORD THAT DOES NOT CONFORM IS REFUSED

*（导入开场帧，旧稿未覆盖——照着幻灯片讲即可。）*

### 帧 16 — SCHEMA · ONLY IT CAN MAKE AN ANSWER IMPOSSIBLE TO EXPRESS

*（导入开场帧，旧稿未覆盖——照着幻灯片讲即可。）*

### 帧 17 — A REQUEST CAN BE IGNORED · A CONSTRAINT CANNOT

> **新增帧。** deck 内置 speaker note：

> THE HINGE OF THE TALK. Do not rush this frame.
>
> The previous slide said it in the source deck's own words: the prompt, the skill and the tool call are all requests. The model can read them and not follow them, and the transcript looks identical either way. Only the schema can make an answer impossible to express.
>
> Now spend that sentence. A paper's claims are requests too. 'By Theorem 3 of reference 14' is a request that the reader go and check something, and almost nobody does, and the paper looks the same either way.
>
> So the question for the rest of the talk is: what would it take to make a paper's claims refusable? That is the only thing being attempted here.
>

---

## IV · WHAT WE ARE TRYING TO TRUST（帧 18–23）

### 帧 18 — “PLEASE HELP ME …” · LEARN BACKWARDS

*（导入开场帧，旧稿未覆盖——照着幻灯片讲即可。）*

### 帧 19 — “PLEASE HELP ME …” · REASONING FORWARDS

*（导入开场帧，旧稿未覆盖——照着幻灯片讲即可。）*

### 帧 20 — “PLEASE HELP ME …” · OR, SOMETIMES TOGETHER

*（导入开场帧，旧稿未覆盖——照着幻灯片讲即可。）*

### 帧 21 — WHAT WE ACTUALLY CARE ABOUT · AND WHAT CAN WE TRUST?

*（导入开场帧，旧稿未覆盖——照着幻灯片讲即可。）*

### 帧 22 — OF THE FOUR, THIS TALK IS ABOUT THE SECOND

*（导入开场帧，旧稿未覆盖——照着幻灯片讲即可。）*

### 帧 23 — THE ROUTE · WHAT IS COMING, AND WHY

> **新增帧。** deck 内置 speaker note：

> THE ROADMAP, and the only one in the deck - say it once, clearly, and then do not repeat it.
>
> Three things a later paper needs before it can use your conclusion: what you actually said, what you relied on, and which parts anybody checked. A PDF gives you the first, sometimes. It does not give you the other two in any form a machine - or a hurried human - can follow.
>
> Then the route across the bottom. One paper, frozen. Its claims and the dependencies between them. One theorem's chain pulled out of that graph. And then, honestly, where the whole thing stops - because it does stop, and the last act of this talk is about exactly where.
>
> The promise on the last line matters more than it looks: every number from here on is read out of this repository's own logs. Where nobody has measured something, the frame says nobody measured it.
>

---

## V · HOW A PAPER BECOMES CLAIMS（帧 24–36）

### 帧 24 — IMAGING PAPER AS AN AGENT

*（导入开场帧，旧稿未覆盖——照着幻灯片讲即可。）*

### 帧 25 — HOW FORMALIZATION WORKS

*（导入开场帧，旧稿未覆盖——照着幻灯片讲即可。）*

### 帧 26 — LEAN 4 · A DEFINITION, A CLAIM, A PROOF

> **新增帧。** deck 内置 speaker note：

> THE ONLY CODE IN THE TALK. Give it a full minute; most of the room has never seen Lean.
>
> Read it top to bottom. 'def double' - I am building a thing. Nothing is being claimed yet, so there is nothing to check; a definition cannot be wrong, only useless.
>
> 'theorem double_eq_add' - now I am claiming something about the thing I built. Point at this line and say: this is the only line a human has to read. Everything below it is for the machine.
>
> ':= by unfold double; omega' - the proof. It is a program. 'unfold' replaces the name by what it stands for, 'omega' is a decision procedure for linear arithmetic. When you compile this file the kernel re-runs both from scratch and either accepts or does not.
>
> Land the bottom two lines: you give up prose, and you get back a claim that can be refused. That trade is the entire subject of the talk.
>

### 帧 27 — ACCEPTED, OR REFUSED · AND THE ONE WAY TO CHEAT

> **新增帧。** deck 内置 speaker note：

> THE POINT OF THE WHOLE APPROACH IS ON THIS FRAME.
>
> A referee can be tired, generous, or in a hurry. A kernel is none of those. It re-checks every step, and it does not know whose proof it is.
>
> The right-hand box matters more than it looks. When Lean refuses, it tells you WHICH step it would not take. A 'no' with a specific unmet obligation is a to-do list. A 'no' without one is just a failure. That distinction is why this is worth doing at all.
>
> Then be honest about the escape hatch. 'sorry' means: accept this without proof. It compiles. Anybody can write it. The difference from prose is that it is WRITTEN DOWN - you cannot wave at it, it sits in the file and anybody grepping finds it.
>
> The four numbers are this repository, counted this morning: sixty-six files, and not one sorry, admit, or new axiom. Say 'counted this morning' - it is the kind of claim you should be able to date.
>

### 帧 28 — THE LIBRARIES · AND THE ONE PHYSICS DOES NOT HAVE

> **新增帧。** deck 内置 speaker note：

> THE FRAME FOR THIS AUDIENCE. Slow down here; this is the part a physicist should leave the room remembering.
>
> Three bars. Mathlib is the mathematics - it is enormous, it is other people's work, and it is pinned in this project to one exact revision, so 'it compiles' means something a year from now. Quantumlib is much smaller and sits on top of it. The bottom bar - sixty-six files - is the only part that is ours.
>
> Look at the ratio and say the obvious thing: almost none of this is my work, and that is the point. Formalization is only affordable because the ground already exists.
>
> Then the honest line. Mathematics has a Mathlib. Physics does not have an equivalent - there are efforts, PhysLean is the one to look up, but nothing on that scale. Every time our subject needs an object that is not already in Mathlib, somebody has to build it first, and that is most of the reason this is hard for us and comparatively easy for number theory.
>
> If you are asked about PhysLean, say what is true: I have not used it, and I am not in a position to assess it from this work.
>

### 帧 29 — AUTOFORMALIZATION

*（导入开场帧，旧稿未覆盖——照着幻灯片讲即可。）*

### 帧 30 — ONE PAPER · FROZEN

*A paper, frozen. Every downstream pointer is a byte offset into these exact bytes, so nothing can drift underneath the record while the work is going on. This is the cheapest and least glamorous idea in the system, and it is the one that makes everything else auditable.*

### 帧 31 — EVERY STATEMENT BECOMES ONE CLAIM RECORD

*Every statement becomes one record carrying three things: what it says, where in the source it came from, and a fingerprint. "Where" is a byte range, not a page number. "A fingerprint" is a hash — so re-wording produces a different record rather than silently editing the old one.*

### 帧 32 — THE CLAIMS POINT AT EACH OTHER · A DEPENDENCY GRAPH

*The records point at each other. This premise discharges that conclusion. Do that for every record and you no longer have a list, you have a network. This sketch is a cartoon; two slides from now you see the real one.*

### 帧 33 — AND SOME POINT OUTSIDE THE PAPER

⚠️暖 *Some records point outside the paper, at work it leans on that nobody has fetched.* **在这里把颜色约定讲死：** *Warm means exactly one thing in every frame of this deck — not from this paper. This box is where most of the honest difficulty lives. A paper's citations are promises, and until somebody resolves one it is a promise the machine cannot check.*

### 帧 34 — THE CORE CLAIMS · ONLY WHAT THE RESULT RESTS ON

*Choose one result and keep only what it rests on. Everything else goes faint — not deleted, just not part of this question. This is the single most useful operation in the system, and it is also the answer to "why are there so many claims?" There are that many because nobody asked a question yet. Ask one, and the graph collapses to the part that answers it.*

### 帧 35 — EVERY REMAINING STEP GOES TO AUTO-FORMALIZATION

*Every surviving step goes to a checker that cannot be argued with. It does not negotiate, it does not get tired on the fortieth lemma, and it does not care who wrote the step. That is the entire reason for the machinery in front of it.*

### 帧 36 — IT HOLDS · OR WHAT IS MISSING GOES BACK IN

*Two exits, and that is the point of the design. It holds — every step accepted. Or it does not, and the system names what is missing. The second exit is the valuable one: a "no" that comes with a specific unmet obligation is a research to-do list; a "no" without one is just a failure. What it never does is the third thing — return something that looks like a proof because the prose around it was fluent.*

---

## VI · ONE REAL PAPER（帧 37–43）

### 帧 37 — ONE MATH CLAIM  ·  NORMALIZED, HASHED, ANCHORED

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

### 帧 38 — ONE LAMPORT PROOF  ·  WHAT THE MODEL RETURNED, THEN WHAT THE HOST DID

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

### 帧 39 — 613 NODES  ·  634 DEPENDENCIES  ·  ONE PASS OVER ONE PAPER

**屏幕：** 整张抽取图，几百个空心记号。

**出处：** `runs/research-terra-continuation-20260920/graphs/00001-db0e3d21/graph.json`。`legacy_dag_edges_used: false`。

> This is what you get when you ask a machine to extract every mathematical claim in one paper, and every dependency between them. Six hundred and thirteen nodes, six hundred and thirty-four edges, assembled from the frozen bytes of the paper, using no hand-authored graph at all.
>
> Shape is node kind. Everything is hollow, because this version of the schema has no accepted state to fill a mark with — `accepted_support_edges` is zero.
>
> And before anyone starts counting their own theorems and getting suspicious: this paper numbers **nine** things. Two theorems, three lemmas, three propositions, one definition. So where do two hundred and forty come from? I will show you, on this paper, in two slides.

⏱ 1 min。**最后那句必须说**——听众此刻一定在想这件事，不接住的话后面二十帧他都在想。完整回答在 §10。

---

### 帧 40 — 240 FROM THE TARGET PAPER  ·  373 EVERYTHING ELSE

*（导入开场帧，旧稿未覆盖——照着幻灯片讲即可。）*

### 帧 41 — 14 OF THE 240 LAND ON A RESULT THE PAPER DECLARES  ·  9 OF 9 HIT

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

### 帧 42 — A DIFFERENT OBJECT  ·  74 CLAIMS, AUTHORED BY HAND

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

### 帧 43 — 29 OF 74  ·  THE CLOSURE OF ONE THEOREM

**出处：** `closed-form-branch.json`：29 节点。build 脚本 assert 这 29 个 id 是那 74 个的真子集。

> This extraction is real, and verified in code: the twenty-nine node ids of the closure are a strict subset of the seventy-four authored ids. The build fails if that ever stops being true.
>
> Ink is the backward closure of the main theorem. Ghosted is the other forty-five claims of the paper — which include five further external roots, the whole empirical branch behind Figure 2, three open problems and two stated limitations.
>
> So: the figure everything after this is built on covers twenty-nine of the paper's seventy-four claims. Thirty-nine percent. A closure answers "what does this theorem rest on". It does not answer "what is in this paper".

⏱ 1 min。

---

---

## VII · ONE THEOREM’S CHAIN（帧 44–54）

### 帧 44 — 1 CLAIM

*Start at the theorem. Nothing under it yet.*

### 帧 45 — 4 CLAIMS  ·  1 AND-GROUP

*Its support group opens: three premises. Drawn as a bracket, not three arrows, because it is an AND — any one missing and the target is not discharged.*

### 帧 46 — 7 CLAIMS  ·  3 GROUPS

*The same question asked of each premise: what discharges this? Two more groups open.*

### 帧 47 — 13 CLAIMS  ·  5 GROUPS

*The relaxation branch and the antiblocker branch descend separately. From here a heavier stroke and a faint ring mark what arrived at this step.*

### 帧 48 — 23 CLAIMS  ·  10 GROUPS

*The widest step — ten new claims at once, and three of the roots arrive together.*

### 帧 49 — 26 CLAIMS  ·  16 GROUPS

*Three more, completing the reduced-polytope side.*

### 帧 50 — 28 CLAIMS  ·  19 GROUPS

*Two: the full robustness of magic, and the resource theory that defines it.*

### 帧 51 — 29 CLAIMS  ·  20 GROUPS  ·  NOTHING LEFT TO EXPAND

见下

### 帧 52 — 9 ROOTS  ·  NOTHING BELOW THEM

**出处：** `closed-form-branch.json`：`roots` = 9。

> Nine claims have no support group at all. Nothing in the chain explains them. They are where the paper stops arguing and starts citing.
>
> Six are imported foundations. Three are the paper's own definitions that rest on nothing — which is why the DAG has nine sources rather than six.

⏱ 1 min。

---

### 帧 53 — FORMALIZATION ORDER  ·  14 OF 29

**出处：** `closed-form-branch.json`：`formalization_order` = 14 条。

> The system orders the chain for Lean, and can reach fourteen of the twenty-nine. The order begins at the MWIS definition, the Pauli window, the perfect-graph definition, and finite LP strong duality.
>
> Note the shape. Every filled mark sits in the lower-left mass. Nothing near the top is reachable.

⏱ 45 秒。

---

### 帧 54 — 15 UNREACHABLE  ·  CHAIN_INCOMPLETE

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

---

## VIII · THREE WISHES（帧 55–62）

### 帧 55 — ONE THEOREM’S CHAIN · 29 CLAIMS, 46 DEPENDENCIES

> Start from the object the deck has been building: the closure of one theorem. Twenty-nine claims, forty-six dependencies, laid out exactly as in the chain frames — same positions, same shapes, same claims.

⏱ 30 秒。

### 帧 56 — WISH ONE · MORE PAPERS, ONE NETWORK

> **Wish one.** Do this to the next paper, and the next. The heavier lines between clusters are the point: the same claim, leaned on by two different papers. That is the moment a pile of decomposed papers becomes one network.
>
> It is also the joint I said I cannot build. Deciding that this lemma and that lemma are the **same** lemma is an identity question, and my system does not answer it. Schematic layout, no counts, nothing asserted.

⏱ 1 min。

### 帧 57 — CUT ONE CLAIM OUT · COUNT WHAT LEAVES THE CLOSURE

**出处：** `closed-form-branch.json` 的 `edge_criticality`，46 条。`gen_skeleton.py` 里有断言，重算对不上就 build 失败。

> **Not a wish.** Cut one claim out of the graph — remove every dependency into it — and recompute the backward closure of the theorem. Count what is no longer in it. Size and ink are that count.
>
> Before you trust any of this: my computation reproduces all forty-six of the omission experiments the pipeline recorded, edge for edge. The assertion is in the build script and the build fails if it ever stops matching. I am not showing you a model of the pipeline. I am showing you the pipeline's own arithmetic.
>
> The graph program carries twenty-five of the twenty-nine. The distribution has a long thin tail and one spike — and that shape is what makes the rest of this worth attempting. You do not need taste to find the load-bearing parts. You need an omission test.

⏱ 1 min 30 s。

### 帧 58 — 46 DEPENDENCIES · WEIGHTED BY WHAT REMOVING ONE COSTS

> The same question asked of every dependency rather than every claim — and this one the pipeline had already answered for itself, in all forty-six cases.
>
> Line weight is what removing that one edge costs. Most of the graph is thin. The small chart is the whole distribution, sorted. It is deliberately small: the number on any one bar does not matter. The shape does. And the shape is a cliff.

⏱ 45 秒。

### 帧 59 — 29 FREE ON THEIR OWN · TOGETHER THEY COST 14 CLAIMS

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

### 帧 60 — THE SKELETON · 28 DEPENDENCIES, NOTHING LOST

> So the skeleton has to be computed properly: remove one dependency, recheck the whole closure, and only then try the next. Greedily, to exhaustion.
>
> Eighteen can go. Twenty-eight remain, and all twenty-nine claims are still reachable.
>
> That is what I mean by the skeleton of a theory. Not a summary, and not "the important bits" as judged by anybody — the subgraph you cannot cut any further without losing something, arrived at by an operation with no opinion in it.
>
> Two honest caveats. It is a statement about the graph **as recorded**: if the extraction missed a route, an edge looks more necessary than it is. And twenty-nine claims is small enough that a careful person could have done this by hand — slowly, and as the previous frame shows, probably wrongly.

⏱ 1 min 15 s。

### 帧 61 — WISH TWO · A CLAIM IN A GAP THE STRUCTURE NAMES

> **Wish two.** If you can compute where the load sits, you can also see where the structure is thin — a place where several load-bearing claims converge and nothing has been written.
>
> The diamond is a claim nobody has stated, proposed because the shape of the network says something belongs there.
>
> And note that the junction is drawn exactly like every other junction in this deck. A proposed claim gets no special status. Same AND-junction, same premises, same arrow, same kernel. Accepted, it is knowledge. Refused, the system names what was missing — and that becomes the next thing to read.

⏱ 1 min。

### 帧 62 — WISH THREE · A NEW PAPER INHERITS WHAT IS ALREADY CHECKED

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

---

## IX · IN CLOSING（帧 63–64）

### 帧 63 — IN CLOSING · WHAT IS SHOWN, AND WHAT IS NOT

> **新增帧。** deck 内置 speaker note：

> THE CONCLUSION. Do not soften it and do not oversell it - the credibility of the whole talk is spent or kept here.
>
> Two things are shown. A chain for one theorem that actually runs, and a structure whose load-bearing parts can be measured rather than guessed.
>
> Three things are not. The big extraction is not usable - every one of those six hundred nodes is blocked pending a review nobody has done. The chain that does run stands on a dependency graph I wrote by hand for this paper, and automatic library lookup - finding the matching declaration in Mathlib - is zero lines of code today. And none of this touches whether the formal object means the physics you had in mind; no kernel judges that.
>
> Then the last line, which is the honest version of the whole talk: the claim is not that this works. It is that it has become small enough to argue about. A year ago I could not have shown you a specific place where it stops.
>

### 帧 64 — DISCUSSION

> **新增帧。** deck 内置 speaker note：

> THE LAST FRAME. Ask, then stop talking. Do not answer your own questions.
>
> The framing is the useful part: it is entirely possible that this is a golden age for theoretical RESEARCH and a difficult one for theoretical RESEARCHERS, and those two things pull in opposite directions. Say that out loud - most people in the room have thought it and not said it.
>
> Question one is the honest one and usually gets the room going: excited, or frustrated? Both answers are respectable and people will disagree in public, which is what you want.
>
> Question two is the one that produces the best answers. If the machine can produce the result, which part did you actually want to do? Some people will say the proof; more will say the question, or the picture, or the argument about what it means.
>
> Question three brings it back to this talk: what would have to be checked before you would build on it. That is the only question the last forty minutes was about.
>
> If the room is slow, ask somebody what the ROOT claims of their last paper would be - the things they assumed without proof - and whether they would have been willing to write them down.
>

---

## 附录（从旧稿原样搬运）

> ⚠️ **下面这几节里的「帧 N」是 v0 编号，没有改。** 需要换算时查 §2 的对照表。

## 10. 专题：为什么一篇只有几个定理的短文会有 240 条 math claim

**这是全场最容易被打断的地方。** 听众看到 613 / 240 会立刻想："我的论文只有三个定理，哪来 240 条？"——这个念头一旦升起，后面二十帧他都在想这个。所以**要主动讲，不要等提问**。

建议安排：**帧 45（613 第一次出现）先埋一句**，**帧 47（240 → 14 的收缩）讲完整的例子**。

### 10.1 一句话版本（帧 45 用）

> Before anyone starts counting their own theorems and getting suspicious: this paper numbers **nine** things. Nine formal environments — two theorems, three lemmas, three propositions, one definition. So where do two hundred and forty come from? I will show you, on this paper, in two slides.

### 10.2 完整的例子（帧 47 用，约 2 分 30 秒）

**这是本次为你准备的核心材料。数据是今天从 `draft.tex` 和抽取产物里现算的。**

取论文的主定理 `thm:solvable`（draft.tex 第 270–283 行），和**紧接着它的那一段普通正文**（第 283–292 行）。两段紧挨着，一段带编号，一段不带。

| 区块 | 字节 | 行 | 有编号吗 | 抽出的 claim |
|---|---:|---|---|---:|
| `\begin{theorem} … \end{theorem}` | 607 B | 270–283 | 有 | **1** |
| 紧随其后的正文段落 | 1,817 B | 283–292 | **没有** | **5** |

**讲稿：**

> Here is the answer, and it is on this paper, not in the abstract.
>
> This is the main theorem — the closed form. Six printed lines, one numbered environment, six hundred bytes. The machine extracts from it exactly **one** claim. Fine. That matches your intuition.
>
> Now here is the paragraph immediately after it. Nine lines of ordinary running text. No environment. No number. Nothing you would cite. The machine extracts **five** claims from it:
>
> One — evaluating the closed form is a maximum-weight clique problem with weights the absolute expectation values.
> Two — every proper colouring of the frustration graph partitions the measurement set into commuting families, which can be measured jointly after Clifford diagonalisation.
> Three — because chromatic number equals clique number here, all the expectations you need can be collected in at most clique-number settings, instead of m.
> Four — the clique number of an n-qubit frustration graph is at most 2n+1.
> Five — and therefore the robustness of magic is at most the square root of 2n+1, throughout the solvable regime.
>
> Look at that last one. **That is the universal ceiling. It is one of the headline results of the paper — and it is a sentence with no number on it.**
>
> So: one numbered theorem, one claim. One unnumbered paragraph, five claims — one of which is a headline result. That ratio, not the theorem count, is what produces two hundred and forty.

**（如果房间反应好，再加这一句——很有杀伤力）**

> And I want to be clear that this is not the paper being sloppy. This is what every paper in our field looks like. We put numbers on the things we expect to be cited, not on the things we expect to be used.

### 10.3 另外三个来源（讲稿，约 1 分 30 秒，可压缩成一句）

> Unnumbered assertions are the biggest source. There are three more, and they are quicker.
>
> **First: vocabulary is claims too.** The closure of that one theorem is twenty-nine claims, and **eleven of them are definitions**. This paper numbers exactly **one** definition. To check the theorem you need to know what the measurement set is, what "no active dependencies" means, what the frustration graph is, what "perfect" means — and what the robustness of magic is, which is five definitions deep on its own: reduced robustness, reduced stabilizer polytope, full stabilizer polytope, full robustness. That is five chained definitions **for the single symbol on the left of the equals sign**.
>
> **Second: what the sentence does not say.** The record for this theorem carries four quantifiers, and **three of them are marked source-implicit** — n, m and the measurement set are never quantified anywhere in the sentence. It carries two stated assumptions, and **one more that is not stated**: m at least one, which the proof uses and the theorem header omits. Plus a convention: the empty clique contributes zero. None of that is visible in the six printed lines. Every bit of it is needed to check them.
>
> **Third: imports.** Five of the twenty-nine are things the paper cites rather than proves.
>
> Add those up and twenty-nine is not a surprising number for one theorem. It is a low one.

### 10.4 收束——这一段的真正论点（约 40 秒）

**这是整个专题的落点，比数字本身重要。**

> So here is how I would ask you to read the number two hundred and forty.
>
> It is **not** a measure of how complicated this paper is. It is a measure of **how much a reader has to reconstruct in order to check it**.
>
> A short paper is short precisely because it assumes a competent reader will silently rebuild all of that — the definitions, the implicit quantifiers, the hypothesis that only appears in the proof, the five unnumbered assertions in the paragraph after the theorem. Every one of us does that reconstruction, every time we read seriously, and then we throw it away.
>
> Two hundred and forty is not "this paper is complicated". It is **what you were already doing in your head**.

### 10.5 必须跟上的诚实补充（20 秒，不要省）

> One qualifier, because the rest of my talk depends on me not overselling this one. Two hundred and forty is an **unreviewed candidate count**, not a proven enumeration. Several of the two hundred and forty are restatements of each other. Nobody has read them. The only number here that survived a mechanical check is the one on the next line: **fourteen candidates, hitting nine of nine** declared results.

---

### 10.6 这一专题的数据出处

| 数字 | 出处 | 复核 |
|---|---|---|
| 论文共 9 个编号环境（2 thm / 3 lem / 3 prop / 1 def） | `draft.tex` 逐个 grep | ✅ |
| 主定理块 607 B（行 270–283）→ 1 条 candidate | `draft.tex` 字节 18668–19275 ∩ `assembly.json` source_spans | ✅ |
| 其后正文 1,817 B（行 283–292）→ 5 条 candidate + 2 条未解析位置 | `draft.tex` 字节 19275–21092 ∩ 同上 | ✅ |
| 闭包 29 条中 11 条是 definition | `closed-form-branch.json` 按 kind 统计（11 def / 6 lem / 5 external_contract / 4 thm / 2 prop / 1 foundation） | ✅ |
| 4 个量词中 3 个 SOURCE_IMPLICIT（n, m, M） | `MathClaimIRRegistry/.../graph-theoretic-nonstabilizerness.jsonl`，`structured_statement.quantifiers` | ✅ |
| 未声明假设 `m ≥ 1`，锚在 proof 而非 statement | 同上，`assumptions.source_implicit[0]`，`source_anchor: …closed-form-proof` | ✅ |
| 约定"空 clique 贡献 0" | 同上，`structured_statement.conventions` | ✅ |
| 5 条 external_contract：Gottesman / Howard–Campbell / Veitch / Varela / perfect-graph weighted duality | `closed-form-branch.json` | ✅ |

**RoM 的五级定义链**（如果被要求当场展开）：
`claim:reduced-rom` → `claim:reduced-stabilizer-polytope` → `claim:full-stabilizer-polytope` → `claim:full-rom` → `root:howard-campbell-rom`（外部引用）。五条里只有最后一条是论文明确标注为"引用"的。

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
