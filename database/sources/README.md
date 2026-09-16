# Sources

本目录保存冻结论文版本的清单，不要求复制原文 bytes。推荐路径：

```text
sources/<provider>/<paper-work-key>/<version>/manifest.json
```

每个清单至少固定 `paper_version_id`、`primary_source_artifact_id`、完整 `source_artifact_ids`、仓库相对路径或 URI、media type、byte size、SHA-256、获取时间和许可信息。TeX 主文件、宏、参考文献、图和补充材料属于同一 source bundle；未枚举完整时必须标记 `source_bundle_complete=false`。新版本追加目录，禁止覆盖旧版本。
