# Docs 目录索引

这份索引用来帮助你快速找到项目里的文档，也说明以后新文档应该放到哪里。

## 当前目录结构

### `docs/interfaces/`

存放 5 个一级菜单界面的说明，以及合并后的总览文档。

- `interface_manual_full.md`
- `talents_interface_guide.md`
- `scripts_generate_interface_guide.md`
- `scripts_review_interface_guide.md`
- `trends_interface_guide.md`
- `library_interface_guide.md`

### `docs/operations/`

存放部署、数据库迁移、后端启动这类操作手册。

- `postgresql_deployment_guide.md`
- `database_change_workflow.md`
- `backend_api_quickstart.md`

### `docs/architecture/`

存放系统总体理解、Agent 架构和外部能力说明。

- `walkthrough_allbyopus.md`
- `compliance_rag_agent_guide.md`
- `tavily_trend_hunter_guide.md`

### `docs/knowledge-base/`

存放知识库建设方案、采集计划和采集状态。

- `rag_kb_collection_plan.md`
- `rag_kb_collection_status.md`

### `docs/testing/`

存放测试报告。

- `full_system_test_report.md`
- `human_behavior_test_report.md`

### `docs/project-history/`

存放项目执行记录、阶段性计划和重构过程文档。

- `implementation_plan.md`
- `refactor_execution_log.md`

## 推荐阅读顺序

如果你是第一次接触项目，建议按这个顺序看：

1. `docs/interfaces/interface_manual_full.md`
2. `docs/architecture/walkthrough_allbyopus.md`
3. `docs/operations/postgresql_deployment_guide.md`
4. `docs/operations/database_change_workflow.md`
5. `docs/testing/human_behavior_test_report.md`

## 以后新增文档怎么放

- 界面怎么用：放到 `docs/interfaces/`
- 启动、部署、数据库、运维：放到 `docs/operations/`
- 系统架构、Agent、外部服务说明：放到 `docs/architecture/`
- 知识库采集与资料治理：放到 `docs/knowledge-base/`
- 测试结果与回归记录：放到 `docs/testing/`
- 项目过程、计划、重构纪要：放到 `docs/project-history/`
