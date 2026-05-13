"""
Скрипт заполнения БД тестовыми данными.
Создаёт 3 пользователей, 2 проекта и 15+ требований.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from db.database import init_db, get_connection
from logic.auth import hash_password


def seed():
    init_db()
    conn = get_connection()

    # ── Users ──────────────────────────────────────────────────────────────
    users = [
        ("admin@reqmanager.ru", hash_password("admin123"), "Комлев Артём Александрович"),
        ("ivanova@reqmanager.ru", hash_password("pass123"), "Иванова Мария Петровна"),
        ("petrov@reqmanager.ru", hash_password("pass123"), "Петров Иван Сергеевич"),
        ("sidorova@reqmanager.ru", hash_password("pass123"), "Сидорова Анна Владимировна"),
    ]
    user_ids = []
    for email, ph, name in users:
        existing = conn.execute("SELECT id FROM users WHERE email=?", (email,)).fetchone()
        if existing:
            user_ids.append(existing['id'])
        else:
            cur = conn.execute(
                "INSERT INTO users (email, password_hash, full_name) VALUES (?, ?, ?)",
                (email, ph, name)
            )
            user_ids.append(cur.lastrowid)
    conn.commit()

    u_admin, u_ivanova, u_petrov, u_sidorova = user_ids

    # ── Project 1: Интернет-магазин ────────────────────────────────────────
    existing_p1 = conn.execute("SELECT id FROM projects WHERE name='Интернет-магазин'").fetchone()
    if existing_p1:
        p1 = existing_p1['id']
    else:
        cur = conn.execute(
            "INSERT INTO projects (name, description, status, start_date, end_date, created_by) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            ("Интернет-магазин", "Разработка платформы электронной коммерции",
             "активный", "2026-01-15", "2026-07-31", u_admin)
        )
        p1 = cur.lastrowid
        conn.execute(
            "INSERT OR IGNORE INTO project_members (project_id, user_id, role) VALUES (?, ?, ?)",
            (p1, u_admin, 'руководитель')
        )
        conn.commit()

    # Members for p1
    for uid, role in [(u_ivanova, 'исполнитель'), (u_petrov, 'исполнитель'), (u_sidorova, 'наблюдатель')]:
        conn.execute(
            "INSERT OR IGNORE INTO project_members (project_id, user_id, role) VALUES (?, ?, ?)",
            (p1, uid, role)
        )
    conn.commit()

    # ── Project 2: Мобильное приложение ────────────────────────────────────
    existing_p2 = conn.execute("SELECT id FROM projects WHERE name='Мобильное приложение'").fetchone()
    if existing_p2:
        p2 = existing_p2['id']
    else:
        cur = conn.execute(
            "INSERT INTO projects (name, description, status, start_date, end_date, created_by) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            ("Мобильное приложение", "Мобильное приложение для iOS и Android",
             "активный", "2026-02-01", "2026-09-30", u_ivanova)
        )
        p2 = cur.lastrowid
        conn.execute(
            "INSERT OR IGNORE INTO project_members (project_id, user_id, role) VALUES (?, ?, ?)",
            (p2, u_ivanova, 'руководитель')
        )
        conn.commit()

    for uid, role in [(u_admin, 'исполнитель'), (u_petrov, 'исполнитель')]:
        conn.execute(
            "INSERT OR IGNORE INTO project_members (project_id, user_id, role) VALUES (?, ?, ?)",
            (p2, uid, role)
        )
    conn.commit()

    # Helper to add requirement if not exists
    def add_req(project_id, parent_id, title, description, req_type, priority, status, source, author_id):
        existing = conn.execute(
            "SELECT id FROM requirements WHERE project_id=? AND title=?",
            (project_id, title)
        ).fetchone()
        if existing:
            return existing['id']

        # Generate display_id
        if parent_id is None:
            row = conn.execute(
                "SELECT MAX(CAST(display_id AS INTEGER)) FROM requirements "
                "WHERE project_id=? AND parent_id IS NULL",
                (project_id,)
            ).fetchone()
            display_id = str((row[0] or 0) + 1)
        else:
            parent = conn.execute("SELECT display_id FROM requirements WHERE id=?", (parent_id,)).fetchone()
            pdid = parent['display_id']
            rows = conn.execute("SELECT display_id FROM requirements WHERE parent_id=?", (parent_id,)).fetchall()
            max_sub = 0
            for r in rows:
                parts = r['display_id'].split('.')
                if len(parts) >= 2:
                    try:
                        max_sub = max(max_sub, int(parts[-1]))
                    except ValueError:
                        pass
            display_id = f"{pdid}.{max_sub + 1}"

        cur = conn.execute(
            "INSERT INTO requirements "
            "(project_id, display_id, parent_id, title, description, type, priority, status, source, author_id) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (project_id, display_id, parent_id, title, description, req_type, priority, status, source, author_id)
        )
        req_id = cur.lastrowid
        conn.execute(
            "INSERT INTO requirement_history (requirement_id, user_id, action, new_value) VALUES (?, ?, 'создано', ?)",
            (req_id, author_id, title)
        )
        conn.execute(
            "INSERT INTO activity_log (project_id, user_id, action_type, entity_type, entity_id, description) "
            "VALUES (?, ?, 'создано', 'requirement', ?, ?)",
            (project_id, author_id, req_id, f"Создано требование {display_id}: {title}")
        )
        conn.commit()
        return req_id

    # ── Requirements for Project 1: Интернет-магазин ───────────────────────

    # Root requirements
    r1 = add_req(p1, None, "Авторизация и регистрация пользователей",
                 "Пользователь должен иметь возможность зарегистрироваться и войти в систему",
                 'бизнес', 'высокий', 'утверждено', 'заказчик', u_admin)

    r2 = add_req(p1, None, "Каталог товаров",
                 "Система должна отображать каталог товаров с фильтрацией и поиском",
                 'функциональное', 'высокий', 'реализовано', 'заказчик', u_ivanova)

    r3 = add_req(p1, None, "Корзина и оформление заказа",
                 "Пользователь должен иметь возможность добавлять товары в корзину и оформлять заказ",
                 'функциональное', 'высокий', 'на рассмотрении', 'заказчик', u_admin)

    r4 = add_req(p1, None, "Система уведомлений",
                 "Отправка email-уведомлений при изменении статуса заказа",
                 'нефункциональное', 'средний', 'черновик', 'команда', u_ivanova)

    r5 = add_req(p1, None, "Производительность системы",
                 "Система должна выдерживать нагрузку 1000 одновременных пользователей",
                 'нефункциональное', 'высокий', 'черновик', 'заказчик', u_admin)

    r6 = add_req(p1, None, "Личный кабинет пользователя",
                 "Пользователь должен иметь доступ к истории заказов и настройкам профиля",
                 'пользовательское', 'средний', 'утверждено', 'заказчик', u_admin)

    r7 = add_req(p1, None, "Платёжная система",
                 "Интеграция с платёжными шлюзами (банковские карты, СБП)",
                 'бизнес', 'высокий', 'проверено', 'заказчик', u_admin)

    # Sub-requirements for r1
    r1_1 = add_req(p1, r1, "Регистрация через email",
                   "Форма регистрации с подтверждением email",
                   'функциональное', 'высокий', 'реализовано', 'заказчик', u_ivanova)

    r1_2 = add_req(p1, r1, "Вход через социальные сети",
                   "OAuth2-авторизация через VK и Google",
                   'функциональное', 'средний', 'утверждено', 'заказчик', u_ivanova)

    # Sub-requirements for r3
    r3_1 = add_req(p1, r3, "Добавление товара в корзину",
                   "Кнопка добавления в корзину на карточке товара",
                   'функциональное', 'высокий', 'реализовано', 'команда', u_admin)

    r3_2 = add_req(p1, r3, "Оформление заказа",
                   "Многошаговая форма оформления заказа с выбором адреса и способа доставки",
                   'функциональное', 'высокий', 'на рассмотрении', 'заказчик', u_admin)

    # ── Requirements for Project 2: Мобильное приложение ──────────────────

    m1 = add_req(p2, None, "Онбординг и обучение",
                 "Экраны приветствия и обучения для новых пользователей",
                 'пользовательское', 'средний', 'утверждено', 'заказчик', u_ivanova)

    m2 = add_req(p2, None, "Push-уведомления",
                 "Настраиваемые push-уведомления для пользователей",
                 'функциональное', 'высокий', 'черновик', 'команда', u_admin)

    m3 = add_req(p2, None, "Офлайн-режим",
                 "Приложение должно работать без интернета с синхронизацией при подключении",
                 'нефункциональное', 'средний', 'черновик', 'заказчик', u_ivanova)

    m4 = add_req(p2, None, "Биометрическая аутентификация",
                 "Вход по отпечатку пальца и Face ID",
                 'функциональное', 'низкий', 'черновик', 'команда', u_admin)

    # Sub-requirements for m1
    m1_1 = add_req(p2, m1, "Экран приветствия",
                   "Анимированный экран с логотипом при запуске приложения",
                   'пользовательское', 'низкий', 'реализовано', 'заказчик', u_ivanova)

    m1_2 = add_req(p2, m1, "Слайдер обучения",
                   "Интерактивный тур по функциям приложения (3-5 экранов)",
                   'пользовательское', 'средний', 'утверждено', 'заказчик', u_ivanova)

    # Add some comments
    existing_comment = conn.execute(
        "SELECT id FROM comments WHERE requirement_id=? LIMIT 1", (r3,)
    ).fetchone()
    if not existing_comment:
        conn.execute(
            "INSERT INTO comments (requirement_id, user_id, content) VALUES (?, ?, ?)",
            (r3, u_ivanova, "Нужно уточнить способы оплаты у заказчика")
        )
        conn.execute(
            "INSERT INTO comments (requirement_id, user_id, content) VALUES (?, ?, ?)",
            (r3, u_admin, "@ivanova уже уточнил — только банковские карты на первом этапе")
        )
        # Add history entries for status changes
        conn.execute(
            "INSERT INTO requirement_history (requirement_id, user_id, action, field_name, old_value, new_value) "
            "VALUES (?, ?, 'статус изменён', 'status', 'черновик', 'на рассмотрении')",
            (r3, u_admin)
        )
        conn.execute(
            "INSERT INTO activity_log (project_id, user_id, action_type, entity_type, entity_id, description) "
            "VALUES (?, ?, 'статус', 'requirement', ?, ?)",
            (p1, u_admin, r3, "Статус требования 3 изменён: черновик → на рассмотрении")
        )
        conn.commit()

    # Notifications
    existing_notif = conn.execute(
        "SELECT id FROM notifications WHERE user_id=? LIMIT 1", (u_admin,)
    ).fetchone()
    if not existing_notif:
        conn.execute(
            "INSERT INTO notifications (user_id, type, requirement_id, message) VALUES (?, ?, ?, ?)",
            (u_admin, 'status_change', r2,
             "Требование 'Каталог товаров' переведено в статус 'реализовано'")
        )
        conn.execute(
            "INSERT INTO notifications (user_id, type, requirement_id, message) VALUES (?, ?, ?, ?)",
            (u_admin, 'mention', r3,
             "Иванова Мария Петровна оставила комментарий к требованию 'Корзина и оформление заказа'")
        )
        conn.commit()

    conn.close()
    print("OK: База данных заполнена тестовыми данными")
    print("  Пользователей: 4")
    print("  Проектов: 2")
    print("  Требований в проекте 1: 11")
    print("  Требований в проекте 2: 6")
    print()
    print("Тестовые аккаунты:")
    print("  admin@reqmanager.ru / admin123  (руководитель)")
    print("  ivanova@reqmanager.ru / pass123 (исполнитель)")
    print("  petrov@reqmanager.ru / pass123  (исполнитель)")
    print("  sidorova@reqmanager.ru / pass123 (наблюдатель)")


if __name__ == '__main__':
    seed()
