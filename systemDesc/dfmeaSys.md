# DFMEA 个人记录系统 — 开发需求文档

## 1. 项目概述

### 1.1 背景
需要一个**个人使用的通用 DFMEA 记录系统**，以"系统/部件"为单位创建和组织 DFMEA 分析。首个分析对象为**液冷机组电控系统**，从**控制器**开始。

### 1.2 核心目标
- **通用化**：模板与系统解耦，可复用于任意产品或部件
- **渐进填充**：支持按分析流程逐步录入（结构 → 功能 → 失效 → 风险 → 措施），不用一次填完
- **可追溯**：每个分析项可关联参考材料（系统图、部件规格书、功能分析文档等）
- **个人友好**：本地运行，数据自有，易于备份

### 1.3 技术栈

| 层 | 选型 | 理由 |
|---|---|---|
| 后端 | Python 3 + **FastAPI** | Pydantic 自动校验 18+ 列 DFMEA 数据；Swagger 文档自动生成；异步文件上传 |
| 前端 | **Vue 3 CDN**（核心表格/树组件） + 原生 JS（简单页面） | 响应式 computed 自动计算 RPN/AP；v-for 渲染表格行；无构建步骤，单 `<script>` 标签引入 |
| 数据库 | **SQLite** | 零配置、单文件、Python 内置；DFMEA 是 OLTP CRUD 场景，SQLite 最匹配 |
| 文件存储 | **文件系统** `C:\Users\invok\dfmea_db\uploads\` | 大文件（图纸、PDF、样本）存文件系统，DB 只存路径；文件可直接在资源管理器打开 |
| 样式 | 自写 CSS（桌面端优先） | 不用框架，保持依赖最小化 |
| 运行方式 | `uvicorn app:app --port 5000` 一键启动，浏览器访问 `localhost:5000` | |

### 1.4 技术决策说明

**为什么不是 Streamlit？** Streamlit 的每次交互触发全量 Python 脚本重跑，与可编辑多列电子表格的交互模式冲突——每次单元格编辑都会导致页面闪烁重渲染。此外树形导航+右侧详情面板的布局在 Streamlit 中很难实现。

**为什么不是 Flask？** FastAPI 的 Pydantic 模型对 DFMEA 这种字段多、约束多（S/O/D 1-10 分、AP 查表判定、层级树递归结构）的数据验证场景，能省掉大量手写校验代码。且 `/docs` 自动生成 Swagger 接口文档，方便调试。

**为什么是 Vue 3 CDN 而非完整 SPA 框架？** 120KB gzip 的 CDN 引入，零构建步骤。DFMEA 表格需要：单元格编辑 → 自动重算 RPN → 查表判定 AP → 行高亮变色 → debounce 保存，这些用 Vue 的 `reactive()` + `computed()` + `watch()` 几行代码解决，原生 JS 需要大量 DOM 操作代码。

**为什么 SQLite + 文件系统分离？** 图纸、样本文件可能较大，放 BLOB 会让 DB 膨胀，备份缓慢。文件存 `C:\Users\invok\dfmea_db\uploads\`，DB 只存相对路径，DB 保持精简快速，文件可随时在资源管理器打开。

---

## 2. 数据模型

### 2.1 核心实体

```
Project（项目）
  ├── System（系统）          e.g. 液冷机组
  │     ├── Subsystem（子系统）  e.g. 电控系统
  │     │     ├── Component（部件） e.g. 控制器
  │     │     │     ├── Function（功能项）
  │     │     │     │     ├── FailureMode（失效模式）
  │     │     │     │     │     ├── FailureEffect（失效影响）
  │     │     │     │     │     ├── FailureCause（失效原因）
  │     │     │     │     │     └── ControlMethod（现行控制）
  │     │     │     │     └── ...
  │     │     │     └── Reference（参考材料）
  │     │     └── ...
  │     └── ...
  └── Template（模板） — 与 Project 关联的可复用结构
```

### 2.2 表结构设计（SQLite）

```sql
-- 项目表
project: id, name, description, created_at, updated_at

