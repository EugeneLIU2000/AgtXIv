# Runs

本目录保存每次 Query 执行的不可变数据集清单。推荐路径：

```text
runs/<query-key>/<run-id>/manifest.json
```

一个 Run 必须固定 Query、paper versions、代码、`reproducibility_refs`、输入 snapshot、全部输入输出及 provenance。`run_artifacts[]` 表示 Run–Artifact 关联，因此 role 和 path 不属于全局 Artifact 身份。程序执行状态与科学 resolution outcome 分开记录。完成后的 manifest 不原地修改；重试创建新 Run 并用 `retry_of_run_id` 指向旧日志。
