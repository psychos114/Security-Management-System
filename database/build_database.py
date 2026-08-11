from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "security_management_demo.db"
KNOWLEDGE_DIR = ROOT / "knowledge_documents"
AS_OF_DATE = "2026-08-11"


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def dumps(value) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


SQLITE_SCHEMA = r"""
PRAGMA foreign_keys = ON;

CREATE TABLE metadata (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE departments (
    id INTEGER PRIMARY KEY,
    code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT ''
);

CREATE TABLE roles (
    id INTEGER PRIMARY KEY,
    code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    permissions_json TEXT NOT NULL CHECK (json_valid(permissions_json))
);

CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    display_name TEXT NOT NULL,
    role_id INTEGER NOT NULL REFERENCES roles(id),
    department_id INTEGER NOT NULL REFERENCES departments(id),
    is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
    is_demo INTEGER NOT NULL DEFAULT 1 CHECK (is_demo IN (0, 1))
);

CREATE TABLE locations (
    id INTEGER PRIMARY KEY,
    code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    location_type TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    parent_id INTEGER REFERENCES locations(id)
);

CREATE TABLE event_types (
    id INTEGER PRIMARY KEY,
    code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    default_severity TEXT NOT NULL CHECK (default_severity IN ('S1', 'S2', 'S3', 'S4')),
    default_owner_role_code TEXT NOT NULL REFERENCES roles(code),
    response_minutes INTEGER NOT NULL CHECK (response_minutes > 0),
    critical_confirmation_required INTEGER NOT NULL CHECK (critical_confirmation_required IN (0, 1)),
    description TEXT NOT NULL,
    safety_boundary TEXT NOT NULL
);

CREATE TABLE event_playbook_steps (
    id INTEGER PRIMARY KEY,
    event_type_id INTEGER NOT NULL REFERENCES event_types(id) ON DELETE CASCADE,
    step_no INTEGER NOT NULL,
    action TEXT NOT NULL,
    owner_role_code TEXT NOT NULL REFERENCES roles(code),
    time_limit_minutes INTEGER NOT NULL CHECK (time_limit_minutes > 0),
    approval_required INTEGER NOT NULL CHECK (approval_required IN (0, 1)),
    approval_role_code TEXT REFERENCES roles(code),
    is_critical_action INTEGER NOT NULL CHECK (is_critical_action IN (0, 1)),
    notes TEXT NOT NULL DEFAULT '',
    UNIQUE(event_type_id, step_no)
);

CREATE TABLE incident_examples (
    id INTEGER PRIMARY KEY,
    incident_no TEXT NOT NULL UNIQUE,
    event_type_id INTEGER NOT NULL REFERENCES event_types(id),
    location_id INTEGER NOT NULL REFERENCES locations(id),
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    severity TEXT NOT NULL CHECK (severity IN ('S1', 'S2', 'S3', 'S4')),
    status TEXT NOT NULL,
    reported_by_user_id INTEGER NOT NULL REFERENCES users(id),
    assigned_role_code TEXT NOT NULL REFERENCES roles(code),
    ai_assessment TEXT NOT NULL,
    human_confirmation_status TEXT NOT NULL,
    occurred_at TEXT NOT NULL,
    is_synthetic INTEGER NOT NULL DEFAULT 1 CHECK (is_synthetic IN (0, 1))
);

CREATE TABLE inspection_scenes (
    id INTEGER PRIMARY KEY,
    code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    default_owner_role_code TEXT NOT NULL REFERENCES roles(code)
);

CREATE TABLE inspection_items (
    id INTEGER PRIMARY KEY,
    scene_id INTEGER NOT NULL REFERENCES inspection_scenes(id) ON DELETE CASCADE,
    item_code TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    inspection_question TEXT NOT NULL,
    expected_visual_evidence TEXT NOT NULL,
    risk_level TEXT NOT NULL CHECK (risk_level IN ('low', 'medium', 'high', 'critical')),
    can_confirm_from_single_photo INTEGER NOT NULL CHECK (can_confirm_from_single_photo IN (0, 1)),
    handling_advice TEXT NOT NULL
);

CREATE TABLE sla_policies (
    id INTEGER PRIMARY KEY,
    severity TEXT NOT NULL UNIQUE CHECK (severity IN ('S1', 'S2', 'S3', 'S4')),
    response_minutes INTEGER NOT NULL,
    resolution_minutes INTEGER NOT NULL,
    first_escalation_role_code TEXT NOT NULL REFERENCES roles(code),
    second_escalation_role_code TEXT NOT NULL REFERENCES roles(code),
    description TEXT NOT NULL
);

CREATE TABLE complaints (
    id INTEGER PRIMARY KEY,
    complaint_no TEXT NOT NULL UNIQUE,
    source_type TEXT NOT NULL CHECK (source_type IN ('phone', 'paper', 'superior_notice')),
    complainant_type TEXT NOT NULL CHECK (complainant_type IN ('medical_staff', 'patient', 'hospital_leader', 'superior_unit')),
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    severity TEXT NOT NULL REFERENCES sla_policies(severity),
    responsible_department_code TEXT NOT NULL REFERENCES departments(code),
    status TEXT NOT NULL,
    received_at TEXT NOT NULL,
    response_due_at TEXT NOT NULL,
    resolution_due_at TEXT NOT NULL,
    callback_status TEXT NOT NULL,
    satisfaction_score INTEGER CHECK (satisfaction_score BETWEEN 1 AND 5),
    ai_reply_draft TEXT NOT NULL,
    rectification_summary TEXT NOT NULL,
    converted_to_risk INTEGER NOT NULL DEFAULT 0 CHECK (converted_to_risk IN (0, 1)),
    converted_to_case INTEGER NOT NULL DEFAULT 0 CHECK (converted_to_case IN (0, 1)),
    is_synthetic INTEGER NOT NULL DEFAULT 1 CHECK (is_synthetic IN (0, 1))
);

CREATE TABLE risk_points (
    id INTEGER PRIMARY KEY,
    risk_no TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    category TEXT NOT NULL,
    source_type TEXT NOT NULL,
    source_reference TEXT NOT NULL,
    scene_code TEXT REFERENCES inspection_scenes(code),
    risk_level TEXT NOT NULL CHECK (risk_level IN ('low', 'medium', 'high', 'critical')),
    recognition_hint TEXT NOT NULL,
    inspection_advice TEXT NOT NULL,
    rectification_knowledge TEXT NOT NULL,
    status TEXT NOT NULL,
    is_synthetic INTEGER NOT NULL DEFAULT 1 CHECK (is_synthetic IN (0, 1))
);

CREATE TABLE knowledge_sources (
    id INTEGER PRIMARY KEY,
    source_code TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    issuing_authority TEXT NOT NULL,
    document_number TEXT NOT NULL DEFAULT '',
    jurisdiction TEXT NOT NULL,
    source_type TEXT NOT NULL,
    published_date TEXT,
    effective_date TEXT,
    validity_status TEXT NOT NULL CHECK (validity_status IN ('active', 'historical', 'needs_review')),
    official_url TEXT NOT NULL,
    retrieval_date TEXT NOT NULL,
    notes TEXT NOT NULL DEFAULT ''
);

CREATE TABLE knowledge_documents (
    id INTEGER PRIMARY KEY,
    doc_code TEXT NOT NULL UNIQUE,
    category TEXT NOT NULL CHECK (category IN ('emergency_response', 'inspection', 'complaint', 'daily_report', 'fire_assistant', 'multimodal')),
    title TEXT NOT NULL,
    document_type TEXT NOT NULL,
    source_id INTEGER REFERENCES knowledge_sources(id),
    jurisdiction TEXT NOT NULL,
    citation_locator TEXT NOT NULL DEFAULT '',
    summary TEXT NOT NULL,
    content TEXT NOT NULL,
    tags_json TEXT NOT NULL CHECK (json_valid(tags_json)),
    is_official INTEGER NOT NULL CHECK (is_official IN (0, 1)),
    requires_human_review INTEGER NOT NULL CHECK (requires_human_review IN (0, 1)),
    source_file TEXT NOT NULL,
    content_sha256 TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE knowledge_chunks (
    id INTEGER PRIMARY KEY,
    document_id INTEGER NOT NULL REFERENCES knowledge_documents(id) ON DELETE CASCADE,
    chunk_no INTEGER NOT NULL,
    heading TEXT NOT NULL,
    content TEXT NOT NULL,
    citation_locator TEXT NOT NULL DEFAULT '',
    metadata_json TEXT NOT NULL CHECK (json_valid(metadata_json)),
    UNIQUE(document_id, chunk_no)
);

CREATE TABLE daily_plan_templates (
    id INTEGER PRIMARY KEY,
    template_code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    applicable_role_code TEXT NOT NULL REFERENCES roles(code),
    trigger_time TEXT NOT NULL,
    plan_items_json TEXT NOT NULL CHECK (json_valid(plan_items_json)),
    notes TEXT NOT NULL
);

CREATE TABLE daily_report_samples (
    id INTEGER PRIMARY KEY,
    report_no TEXT NOT NULL UNIQUE,
    report_date TEXT NOT NULL,
    shift_name TEXT NOT NULL,
    summary TEXT NOT NULL,
    incident_summary TEXT NOT NULL,
    inspection_summary TEXT NOT NULL,
    complaint_summary TEXT NOT NULL,
    pending_actions TEXT NOT NULL,
    recipients_json TEXT NOT NULL CHECK (json_valid(recipients_json)),
    human_review_status TEXT NOT NULL,
    is_synthetic INTEGER NOT NULL DEFAULT 1 CHECK (is_synthetic IN (0, 1))
);

CREATE TABLE notification_rules (
    id INTEGER PRIMARY KEY,
    rule_code TEXT NOT NULL UNIQUE,
    trigger_type TEXT NOT NULL,
    condition_json TEXT NOT NULL CHECK (json_valid(condition_json)),
    recipient_role_codes_json TEXT NOT NULL CHECK (json_valid(recipient_role_codes_json)),
    channel TEXT NOT NULL CHECK (channel IN ('in_app', 'email_optional')),
    critical_confirmation_required INTEGER NOT NULL CHECK (critical_confirmation_required IN (0, 1)),
    description TEXT NOT NULL
);

CREATE INDEX idx_event_steps_type ON event_playbook_steps(event_type_id, step_no);
CREATE INDEX idx_inspection_items_scene ON inspection_items(scene_id);
CREATE INDEX idx_complaints_status_due ON complaints(status, response_due_at, resolution_due_at);
CREATE INDEX idx_risk_points_scene ON risk_points(scene_code, risk_level);
CREATE INDEX idx_knowledge_documents_category ON knowledge_documents(category);
CREATE INDEX idx_knowledge_chunks_document ON knowledge_chunks(document_id, chunk_no);

CREATE VIEW v_patrol_checklist AS
SELECT s.code AS scene_code, s.name AS scene_name, i.item_code, i.title,
       i.inspection_question, i.expected_visual_evidence, i.risk_level,
       i.can_confirm_from_single_photo, i.handling_advice
FROM inspection_scenes s
JOIN inspection_items i ON i.scene_id = s.id
ORDER BY s.id, i.id;

CREATE VIEW v_knowledge_citations AS
SELECT d.doc_code, d.category, d.title, d.citation_locator, d.summary,
       s.title AS source_title, s.issuing_authority, s.published_date,
       s.effective_date, s.validity_status, s.official_url
FROM knowledge_documents d
LEFT JOIN knowledge_sources s ON s.id = d.source_id;
"""