-- 结构树（递归父子关系，灵活支持系统/子系统/部件/零件多层级）
structure_node: id, project_id, parent_id(NULL=顶层), name, type(系统/子系统/部件/零件), 
               part_number, description, order_index, created_at, updated_at

-- 功能分析
function_item: id, node_id, function_desc, requirement, performance_spec, 
               work_mode, interface_desc, order_index

-- 失效模式（DFMEA 核心工作表）
failure_mode: id, function_item_id, mode_desc, severity(S), 
              classification(特殊特性), potential_effect, potential_cause,
              occurrence(O), prevention_control, detection_control, detection(D),
              rpn(S*O*D), action_priority(H/M/L), recommended_action,
              action_owner, action_due_date, action_status, action_effect,
              revised_S, revised_O, revised_D, revised_RPN,
              notes, order_index

-- 参考材料
reference: id, project_id, node_id(NULL=项目级), title, type(系统图/规格书/分析报告/其他),
           file_path, url, notes, created_at

-- 操作日志
audit_log: id, project_id, action, entity_type, entity_id, detail, created_at
```

### 2.3 模板机制
- 每个 Project 创建时可选择从**空白开始**或从**已有项目复制结构**（作为模板）
- 结构树层级不硬编码，用户自由定义

---

## 3. 功能模块

### 3.1 项目仪表盘 `/`
| 功能 | 说明 |
|------|------|
| 项目列表 | 卡片式展示所有 DFMEA 项目 |
| 新建项目 | 输入名称、描述，可选从已有项目复制结构 |
| 删除项目 | 确认后删除（软删除，可恢复） |
| 项目搜索 | 按名称模糊搜索 |
| 快捷统计 | 每个项目显示：部件数、已分析功能数、高风险项数(RPN>100 或 AP=H) |

### 3.2 结构树管理 `/project/{id}/structure`
| 功能 | 说明 |
|------|------|
| 树形展示 | 左侧树形导航（系统 → 子系统 → 部件 → ...） |
| 增删节点 | 右键菜单：添加子节点、重命名、删除、上移/下移 |
| 拖拽排序 | 支持同级节点拖拽调整顺序 |
| 节点详情 | 点击节点右侧显示部件号、描述等信息 |
| 层级 | 不限制层级深度 |

### 3.3 功能分析 `/project/{id}/node/{node_id}/functions`
| 功能 | 说明 |
|------|------|
| 功能列表 | 表格展示当前节点所有功能项 |
| 添加功能 | 功能描述、设计要求、性能指标、工作模式、接口说明 |
| 批量导入 | 支持粘贴多行文本批量创建功能项 |
| 编辑/删除 | 行内编辑或弹窗编辑 |

### 3.4 DFMEA 工作表 `/project/{id}/node/{node_id}/dfmea`
这是核心模块，标准 DFMEA 表格视图：

| 列 | 中文 | 输入方式 | 说明 |
|---|---|---|---|
| 序号 | # | 自动 | |
| 功能 | 功能描述 | 自动关联 | 从功能分析读取 |
| 失效模式 | Failure Mode | 文本输入 | |
| 失效影响 | Failure Effect | 文本输入 + 多选 | 可串联下一层级影响 |
| 严重度 S | Severity | 下拉 1-10 | 按评分准则 |
| 特殊特性 | Classification | 下拉 | SC/CC/— |
| 失效原因 | Failure Cause | 文本输入 | |
| 频度 O | Occurrence | 下拉 1-10 | |
| 预防控制 | Prevention | 文本输入 | |
| 探测控制 | Detection | 文本输入 | |
| 探测度 D | Detection | 下拉 1-10 | |
| RPN | S×O×D | 自动计算 | |
| AP | 措施优先级 | 自动判定 H/M/L | AIAG-VDA 表 |
| 建议措施 | Recommended Action | 文本输入 | |
| 责任人/期限 | Owner/Date | 文本+日期 | |
| 措施状态 | Status | 下拉 | 未开始/进行中/已完成 |
| 措施效果 | Action Effect | 文本 | |
| 修订S/O/D/RPN | Revised | 手动输入 | |

**交互特性：**
- 行内编辑（点击单元格直接改）
- 支持添加/删除行、上移/下移
- 按 RPN 或 AP 自动高亮（红/黄/绿）
- 表头固定，横向滚动

### 3.5 参考材料 `/project/{id}/references`
| 功能 | 说明 |
|------|------|
| 上传文件 | 支持 PDF、图片(png/jpg)、Office 文档 |
| 外部链接 | 添加 URL 引用 |
| 分类标签 | 系统图/规格书/分析报告/其他 |
| 关联节点 | 材料可关联到特定结构节点 |
| 预览 | 图片和 PDF 在浏览器内预览 |

### 3.6 导出 `/project/{id}/export`
| 功能 | 说明 |
|------|------|
| 导出 Excel | 标准 DFMEA 工作表导出 .xlsx |
| 导出 JSON | 完整项目数据备份 |
| 导入 JSON | 从备份恢复 |

---

## 4. 交互设计原则

### 4.1 导航结构
```
┌──────────────────────────────────────────────┐
│  [← 返回首页]  项目名称    [结构] [功能] [DFMEA] [参考资料] [导出] │  ← 顶部 Tab
├────────────┬─────────────────────────────────┤
│  结构树    │                                 │
│  ├ 液冷机组 │        主工作区                  │
│  │ ├ 电控   │                                 │
│  │ │ ├ 控制器│    （表格 / 表单 / 预览）         │
│  │ │ ├ 传感器│                                 │
│  │ ├ 水路   │                                 │
│  │ ...     │                                 │
└────────────┴─────────────────────────────────┘
```

### 4.2 设计约束
- **桌面端优先**：针对 1920×1080 及以上分辨率设计
- **无登录**：个人单机使用，不需要用户系统
- **自动保存**：编辑后 2 秒自动保存（debounce）
- **操作可撤销**：关键操作提供撤销提示（toast 通知，5 秒可点击撤销）
- **深色/浅色主题**：跟随系统设置

---

## 5. 文件结构

```
YL/                                  # 代码目录
├── app.py                           # FastAPI 入口
├── requirements.txt                 # Python 依赖
├── config.py                        # 配置（数据库路径、上传目录等）
├── db/
│   ├── schema.sql                   # 建表语句
│   └── seed.sql                     # 初始数据（评分准则、AP 判定矩阵等）
├── models/                          # 数据访问层
│   ├── project.py
│   ├── structure.py
│   ├── function.py
│   ├── failure_mode.py
│   ├── reference.py
│   └── audit.py
├── routes/                          # FastAPI 路由
│   ├── pages.py                     # 页面路由（返回 HTML）
│   ├── api_project.py
│   ├── api_structure.py
│   ├── api_function.py
│   ├── api_failure.py
│   ├── api_reference.py
│   └── api_export.py
├── services/                        # 业务逻辑
│   ├── dfmea_calc.py                # RPN 计算、AP 判定
│   ├── export.py                    # Excel/JSON 导出
│   └── import.py                    # JSON 导入
├── static/
│   ├── css/
│   │   └── style.css
│   ├── js/
│   │   ├── app.js                   # 全局（路由、导航、通知）
│   │   ├── structure.js             # 结构树组件（Vue）
│   │   ├── function.js              # 功能分析组件
│   │   ├── dfmea.js                 # DFMEA 表格组件（Vue）
│   │   ├── reference.js             # 参考资料组件
│   │   └── utils.js                 # 工具函数（debounce、格式化、API 封装）
│   └── uploads/                     # [废弃，改存用户目录]
├── templates/                       # Jinja2 页面模板
│   ├── base.html                    # 基础布局（含 Vue 3 CDN）
│   ├── index.html                   # 首页仪表盘
│   └── project.html                 # 项目详情（含 Tab 切换）
│
C:\Users\invok\dfmea_db\             # 数据目录（独立于代码）
    ├── dfmea.db                     # SQLite 数据库
    └── uploads\                     # 上传文件存储
        └── {project_id}\            # 按项目分文件夹
