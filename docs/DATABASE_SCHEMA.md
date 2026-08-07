# Database Schema - PostgreSQL

## Status: VALIDATED FOR DEVELOPMENT

This schema supports role-based permissions, authentication, cost tracking, and audit logging.

---

## TABLE: users

Extends Django's built-in User model. Stores user account information.

```sql
CREATE TABLE auth_user (
    id SERIAL PRIMARY KEY,
    username VARCHAR(150) UNIQUE NOT NULL,
    email VARCHAR(254) UNIQUE NOT NULL,
    password VARCHAR(128) NOT NULL,
    first_name VARCHAR(150),
    last_name VARCHAR(150),
    is_active BOOLEAN DEFAULT TRUE,
    is_staff BOOLEAN DEFAULT FALSE,
    is_superuser BOOLEAN DEFAULT FALSE,
    last_login TIMESTAMP,
    date_joined TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Purpose:** Django's built-in User model. No need to extend for Phase 1.

---

## TABLE: core_project

Stores projects owned by users. Each project contains files.

```sql
CREATE TABLE core_project (
    id SERIAL PRIMARY KEY,
    project_name VARCHAR(255) NOT NULL,
    description TEXT,
    owner_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (owner_id) REFERENCES auth_user(id) ON DELETE CASCADE
);
```

**Columns:**
- `id` — Unique project identifier
- `project_name` — Project name (e.g., "VFX Shots - Q3 2026")
- `description` — Optional description
- `owner_id` — User who owns the project (FK to auth_user)
- `created_at`, `updated_at` — Timestamps

**Indexes:** `CREATE INDEX ON core_project(owner_id);`

---

## TABLE: core_file

Stores file metadata from S3 Inventory. Each file belongs to a project.

```sql
CREATE TABLE core_file (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL,
    s3_key VARCHAR(1024) NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    file_size BIGINT NOT NULL,
    storage_class VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_modified TIMESTAMP,
    is_duplicate BOOLEAN DEFAULT FALSE,
    is_stale BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (project_id) REFERENCES core_project(id) ON DELETE CASCADE
);
```

**Columns:**
- `id` — Unique file identifier
- `project_id` — Project this file belongs to (FK)
- `s3_key` — Full S3 object key (path)
- `file_name` — Human-readable file name
- `file_size` — Size in bytes
- `storage_class` — S3 storage class (STANDARD, GLACIER, etc.)
- `created_at` — When record was created
- `last_modified` — Last S3 modification date
- `is_duplicate` — Flag set by analysis engine
- `is_stale` — Flag set by analysis engine (no access > 90 days)

**Indexes:** 
```sql
CREATE INDEX ON core_file(project_id);
CREATE INDEX ON core_file(is_duplicate);
CREATE INDEX ON core_file(is_stale);
```

---

## TABLE: core_role

Defines available roles in the system (Admin, Editor, Viewer).

```sql
CREATE TABLE core_role (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    description TEXT
);
```

**Pre-populated data:**
```sql
INSERT INTO core_role (name, description) VALUES
('Admin', 'Full access to projects and permissions'),
('Editor', 'Can edit projects and upload files'),
('Viewer', 'Read-only access to projects and files');
```

---

## TABLE: core_permission

Maps users to projects with specific roles (role-based access control).

```sql
CREATE TABLE core_permission (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    project_id INTEGER NOT NULL,
    role_id INTEGER NOT NULL,
    granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    granted_by_id INTEGER,
    FOREIGN KEY (user_id) REFERENCES auth_user(id) ON DELETE CASCADE,
    FOREIGN KEY (project_id) REFERENCES core_project(id) ON DELETE CASCADE,
    FOREIGN KEY (role_id) REFERENCES core_role(id),
    FOREIGN KEY (granted_by_id) REFERENCES auth_user(id) ON DELETE SET NULL,
    UNIQUE(user_id, project_id)
);
```

**Columns:**
- `id` — Unique permission record
- `user_id` — User being granted access (FK)
- `project_id` — Project they access (FK)
- `role_id` — Role they have (Admin/Editor/Viewer) (FK)
- `granted_at` — When permission was granted
- `granted_by_id` — Admin who granted it (FK to auth_user, nullable)
- `UNIQUE(user_id, project_id)` — One role per user per project

**Indexes:**
```sql
CREATE INDEX ON core_permission(user_id);
CREATE INDEX ON core_permission(project_id);
CREATE INDEX ON core_permission(role_id);
```

---

## TABLE: core_costlog

Tracks storage costs per project over time.

```sql
CREATE TABLE core_costlog (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL,
    total_size_bytes BIGINT NOT NULL,
    monthly_cost DECIMAL(10, 2),
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES core_project(id) ON DELETE CASCADE
);
```

**Columns:**
- `id` — Unique log entry
- `project_id` — Project measured (FK)
- `total_size_bytes` — Total storage in bytes
- `monthly_cost` — Estimated monthly cost (optional for Phase 1)
- `recorded_at` — When measurement was taken

**Index:** `CREATE INDEX ON core_costlog(project_id);`

---

## TABLE: core_auditlog

Tracks all permission changes and important actions (audit trail).

```sql
CREATE TABLE core_auditlog (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50) NOT NULL,
    resource_id INTEGER,
    details JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES auth_user(id) ON DELETE SET NULL
);
```

**Columns:**
- `id` — Unique audit entry
- `user_id` — User who performed action (nullable for system actions)
- `action` — Action type (e.g., "permission_granted", "file_deleted", "login")
- `resource_type` — What was affected (e.g., "project", "permission", "file")
- `resource_id` — ID of affected resource
- `details` — JSON blob for extra context
- `created_at` — When action occurred

**Index:** `CREATE INDEX ON core_auditlog(user_id); CREATE INDEX ON core_auditlog(created_at);`

---

## TABLE: core_recommendation

Stores AI-generated recommendations (Phase 4, optional).

```sql
CREATE TABLE core_recommendation (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL,
    recommendation_type VARCHAR(50) NOT NULL,
    description TEXT NOT NULL,
    potential_savings DECIMAL(10, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES core_project(id) ON DELETE CASCADE
);