POSTGRESQL_SCHEMA = r"""
-- PostgreSQL 15+ structure for the hospital property-security demo database.
CREATE TABLE metadata (
    key text PRIMARY KEY,
    value text NOT NULL,
    updated_at timestamptz NOT NULL
);

CREATE TABLE departments (
    id bigint GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    code text NOT NULL UNIQUE,
    name text NOT NULL,
    description text NOT NULL DEFAULT ''
);

CREATE TABLE roles (
    id bigint GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    code text NOT NULL UNIQUE,
    name text NOT NULL,
    permissions_json jsonb NOT NULL
);

CREATE TABLE users (
    id bigint GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    username text NOT NULL UNIQUE,
    display_name text NOT NULL,
    role_id bigint NOT NULL REFERENCES roles(id),
    department_id bigint NOT NULL REFERENCES departments(id),
    is_active boolean NOT NULL DEFAULT true,
    is_demo boolean NOT NULL DEFAULT true
);

CREATE TABLE locations (
    id bigint GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    code text NOT NULL UNIQUE,
    name text NOT NULL,
    location_type text NOT NULL,
    description text NOT NULL DEFAULT '',
    parent_id bigint REFERENCES locations(id)
);

CREATE TABLE event_types (
    id bigint GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    code text NOT NULL UNIQUE,
    name text NOT NULL,
    category text NOT NULL,
    default_severity text NOT NULL CHECK (default_severity IN ('S1','S2','S3','S4')),
    default_owner_role_code text NOT NULL REFERENCES roles(code),
    response_minutes integer NOT NULL CHECK (response_minutes > 0),
    critical_confirmation_required boolean NOT NULL,
    description text NOT NULL,
    safety_boundary text NOT NULL
);

CREATE TABLE event_playbook_steps (
    id bigint GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    event_type_id bigint NOT NULL REFERENCES event_types(id) ON DELETE CASCADE,
    step_no integer NOT NULL,
    action text NOT NULL,
    owner_role_code text NOT NULL REFERENCES roles(code),
    time_limit_minutes integer NOT NULL CHECK (time_limit_minutes > 0),
    approval_required boolean NOT NULL,
    approval_role_code text REFERENCES roles(code),
    is_critical_action boolean NOT NULL,
    notes text NOT NULL DEFAULT '',
    UNIQUE(event_type_id, step_no)
);

CREATE TABLE incident_examples (
    id bigint GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    incident_no text NOT NULL UNIQUE,
    event_type_id bigint NOT NULL REFERENCES event_types(id),
    location_id bigint NOT NULL REFERENCES locations(id),
    title text NOT NULL,
    description text NOT NULL,
    severity text NOT NULL CHECK (severity IN ('S1','S2','S3','S4')),
    status text NOT NULL,
    reported_by_user_id bigint NOT NULL REFERENCES users(id),
    assigned_role_code text NOT NULL REFERENCES roles(code),
    ai_assessment text NOT NULL,
    human_confirmation_status text NOT NULL,
    occurred_at timestamptz NOT NULL,
    is_synthetic boolean NOT NULL DEFAULT true
);

CREATE TABLE inspection_scenes (
    id bigint GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    code text NOT NULL UNIQUE,
    name text NOT NULL,
    description text NOT NULL,
    default_owner_role_code text NOT NULL REFERENCES roles(code)
);

CREATE TABLE inspection_items (
    id bigint GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    scene_id bigint NOT NULL REFERENCES inspection_scenes(id) ON DELETE CASCADE,
    item_code text NOT NULL UNIQUE,
    title text NOT NULL,
    inspection_question text NOT NULL,
    expected_visual_evidence text NOT NULL,
    risk_level text NOT NULL CHECK (risk_level IN ('low','medium','high','critical')),
    can_confirm_from_single_photo boolean NOT NULL,
    handling_advice text NOT NULL
);

CREATE TABLE sla_policies (
    id bigint GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    severity text NOT NULL UNIQUE CHECK (severity IN ('S1','S2','S3','S4')),
    response_minutes integer NOT NULL,
    resolution_minutes integer NOT NULL,
    first_escalation_role_code text NOT NULL REFERENCES roles(code),
    second_escalation_role_code text NOT NULL REFERENCES roles(code),
    description text NOT NULL
);

CREATE TABLE complaints (
    id bigint GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    complaint_no text NOT NULL UNIQUE,
    source_type text NOT NULL,
    complainant_type text NOT NULL,
    title text NOT NULL,
    description text NOT NULL,
    severity text NOT NULL REFERENCES sla_policies(severity),
    responsible_department_code text NOT NULL REFERENCES departments(code),
    status text NOT NULL,
    received_at timestamptz NOT NULL,
    response_due_at timestamptz NOT NULL,
    resolution_due_at timestamptz NOT NULL,
    callback_status text NOT NULL,
    satisfaction_score integer CHECK (satisfaction_score BETWEEN 1 AND 5),
    ai_reply_draft text NOT NULL,
    rectification_summary text NOT NULL,
    converted_to_risk boolean NOT NULL DEFAULT false,
    converted_to_case boolean NOT NULL DEFAULT false,
    is_synthetic boolean NOT NULL DEFAULT true
);

CREATE TABLE risk_points (
    id bigint GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    risk_no text NOT NULL UNIQUE,
    title text NOT NULL,
    category text NOT NULL,
    source_type text NOT NULL,
    source_reference text NOT NULL,
    scene_code text REFERENCES inspection_scenes(code),
    risk_level text NOT NULL CHECK (risk_level IN ('low','medium','high','critical')),
    recognition_hint text NOT NULL,
    inspection_advice text NOT NULL,
    rectification_knowledge text NOT NULL,
    status text NOT NULL,
    is_synthetic boolean NOT NULL DEFAULT true
);

CREATE TABLE knowledge_sources (
    id bigint GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    source_code text NOT NULL UNIQUE,
    title text NOT NULL,
    issuing_authority text NOT NULL,
    document_number text NOT NULL DEFAULT '',
    jurisdiction text NOT NULL,
    source_type text NOT NULL,
    published_date date,
    effective_date date,
    validity_status text NOT NULL CHECK (validity_status IN ('active','historical','needs_review')),
    official_url text NOT NULL,
    retrieval_date date NOT NULL,
    notes text NOT NULL DEFAULT ''
);

CREATE TABLE knowledge_documents (
    id bigint GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    doc_code text NOT NULL UNIQUE,
    category text NOT NULL,
    title text NOT NULL,
    document_type text NOT NULL,
    source_id bigint REFERENCES knowledge_sources(id),
    jurisdiction text NOT NULL,
    citation_locator text NOT NULL DEFAULT '',
    summary text NOT NULL,
    content text NOT NULL,
    tags_json jsonb NOT NULL,
    is_official boolean NOT NULL,
    requires_human_review boolean NOT NULL,
    source_file text NOT NULL,
    content_sha256 text NOT NULL,
    created_at timestamptz NOT NULL
);

CREATE TABLE knowledge_chunks (
    id bigint GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    document_id bigint NOT NULL REFERENCES knowledge_documents(id) ON DELETE CASCADE,
    chunk_no integer NOT NULL,
    heading text NOT NULL,
    content text NOT NULL,
    citation_locator text NOT NULL DEFAULT '',
    metadata_json jsonb NOT NULL,
    UNIQUE(document_id, chunk_no)
);

CREATE TABLE daily_plan_templates (
    id bigint GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    template_code text NOT NULL UNIQUE,
    name text NOT NULL,
    applicable_role_code text NOT NULL REFERENCES roles(code),
    trigger_time time NOT NULL,
    plan_items_json jsonb NOT NULL,
    notes text NOT NULL
);

CREATE TABLE daily_report_samples (
    id bigint GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    report_no text NOT NULL UNIQUE,
    report_date date NOT NULL,
    shift_name text NOT NULL,
    summary text NOT NULL,
    incident_summary text NOT NULL,
    inspection_summary text NOT NULL,
    complaint_summary text NOT NULL,
    pending_actions text NOT NULL,
    recipients_json jsonb NOT NULL,
    human_review_status text NOT NULL,
    is_synthetic boolean NOT NULL DEFAULT true
);

CREATE TABLE notification_rules (
    id bigint GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    rule_code text NOT NULL UNIQUE,
    trigger_type text NOT NULL,
    condition_json jsonb NOT NULL,
    recipient_role_codes_json jsonb NOT NULL,
    channel text NOT NULL,
    critical_confirmation_required boolean NOT NULL,
    description text NOT NULL
);

CREATE INDEX idx_event_steps_type ON event_playbook_steps(event_type_id, step_no);
CREATE INDEX idx_inspection_items_scene ON inspection_items(scene_id);
CREATE INDEX idx_complaints_status_due ON complaints(status, response_due_at, resolution_due_at);
CREATE INDEX idx_risk_points_scene ON risk_points(scene_code, risk_level);
CREATE INDEX idx_knowledge_documents_category ON knowledge_documents(category);
CREATE INDEX idx_knowledge_chunks_document ON knowledge_chunks(document_id, chunk_no);
"""


