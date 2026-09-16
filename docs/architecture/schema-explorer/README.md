# 架构与 Schema 交互图

打开 `index.html` 即可离线使用，无 CDN、无 API 调用。浅色主题，四个主题视图、模块输入输出、实现状态、字段筛选、原始 schema 下载与代码证据。

字段和证据是构建时快照，刷新：

```sh
node docs/architecture/schema-explorer/build-data.mjs
```

`schema-data.js` 是从仓库生成的只读展示数据。图中的模块说明和实现状态在 `app.js` 中维护，必须随代码审阅更新；schema 的存在不代表执行服务已实现。最近核对：2026-09-11。未执行科学验证。

图为目标架构与现状对照，不是全部 64 类契约的依赖总图，也不改变原 schema 约束。现有计划、范围冻结、发布审计等契约未全部铺在主图上，可以通过原始 schema 引用继续查阅。
