# Memory

记忆索引。详细内容放 `memory/` 下的主题文件，这里只留一行指针。

## 写法（穴居语压缩）
- 用压缩中文省 context：去虚词和连接词、留实义。技术词保留英文（file:line、API、flag、commit 等）。
- 追加，不覆写已有条目。绝不存密码、API key、密钥。
- 一条 = 一个事实或一个决定，带证据锚点（file:line / 命令 / URL）。

## 例
- 修 audio desync：bakeAudio 用截断后时长，别用原窗口长。Mp4Bake.java:264。
- z.ai 约 30s 空闲重置，thinking_mode 长静默是主因。调低 thinking 或换 bigmodel 端点。
- 用户 prefer：不用 em dash；研究自己 inline 做别 fanout。

## 索引
- (在这里加 `- [主题](memory/主题.md) — 一句话` 形式的指针)