DEPARTMENTS = [
    (1, "SECURITY", "安管部", "负责医院物业安保、巡检与事件响应"),
    (2, "PROJECT", "项目管理部", "负责物业项目统筹与重大事项协调"),
    (3, "CUSTOMER_SERVICE", "客服部", "负责投诉受理、回访与满意度"),
    (4, "PROPERTY", "物业管理层", "负责重大决策和资源协调"),
    (5, "ENGINEERING", "工程部", "负责设备、电力、电梯、漏水等维修处置"),
    (6, "HOSPITAL_LIAISON", "院方联络", "演示用院方接口角色，不代表真实医院组织结构"),
]


ROLES = [
    (1, "guard", "保安", ["incident:create", "inspection:create", "task:view_self"]),
    (2, "squad_leader", "班长", ["incident:confirm", "task:assign", "inspection:review"]),
    (3, "security_manager", "安管经理", ["incident:approve_critical", "sla:manage", "report:approve"]),
    (4, "project_manager", "项目经理", ["incident:approve_major", "dashboard:view_all", "report:receive"]),
    (5, "customer_service", "客服", ["complaint:create", "complaint:callback", "report:receive"]),
    (6, "property_manager", "物业经理", ["dashboard:view_all", "policy:approve", "report:receive"]),
]


USERS = [
    (1, "demo.guard", "演示保安", 1, 1),
    (2, "demo.leader", "演示班长", 2, 1),
    (3, "demo.security", "演示安管经理", 3, 1),
    (4, "demo.project", "演示项目经理", 4, 2),
    (5, "demo.service", "演示客服", 5, 3),
    (6, "demo.property", "演示物业经理", 6, 4),
]


LOCATIONS = [
    (1, "HOSPITAL", "示例医院", "site", "虚构医院，仅用于学习演示", None),
    (2, "WARD_3F", "住院部三层", "ward", "病区走廊、护士站及公共区域", 1),
    (3, "OUTPATIENT_1F", "门诊一层", "outpatient", "门诊大厅及主要出入口", 1),
    (4, "FIRE_STAIRS_A", "A区消防楼梯", "fire_stair", "疏散通道和前室", 1),
    (5, "FIRE_CONTROL", "消防控制室", "fire_control_room", "消防控制与值班区域", 1),
    (6, "POWER_ROOM", "配电房", "power_room", "配电与应急供电区域", 1),
    (7, "ELEVATOR_A", "A区电梯厅", "elevator", "电梯厅及困梯联络点", 1),
    (8, "PARKING_B1", "地下一层停车场", "parking", "车辆通道与消防车道连接区域", 1),
    (9, "OXYGEN_STATION", "中心供氧区域", "medical_gas", "重点防火区域，仅限授权人员进入", 1),
    (10, "PUMP_ROOM", "消防水泵房", "pump_room", "消防供水设施区域", 1),
]


EVENTS = [
    (1, "FIRE", "火灾或疑似火情", "fire", "S4", "squad_leader", 5, 1,
     "烟雾、明火、火灾报警或焦糊味等情况。", "AI不能代替现场确认；确认火灾后不得因审批流程延误报警、疏散和救援。"),
    (2, "CONFLICT", "人员冲突", "security", "S3", "squad_leader", 10, 1,
     "医患、访客或其他人员发生争执、推搡、威胁等。", "以人员安全和降级处置为先；存在武器或现实人身危险时立即报警，不要求保安冒险接触。"),
    (3, "EQUIPMENT_FAILURE", "设备故障", "facility", "S2", "squad_leader", 15, 0,
     "物业或公共设施出现故障、异响或停止运行。", "保安只负责警戒、报告和引导，不进行无资质维修。"),
    (4, "POWER_OUTAGE", "停电", "facility", "S3", "squad_leader", 5, 1,
     "局部或全院停电、应急照明异常。", "不得擅自操作高压设备；涉及医疗关键负荷时立即通知院方和工程人员。"),
    (5, "ELEVATOR_TRAP", "困梯", "facility", "S3", "squad_leader", 5, 1,
     "人员被困电梯或电梯异常停层。", "不得强行扒门或无资质施救，应联系维保和专业救援。"),
    (6, "WATER_LEAK", "漏水", "facility", "S2", "squad_leader", 10, 0,
     "管道、天花或设备区域漏水。", "临近电气设备时按高风险处理，由工程人员决定断电和维修。"),
    (7, "VEHICLE_ACCIDENT", "车辆事故", "traffic", "S2", "squad_leader", 10, 1,
     "院区车辆碰撞、刮擦或人员受伤。", "优先救助伤者和保护现场；不代替交警进行责任认定。"),
    (8, "PATIENT_UNAUTHORIZED_EXIT", "住院患者疑似违规外出", "hospital", "S3", "squad_leader", 5, 1,
     "发现住院患者未经确认离开规定区域。", "先向护士站核验；尊重患者人格和人身权利，不得仅凭AI判断实施强制限制。"),
    (9, "PATIENT_FALL", "患者摔倒", "hospital", "S4", "squad_leader", 3, 1,
     "患者在公共区域跌倒或疑似受伤。", "立即呼叫医护人员；除现场存在继续伤害风险或受过训练外，不擅自搬动患者。"),
    (10, "PATIENT_RESCUE", "患者需要抢救协助", "hospital", "S4", "squad_leader", 3, 1,
     "院方发出抢救协助请求或公共区域发现患者危急。", "安保职责是报警、清障、引导和秩序维护；医疗操作仅由有资质人员实施。"),
]


PLAYBOOKS = {
    "FIRE": [
        ("立即确认报警位置和可见火情，保持安全距离", "guard", 2, 0, None, 0, "通过消防控制室和就近人员双重确认"),
        ("现场确认火情后立即拨打119并启动医院火灾预案", "squad_leader", 3, 1, "squad_leader", 1, "确认动作不得造成不合理延误"),
        ("通知安管经理、项目经理和院方联络人员", "squad_leader", 5, 0, None, 0, "站内通知自动生成"),
        ("组织疏散引导、保持消防通道畅通并协助行动不便人员", "guard", 5, 0, None, 1, "服从现场应急指挥"),
        ("记录时间线并保护现场，未经许可不移动相关物品", "security_manager", 30, 0, None, 0, "抢救生命和防止危险扩大除外"),
    ],
    "CONFLICT": [
        ("报告位置、人数、是否有武器及是否有人受伤", "guard", 2, 0, None, 0, "避免靠近明显危险人员"),
        ("班长调配支援并通知院方相关科室", "squad_leader", 5, 0, None, 0, "优先隔离围观人员"),
        ("采用非对抗语言降级冲突并划定安全距离", "guard", 5, 0, None, 0, "不得使用侮辱性或刺激性语言"),
        ("存在现实人身危险时报警并通知安管经理", "squad_leader", 5, 1, "squad_leader", 1, "紧迫危险时不得等待更高层审批"),
        ("保存公共区域证据并形成事件记录", "security_manager", 30, 0, None, 0, "严格控制患者隐私和影像访问"),
    ],
    "EQUIPMENT_FAILURE": [
        ("设置临时警戒并记录设备编号和故障表现", "guard", 5, 0, None, 0, "不触碰裸露电气部件"),
        ("自动派单至工程部并通知班长", "squad_leader", 10, 0, None, 0, "附现场照片"),
        ("评估是否影响疏散、诊疗或其他关键区域", "squad_leader", 10, 0, None, 0, "影响关键服务时升级S3"),
        ("工程人员处置期间维持隔离和人员引导", "guard", 30, 0, None, 0, "按工程人员要求调整范围"),
        ("复核恢复状态并关闭工单", "squad_leader", 120, 0, None, 0, "必须有工程反馈"),
    ],
    "POWER_OUTAGE": [
        ("确认停电范围并检查应急照明是否投入", "guard", 3, 0, None, 0, "不得进入未授权电气区域"),
        ("通知工程部、班长和院方值班人员", "squad_leader", 5, 0, None, 0, "标注是否影响病区或急诊"),
        ("涉及医疗关键负荷时升级安管经理和项目经理", "squad_leader", 5, 1, "security_manager", 1, "系统自动升级"),
        ("在黑暗区域设置警戒并引导人员安全通行", "guard", 5, 0, None, 0, "使用合规照明工具"),
        ("恢复供电后复核电梯、门禁和消防系统状态", "squad_leader", 30, 0, None, 0, "异常项另建工单"),
    ],
    "ELEVATOR_TRAP": [
        ("通过对讲确认被困人数、健康状况和电梯位置", "guard", 2, 0, None, 0, "安抚被困人员，告知不要扒门"),
        ("联系电梯维保和工程部并通知班长", "squad_leader", 5, 0, None, 0, "记录呼叫时间"),
        ("有人不适或存在立即危险时联络医护和专业救援", "squad_leader", 5, 1, "squad_leader", 1, "不得无资质强行施救"),
        ("在相关楼层设置警戒并保持救援通道畅通", "guard", 5, 0, None, 0, "避免其他人员继续使用故障电梯"),
        ("救援结束后核对人员和维保结论并记录", "squad_leader", 30, 0, None, 0, "未确认恢复前保持停用"),
    ],
    "WATER_LEAK": [
        ("确认漏水位置、范围及附近电气风险", "guard", 5, 0, None, 0, "不进入积水中的电气设备区域"),
        ("设置防滑警示和临时隔离", "guard", 5, 0, None, 0, "保护患者与访客通行"),
        ("自动派单工程部并通知班长", "squad_leader", 10, 0, None, 0, "附照片和位置"),
        ("临近配电设施或影响诊疗时升级安管经理", "squad_leader", 10, 1, "security_manager", 1, "由工程人员决定断电"),
        ("清理后复核地面、防滑标识和次生损坏", "squad_leader", 60, 0, None, 0, "保留整改前后照片"),
    ],
    "VEHICLE_ACCIDENT": [
        ("确认是否有人受伤并保护现场", "guard", 3, 0, None, 0, "伤者优先"),
        ("有人受伤时呼叫院内医护或120", "squad_leader", 5, 1, "squad_leader", 1, "根据现场紧急程度处理"),
        ("疏导车辆并保持急救和消防通道畅通", "guard", 5, 0, None, 0, "避免二次事故"),
        ("通知班长并按需报警处理", "squad_leader", 10, 1, "security_manager", 1, "不代替交警认定责任"),
        ("记录车辆、位置、时间及公共区域影像索引", "squad_leader", 30, 0, None, 0, "保护个人信息"),
    ],
    "PATIENT_UNAUTHORIZED_EXIT": [
        ("向护士站核验患者身份、外出申请和风险提示", "guard", 3, 0, None, 0, "不得只凭服装或外观识别"),
        ("通知班长、责任病区和院方联络人员", "squad_leader", 5, 0, None, 0, "记录最后出现位置"),
        ("按院方确认范围开展非对抗性查找和出口提示", "guard", 10, 1, "squad_leader", 1, "不得擅自采取强制限制措施"),
        ("发现患者时通知医护人员到场评估并陪同处置", "squad_leader", 5, 0, None, 0, "患者出现危急症状时转入抢救流程"),
        ("完成时间线、交接和门岗流程复盘", "security_manager", 60, 0, None, 0, "不在普通日志记录诊疗详情"),
    ],
    "PATIENT_FALL": [
        ("立即呼叫护士站或院内急救响应", "guard", 1, 0, None, 1, "不等待系统审批"),
        ("保护现场，提醒患者不要自行起身", "guard", 2, 0, None, 0, "除持续危险或受过训练外不搬动"),
        ("疏散围观人员并为医护人员清出通道", "squad_leader", 3, 0, None, 0, "保护患者隐私"),
        ("如现场存在漏水、障碍物等立即隔离并拍照", "guard", 5, 0, None, 0, "照片避免拍摄患者面部"),
        ("医护接管后记录安保相关事实并生成隐患整改项", "security_manager", 30, 1, "security_manager", 1, "不记录医疗诊断结论"),
    ],
    "PATIENT_RESCUE": [
        ("立即触发院内急救呼叫并报告准确位置", "guard", 1, 0, None, 1, "不等待系统审批"),
        ("清理通道并引导抢救人员和设备到场", "guard", 2, 0, None, 0, "保持电梯和关键通道可用"),
        ("控制围观和现场秩序，保护患者隐私", "squad_leader", 3, 0, None, 0, "未经授权不得拍摄传播"),
        ("按医护指令协助非医疗事项", "guard", 5, 1, "squad_leader", 1, "仅在培训和授权范围内行动"),
        ("记录安保响应时间和交接情况", "security_manager", 30, 0, None, 0, "不写入临床诊断和治疗详情"),
    ],
}


