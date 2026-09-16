# Knowledge

本目录只保存通过独立发布门的可复用记录。推荐路径：

```text
knowledge/<record-kind>/<record-key>/r000001.json
```

记录采用 immutable revision；修正通过 `supersedes` 指向旧 revision。Run 产物不会自动进入本目录。Claim、证据、形式化和 StatusView 分离，禁止把汇总状态写回 immutable claim。

