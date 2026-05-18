-- DFMEA 个人记录系统 — 数据库表结构
-- 版本: v2.0, 对应需求文档 section 2.2

PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

-- ============================================================
-- 1. 项目表
-- ============================================================
CREATE TABLE IF NOT EXISTS project (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL,
    description TEXT    DEFAULT '',
    is_deleted  INTEGER DEFAULT 0,   -- 软删除标记
    created_at  TEXT    DEFAULT (datetime('now', 'localtime')),
    updated_at  TEXT    DEFAULT (datetime('now', 'localtime'))
);

-- ============================================================
-- 2. 结构树节点（递归父子关系，不限制层级深度）
-- ============================================================
CREATE TABLE IF NOT EXISTS structure_node (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id   INTEGER NOT NULL REFERENCES project(id) ON DELETE CASCADE,
    parent_id    INTEGER REFERENCES structure_node(id) ON DELETE CASCADE,
    name         TEXT    NOT NULL,
    type         TEXT    NOT NULL DEFAULT '部件'  CHECK(type IN ('系统', '子系统', '部件', '零件')),
    part_number  TEXT    DEFAULT '',
    description  TEXT    DEFAULT '',
    order_index  INTEGER DEFAULT 0,
    created_at   TEXT    DEFAULT (datetime('now', 'localtime')),
    updated_at   TEXT    DEFAULT (datetime('now', 'localtime'))
);

CREATE INDEX IF NOT EXISTS idx_structure_project ON structure_node(project_id);
CREATE INDEX IF NOT EXISTS idx_structure_parent  ON structure_node(parent_id);

-- ============================================================
-- 3. 功能分析
-- ============================================================
CREATE TABLE IF NOT EXISTS function_item (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    node_id         INTEGER NOT NULL REFERENCES structure_node(id) ON DELETE CASCADE,
    function_desc   TEXT    NOT NULL,
    requirement     TEXT    DEFAULT '',
    performance_spec TEXT   DEFAULT '',
    interface_desc  TEXT    DEFAULT '',   -- 接口说明（输入/输出）
    order_index     INTEGER DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_function_node ON function_item(node_id);

-- ============================================================
-- 4. 失效模式（DFMEA 核心工作表）
-- ============================================================
CREATE TABLE IF NOT EXISTS failure_mode (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    function_item_id   INTEGER NOT NULL REFERENCES function_item(id) ON DELETE CASCADE,

    -- 失效分析
    mode_desc          TEXT    DEFAULT '',
    local_effect       TEXT    DEFAULT '',   -- 对当前元素的影响
    potential_effect   TEXT    DEFAULT '',   -- 对系统/上层的影响
    severity_S         INTEGER DEFAULT 1 CHECK(severity_S BETWEEN 1 AND 10),
    classification     TEXT    DEFAULT ''   CHECK(classification IN ('', 'SC', 'CC')),
    potential_cause    TEXT    DEFAULT '',
    occurrence_O       INTEGER DEFAULT 1 CHECK(occurrence_O BETWEEN 1 AND 10),
    prevention_control TEXT    DEFAULT '',
    detection_control  TEXT    DEFAULT '',
    detection_D        INTEGER DEFAULT 1 CHECK(detection_D BETWEEN 1 AND 10),

    -- 自动计算
    rpn                INTEGER DEFAULT 1,       -- S × O × D
    action_priority    TEXT    DEFAULT 'L'       CHECK(action_priority IN ('H', 'M', 'L')),

    -- 改进措施
    recommended_action TEXT    DEFAULT '',
    action_owner       TEXT    DEFAULT '',
    action_due_date    TEXT    DEFAULT '',
    action_status      TEXT    DEFAULT '未开始' CHECK(action_status IN ('未开始', '进行中', '已完成', '已取消')),
    action_effect      TEXT    DEFAULT '',

    -- 修订评分
    revised_S          INTEGER DEFAULT NULL CHECK(revised_S IS NULL OR revised_S BETWEEN 1 AND 10),
    revised_O          INTEGER DEFAULT NULL CHECK(revised_O IS NULL OR revised_O BETWEEN 1 AND 10),
    revised_D          INTEGER DEFAULT NULL CHECK(revised_D IS NULL OR revised_D BETWEEN 1 AND 10),
    revised_RPN        INTEGER DEFAULT NULL,

    notes              TEXT    DEFAULT '',
    order_index        INTEGER DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_failure_function ON failure_mode(function_item_id);

-- ============================================================
-- 5. 参考材料
-- ============================================================
CREATE TABLE IF NOT EXISTS reference (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id  INTEGER NOT NULL REFERENCES project(id) ON DELETE CASCADE,
    node_id     INTEGER REFERENCES structure_node(id) ON DELETE SET NULL,
    title       TEXT    NOT NULL,
    type        TEXT    NOT NULL DEFAULT '其他' CHECK(type IN ('链接', '文档', '图片', '其他')),
    file_path   TEXT    DEFAULT '',   -- 相对 uploads/ 的路径
    url         TEXT    DEFAULT '',   -- 外部链接
    notes       TEXT    DEFAULT '',
    created_at  TEXT    DEFAULT (datetime('now', 'localtime'))
);

CREATE INDEX IF NOT EXISTS idx_ref_project ON reference(project_id);

-- ============================================================
-- 6. 结构节点 ↔ 参考资料关联（多对多）
-- ============================================================
CREATE TABLE IF NOT EXISTS reference_node (
    reference_id  INTEGER NOT NULL REFERENCES reference(id) ON DELETE CASCADE,
    node_id       INTEGER NOT NULL REFERENCES structure_node(id) ON DELETE CASCADE,
    PRIMARY KEY (reference_id, node_id)
);

CREATE INDEX IF NOT EXISTS idx_rn_ref  ON reference_node(reference_id);
CREATE INDEX IF NOT EXISTS idx_rn_node ON reference_node(node_id);

-- ============================================================
-- 7. 失效模式 ↔ 参考资料关联（多对多）
-- ============================================================
CREATE TABLE IF NOT EXISTS failure_mode_reference (
    failure_mode_id INTEGER NOT NULL REFERENCES failure_mode(id) ON DELETE CASCADE,
    reference_id    INTEGER NOT NULL REFERENCES reference(id) ON DELETE CASCADE,
    PRIMARY KEY (failure_mode_id, reference_id)
);

CREATE INDEX IF NOT EXISTS idx_fmr_failure ON failure_mode_reference(failure_mode_id);
CREATE INDEX IF NOT EXISTS idx_fmr_ref     ON failure_mode_reference(reference_id);

-- ============================================================
-- 8. 操作日志
-- ============================================================
CREATE TABLE IF NOT EXISTS audit_log (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id  INTEGER NOT NULL REFERENCES project(id) ON DELETE CASCADE,
    action      TEXT    NOT NULL,   -- CREATE / UPDATE / DELETE
    entity_type TEXT    NOT NULL,   -- project / node / function / failure / reference
    entity_id   INTEGER,
    detail      TEXT    DEFAULT '',
    created_at  TEXT    DEFAULT (datetime('now', 'localtime'))
);

CREATE INDEX IF NOT EXISTS idx_audit_project ON audit_log(project_id);