SCENES = [
    (1, "WARD_CORRIDOR", "病区走廊", "上传走廊全景照片并选择具体楼层；单张照片只能判断可见范围。", "guard"),
    (2, "FIRE_PASSAGE", "消防通道与楼梯间", "检查疏散通道、前室、防火门及可见消防标识。", "guard"),
    (3, "FIRE_CONTROL_ROOM", "消防控制室", "检查值班环境和可见设备状态；证件、人数和日志完整性需人工复核。", "squad_leader"),
    (4, "POWER_ROOM", "配电与应急供电区域", "仅在授权区域拍照；不要求保安进入危险带电区域。", "squad_leader"),
    (5, "ELEVATOR_AREA", "电梯厅", "检查出入口、警示、积水、障碍物和可见异常。", "guard"),
    (6, "PARKING_TRAFFIC", "停车场与车辆通道", "检查消防车道、停车秩序、油污积水和标识。", "guard"),
    (7, "MEDICAL_GAS", "中心供氧及医用气体周边", "仅检查外围可见安全条件，泄漏和设备性能必须由专业人员检测。", "squad_leader"),
]


INSPECTION_ITEMS = {
    "WARD_CORRIDOR": [
        ("通道是否被推车、纸箱或座椅占用", "走廊有效通行宽度清晰可见", "high", 1, "立即移除可移动障碍，不能处理则建整改工单"),
        ("安全出口和疏散指示是否可见且未遮挡", "完整可见的出口与方向标志", "high", 1, "清除遮挡并通知工程复核灯具状态"),
        ("地面是否存在积水、线缆或绊倒物", "地面连续、干燥且无明显障碍", "high", 1, "立即设置警示并处理次生风险"),
        ("防火门是否被物品顶住或明显损坏", "门体、闭门器及门前区域可见", "high", 1, "移除顶门物，损坏则派工程工单"),
        ("消火栓或灭火器是否被遮挡", "消防设施正面和取用空间可见", "high", 1, "清除遮挡并补拍复核照片"),
        ("应急照明是否实际可用", "单张静态照片通常无法证明功能", "high", 0, "由人工测试或读取巡检记录确认"),
    ],
    "FIRE_PASSAGE": [
        ("疏散楼梯和前室是否堆放杂物", "楼梯、平台及前室无堆物", "critical", 1, "立即清理并记录整改前后照片"),
        ("安全出口门是否锁闭", "门状态和锁具区域清晰可见", "critical", 1, "疑似锁闭应现场人工验证并立即上报"),
        ("常闭式防火门是否保持关闭", "门扇闭合状态可见", "high", 1, "移除阻挡物并检查闭门器"),
        ("疏散指示标志是否连续且方向清楚", "照片能覆盖相邻方向标志", "high", 1, "缺失或遮挡则派工程工单"),
        ("消防车通道是否被车辆或设施占用", "通道全景与标线可见", "critical", 1, "立即联系移车并升级班长"),
        ("应急照明和防火门联动是否有效", "静态照片不能证明联动功能", "high", 0, "查阅测试记录并由专业人员验证"),
    ],
    "FIRE_CONTROL_ROOM": [
        ("控制台是否显示可见故障或屏蔽提示", "显示屏无遮挡且文字可辨", "critical", 1, "值班员现场核验并按制度处理"),
        ("控制室通道和设备前是否堆物", "设备周边净空可见", "high", 1, "立即清理"),
        ("值班人员是否达到规定人数", "单张照片无法证明整班人数", "critical", 0, "结合排班、门禁和现场点名人工确认"),
        ("值班人员资质是否有效", "照片不可作为有效资质核验", "critical", 0, "核验证书原件或系统档案"),
        ("值班和故障记录是否连续", "单张照片无法证明日志完整性", "high", 0, "人工检查日志时间序列"),
        ("消防联动控制是否处于规定状态", "界面状态需值班员解释确认", "critical", 0, "由持证人员确认，AI仅提示疑点"),
    ],
    "POWER_ROOM": [
        ("门口是否有警示标识和限制进入措施", "门、标识和锁闭状态可见", "high", 1, "缺失则补设标识并限制无关人员"),
        ("设备周边是否堆放可燃物或杂物", "设备前后可见区域无堆物", "critical", 1, "立即隔离并联系工程清理"),
        ("地面或顶部是否有漏水迹象", "积水、水渍或滴漏点可见", "critical", 1, "设置警戒并立即通知工程"),
        ("是否存在裸露线缆、破损箱门或异常焦痕", "安全距离外的外观照片", "critical", 1, "不得触碰，立即升级工程人员"),
        ("灭火器材是否在位且无遮挡", "器材和取用空间可见", "high", 1, "清除遮挡；有效期需人工核验"),
        ("温度、负荷和内部电气状态是否正常", "静态照片不能可靠判断", "critical", 0, "读取仪表并由专业电工判断"),
    ],
    "ELEVATOR_AREA": [
        ("厅门是否变形、破损或存在异常缝隙", "厅门正面完整可见", "high", 1, "立即停用疑似故障电梯并联系维保"),
        ("电梯口是否有积水或绊倒物", "门前地面清晰可见", "high", 1, "设置警示并清理"),
        ("候梯区是否被设备或推车阻挡", "候梯区全景可见", "medium", 1, "疏通等待和抢救通道"),
        ("检修或停用标识是否清晰", "标识与对应电梯可见", "high", 1, "补设可靠停用隔离"),
        ("紧急对讲是否可用", "单张照片只能确认装置外观", "high", 0, "通过测试记录或现场通话验证"),
        ("电梯运行是否平稳", "静态照片不能判断运行性能", "high", 0, "由维保人员测试"),
    ],
    "PARKING_TRAFFIC": [
        ("消防车道或登高面是否被占用", "标线、通道和车辆位置可见", "critical", 1, "立即移车并升级班长"),
        ("车辆通道是否拥堵或逆向占道", "通道全景可见", "high", 1, "现场疏导并调整临时路线"),
        ("消火栓、水泵接合器是否被遮挡", "设施和周边净空可见", "critical", 1, "清除遮挡"),
        ("地面是否有油污、积水或破损", "地面异常清晰可见", "high", 1, "设置警示并派清洁或工程工单"),
        ("限速、禁停和方向标识是否可见", "标识与道路关系可见", "medium", 1, "补设或清洁标识"),
        ("监控和照明是否实际有效", "单张照片不能全面证明", "medium", 0, "人工查看画面和照度测试"),
    ],
    "MEDICAL_GAS": [
        ("周边是否有吸烟、明火或动火迹象", "禁火区和可见火源区域", "critical", 1, "立即制止并升级"),
        ("禁火禁烟及危险警示是否清晰", "入口标识可见", "high", 1, "补设或更换标识"),
        ("外围是否堆放无关物品或可燃物", "周边净空可见", "critical", 1, "隔离并清理"),
        ("气瓶是否有可见倾倒、无固定等异常", "仅限安全距离外可见部分", "critical", 1, "不得自行搬动，联系专业人员"),
        ("灭火器材和应急联络信息是否可见", "器材和联络牌可见", "high", 1, "清除遮挡并补齐标识"),
        ("是否存在气体泄漏或压力异常", "照片无法确认泄漏和压力", "critical", 0, "使用合规检测设备并由专业人员确认"),
    ],
}


SLA_POLICIES = [
    (1, "S1", 120, 1440, "squad_leader", "security_manager", "一般服务问题；2小时响应，24小时完成或给出计划。"),
    (2, "S2", 30, 480, "squad_leader", "security_manager", "影响秩序或存在明显隐患；30分钟响应，8小时完成或控制风险。"),
    (3, "S3", 10, 120, "security_manager", "project_manager", "较高安全风险或上级通知；10分钟响应，2小时形成处置结果。"),
    (4, "S4", 5, 30, "security_manager", "property_manager", "生命安全或重大火灾风险；立即行动，5分钟内确认响应。"),
]


