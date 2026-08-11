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
