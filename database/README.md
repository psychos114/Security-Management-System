# 医院物业安管系统小型数据库

本目录只包含数据库、样例资料和数据库结构，不包含前端、后端或完整项目。

## 主要文件

- `security_management_demo.db`：可直接打开的 SQLite 数据库。
- `knowledge_documents/`：42 份可供后续知识库/RAG 使用的 Markdown 小资料。
- `source_catalog.json`：10 项官方法规、标准和指导资料的来源目录。
- `schema_sqlite.sql`：SQLite 表结构。
- `schema_postgresql.sql`：后续迁移 PostgreSQL 时使用的表结构。
- `data_dictionary.md`：数据表用途说明。
- `validation_report.json`：完整性、外键、数据量和全文检索验证结果。
- `build_database.py`：重新生成全部数据库产物的脚本。

## 数据内容

- 6 个角色和 6 个虚构演示账号。
- 10 类医院物业突发事件、50 个处置步骤、10 条虚构事件样例。
- 7 个照片巡检场景、42 个检查项。每个检查项明确标记是否能由单张照片判断。
- 4 级演示 SLA、8 条虚构投诉、10 个沉淀风险点。
- 10 项官方来源目录、42 份知识资料及 SQLite 中文全文检索索引。
- 5 类每日计划、5 份虚构日报、5 条站内通知规则。

六类知识资料数量均在 5～10 份之间：

| 类别 | 数量 |
|---|---:|
| 应急处置 | 10 |
| 照片巡检 | 7 |
| 投诉闭环 | 5 |
| 日报 | 5 |
| 消防助手 | 10 |
| 多模态规范 | 5 |

## 查看方法

可以使用 DB Browser for SQLite 等图形化工具打开 `security_management_demo.db`。也可以使用 Python 内置的 `sqlite3` 模块读取。

常用查询示例：

```sql
-- 查看所有事件类型
SELECT code, name, default_severity, response_minutes
FROM event_types
ORDER BY id;

-- 查看消防通道照片巡检清单
SELECT *
FROM v_patrol_checklist
WHERE scene_code = 'FIRE_PASSAGE';

-- 查看无法仅凭单张照片确认的检查项
SELECT scene_name, title, expected_visual_evidence
FROM v_patrol_checklist
WHERE can_confirm_from_single_photo = 0;

-- 查看投诉及 SLA 状态
SELECT complaint_no, title, severity, status, response_due_at, resolution_due_at
FROM complaints
ORDER BY received_at;

-- 搜索消防安全知识
SELECT doc_code, title
FROM knowledge_fts
WHERE knowledge_fts MATCH '消防安全';

-- 查看带官方来源的知识条目
SELECT *
FROM v_knowledge_citations
WHERE category = 'fire_assistant';
```

## 重新生成

在项目文件夹中运行：

```powershell
python database\build_database.py
```

脚本会重新生成 SQLite 数据库、知识资料、来源目录、两个结构脚本和验证报告。

## 重要边界

1. 所有事件、投诉、日报、人员和医院名称都是虚构演示数据，不含真实患者信息。
2. 应急处置卡是学习项目的流程样例，不是医院正式应急预案，也不构成医疗、法律、消防或工程意见。
3. AI 可自动生成任务和通知，但高风险动作需要有权限人员确认；现实中的紧急报警、抢救和避险不得因系统审批延误。
4. `深圳市医院消防安全管理规定` 发布于 2010 年，数据库已标记为 `needs_review`。正式使用前需向深圳消防、卫健等主管部门核验文件效力。
5. 官方资料只保存来源元数据和检索摘要。消防助手回答具体问题时，应回到官方全文核对条款、日期和有效状态。
6. `schema_postgresql.sql` 提供后续正式项目的结构基础；当前样例数据以 SQLite 为准。