COMPLAINTS = [
    (1, "CMP-20260801-001", "phone", "medical_staff", "病区走廊被推车占用",
     "医护人员电话反映住院部三层夜间多辆推车占用通道。", "S2", "SECURITY", "rectified",
     "2026-08-01T20:00:00+08:00", "2026-08-01T20:30:00+08:00", "2026-08-02T04:00:00+08:00", "completed", 5,
     "已收到反馈，将立即核查并清理通道，同时复核同楼层其他疏散路径。", "清理推车并重新划定临时停放区，纳入病区走廊巡检风险点。", 1, 1),
    (2, "CMP-20260802-001", "paper", "patient", "门岗沟通态度生硬",
     "患者书面反映门岗解释探视要求时语气生硬。", "S1", "SECURITY", "closed",
     "2026-08-02T10:00:00+08:00", "2026-08-02T12:00:00+08:00", "2026-08-03T10:00:00+08:00", "completed", 4,
     "对沟通体验表示歉意，将核查当班情况并开展服务用语复训。", "完成当班谈话和服务用语培训，增加班前沟通提醒。", 1, 1),
    (3, "CMP-20260803-001", "phone", "hospital_leader", "门诊入口车辆拥堵",
     "院方领导反映高峰期网约车停留导致救护通道拥堵。", "S2", "SECURITY", "rectified",
     "2026-08-03T08:10:00+08:00", "2026-08-03T08:40:00+08:00", "2026-08-03T16:10:00+08:00", "completed", 5,
     "立即增派人员疏导并设置临时即停即走区。", "调整高峰岗并增设落客区引导牌，纳入停车场巡检。", 1, 1),
    (4, "CMP-20260804-001", "superior_notice", "superior_unit", "消防楼梯安全出口疑似锁闭",
     "上级检查通知指出A区消防楼梯某层出口存在锁闭风险。", "S3", "SECURITY", "closed",
     "2026-08-04T09:00:00+08:00", "2026-08-04T09:10:00+08:00", "2026-08-04T11:00:00+08:00", "completed", 5,
     "已立即安排现场核验，发现锁闭将当场解除并启动同类点位排查。", "现场解除不合规门禁设置并完成全楼抽查，建立安全出口专项清单。", 1, 1),
    (5, "CMP-20260805-001", "phone", "medical_staff", "困梯响应沟通不及时",
     "医护人员反映困梯后未及时获知维保到场进度。", "S3", "ENGINEERING", "follow_up",
     "2026-08-05T14:00:00+08:00", "2026-08-05T14:10:00+08:00", "2026-08-05T16:00:00+08:00", "pending", None,
     "已升级班长和工程部，将每5分钟同步一次救援进度。", "建立困梯事件进度播报节点，救援结束后由客服回访。", 1, 1),
    (6, "CMP-20260806-001", "paper", "patient", "夜间公共区域争吵影响休息",
     "患者书面反映夜间公共区域有人争吵，保安到场较慢。", "S2", "SECURITY", "processing",
     "2026-08-06T22:30:00+08:00", "2026-08-06T23:00:00+08:00", "2026-08-07T06:30:00+08:00", "scheduled", None,
     "将核查当班响应记录并调整夜间巡查点位。", "夜间重点时段增加住院部公共区域巡查。", 1, 1),
    (7, "CMP-20260807-001", "phone", "hospital_leader", "患者外出核验流程存在空档",
     "院方领导反映门岗未能快速查询患者外出申请状态。", "S3", "SECURITY", "processing",
     "2026-08-07T11:00:00+08:00", "2026-08-07T11:10:00+08:00", "2026-08-07T13:00:00+08:00", "scheduled", None,
     "已通知班长核验现行流程并与责任病区确认联络方式。", "拟建立人工核验登记和双人确认，首版不连接HIS。", 1, 1),
    (8, "CMP-20260808-001", "superior_notice", "superior_unit", "消防控制室值班记录不连续",
     "上级书面通知指出某时段值班记录存在空白。", "S3", "SECURITY", "rectified",
     "2026-08-08T09:30:00+08:00", "2026-08-08T09:40:00+08:00", "2026-08-08T11:30:00+08:00", "completed", 4,
     "立即核验排班、门禁和纸质记录，缺失项按制度整改。", "补充交接检查和班长每日复核，不以单张照片代替日志完整性核验。", 1, 1),
]


RISK_POINTS = [
    (1, "RSK-001", "病区走廊推车占用疏散路径", "fire", "complaint", "CMP-20260801-001", "WARD_CORRIDOR", "high",
     "走廊可见多辆推车连续摆放，影响有效通行宽度。", "拍摄走廊全景并核对临时停放区。", "设置固定停放区，班后清场并复查。", "active"),
    (2, "RSK-002", "门岗服务用语不规范", "service", "complaint", "CMP-20260802-001", None, "medium",
     "该风险无法通过现场照片可靠识别。", "通过投诉、抽查和培训记录识别。", "班前提醒、服务用语培训和回访。", "active"),
    (3, "RSK-003", "门诊入口车辆拥堵", "traffic", "complaint", "CMP-20260803-001", "PARKING_TRAFFIC", "high",
     "入口区域车辆排队或占用急救通道。", "高峰期拍摄入口全景并记录持续时间。", "设置即停即走区和高峰岗。", "active"),
    (4, "RSK-004", "安全出口锁闭", "fire", "complaint", "CMP-20260804-001", "FIRE_PASSAGE", "critical",
     "照片可能看到锁具，但必须现场推门验证。", "人工验证门可从疏散方向开启。", "解除不合规锁闭并检查门禁逻辑。", "active"),
    (5, "RSK-005", "困梯进度沟通中断", "facility", "complaint", "CMP-20260805-001", "ELEVATOR_AREA", "high",
     "无法通过照片判断，需要查看事件时间线。", "检查维保呼叫、到场和播报节点。", "设置5分钟进度播报和超时升级。", "active"),
    (6, "RSK-006", "夜间冲突响应慢", "security", "complaint", "CMP-20260806-001", "WARD_CORRIDOR", "high",
     "由投诉和响应时间记录识别。", "复核夜间巡查和事件响应日志。", "增加重点时段巡查和就近派单。", "active"),
    (7, "RSK-007", "患者外出申请核验空档", "hospital", "complaint", "CMP-20260807-001", "WARD_CORRIDOR", "critical",
     "不能通过照片判断申请状态。", "核验护士站确认和门岗登记。", "建立双向联络、人工确认和交接记录。", "active"),
    (8, "RSK-008", "消防控制室日志缺失", "fire", "complaint", "CMP-20260808-001", "FIRE_CONTROL_ROOM", "critical",
     "单张照片不能证明日志连续性。", "逐时核对排班、门禁和日志。", "班长每日复核并留痕。", "active"),
    (9, "RSK-009", "配电房附近漏水", "facility", "synthetic_case", "INC-20260806-001", "POWER_ROOM", "critical",
     "地面积水、水渍或顶部滴漏可见。", "安全距离拍照并立即隔离。", "工程排查水源、电气安全和修复结果。", "active"),
    (10, "RSK-010", "中心供氧周边堆放可燃物", "fire", "synthetic_case", "PATROL-DEMO-001", "MEDICAL_GAS", "critical",
     "外围可见纸箱或其他可燃物。", "检查禁火区净空和警示标识。", "立即清理并复核责任区域。", "active"),
]


SOURCES = [
    (1, "SRC-FIRE-LAW", "中华人民共和国消防法（2021修正）", "全国人民代表大会常务委员会", "主席令第81号", "中国", "法律",
     "2021-04-29", "2021-04-29", "active", "https://policy.mofcom.gov.cn/claw/clawContent.shtml?id=90360",
     "商务部法规平台注明信息来源为中国人大网；生产使用前应再次核验国家法律法规数据库。"),
    (2, "SRC-GD-FIRE", "广东省实施《中华人民共和国消防法》办法（2022修订）", "广东省人民代表大会常务委员会", "", "广东省", "地方性法规",
     "2022-03-29", "2022-07-01", "active", "https://yjglj.gz.gov.cn/zwgk/zcfgk/yjgl/flfg/content/post_10811715.html",
     "官方政府站点转载现行文本。"),
    (3, "SRC-SZ-FIRE", "深圳经济特区消防条例", "深圳市人民代表大会常务委员会", "公告第一〇二号", "深圳市", "经济特区法规",
     "2023-08-02", "2023-11-01", "active", "https://yjgl.sz.gov.cn/gkmlpt/content/11/11002/mpost_11002824.html",
     "深圳市应急管理局页面标注现行有效。"),
    (4, "SRC-SZ-HOSPITAL-FIRE", "深圳市医院消防安全管理规定", "原深圳市公安局消防局", "深公消〔2010〕39号", "深圳市", "部门规范性文件",
     "2010-05-31", None, "needs_review", "https://www.sz.gov.cn/zfgb/2010/gb701/content/post_4980621.html",
     "年代较早且消防监管机构已经改革；数据库保留作深圳医院场景参考，生产使用前必须向主管部门核验效力。"),
    (5, "SRC-NHC-NINE", "医疗机构消防安全管理九项规定（2020年版）", "国家卫生健康委、应急管理部、国家中医药管理局", "国卫办发〔2020〕1号", "中国", "部门规范性文件",
     "2020-01-08", "2020-02-16", "active", "https://www.nhc.gov.cn/bgt/c100023/202002/8192538054744480874667783cfbfed9.shtml",
     "原2015版同时废止。"),
    (6, "SRC-WS308", "医疗机构消防安全管理", "国家卫生健康委员会", "WS 308—2019", "中国", "强制性卫生行业标准",
     "2019-10-18", "2020-05-01", "active", "https://www.nhc.gov.cn/fzs/c100048/201911/9f1d3cd8faf5462e8074915ecb63b1dc/files/1734000625046_49175.pdf",
     "代替WS 308—2009。"),
    (7, "SRC-ORDER61", "机关、团体、企业、事业单位消防安全管理规定", "中华人民共和国公安部", "公安部令第61号", "中国", "部门规章",
     "2001-11-14", "2002-05-01", "active", "https://www.119.gov.cn/gk/flfg/bmgz/2022/29134.shtml",
     "国家消防救援局官方法规页面。"),
    (8, "SRC-HIGHRISE", "高层民用建筑消防安全管理规定", "中华人民共和国应急管理部", "应急管理部令第5号", "中国", "部门规章",
     "2021-06-21", "2021-08-01", "active", "https://www.mem.gov.cn/gk/zfxxgkpt/fdzdgknr/202106/t20210625_389980.shtml",
     "适用于已建成并依法投入使用的高层民用建筑。"),
    (9, "SRC-HOSPITAL-SECURITY", "关于推进医院安全秩序管理工作的指导意见", "国家卫生健康委等八部门", "", "中国", "指导意见",
     "2021-09-22", None, "active", "https://www.nhc.gov.cn/yzygj/c100068/202109/a64d79d62ee54efeb50b41870d2fc7d9.shtml",
     "用于医院治安防控和保安配置参考。"),
    (10, "SRC-SZ-EMERGENCY-MED", "深圳经济特区医疗急救条例", "深圳市人民代表大会常务委员会", "深圳市六届人大常委会公告第一〇九号", "深圳市", "经济特区法规",
     "2018-06-27", None, "active", "https://www.sz.gov.cn/cn/xxgk/zfxxgj/zcfg/content/post_8967830.html",
     "页面文本含2019年修正信息；当前立法动态可能继续修改，生产使用前应核验最新版。"),
]


