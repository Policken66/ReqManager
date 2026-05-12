import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).parent.parent / "reqmanager.db"

SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(30) DEFAULT 'активный',
    start_date DATE,
    end_date DATE,
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS project_members (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    role VARCHAR(30) NOT NULL,
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(project_id, user_id)
);

CREATE TABLE IF NOT EXISTS requirements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
    display_id VARCHAR(30),
    parent_id INTEGER REFERENCES requirements(id) ON DELETE SET NULL,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    type VARCHAR(30) DEFAULT 'функциональное',
    priority VARCHAR(30) DEFAULT 'средний',
    status VARCHAR(30) DEFAULT 'черновик',
    source VARCHAR(30),
    author_id INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS requirement_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    requirement_id INTEGER REFERENCES requirements(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id),
    action VARCHAR(50),
    field_name VARCHAR(50),
    old_value TEXT,
    new_value TEXT,
    comment TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    requirement_id INTEGER REFERENCES requirements(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id),
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS comment_mentions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    comment_id INTEGER REFERENCES comments(id) ON DELETE CASCADE,
    mentioned_user_id INTEGER REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER REFERENCES users(id),
    type VARCHAR(30),
    requirement_id INTEGER REFERENCES requirements(id) ON DELETE SET NULL,
    message VARCHAR(500),
    is_read BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS activity_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id),
    action_type VARCHAR(30),
    entity_type VARCHAR(30),
    entity_id INTEGER,
    description VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""


def get_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def init_db():
    conn = get_connection()
    conn.executescript(SCHEMA)
    conn.commit()
    conn.close()


# ─── Users ───────────────────────────────────────────────────────────────────

def create_user(email: str, password_hash: str, full_name: str) -> int:
    conn = get_connection()
    try:
        cur = conn.execute(
            "INSERT INTO users (email, password_hash, full_name) VALUES (?, ?, ?)",
            (email, password_hash, full_name)
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def get_user_by_email(email: str):
    conn = get_connection()
    try:
        return conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    finally:
        conn.close()


def get_user_by_id(user_id: int):
    conn = get_connection()
    try:
        return conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    finally:
        conn.close()


def get_all_users():
    conn = get_connection()
    try:
        return conn.execute("SELECT id, email, full_name FROM users ORDER BY full_name").fetchall()
    finally:
        conn.close()


# ─── Projects ────────────────────────────────────────────────────────────────

def create_project(name, description, status, start_date, end_date, created_by) -> int:
    conn = get_connection()
    try:
        cur = conn.execute(
            "INSERT INTO projects (name, description, status, start_date, end_date, created_by) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (name, description, status, start_date, end_date, created_by)
        )
        project_id = cur.lastrowid
        conn.execute(
            "INSERT INTO project_members (project_id, user_id, role) VALUES (?, ?, ?)",
            (project_id, created_by, 'руководитель')
        )
        conn.commit()
        return project_id
    finally:
        conn.close()


def update_project(project_id, name, description, status, start_date, end_date):
    conn = get_connection()
    try:
        conn.execute(
            "UPDATE projects SET name=?, description=?, status=?, start_date=?, end_date=? WHERE id=?",
            (name, description, status, start_date, end_date, project_id)
        )
        conn.commit()
    finally:
        conn.close()


def get_project(project_id: int):
    conn = get_connection()
    try:
        return conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
    finally:
        conn.close()


def get_projects_for_user(user_id: int):
    conn = get_connection()
    try:
        return conn.execute(
            "SELECT p.*, pm.role FROM projects p "
            "JOIN project_members pm ON pm.project_id = p.id "
            "WHERE pm.user_id = ? ORDER BY p.created_at DESC",
            (user_id,)
        ).fetchall()
    finally:
        conn.close()


# ─── Project Members ──────────────────────────────────────────────────────────

def add_project_member(project_id, user_id, role):
    conn = get_connection()
    try:
        conn.execute(
            "INSERT OR IGNORE INTO project_members (project_id, user_id, role) VALUES (?, ?, ?)",
            (project_id, user_id, role)
        )
        conn.commit()
    finally:
        conn.close()


def remove_project_member(project_id, user_id):
    conn = get_connection()
    try:
        conn.execute(
            "DELETE FROM project_members WHERE project_id=? AND user_id=?",
            (project_id, user_id)
        )
        conn.commit()
    finally:
        conn.close()


def update_member_role(project_id, user_id, role):
    conn = get_connection()
    try:
        conn.execute(
            "UPDATE project_members SET role=? WHERE project_id=? AND user_id=?",
            (role, project_id, user_id)
        )
        conn.commit()
    finally:
        conn.close()


def get_project_members(project_id: int):
    conn = get_connection()
    try:
        return conn.execute(
            "SELECT u.id, u.email, u.full_name, pm.role, pm.joined_at "
            "FROM project_members pm JOIN users u ON u.id = pm.user_id "
            "WHERE pm.project_id = ? ORDER BY u.full_name",
            (project_id,)
        ).fetchall()
    finally:
        conn.close()


def get_user_role_in_project(project_id: int, user_id: int):
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT role FROM project_members WHERE project_id=? AND user_id=?",
            (project_id, user_id)
        ).fetchone()
        return row['role'] if row else None
    finally:
        conn.close()


