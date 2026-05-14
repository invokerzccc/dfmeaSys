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

数据文件（数据库 & 上传文件）默认存储在 `C:\Users\<用户名>\dfmea_db\`，可通过环境变量 `DFMEA_DB_DIR` 自定义路径。

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