FIRE_DOCUMENTS = [
    ("FIRE-001", 1, "中华人民共和国消防法：单位责任与火灾处置", "第十六条、第四十四条",
     "单位应落实消防责任、维护设施和疏散通道；发现火灾应立即报警，人员密集场所应组织疏散。",
     ["消防责任", "报警", "疏散", "国家法律"]),
    ("FIRE-002", 2, "广东省消防法实施办法：属地责任参考", "单位消防安全相关条款（使用前核对全文）",
     "作为广东省层面的消防责任补充依据；系统回答应链接正式全文，不自行推断处罚结论。",
     ["广东", "消防责任", "地方性法规"]),
    ("FIRE-003", 3, "深圳经济特区消防条例：单位与重点单位职责", "第十八条、第十九条",
     "单位应建立制度和预案、维护设施、保持通道畅通；重点单位实行每日防火巡查并保存记录。",
     ["深圳", "每日巡查", "消防档案"]),
    ("FIRE-004", 3, "深圳经济特区消防条例：高层公共建筑与物业职责", "第二十一条、第二十四条、第一百零五条",
     "高层公共建筑需公示消防安全管理人、设置禁火禁烟区域并组织综合演练；火灾隐患范围包括疏散、设施和防火分区等问题。",
     ["深圳", "高层建筑", "物业", "火灾隐患"]),
    ("FIRE-005", 4, "深圳市医院消防安全管理规定：医院职责与疏散设施", "第五条至第八条、第十三条、第十四条",
     "适用于深圳医院消防职责和设施管理的场景参考，但该2010文件效力必须人工复核。",
     ["深圳医院", "疏散", "待核验"]),
    ("FIRE-006", 5, "医疗机构消防安全管理九项规定（2020版）", "第三项、第四项、第五项、第六项",
     "强调日常巡查、隐患闭环、禁止行为、培训演练和行动不便患者的针对性疏散安排。",
     ["医疗机构", "巡查", "隐患闭环", "培训演练"]),
    ("FIRE-007", 6, "WS 308—2019 医疗机构消防安全管理", "第4章至第12章（以正式PDF为准）",
     "强制性卫生行业标准，覆盖责任、制度、重点部位、巡查检查、预案和培训等要求。",
     ["WS308", "强制性标准", "医疗机构"]),
    ("FIRE-008", 7, "公安部令第61号：单位消防安全管理基础", "防火巡查、检查、隐患整改和灭火疏散相关条款",
     "用于单位消防组织、巡查检查、隐患整改、宣传培训和预案管理的基础参考。",
     ["公安部令61号", "单位消防", "巡查"]),
    ("FIRE-009", 8, "高层民用建筑消防安全管理规定", "第四条、第七条、第八条、第十五条、第二十二条",
     "明确高层公共建筑业主、使用人和受托物业的责任，并对动火、通道和消防管理人提出要求。",
     ["高层建筑", "物业", "动火", "消防车道"]),
    ("FIRE-010", 9, "医院安全秩序管理工作指导意见", "人防、物防、技防和医院保安配置部分",
     "用于医院治安防控、保安力量和警医联动的方向性参考，不作为具体强制措施的唯一依据。",
     ["医院治安", "保安", "警医联动"]),
]


COMPLAINT_GUIDES = [
    ("COMP-GUIDE-001", "投诉受理与分类", "记录来源、投诉人类型、事实、时间、地点和期望；不收集与处理无关的患者诊疗信息。"),
    ("COMP-GUIDE-002", "SLA与超时升级", "按S1至S4配置响应和解决时限；超时先升级安管经理，再升级项目经理或物业经理。"),
    ("COMP-GUIDE-003", "回访与满意度", "处理完成后由客服回访，记录是否解决、满意度、补充意见和再次打开原因。"),
    ("COMP-GUIDE-004", "投诉转风险与整改知识", "经人工审核后，将事实明确且可复用的投诉转成风险点、典型案例和整改知识。"),
    ("COMP-GUIDE-005", "纸质通知OCR录入", "OCR结果只作为草稿；客服必须核对标题、文号、日期、责任部门和时限后再提交。"),
]


DAILY_GUIDES = [
    ("DAILY-GUIDE-001", "早班工作计划模板", "从未关闭事件、到期投诉、巡检风险点和月度计划中生成今日任务。"),
    ("DAILY-GUIDE-002", "晚间日报模板", "汇总事件、巡检、投诉、整改、超时项和次日关注点，生成后由安管经理审核。"),
    ("DAILY-GUIDE-003", "突发事件日报摘要", "只记录安保所需事实、响应节点、任务状态和待确认事项，不记录患者诊疗详情。"),
    ("DAILY-GUIDE-004", "投诉日报摘要", "按来源、等级、责任部门、SLA状态、回访和满意度汇总。"),
    ("DAILY-GUIDE-005", "巡检日报摘要", "按场景汇总照片识别结果、人工确认结果、无法从照片判断的项目和整改状态。"),
]


MULTIMODAL_GUIDES = [
    ("MM-GUIDE-001", "照片拍摄要求", "选择场景后拍摄清晰全景，避免逆光和过度压缩；必要时补拍局部证据。"),
    ("MM-GUIDE-002", "单张照片能力边界", "照片只能判断可见事实，不能证明值班人数、证件有效、设备功能、日志连续或气体泄漏。"),
    ("MM-GUIDE-003", "隐私与脱敏", "尽量避开患者面部、腕带、病历、屏幕和车牌；确需采集时限制访问和保存期限。"),
    ("MM-GUIDE-004", "AI置信度与人工复核", "AI输出应包含置信度、可见证据、无法判断项和建议复核方式；高风险结果必须人工确认。"),
    ("MM-GUIDE-005", "文档OCR质量控制", "纸质投诉和通知OCR后保留原件索引，并由客服核对日期、文号、责任部门、时限和联系人。"),
]


DAILY_PLANS = [
    (1, "PLAN-GUARD-DAY", "保安日班计划", "guard", "07:45", ["查看待办", "完成分配场景照片巡检", "处理站内事件任务", "提交交接记录"], "演示模板"),
    (2, "PLAN-GUARD-NIGHT", "保安夜班计划", "guard", "19:45", ["查看夜间重点点位", "病区和消防通道巡查", "复核门岗联络", "提交夜班记录"], "演示模板"),
    (3, "PLAN-LEADER", "班长每日计划", "squad_leader", "07:30", ["检查在岗和交接", "确认高风险事件", "抽查巡检结果", "处理超时任务"], "演示模板"),
    (4, "PLAN-SECURITY-MANAGER", "安管经理每日计划", "security_manager", "08:00", ["审批关键动作", "审查SLA", "复核高风险整改", "审核日报"], "演示模板"),
    (5, "PLAN-CUSTOMER-SERVICE", "客服每日计划", "customer_service", "08:15", ["录入新投诉", "核对OCR草稿", "执行回访", "汇总满意度"], "演示模板"),
]


DAILY_REPORTS = [
    (1, "RPT-20260804", "2026-08-04", "日班", "完成消防通道专项核查，1项高风险问题已整改。", "无人员伤害事件。", "完成7个场景抽查。", "上级通知1件，已闭环。", "次日复核A区安全出口。", "approved"),
    (2, "RPT-20260805", "2026-08-05", "日班", "发生困梯演示事件，维保已到场，待客服回访。", "困梯1件，无人员不适。", "电梯厅补拍2张。", "投诉1件进入回访。", "检查困梯进度播报机制。", "reviewed"),
    (3, "RPT-20260806", "2026-08-06", "夜班", "夜间公共区域秩序总体稳定。", "人员冲突演示事件1件，已降级处置。", "病区走廊巡检发现1项通道堆物。", "患者投诉1件处理中。", "增加住院部重点时段巡查。", "draft"),
    (4, "RPT-20260807", "2026-08-07", "日班", "患者外出核验流程开展复盘。", "疑似违规外出演示1件，患者已由医护接管。", "门岗和病区联络点完成抽查。", "院方领导投诉1件处理中。", "建立双人确认表。", "reviewed"),
    (5, "RPT-20260808", "2026-08-08", "日班", "消防控制室记录专项整改完成。", "无新增重大事件。", "控制室人工复核完成。", "上级通知1件已回访。", "连续7天抽查值班日志。", "approved"),
]