# ─── Requirements ─────────────────────────────────────────────────────────────

def _generate_display_id(conn, project_id: int, parent_id) -> str:
    if parent_id is None:
        row = conn.execute(
            "SELECT MAX(CAST(display_id AS INTEGER)) FROM requirements "
            "WHERE project_id=? AND parent_id IS NULL",
            (project_id,)
        ).fetchone()
        max_num = row[0] or 0
        return str(max_num + 1)
    else:
        parent = conn.execute(
            "SELECT display_id FROM requirements WHERE id=?", (parent_id,)
        ).fetchone()
        parent_did = parent['display_id']
        rows = conn.execute(
            "SELECT display_id FROM requirements WHERE parent_id=?", (parent_id,)
        ).fetchall()
        max_sub = 0
        for r in rows:
            parts = r['display_id'].split('.')
            if len(parts) >= 2:
                try:
                    max_sub = max(max_sub, int(parts[-1]))
                except ValueError:
                    pass
        return f"{parent_did}.{max_sub + 1}"


def create_requirement(project_id, parent_id, title, description, req_type,
                       priority, status, source, author_id) -> int:
    conn = get_connection()
    try:
        display_id = _generate_display_id(conn, project_id, parent_id)
        cur = conn.execute(
            "INSERT INTO requirements "
            "(project_id, display_id, parent_id, title, description, type, priority, status, source, author_id) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (project_id, display_id, parent_id, title, description,
             req_type, priority, status, source, author_id)
        )
        req_id = cur.lastrowid
        conn.execute(
            "INSERT INTO requirement_history (requirement_id, user_id, action, new_value) "
            "VALUES (?, ?, 'создано', ?)",
            (req_id, author_id, title)
        )
        conn.execute(
            "INSERT INTO activity_log (project_id, user_id, action_type, entity_type, entity_id, description) "
            "VALUES (?, ?, 'создано', 'requirement', ?, ?)",
            (project_id, author_id, req_id, f"Создано требование {display_id}: {title}")
        )
        conn.commit()
        return req_id
    finally:
        conn.close()


def update_requirement(req_id, title, description, req_type, priority,
                       source, user_id, comment=""):
    conn = get_connection()
    try:
        old = conn.execute("SELECT * FROM requirements WHERE id=?", (req_id,)).fetchone()
        fields = {
            'title': (old['title'], title),
            'description': (old['description'], description),
            'type': (old['type'], req_type),
            'priority': (old['priority'], priority),
            'source': (old['source'], source),
        }
        conn.execute(
            "UPDATE requirements SET title=?, description=?, type=?, priority=?, source=?, updated_at=? WHERE id=?",
            (title, description, req_type, priority, source, datetime.now().isoformat(), req_id)
        )
        for field, (old_val, new_val) in fields.items():
            if old_val != new_val:
                conn.execute(
                    "INSERT INTO requirement_history "
                    "(requirement_id, user_id, action, field_name, old_value, new_value, comment) "
                    "VALUES (?, ?, 'изменено', ?, ?, ?, ?)",
                    (req_id, user_id, field, str(old_val), str(new_val), comment)
                )
        conn.execute(
            "INSERT INTO activity_log (project_id, user_id, action_type, entity_type, entity_id, description) "
            "VALUES (?, ?, 'изменено', 'requirement', ?, ?)",
            (old['project_id'], user_id, req_id, f"Изменено требование {old['display_id']}: {title}")
        )
        conn.commit()
    finally:
        conn.close()