```

---

## 6. API 设计概要

遵循 RESTful 风格，所有数据接口以 `/api/v1/` 为前缀：

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/projects` | 项目列表 |
| POST | `/api/v1/projects` | 创建项目 |
| GET | `/api/v1/projects/{id}` | 项目详情 |
| PUT | `/api/v1/projects/{id}` | 更新项目 |
| DELETE | `/api/v1/projects/{id}` | 删除项目 |
| GET | `/api/v1/projects/{id}/structure` | 结构树 |
| POST | `/api/v1/projects/{id}/structure` | 添加节点 |
| PUT | `/api/v1/structure/{id}` | 更新节点 |
| DELETE | `/api/v1/structure/{id}` | 删除节点 |
| PUT | `/api/v1/structure/{id}/move` | 移动/排序 |
| GET | `/api/v1/nodes/{id}/functions` | 功能列表 |
| POST | `/api/v1/nodes/{id}/functions` | 添加功能 |
| PUT | `/api/v1/functions/{id}` | 更新功能 |
| DELETE | `/api/v1/functions/{id}` | 删除功能 |
| GET | `/api/v1/nodes/{id}/failures` | DFMEA 工作表 |
| POST | `/api/v1/nodes/{id}/failures` | 添加失效行 |
| PUT | `/api/v1/failures/{id}` | 更新失效行 |
| DELETE | `/api/v1/failures/{id}` | 删除失效行 |
| GET | `/api/v1/projects/{id}/references` | 参考材料列表 |
| POST | `/api/v1/projects/{id}/references` | 上传/添加参考 |
| GET | `/api/v1/projects/{id}/export/xlsx` | 导出 Excel |
| GET | `/api/v1/projects/{id}/export/json` | 导出 JSON |
| POST | `/api/v1/projects/{id}/import` | 导入 JSON |

