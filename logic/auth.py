import hashlib
import re
from db import database as db

# Roles with full access to create/edit requirements
EDITOR_ROLES = {'руководитель', 'исполнитель'}
# Roles that can review (but not own requirements)
REVIEWER_ROLES = {'руководитель', 'исполнитель'}
# All valid roles
ALL_ROLES = ['руководитель', 'исполнитель', 'наблюдатель']

# Status order (for determining forward/backward direction)
STATUS_ORDER = ['черновик', 'на рассмотрении', 'утверждено', 'реализовано', 'проверено']

# Valid status transitions
# Forward (green button): higher index in STATUS_ORDER
# Backward (red button): lower index in STATUS_ORDER
STATUS_TRANSITIONS = {
    'черновик': ['на рассмотрении'],
    'на рассмотрении': ['утверждено', 'черновик'],
    'утверждено': ['реализовано', 'на рассмотрении'],
    'реализовано': ['проверено', 'утверждено'],
    'проверено': ['на рассмотрении'],
}

_session: dict = {}


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode('utf-8')).hexdigest()


def register(email: str, password: str, full_name: str) -> tuple[bool, str]:
    email = email.strip().lower()
    if not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
        return False, "Некорректный формат email"
    if len(password) < 6:
        return False, "Пароль должен содержать не менее 6 символов"
    if not full_name.strip():
        return False, "ФИО не может быть пустым"
    existing = db.get_user_by_email(email)
    if existing:
        return False, "Пользователь с таким email уже существует"
    password_hash = hash_password(password)
    db.create_user(email, password_hash, full_name.strip())
    return True, "Регистрация успешна"


def login(email: str, password: str) -> tuple[bool, str]:
    email = email.strip().lower()
    user = db.get_user_by_email(email)
    if not user:
        return False, "Пользователь не найден"
    if user['password_hash'] != hash_password(password):
        return False, "Неверный пароль"
    _session['user'] = dict(user)
    return True, "Вход выполнен"


def logout():
    _session.clear()


def current_user() -> dict | None:
    return _session.get('user')


def can_edit(project_id: int) -> bool:
    user = current_user()
    if not user:
        return False
    role = db.get_user_role_in_project(project_id, user['id'])
    return role in EDITOR_ROLES


def can_review(project_id: int, requirement_author_id: int) -> bool:
    user = current_user()
    if not user:
        return False
    if user['id'] == requirement_author_id:
        return False
    role = db.get_user_role_in_project(project_id, user['id'])
    return role in REVIEWER_ROLES


def can_view(project_id: int) -> bool:
    user = current_user()
    if not user:
        return False
    role = db.get_user_role_in_project(project_id, user['id'])
    return role is not None


def is_valid_status_transition(current_status: str, new_status: str) -> bool:
    allowed = STATUS_TRANSITIONS.get(current_status, [])
    return new_status in allowed


def get_allowed_transitions(current_status: str) -> list[str]:
    return STATUS_TRANSITIONS.get(current_status, [])