INCIDENTS = [
    (1, "INC-20260801-001", "FIRE", "FIRE_STAIRS_A", "A区楼梯间闻到焦糊味", "现场未见明火，已通知控制室和工程核验。", "S3", "closed", 1, "squad_leader", "疑似电气或烟气来源，需现场确认。", "confirmed_by_leader", "2026-08-01T09:15:00+08:00"),
    (2, "INC-20260802-001", "CONFLICT", "OUTPATIENT_1F", "门诊大厅人员争执", "两名访客发生高声争执，无武器，无人受伤。", "S2", "closed", 1, "squad_leader", "建议非对抗分隔并通知院方。", "confirmed_by_leader", "2026-08-02T15:20:00+08:00"),
    (3, "INC-20260803-001", "EQUIPMENT_FAILURE", "OUTPATIENT_1F", "门禁设备无法读取", "门诊侧门门禁读卡器离线。", "S2", "closed", 1, "squad_leader", "需设置人工值守并派工程工单。", "not_required", "2026-08-03T10:10:00+08:00"),
    (4, "INC-20260804-001", "POWER_OUTAGE", "WARD_3F", "住院部三层局部停电", "走廊应急照明已亮，部分普通照明熄灭。", "S3", "closed", 2, "squad_leader", "涉及病区，需立即通知工程和院方。", "approved_by_security_manager", "2026-08-04T13:05:00+08:00"),
    (5, "INC-20260805-001", "ELEVATOR_TRAP", "ELEVATOR_A", "A区电梯困人", "两人被困，无明显不适，维保已联系。", "S3", "closed", 1, "squad_leader", "禁止扒门，持续对讲并保持救援通道。", "confirmed_by_leader", "2026-08-05T14:02:00+08:00"),
    (6, "INC-20260806-001", "WATER_LEAK", "POWER_ROOM", "配电房门外顶部滴水", "水滴位于配电房门外，已隔离。", "S3", "processing", 1, "squad_leader", "存在电气次生风险，需工程人员立即评估。", "approved_by_security_manager", "2026-08-06T08:45:00+08:00"),
    (7, "INC-20260807-001", "VEHICLE_ACCIDENT", "PARKING_B1", "停车场轻微碰撞", "两车刮擦，无人员受伤，通道短时受阻。", "S2", "closed", 1, "squad_leader", "疏导车辆并保留公共区域记录。", "confirmed_by_leader", "2026-08-07T09:20:00+08:00"),
    (8, "INC-20260807-002", "PATIENT_UNAUTHORIZED_EXIT", "OUTPATIENT_1F", "疑似住院患者从门诊出口离开", "护士站反馈无已核验的外出申请，人员已在院内找到。", "S3", "closed", 2, "squad_leader", "需院方确认身份和申请状态，不采取强制限制。", "confirmed_by_leader", "2026-08-07T11:05:00+08:00"),
    (9, "INC-20260808-001", "PATIENT_FALL", "WARD_3F", "病区走廊患者摔倒", "保安发现后立即呼叫护士站并清空通道。", "S4", "closed", 1, "squad_leader", "医护优先接管，安保保护现场并排查地面风险。", "approved_by_security_manager", "2026-08-08T16:40:00+08:00"),
    (10, "INC-20260809-001", "PATIENT_RESCUE", "OUTPATIENT_1F", "门诊大厅患者需要抢救协助", "安保引导急救人员并疏散围观。", "S4", "closed", 1, "squad_leader", "安保只执行清障、引导和秩序维护。", "approved_by_security_manager", "2026-08-09T10:25:00+08:00"),
]


def connect_database() -> sqlite3.Connection:
    ROOT.mkdir(parents=True, exist_ok=True)
    if DB_PATH.exists():
        DB_PATH.unlink()
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.executescript(SQLITE_SCHEMA)
    return connection