---

## 7. RPN 与 AP 判定逻辑

### 7.1 RPN = S × O × D
- 范围：1 ～ 1000
- 高风险阈值：RPN ≥ 100（可配置）
- 自动高亮：红(RPN≥200)、橙(100≤RPN<200)、黄(RPN<100)

### 7.2 AP（Action Priority）— 基于 AIAG-VAG FMEA 手册
根据 S、O、D 组合查表判定 H(高)/M(中)/L(低)：
- H：必须定义改进措施
- M：应该定义改进措施
- L：可定义改进措施

（查表数据在 `db/seed.sql` 中初始化）

---

## 8. 实施计划

| 阶段 | 内容 | 预计产出 |
|------|------|----------|
| **Phase 1** | 项目骨架：FastAPI 入口、数据库建表、基础 HTML 布局、首页仪表盘 | 可启动的项目框架 |
| **Phase 2** | 结构树管理：树形 CRUD、拖拽排序、左侧导航 | 可管理结构层级 |
| **Phase 3** | 功能分析：功能项 CRUD、批量导入 | 可录入功能项 |
| **Phase 4** | DFMEA 核心工作表：完整表格编辑、RPN/AP 自动计算、高亮 | 核心 DFMEA 可用 |
| **Phase 5** | 参考材料：上传、分类、关联 | 可管理参考资料 |
| **Phase 6** | 导入导出：Excel/JSON 导出，JSON 导入恢复 | 数据可移植 |
| **Phase 7** | 打磨：自动保存、操作撤销、深色主题、评分准则参考弹窗 | 体验完善 |

---

## 9. 已确认事项

| # | 事项 | 决定 |
|---|------|------|
| 1 | 开发节奏 | Phase 1→7 顺序全量开发，先拉通骨架再逐步填充 |
| 2 | 评分准则 | 内置 AIAG-VDA S/O/D 评分标准表，作为 DFMEA 工作表填写时的参考弹窗 |
| 3 | 首个项目 | "液冷机组电控-控制器"作为第一个正式分析数据 |
| 4 | 前端框架 | Vue 3 CDN（核心表格/树组件），原生 JS（简单页面） |
| 5 | 数据库位置 | `C:\Users\invok\dfmea_db\` 独立于代码目录；数据文件分离存储 |

## 10. 待用户确认

1. 更新后的技术栈（FastAPI + Vue 3 CDN + SQLite + 文件系统）是否可以开始？
2. 数据目录 `C:\Users\invok\dfmea_db\` 是否接受？还是改到别的路径？
3. 有无其他补充？

---

*文档版本: v2.0 | 日期: 2026-05-13*
