# DFMEA 个人记录系统

Web 端 DFMEA（设计失效模式与影响分析）工具，以系统/部件为单位组织分析，支持 AIAG-VDA 标准。

## 技术栈

- **后端**: Python 3 + FastAPI
- **前端**: Vue 3 (CDN) + 原生 JS
- **数据库**: SQLite
- **样式**: 自包含 CSS，支持浅色/深色/自动主题

## 快速开始

```bash
# 安装依赖
pip install -r requirements.txt

# 启动服务（默认 http://localhost:5000）
python -m uvicorn app:app --port 5000 --reload
```

上传文件默认存储在 `%USERPROFILE%\dfmea_db\uploads\`，可通过环境变量 `DFMEA_DB_DIR` 自定义路径。

数据库后端支持：

- `DFMEA_DB_BACKEND=postgres`：PostgreSQL（多人部署推荐）
- `DFMEA_DB_BACKEND=sqlite`：SQLite（单机/回退）

PostgreSQL 默认连接参数：

- 数据库：`dfmea`
- 用户：`postgres`
- 主机：`localhost:5432`

可通过 `DFMEA_POSTGRES_PASSWORD`、`DFMEA_DATABASE_URL` 等环境变量覆盖。SQLite 迁移到 PostgreSQL：

```bash
python scripts/migrate_sqlite_to_postgres.py --password <postgres密码> --database dfmea
```

在新机器从 0 部署时，推荐直接运行：

```powershell
.\Startup\run_server.ps1
```

启动脚本会自动检查 Python 依赖、PostgreSQL 服务、连接密码、目标数据库是否存在，并在启动前执行一次数据库初始化测试。全新的空数据库会自动创建默认管理员 `admin / admin123456`；如果是迁移已有 PostgreSQL 数据库，用户账号以数据库中已有记录为准。

首次启动会自动创建管理员账号：

- 用户名：`admin`
- 默认密码：`admin123456`

部署到多人环境前，建议通过环境变量 `DFMEA_ADMIN_PASSWORD` 设置初始密码，或首次登录后立即在“账号管理”中修改。
生产运行请不要使用 `--reload`，可参考 `Startup/run_server.ps1` 直接以 `uvicorn app:app --host 0.0.0.0 --port 10197` 启动。

## 功能

- **多项目管理** — 递归结构树，拖拽排序
- **功能分析** — 功能描述、设计要求、性能指标、接口说明
- **DFMEA 工作表** — 失效模式、失效影响、S/O/D 评分、RPN/AP 自动计算（AIAG-VDA 矩阵）
- **改进措施跟踪** — 责任人、期限、状态、修订评分
- **参考资料关联** — 文件上传 / 外部链接，可关联到失效模式
- **导入导出** — Excel 完整导出 / 模板下载 / JSON 备份与恢复

## 评分依据

严重度 S、频度 O、探测度 D 按 AIAG-VDA 1-10 级标准评分。

AP（措施优先级）根据 S/O/D 组合自动判定 H / M / L（AIAG-VDA 判定矩阵）。