def change_requirement_status(req_id, new_status, user_id, comment=""):
    conn = get_connection()
    try:
        req = conn.execute("SELECT * FROM requirements WHERE id=?", (req_id,)).fetchone()
        old_status = req['status']
        conn.execute(
            "UPDATE requirements SET status=?, updated_at=? WHERE id=?",
            (new_status, datetime.now().isoformat(), req_id)
        )
        conn.execute(
            "INSERT INTO requirement_history "
            "(requirement_id, user_id, action, field_name, old_value, new_value, comment) "
            "VALUES (?, ?, 'статус изменён', 'status', ?, ?, ?)",
            (req_id, user_id, old_status, new_status, comment)
        )
        # Notify author if status changed by someone else
        if req['author_id'] != user_id:
            conn.execute(
                "INSERT INTO notifications (user_id, type, requirement_id, message) VALUES (?, ?, ?, ?)",
                (req['author_id'], 'status_change', req_id,
                 f"Статус требования '{req['title']}' изменён с '{old_status}' на '{new_status}'")
            )
        conn.execute(
            "INSERT INTO activity_log (project_id, user_id, action_type, entity_type, entity_id, description) "
            "VALUES (?, ?, 'статус', 'requirement', ?, ?)",
            (req['project_id'], user_id, req_id,
             f"Статус требования {req['display_id']} изменён: {old_status} → {new_status}")
        )
        # Recalculate parent progress if this is a sub-requirement
        if req['parent_id']:
            _recalculate_progress(conn, req['parent_id'])
        conn.commit()
    finally:
        conn.close()


def _recalculate_progress(conn, parent_id: int):
    rows = conn.execute(
        "SELECT status FROM requirements WHERE parent_id=?", (parent_id,)
    ).fetchall()
    total = len(rows)
    if total == 0:
        return
    done = sum(1 for r in rows if r['status'] in ('реализовано', 'проверено'))
    # Just update updated_at so the parent is flagged; progress is computed on read
    conn.execute(
        "UPDATE requirements SET updated_at=? WHERE id=?",
        (datetime.now().isoformat(), parent_id)
    )


def delete_requirement(req_id, user_id):
    conn = get_connection()
    try:
        req = conn.execute("SELECT * FROM requirements WHERE id=?", (req_id,)).fetchone()
        conn.execute("DELETE FROM requirements WHERE id=?", (req_id,))
        conn.execute(
            "INSERT INTO activity_log (project_id, user_id, action_type, entity_type, entity_id, description) "
            "VALUES (?, ?, 'удалено', 'requirement', ?, ?)",
            (req['project_id'], user_id, req_id,
             f"Удалено требование {req['display_id']}: {req['title']}")
        )
        conn.commit()
    finally:
        conn.close()


def get_requirement(req_id: int):
    conn = get_connection()
    try:
        return conn.execute("SELECT * FROM requirements WHERE id=?", (req_id,)).fetchone()
    finally:
        conn.close()


def get_requirements(project_id: int, filters: dict = None):
    conn = get_connection()
    try:
        query = "SELECT r.*, u.full_name as author_name FROM requirements r LEFT JOIN users u ON u.id = r.author_id WHERE r.project_id=?"
        params = [project_id]
        if filters:
            if filters.get('type'):
                query += " AND r.type=?"
                params.append(filters['type'])
            if filters.get('status'):
                query += " AND r.status=?"
                params.append(filters['status'])
            if filters.get('priority'):
                query += " AND r.priority=?"
                params.append(filters['priority'])
            if filters.get('author_id'):
                query += " AND r.author_id=?"
                params.append(filters['author_id'])
            if filters.get('search'):
                query += " AND (r.title LIKE ? OR r.description LIKE ? OR r.display_id LIKE ?)"
                s = f"%{filters['search']}%"
                params.extend([s, s, s])
        query += " ORDER BY r.updated_at DESC"
        return conn.execute(query, params).fetchall()
    finally:
        conn.close()


