# 操作与存储

脚本使用 Python 3 标准库（sqlite3），不调用外部 API。AI 负责理解与撰写档案，脚本不自动分析文字。

以下 `SCRIPT` 指本 skill 下 `scripts/style_store.py` 的绝对路径；用可用 Python 解释器运行，路径含空格时正确引用。

## 数据位置

默认：`$CODEX_HOME/style-learner/styles.sqlite3`；未设 CODEX_HOME 时为 `~/.codex/style-learner/styles.sqlite3`。环境变量 `STYLE_LEARNER_HOME` 可独立指定数据文件夹，或每次传 `--home`。首次确定后始终使用同一路径；不可写时报告，不能静默更换。测试必须指定临时 `--home`。

`init` 幂等创建空的 `daily` 档案和设置（continuous=true，learn_style=daily，write_style=null）。continuous 是技能内的学习开关，不是系统监听器；没有宿主调用不会自行执行。真正学习仍需本次被调用或持续学习接入。

```text
python SCRIPT init
python SCRIPT list
python SCRIPT create academic --name 论文写作
python SCRIPT show academic
python SCRIPT settings
python SCRIPT settings --learn-style daily --write-style academic
python SCRIPT settings --write-style none
python SCRIPT settings --continuous off
python SCRIPT fingerprint --file extracted.txt
```

Style ID 用小写字母开头，随后小写字母、数字、短横线，最多 48 字符；中文用于显示名称。不存在的默认 style 会报错；不自动指向 daily。

## 保存一次学习

先 `show` 取得 revision，AI 根据旧档案和新证据合并生成 UTF-8 Markdown 档案文件及 JSON 证据文件。证据文件字段如下（实际内容须替换为真实摘要）：

```json
{
  "source_key": "稳定来源标识或内容哈希",
  "kind": "conversation",
  "summary": "无个人事实的特征证据摘要；包括材料范围与规则变化理由"
}
```

kind 允许 conversation、work、reference、correction。执行：

```text
python SCRIPT learn academic --profile-file merged.md --evidence-file evidence.json --expected-revision 0
```

保存是单个数据库事务，同时写档案、证据与版本快照；重复 source_key 返回 duplicate，不重复计数。revision 过期返回冲突：重新读取最新档案，合并后再保存，不覆盖其他对话的更新。`learn` 不检查 continuous，因为暂停自动学习不应阻止用户明确发起的作品学习；AI 必须在自动学习入口检查开关。

```text
python SCRIPT history academic
python SCRIPT restore academic --revision 1 --expected-revision 3
python SCRIPT export academic --dest /absolute/new-folder
python SCRIPT delete academic
```

history 返回历史版本和证据摘要。restore 将旧版本恢复为新的当前版本，保留可追溯历史；旧证据去重键仍保留。export 创建独立的 `style-academic` 技能快照（不是实时同步），不导出证据历史；目标目录必须不存在。导出的 SKILL.md 引用单独的 profile.md，样本衍生文本不会进入指令入口。只在已学习后导出。

delete 仅用于用户明确要求删除整个 style 时：删除该 style 的档案、证据与版本记录，引用它的默认设置清空。它不删除原始作品、导出快照或外部备份，不承诺法证级磁盘擦除。

如果用户要求“忘记某条特征”而不只修改当前规则：先在内存准备保留的净化档案，用 delete 删除该 style 全部历史，再 create 与 learn 保存净化后的档案，最后恢复必要默认设置。明确说明该操作也清除了此 style 的其他历史版本。无法确定删除范围时先澄清。

临时合并文件只包含风格摘要，写入成功后可删除本次创建的临时文件。不要把原始作品复制到技能目录或导出包。跨设备同步需用户自行迁移同一库；不要让云盘同时写 SQLite 文件。
