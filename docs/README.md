# Docs 目录索引

这份索引用来帮助你快速找到代码仓库中保留的项目文档。仓库面向代码审阅和项目运行，论文草稿、参考文献 PDF、Word 导出文件和中期汇报材料不再放入 GitHub。

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

### `docs/knowledge-base/`

存放知识库建设和采集状态说明。

- `rag_kb_collection_status.md`

### `docs/testing/`

存放测试报告。

- `full_system_test_report.md`
- `human_behavior_test_report.md`

## 推荐阅读顺序

如果你是第一次接触项目，建议按这个顺序看：

1. `docs/interfaces/interface_manual_full.md`
2. `docs/operations/postgresql_deployment_guide.md`
3. `docs/operations/database_change_workflow.md`
4. `docs/operations/backend_api_quickstart.md`
5. `docs/testing/human_behavior_test_report.md`

## 以后新增文档怎么放

- 界面怎么用：放到 `docs/interfaces/`
- 启动、部署、数据库、运维：放到 `docs/operations/`
- 知识库采集与资料治理说明：放到 `docs/knowledge-base/`
- 测试结果与回归记录：放到 `docs/testing/`
- 论文草稿、参考文献 PDF、Word 输出、汇报 PPT：不要提交到代码仓库
