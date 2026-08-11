# 数据字典摘要

| 表 | 用途 |
|---|---|
| departments / roles / users | 单公司内部组织和六类演示角色 |
| locations | 虚构医院及重点区域 |
| event_types / event_playbook_steps | 10类突发事件和处置步骤 |
| incident_examples | 每类事件1条虚构演示事件 |
| inspection_scenes / inspection_items | 7类照片场景及检查项，明确哪些不能凭单图判断 |
| sla_policies / complaints | 四级SLA与8条虚构投诉 |
| risk_points | 由投诉或事件沉淀的10个风险点 |
| knowledge_sources | 10项官方法规、标准和指导资料元数据 |
| knowledge_documents / knowledge_chunks | 六类小型知识资料及后续RAG分块 |
| knowledge_fts | SQLite全文检索索引 |
| daily_plan_templates / daily_report_samples | 5类计划与5份虚构日报 |
| notification_rules | 站内通知和超时升级演示规则 |

所有 `*_json` 字段在 SQLite 中以合法 JSON 文本保存，迁移到 PostgreSQL 后使用 `jsonb`。