def search_requirements_global(user_id: int, search: str, filters: dict = None):
    conn = get_connection()
    try:
        query = (
            "SELECT r.*, u.full_name as author_name, p.name as project_name "
            "FROM requirements r "
            "LEFT JOIN users u ON u.id = r.author_id "
            "JOIN projects p ON p.id = r.project_id "
            "JOIN project_members pm ON pm.project_id = r.project_id "
            "WHERE pm.user_id=? AND (r.title LIKE ? OR r.display_id LIKE ?)"
        )
        s = f"%{search}%"
        params = [user_id, s, s]
        if filters:
            if filters.get('type'):
                query += " AND r.type=?"
                params.append(filters['type'])
            if filters.get('status'):
                query += " AND r.status=?"
                params.append(filters['status'])
            if filters.get('priority'):
                query += " AND r.priority=?"
                params.append(filters['priority'])
        query += " ORDER BY r.updated_at DESC"
        return conn.execute(query, params).fetchall()
    finally:
        conn.close()


def get_sub_requirements(parent_id: int):
    conn = get_connection()
    try:
        return conn.execute(
            "SELECT r.*, u.full_name as author_name FROM requirements r "
            "LEFT JOIN users u ON u.id = r.author_id WHERE r.parent_id=? ORDER BY r.display_id",
            (parent_id,)
        ).fetchall()
    finally:
        conn.close()


def get_requirement_progress(parent_id: int):
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT status FROM requirements WHERE parent_id=?", (parent_id,)
        ).fetchall()
        total = len(rows)
        if total == 0:
            return 0, 0, 0
        done = sum(1 for r in rows if r['status'] in ('реализовано', 'проверено'))
        return done, total, int(done / total * 100)
    finally:
        conn.close()


# ─── Requirement History ──────────────────────────────────────────────────────

def get_requirement_history(req_id: int):
    conn = get_connection()
    try:
        return conn.execute(
            "SELECT rh.*, u.full_name FROM requirement_history rh "
            "LEFT JOIN users u ON u.id = rh.user_id "
            "WHERE rh.requirement_id=? ORDER BY rh.created_at DESC",
            (req_id,)
        ).fetchall()
    finally:
        conn.close()


# ─── Comments ─────────────────────────────────────────────────────────────────

def add_comment(req_id, user_id, content) -> int:
    conn = get_connection()
    try:
        req = conn.execute("SELECT * FROM requirements WHERE id=?", (req_id,)).fetchone()
        cur = conn.execute(
            "INSERT INTO comments (requirement_id, user_id, content) VALUES (?, ?, ?)",
            (req_id, user_id, content)
        )
        comment_id = cur.lastrowid
        # Parse @mentions
        import re
        mentions = re.findall(r'@(\S+)', content)
        if mentions:
            all_users = conn.execute("SELECT id, email, full_name FROM users").fetchall()
            for m in mentions:
                for u in all_users:
                    if m.lower() in u['email'].lower() or m.lower() in u['full_name'].lower().replace(' ', '_'):
                        conn.execute(
                            "INSERT INTO comment_mentions (comment_id, mentioned_user_id) VALUES (?, ?)",
                            (comment_id, u['id'])
                        )
                        if u['id'] != user_id:
                            author = conn.execute("SELECT full_name FROM users WHERE id=?", (user_id,)).fetchone()
                            conn.execute(
                                "INSERT INTO notifications (user_id, type, requirement_id, message) VALUES (?, ?, ?, ?)",
                                (u['id'], 'mention', req_id,
                                 f"{author['full_name']} упомянул вас в комментарии к '{req['title']}'")
                            )
        conn.execute(
            "INSERT INTO activity_log (project_id, user_id, action_type, entity_type, entity_id, description) "
            "VALUES (?, ?, 'комментарий', 'requirement', ?, ?)",
            (req['project_id'], user_id, req_id, f"Комментарий к требованию {req['display_id']}")
        )
        conn.commit()
        return comment_id
    finally:
        conn.close()


