# Independent static source-grounding note / 独立静态溯源记录

Scope: candidate extraction for the first real-paper V3 local loop. This is a software-assisted static source review, not adopted scientific authority, mathematical certification, or formal scope approval. Interpretation status: **ORACLE_PROPOSED / UNVERIFIED**. No prior V1/V2 fixture verdict is treated as reviewed V3 truth.

## Selection

The independent reviewer read the selected TeX in full and compared the five local source directories. Main-source sizes: stabilizer-code thesis 333,351 bytes / 6,304 lines; resource theory 110,546 / 1,875; robustness 56,170 / 548; predicting magic 110,488 / 1,129; graph-theoretic nonstabilizerness 69,678 / 1,021 plus its 3,525-byte header.

Selected: `robustness-of-magic`, because the main text and appendix are in one short local source with an explicit representative argument, not because of an expected favorable scientific verdict.

Source: `Reference/Application of a resource theory for magic states to fault-tolerant quantum computing/Robustness_main_appendix.tex`.

Original SHA-256: `48adf581a5f8353bb1125c75b8e0a075ff7ba79917f2a12d9f7e0f4ad1a8312d`.

The reviewer observed six original local files: TeX (56,170 bytes), BBL (32,301), source archive (278,200), `roughFIG.pdf` (113,649), `Geometric_robustness.pdf` (26,918), and `Concentric_robustness2.pdf` (148,921). The archive contains five regular members matching the five non-archive files byte-for-byte. The three figures are present and cited, although not individually listed in the old corpus's `source_asset_paths`; they must appear in the new candidate inventory without changing the old corpus pins.

**Observation update:** Parent inspection subsequently found eight `build/` files in the live source directory (AUX, LOG, FLS, latexmk database, notes bibliography, PDF, SyncTeX and OUT). These are additional local generated artifacts, not source-publication evidence or executions performed by this task. The current candidate capture must inventory them explicitly, preserve their bytes, and distinguish the six archive/source files from the larger live directory denominator. A fresh capture, not this note, determines the exact final file count and hashes.

## Representative chain: R3 trace-preserving monotonicity

All byte offsets below are zero-based, half-open over original TeX bytes.

| Anchor | Lines | Bytes | Candidate interpretation |
|---|---|---|---|
| Robustness definition | 75–79 | `[9218,10126)` | Minimum signed pseudomixture coefficient L1 norm over pure stabilizer atoms |
| R3 statement | 225 | `[33249,33406)` | For trace-preserving stabilizer channels, output robustness is no larger than input robustness |
| Channel action | 251–255 | `[35064,35619)` | Each input stabilizer atom maps to a normalized nonnegative mixture of output stabilizer atoms |
| Output pseudomixture | 256–259 | `[35619,35847)` | Regrouped coefficients give a feasible output decomposition and upper bound |
| Norm contraction | 260–265 | `[35847,36153)` | Triangle inequality and row normalization bound the norm; optimal input decomposition supplies the final equality |
| Separate extension | 266 | `[36153,36418)` | Average/postselection assertion with an external citation, not discharged by the selected trace-preserving argument |
| Downstream relevance | 140–144 | `[21594,22839)` | Robustness comparisons are used for synthesis lower bounds; numerical values and constructions are separate obligations |

Conditions to keep explicit: finite multiqubit density operators; pure stabilizer decomposition atoms; real signed input coefficients; channel linearity; trace preservation; nonnegative mixture coefficients with each row summing to one. **Mixture preservation is not atom-to-atom preservation.** Optimal input decomposition is a contextual reconstructed proof requirement, not an explicit new premise quoted from the proof paragraph. Feasibility/attainment, finite-sum algebra and triangle inequality remain mathematical obligations, not performed checks.

## Open boundaries and omissions

- The line-266 postselection extension is a separate claim. Do not infer monotonicity for every normalized postselected branch from trace-preserving R3.
- Lines 69, 110 and 430 reference supplementary data/material. Numerical matrices, code, datasets and solver certificates were not located in the inspected original directory/archive; this is not a claim about remote submissions or the entire repository.
- Three PDF figures are byte-present but their visual contents and generating computations were not reviewed.
- No active TeX include of another source file was observed; notation macros are inline. External `revtex4-1`/package versions are not bundled or checked. `Robustness_main.bib` is absent locally while the job-name BBL is present. Rebuild completeness and published rendering remain unknown.
- Whole-text static candidate inventory must retain simulation overhead, lower bounds, numerical robustness, maximization, gate classifications, synthesis optimality and interconvertibility as candidate/unreviewed families. A review of R3 does not discharge these claims or establish whole-paper scientific coverage.

## 中文摘要

首篇选择 robustness 论文，理由是原文较短、正文和附录同文件且有可逐步溯源的论证，不是预设结果正确。独立静态审阅确认 R3 原文及对应推导位置；数学条件、最优分解的上下文重构和未检查的背景义务须分开记录。

原始材料六文件中三张 PDF 真实存在，与已固定压缩包成员一致；旧清单未单列它们，不等于文件缺失。后续现场又观察到八个 `build/` 文件，候选清点必须保留这些新增本地文件并明确其生成物性质，不能将其当成本次执行回执或科学支持。最终分母以实际捕获为准。

迹保持命题、平均/后选择推广、数值最优值与门合成结论必须分别保留。补充矩阵、数值代码、宏包/渲染环境、图像含义和外部引用证明尚未验证。本记录仅支持原文溯源及检查边界，不是整篇完备、科学通过、正式冻结或知识准入。
