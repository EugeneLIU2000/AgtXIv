# AgtXIv paper-first architecture explorer

这个 local website 直接根据 `docs/architecture/agtxiv-paper-first-layered.architecture.json` 重建流程图，不是上一版的 schema 教学页。

它保留了原图的 19 个节点、18 条有向关系和 4 个 guided views：

- Construction / 构建
- Verification / 核查
- Release & Knowledge / 发布与知识
- Provisional Path / 临时路径

点击节点可查看其职责、输入、输出和边界；切换 view 会突出原流程图对应的节点和箭头。

从仓库根目录运行：

```bash
python3 -m http.server 8000 --bind 127.0.0.1
```

打开 <http://127.0.0.1:8000/demo_architecture/>。


## Archive location notice — 2026-09-08

This historical prototype moved from `demo_architecture/` to `docs/archive/prototypes/demo_architecture/`. The earlier text is preserved verbatim as historical context; preview addresses above refer to the former location. The maintained V3 website and actual source-analysis service are in `web/`.

From the repository root, run `python3 -m http.server 8000 --bind 127.0.0.1` and open <http://127.0.0.1:8000/docs/archive/prototypes/demo_architecture/>. Alternatively serve the archived prototype with `python3 -m http.server 8000 --bind 127.0.0.1 --directory docs/archive/prototypes/demo_architecture`. Open <http://127.0.0.1:8000/> in that mode. Only this notice was appended; original file prefixes and every other asset remain byte-identical. The path mapping, hashes and recovery instructions are in `docs/audits/repository-archive-manifest.json` and `docs/audits/repository-organization.md`.