def insert_reference_data(conn: sqlite3.Connection) -> None:
    timestamp = now_iso()
    metadata = {
        "database_name": "医院物业安管系统小型演示数据库",
        "schema_version": "1.0.0",
        "as_of_date": AS_OF_DATE,
        "scope": "仅数据库、样例资料和迁移结构，不含前后端项目",
        "data_policy": "全部业务数据为虚构演示数据，不含真实患者或投诉人信息",
        "safety_notice": "AI输出不得替代消防、医疗、执法或工程专业判断；关键动作必须人工确认，但不得用审批延误紧急报警和救援",
    }
    conn.executemany(
        "INSERT INTO metadata(key, value, updated_at) VALUES (?, ?, ?)",
        [(key, value, timestamp) for key, value in metadata.items()],
    )
    conn.executemany("INSERT INTO departments VALUES (?, ?, ?, ?)", DEPARTMENTS)
    conn.executemany(
        "INSERT INTO roles VALUES (?, ?, ?, ?)",
        [(role_id, code, name, dumps(permissions)) for role_id, code, name, permissions in ROLES],
    )
    conn.executemany(
        "INSERT INTO users(id, username, display_name, role_id, department_id) VALUES (?, ?, ?, ?, ?)",
        USERS,
    )
    conn.executemany("INSERT INTO locations VALUES (?, ?, ?, ?, ?, ?)", LOCATIONS)
    conn.executemany(
        """INSERT INTO event_types(
               id, code, name, category, default_severity, default_owner_role_code,
               response_minutes, critical_confirmation_required, description, safety_boundary
           ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        EVENTS,
    )

    event_ids = {row["code"]: row["id"] for row in conn.execute("SELECT id, code FROM event_types")}
    step_rows = []
    step_id = 1
    for event_code, steps in PLAYBOOKS.items():
        for step_no, step in enumerate(steps, start=1):
            action, owner, minutes, approval, approval_role, critical, notes = step
            step_rows.append((step_id, event_ids[event_code], step_no, action, owner, minutes, approval, approval_role, critical, notes))
            step_id += 1
    conn.executemany(
        """INSERT INTO event_playbook_steps(
               id, event_type_id, step_no, action, owner_role_code, time_limit_minutes,
               approval_required, approval_role_code, is_critical_action, notes
           ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        step_rows,
    )

    conn.executemany("INSERT INTO inspection_scenes VALUES (?, ?, ?, ?, ?)", SCENES)
    scene_ids = {row["code"]: row["id"] for row in conn.execute("SELECT id, code FROM inspection_scenes")}
    item_rows = []
    item_id = 1
    for scene_code, items in INSPECTION_ITEMS.items():
        for item_no, item in enumerate(items, start=1):
            question, evidence, risk, can_confirm, advice = item
            item_rows.append((
                item_id,
                scene_ids[scene_code],
                f"{scene_code}-{item_no:02d}",
                question.replace("是否", "").replace("？", ""),
                question,
                evidence,
                risk,
                can_confirm,
                advice,
            ))
            item_id += 1
    conn.executemany(
        """INSERT INTO inspection_items(
               id, scene_id, item_code, title, inspection_question, expected_visual_evidence,
               risk_level, can_confirm_from_single_photo, handling_advice
           ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        item_rows,
    )
    conn.executemany("INSERT INTO sla_policies VALUES (?, ?, ?, ?, ?, ?, ?)", SLA_POLICIES)
    conn.executemany(
        """INSERT INTO complaints(
               id, complaint_no, source_type, complainant_type, title, description, severity,
               responsible_department_code, status, received_at, response_due_at, resolution_due_at,
               callback_status, satisfaction_score, ai_reply_draft, rectification_summary,
               converted_to_risk, converted_to_case
           ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        COMPLAINTS,
    )
    conn.executemany(
        """INSERT INTO risk_points(
               id, risk_no, title, category, source_type, source_reference, scene_code, risk_level,
               recognition_hint, inspection_advice, rectification_knowledge, status
           ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        RISK_POINTS,
    )
    conn.executemany(
        """INSERT INTO knowledge_sources(
               id, source_code, title, issuing_authority, document_number, jurisdiction, source_type,
               published_date, effective_date, validity_status, official_url, retrieval_date, notes
           ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        [source[:-1] + (AS_OF_DATE, source[-1]) for source in SOURCES],
    )
    conn.executemany(
        """INSERT INTO daily_plan_templates(
               id, template_code, name, applicable_role_code, trigger_time, plan_items_json, notes
           ) VALUES (?, ?, ?, ?, ?, ?, ?)""",
        [(row_id, code, name, role, trigger, dumps(items), notes) for row_id, code, name, role, trigger, items, notes in DAILY_PLANS],
    )
    recipients = dumps(["security_manager", "project_manager", "customer_service"])
    conn.executemany(
        """INSERT INTO daily_report_samples(
               id, report_no, report_date, shift_name, summary, incident_summary, inspection_summary,
               complaint_summary, pending_actions, recipients_json, human_review_status
           ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        [(row_id, no, date, shift, summary, incident, inspection, complaint, pending, recipients, status)
         for row_id, no, date, shift, summary, incident, inspection, complaint, pending, status in DAILY_REPORTS],
    )

    location_ids = {row["code"]: row["id"] for row in conn.execute("SELECT id, code FROM locations")}
    incident_rows = []
    for row in INCIDENTS:
        row_id, no, event_code, location_code, title, description, severity, status, user_id, assigned, assessment, confirmation, occurred = row
        incident_rows.append((row_id, no, event_ids[event_code], location_ids[location_code], title, description, severity, status, user_id, assigned, assessment, confirmation, occurred))
    conn.executemany(
        """INSERT INTO incident_examples(
               id, incident_no, event_type_id, location_id, title, description, severity, status,
               reported_by_user_id, assigned_role_code, ai_assessment, human_confirmation_status, occurred_at
           ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        incident_rows,
    )

    notification_rows = [
        (1, "NOTIFY-S3-EVENT", "incident_created", dumps({"severity": ["S3"]}), dumps(["squad_leader", "security_manager"]), "in_app", 1, "S3事件通知班长和安管经理"),
        (2, "NOTIFY-S4-EVENT", "incident_created", dumps({"severity": ["S4"]}), dumps(["squad_leader", "security_manager", "project_manager", "property_manager"]), "in_app", 1, "S4事件通知管理链"),
        (3, "NOTIFY-COMPLAINT-DUE", "complaint_near_due", dumps({"remaining_minutes_lte": 10}), dumps(["customer_service", "squad_leader"]), "in_app", 0, "投诉临近超时提醒"),
        (4, "NOTIFY-COMPLAINT-OVERDUE", "complaint_overdue", dumps({"status_not_in": ["closed", "rectified"]}), dumps(["security_manager", "project_manager"]), "in_app", 0, "投诉超时升级"),
        (5, "NOTIFY-DAILY-REPORT", "daily_report_ready", dumps({"human_review_status": "approved"}), dumps(["security_manager", "project_manager", "customer_service"]), "in_app", 0, "日报审核后发送"),
    ]
    conn.executemany("INSERT INTO notification_rules VALUES (?, ?, ?, ?, ?, ?, ?, ?)", notification_rows)


def markdown_document(title: str, category: str, summary: str, content: str, citation: str, source_url: str | None, official: bool) -> str:
    lines = [
        f"# {title}",
        "",
        f"- 类别：{category}",
        f"- 数据性质：{'官方资料摘要' if official else '虚构演示资料'}",
        f"- 截止日期：{AS_OF_DATE}",
        f"- 引用定位：{citation or '不适用'}",
    ]
    if source_url:
        lines.append(f"- 官方来源：{source_url}")
    lines.extend([
        "",
        "## 摘要",
        "",
        summary,
        "",
        "## 内容",
        "",
        content,
        "",
        "## 使用边界",
        "",
        "本资料用于学习演示。涉及消防、医疗、执法、工程和人身安全的判断必须由有权限、有资质的人员确认；紧急报警和救援不得因系统审批造成延误。",
        "",
    ])
    return "\n".join(lines)


def insert_knowledge(conn: sqlite3.Connection) -> None:
    KNOWLEDGE_DIR.mkdir(parents=True, exist_ok=True)
    source_by_id = {row["id"]: row for row in conn.execute("SELECT * FROM knowledge_sources")}
    documents = []

    for event_id, event_code, event_name in conn.execute("SELECT id, code, name FROM event_types ORDER BY id"):
        steps = list(conn.execute(
            "SELECT step_no, action, owner_role_code, time_limit_minutes, approval_required, notes FROM event_playbook_steps WHERE event_type_id=? ORDER BY step_no",
            (event_id,),
        ))
        content = "\n".join(
            f"{row['step_no']}. {row['action']}（责任角色：{row['owner_role_code']}；时限：{row['time_limit_minutes']}分钟；{'需确认' if row['approval_required'] else '无需额外确认'}）。{row['notes']}"
            for row in steps
        )
        event = conn.execute("SELECT * FROM event_types WHERE id=?", (event_id,)).fetchone()
        documents.append({
            "code": f"ER-{event_id:03d}", "category": "emergency_response", "title": f"{event_name}演示处置卡",
            "type": "internal_playbook", "source_id": None, "jurisdiction": "示例医院",
            "citation": "内部演示流程", "summary": event["description"],
            "content": content + f"\n\n安全边界：{event['safety_boundary']}",
            "tags": [event_code, event["default_severity"], "应急处置"], "official": False, "review": True,
        })

    for scene_id, scene_code, scene_name, description in conn.execute("SELECT id, code, name, description FROM inspection_scenes ORDER BY id"):
        items = list(conn.execute(
            "SELECT item_code, inspection_question, can_confirm_from_single_photo, handling_advice FROM inspection_items WHERE scene_id=? ORDER BY id",
            (scene_id,),
        ))
        content = "\n".join(
            f"- [{row['item_code']}] {row['inspection_question']}；照片判断：{'可以判断可见范围' if row['can_confirm_from_single_photo'] else '不能仅凭单张照片确认'}；建议：{row['handling_advice']}"
            for row in items
        )
        documents.append({
            "code": f"INS-{scene_id:03d}", "category": "inspection", "title": f"{scene_name}照片巡检清单",
            "type": "inspection_checklist", "source_id": None, "jurisdiction": "示例医院",
            "citation": "内部演示清单", "summary": description, "content": content,
            "tags": [scene_code, "照片巡检", "人工复核"], "official": False, "review": True,
        })

    for code, title, content in COMPLAINT_GUIDES:
        documents.append({
            "code": code, "category": "complaint", "title": title, "type": "workflow_guide",
            "source_id": None, "jurisdiction": "示例医院", "citation": "内部演示流程", "summary": content,
            "content": content, "tags": ["投诉", "SLA", "闭环"], "official": False, "review": True,
        })

    for code, title, content in DAILY_GUIDES:
        documents.append({
            "code": code, "category": "daily_report", "title": title, "type": "report_guide",
            "source_id": None, "jurisdiction": "示例医院", "citation": "内部演示模板", "summary": content,
            "content": content, "tags": ["日报", "计划", "人工审核"], "official": False, "review": True,
        })

    for code, source_id, title, citation, summary, tags in FIRE_DOCUMENTS:
        source = source_by_id[source_id]
        content = (
            f"本条目是对《{source['title']}》的检索摘要。引用定位：{citation}。"
            "系统回答时必须同时返回法规名称、定位、发布日期或施行日期以及官方链接；"
            "涉及具体法律责任、处罚或文件效力时，必须打开官方全文并由人工复核。"
        )
        documents.append({
            "code": code, "category": "fire_assistant", "title": title, "type": "official_source_summary",
            "source_id": source_id, "jurisdiction": source["jurisdiction"], "citation": citation,
            "summary": summary, "content": content, "tags": tags, "official": True,
            "review": source["validity_status"] != "active" or source_id in (1, 2, 4, 7, 9, 10),
        })

    for code, title, content in MULTIMODAL_GUIDES:
        documents.append({
            "code": code, "category": "multimodal", "title": title, "type": "ai_usage_guide",
            "source_id": None, "jurisdiction": "示例医院", "citation": "内部演示规范", "summary": content,
            "content": content, "tags": ["多模态", "照片", "OCR", "隐私"], "official": False, "review": True,
        })

    created_at = now_iso()
    document_rows = []
    chunk_rows = []
    source_catalog_by_id = {row["id"]: row for row in conn.execute("SELECT * FROM knowledge_sources")}
    for doc_id, doc in enumerate(documents, start=1):
        source_url = source_catalog_by_id[doc["source_id"]]["official_url"] if doc["source_id"] else None
        markdown = markdown_document(
            doc["title"], doc["category"], doc["summary"], doc["content"], doc["citation"], source_url, doc["official"]
        )
        filename = f"{doc['code']}.md"
        relative_file = f"knowledge_documents/{filename}"
        (KNOWLEDGE_DIR / filename).write_text(markdown, encoding="utf-8")
        document_rows.append((
            doc_id, doc["code"], doc["category"], doc["title"], doc["type"], doc["source_id"],
            doc["jurisdiction"], doc["citation"], doc["summary"], doc["content"], dumps(doc["tags"]),
            int(doc["official"]), int(doc["review"]), relative_file, sha256_text(markdown), created_at,
        ))
        chunk_rows.append((
            doc_id, doc_id, 1, doc["title"], doc["content"], doc["citation"],
            dumps({"category": doc["category"], "official": doc["official"], "tags": doc["tags"]}),
        ))

    conn.executemany(
        """INSERT INTO knowledge_documents(
               id, doc_code, category, title, document_type, source_id, jurisdiction, citation_locator,
               summary, content, tags_json, is_official, requires_human_review, source_file,
               content_sha256, created_at
           ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        document_rows,
    )
    conn.executemany(
        """INSERT INTO knowledge_chunks(
               id, document_id, chunk_no, heading, content, citation_locator, metadata_json
           ) VALUES (?, ?, ?, ?, ?, ?, ?)""",
        chunk_rows,
    )
    conn.execute("CREATE VIRTUAL TABLE knowledge_fts USING fts5(doc_code, title, summary, content, tags, tokenize='trigram')")
    conn.execute(
        """INSERT INTO knowledge_fts(doc_code, title, summary, content, tags)
           SELECT doc_code, title, summary, content, tags_json FROM knowledge_documents"""
    )


def write_supporting_files(conn: sqlite3.Connection) -> None:
    (ROOT / "schema_sqlite.sql").write_text(SQLITE_SCHEMA.strip() + "\n", encoding="utf-8")
    (ROOT / "schema_postgresql.sql").write_text(POSTGRESQL_SCHEMA.strip() + "\n", encoding="utf-8")

    sources = [dict(row) for row in conn.execute("SELECT * FROM knowledge_sources ORDER BY id")]
    (ROOT / "source_catalog.json").write_text(
        json.dumps(sources, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    counts = {}
    for table in [
        "departments", "roles", "users", "locations", "event_types", "event_playbook_steps",
        "incident_examples", "inspection_scenes", "inspection_items", "sla_policies", "complaints",
        "risk_points", "knowledge_sources", "knowledge_documents", "knowledge_chunks",
        "daily_plan_templates", "daily_report_samples", "notification_rules",
    ]:
        counts[table] = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    category_counts = {
        row["category"]: row["count"]
        for row in conn.execute("SELECT category, COUNT(*) AS count FROM knowledge_documents GROUP BY category ORDER BY category")
    }
    scene_counts = {
        row["code"]: row["count"]
        for row in conn.execute(
            """SELECT s.code, COUNT(i.id) AS count FROM inspection_scenes s
               LEFT JOIN inspection_items i ON i.scene_id=s.id GROUP BY s.id ORDER BY s.id"""
        )
    }
    integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
    foreign_key_issues = [dict(row) for row in conn.execute("PRAGMA foreign_key_check")]
    fts_test = [dict(row) for row in conn.execute(
        "SELECT doc_code, title FROM knowledge_fts WHERE knowledge_fts MATCH '\u6d88\u9632\u5b89\u5168' ORDER BY rank LIMIT 5"
    )]
    report = {
        "generated_at": now_iso(),
        "as_of_date": AS_OF_DATE,
        "database": DB_PATH.name,
        "sqlite_version": sqlite3.sqlite_version,
        "integrity_check": integrity,
        "foreign_key_issues": foreign_key_issues,
        "table_counts": counts,
        "knowledge_category_counts": category_counts,
        "inspection_items_per_scene": scene_counts,
        "fts_smoke_test": fts_test,
        "requirements": {
            "each_knowledge_category_between_5_and_10": all(5 <= value <= 10 for value in category_counts.values()),
            "all_inspection_scenes_have_at_least_5_items": all(value >= 5 for value in scene_counts.values()),
            "all_business_samples_are_synthetic": True,
        },
    }
    (ROOT / "validation_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    dictionary = """# 数据字典摘要

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
"""
    (ROOT / "data_dictionary.md").write_text(dictionary, encoding="utf-8")


def validate(conn: sqlite3.Connection) -> None:
    assert conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    assert not list(conn.execute("PRAGMA foreign_key_check"))
    categories = dict(conn.execute("SELECT category, COUNT(*) FROM knowledge_documents GROUP BY category"))
    expected = {"emergency_response", "inspection", "complaint", "daily_report", "fire_assistant", "multimodal"}
    assert set(categories) == expected
    assert all(5 <= count <= 10 for count in categories.values())
    assert conn.execute("SELECT COUNT(*) FROM event_types").fetchone()[0] == 10
    assert conn.execute("SELECT COUNT(*) FROM incident_examples WHERE is_synthetic=1").fetchone()[0] == 10
    assert conn.execute("SELECT COUNT(*) FROM complaints WHERE is_synthetic=1").fetchone()[0] == 8
    assert conn.execute("SELECT COUNT(*) FROM knowledge_sources").fetchone()[0] == 10
    assert conn.execute("SELECT COUNT(*) FROM roles").fetchone()[0] == 6
    assert conn.execute("SELECT COUNT(*) FROM daily_report_samples").fetchone()[0] == 5
    assert conn.execute("SELECT COUNT(*) FROM knowledge_fts WHERE knowledge_fts MATCH '\u6d88\u9632\u5b89\u5168'").fetchone()[0] >= 5


def main() -> None:
    conn = connect_database()
    try:
        insert_reference_data(conn)
        insert_knowledge(conn)
        conn.commit()
        validate(conn)
        write_supporting_files(conn)
        conn.commit()
    finally:
        conn.close()
    print(f"Created {DB_PATH}")


if __name__ == "__main__":
    main()