def get_comments(req_id: int):
    conn = get_connection()
    try:
        return conn.execute(
            "SELECT c.*, u.full_name FROM comments c "
            "LEFT JOIN users u ON u.id = c.user_id "
            "WHERE c.requirement_id=? ORDER BY c.created_at ASC",
            (req_id,)
        ).fetchall()
    finally:
        conn.close()


# ─── Notifications ────────────────────────────────────────────────────────────

def get_notifications(user_id: int, unread_only=False):
    conn = get_connection()
    try:
        query = "SELECT n.*, r.display_id, r.title as req_title FROM notifications n " \
                "LEFT JOIN requirements r ON r.id = n.requirement_id " \
                "WHERE n.user_id=?"
        params = [user_id]
        if unread_only:
            query += " AND n.is_read=0"
        query += " ORDER BY n.created_at DESC LIMIT 50"
        return conn.execute(query, params).fetchall()
    finally:
        conn.close()


def mark_notifications_read(user_id: int):
    conn = get_connection()
    try:
        conn.execute("UPDATE notifications SET is_read=1 WHERE user_id=?", (user_id,))
        conn.commit()
    finally:
        conn.close()


def count_unread_notifications(user_id: int) -> int:
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT COUNT(*) FROM notifications WHERE user_id=? AND is_read=0", (user_id,)
        ).fetchone()
        return row[0]
    finally:
        conn.close()


# ─── Activity Log ─────────────────────────────────────────────────────────────

def get_activity_log(project_id: int, limit=100):
    conn = get_connection()
    try:
        return conn.execute(
            "SELECT al.*, u.full_name FROM activity_log al "
            "LEFT JOIN users u ON u.id = al.user_id "
            "WHERE al.project_id=? ORDER BY al.created_at DESC LIMIT ?",
            (project_id, limit)
        ).fetchall()
    finally:
        conn.close()


# ─── Reports ──────────────────────────────────────────────────────────────────

def get_project_summary(project_id: int) -> dict:
    conn = get_connection()
    try:
        reqs = conn.execute(
            "SELECT status, type, priority FROM requirements WHERE project_id=?", (project_id,)
        ).fetchall()
        total = len(reqs)
        by_status = {}
        by_type = {}
        by_priority = {}
        for r in reqs:
            by_status[r['status']] = by_status.get(r['status'], 0) + 1
            by_type[r['type']] = by_type.get(r['type'], 0) + 1
            by_priority[r['priority']] = by_priority.get(r['priority'], 0) + 1
        done = by_status.get('реализовано', 0) + by_status.get('проверено', 0)
        return {
            'total': total,
            'done': done,
            'percent': int(done / total * 100) if total else 0,
            'by_status': by_status,
            'by_type': by_type,
            'by_priority': by_priority,
        }
    finally:
        conn.close()


def get_members_summary(project_id: int):
    conn = get_connection()
    try:
        members = conn.execute(
            "SELECT u.id, u.full_name, pm.role FROM project_members pm "
            "JOIN users u ON u.id = pm.user_id WHERE pm.project_id=?",
            (project_id,)
        ).fetchall()
        result = []
        for m in members:
            uid = m['id']
            reqs = conn.execute(
                "SELECT COUNT(*) FROM requirements WHERE project_id=? AND author_id=?",
                (project_id, uid)
            ).fetchone()[0]
            reviewed = conn.execute(
                "SELECT COUNT(*) FROM requirement_history "
                "WHERE user_id=? AND action IN ('утверждено', 'отклонено') "
                "AND requirement_id IN (SELECT id FROM requirements WHERE project_id=?)",
                (uid, project_id)
            ).fetchone()[0]
            comms = conn.execute(
                "SELECT COUNT(*) FROM comments "
                "WHERE user_id=? AND requirement_id IN (SELECT id FROM requirements WHERE project_id=?)",
                (uid, project_id)
            ).fetchone()[0]
            result.append({
                'full_name': m['full_name'],
                'role': m['role'],
                'requirements': reqs,
                'reviewed': reviewed,
                'comments': comms,
            })
        return result
    finally:
        conn.close()
