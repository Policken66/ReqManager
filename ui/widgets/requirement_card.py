from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit,
    QPushButton, QFrame, QTabWidget, QWidget, QScrollArea,
    QComboBox, QMessageBox, QSizePolicy, QProgressBar
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from db import database as db
from logic.auth import current_user, can_edit, get_allowed_transitions, STATUS_ORDER
from ui.styles import STATUS_COLORS, PRIORITY_COLORS
from ui.dialogs.requirement_dialog import RequirementDialog

_BTN_SUCCESS = (
    "QPushButton { background-color: #48BB78; color: #ffffff; border: none; "
    "padding: 7px 16px; border-radius: 6px; font-weight: 500; font-size: 13px; }"
    "QPushButton:hover { background-color: #38A169; }"
)
_BTN_DANGER = (
    "QPushButton { background-color: #FC8181; color: #ffffff; border: none; "
    "padding: 7px 16px; border-radius: 6px; font-weight: 500; font-size: 13px; }"
    "QPushButton:hover { background-color: #F56565; }"
)
_BTN_SECONDARY = (
    "QPushButton { background-color: #EDF2F7; color: #4A5568; "
    "border: 1px solid #CBD5E0; padding: 7px 16px; border-radius: 6px; font-weight: 500; font-size: 13px; }"
    "QPushButton:hover { background-color: #E2E8F0; }"
)


class RequirementCard(QDialog):
    requirement_changed = pyqtSignal()

    def __init__(self, parent=None, req_id=None):
        super().__init__(parent)
        self.req_id = req_id
        self.setWindowTitle("Карточка требования")
        self.setMinimumSize(700, 580)
        self.setModal(True)
        self._build_ui()
        self._load()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        self.header = QFrame()
        self.header.setStyleSheet("background: #2B6CB0; border-radius: 0;")
        hdr_layout = QVBoxLayout(self.header)
        hdr_layout.setContentsMargins(24, 16, 24, 16)

        top_row = QHBoxLayout()
        self.lbl_did = QLabel()
        self.lbl_did.setStyleSheet("color: #BEE3F8; font-size: 12px; font-weight: 600;")
        self.lbl_status = QLabel()
        self.lbl_status.setStyleSheet(
            "background: rgba(255,255,255,0.2); color: white; "
            "padding: 3px 10px; border-radius: 12px; font-size: 12px; font-weight: 600;"
        )
        top_row.addWidget(self.lbl_did)
        top_row.addStretch()
        top_row.addWidget(self.lbl_status)
        hdr_layout.addLayout(top_row)

        self.lbl_title = QLabel()
        self.lbl_title.setFont(QFont("Segoe UI", 15, QFont.Weight.Bold))
        self.lbl_title.setStyleSheet("color: white;")
        self.lbl_title.setWordWrap(True)
        hdr_layout.addWidget(self.lbl_title)

        meta_row = QHBoxLayout()
        self.lbl_type = QLabel()
        self.lbl_type.setStyleSheet("color: #BEE3F8; font-size: 12px;")
        self.lbl_priority = QLabel()
        self.lbl_priority.setStyleSheet("color: #BEE3F8; font-size: 12px;")
        self.lbl_author = QLabel()
        self.lbl_author.setStyleSheet("color: #BEE3F8; font-size: 12px;")
        for w in [self.lbl_type, QLabel("·"), self.lbl_priority, QLabel("·"), self.lbl_author]:
            w.setStyleSheet(w.styleSheet() + " color: #BEE3F8; font-size: 12px;")
            meta_row.addWidget(w)
        meta_row.addStretch()
        hdr_layout.addLayout(meta_row)

        layout.addWidget(self.header)

        # Body
        body = QWidget()
        body.setObjectName("req_card_body")
        body.setStyleSheet("#req_card_body { background: #F5F6FA; }")
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(20, 12, 20, 12)
        body_layout.setSpacing(10)

        # Action buttons
        self.actions_row = QHBoxLayout()
        body_layout.addLayout(self.actions_row)

        # Tabs
        self.tabs = QTabWidget()
        body_layout.addWidget(self.tabs)

        # Tab: Details
        details_tab = QScrollArea()
        details_tab.setWidgetResizable(True)
        details_content = QWidget()
        self.details_layout = QVBoxLayout(details_content)
        self.details_layout.setSpacing(12)
        details_tab.setWidget(details_content)
        self.tabs.addTab(details_tab, "Описание")

        # Tab: Sub-requirements
        self.sub_tab = QWidget()
        self.sub_layout = QVBoxLayout(self.sub_tab)
        self.tabs.addTab(self.sub_tab, "Подтребования")

        # Tab: Comments
        self.comments_tab = QWidget()
        comments_layout = QVBoxLayout(self.comments_tab)

        self.comments_scroll = QScrollArea()
        self.comments_scroll.setWidgetResizable(True)
        self.comments_content = QWidget()
        self.comments_content_layout = QVBoxLayout(self.comments_content)
        self.comments_content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.comments_scroll.setWidget(self.comments_content)
        comments_layout.addWidget(self.comments_scroll)

        comment_input_row = QHBoxLayout()
        self.te_comment = QTextEdit()
        self.te_comment.setPlaceholderText("Добавить комментарий... (используйте @имя для упоминания)")
        self.te_comment.setMaximumHeight(70)
        btn_comment = QPushButton("Отправить")
        btn_comment.clicked.connect(self._add_comment)
        btn_comment.setFixedWidth(100)
        comment_input_row.addWidget(self.te_comment)
        comment_input_row.addWidget(btn_comment, alignment=Qt.AlignmentFlag.AlignBottom)
        comments_layout.addLayout(comment_input_row)
        self.tabs.addTab(self.comments_tab, "Комментарии")

        # Tab: History
        self.history_tab = QScrollArea()
        self.history_tab.setWidgetResizable(True)
        self.history_content = QWidget()
        self.history_layout = QVBoxLayout(self.history_content)
        self.history_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.history_tab.setWidget(self.history_content)
        self.tabs.addTab(self.history_tab, "История")

        layout.addWidget(body)

    def _load(self):
        req = db.get_requirement(self.req_id)
        if not req:
            return

        user = current_user()
        self.lbl_did.setText(f"#{req['display_id']}")
        self.lbl_title.setText(req['title'])
        self.lbl_status.setText(req['status'].upper())
        self.lbl_type.setText(f"Тип: {req['type']}")
        self.lbl_priority.setText(f"Приоритет: {req['priority']}")
        author = db.get_user_by_id(req['author_id'])
        self.lbl_author.setText(f"Автор: {author['full_name'] if author else '—'}")

        # Action buttons — полностью очищаем layout через takeAt
        while self.actions_row.count():
            item = self.actions_row.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        edit_ok = can_edit(req['project_id'])
        allowed = get_allowed_transitions(req['status'])

        if edit_ok:
            btn_edit = QPushButton("Редактировать")
            btn_edit.setStyleSheet(_BTN_SECONDARY)
            btn_edit.clicked.connect(self._edit)
            self.actions_row.addWidget(btn_edit)

        if edit_ok and allowed:
            cur_idx = STATUS_ORDER.index(req['status']) if req['status'] in STATUS_ORDER else -1
            # Sort: backward (red) first, forward (green) second
            sorted_transitions = sorted(
                allowed,
                key=lambda s: STATUS_ORDER.index(s) if s in STATUS_ORDER else cur_idx,
            )
            for new_status in sorted_transitions:
                new_idx = STATUS_ORDER.index(new_status) if new_status in STATUS_ORDER else cur_idx
                is_forward = new_idx > cur_idx
                label = f"→ {new_status.capitalize()}" if is_forward else f"← {new_status.capitalize()}"
                btn = QPushButton(label)
                btn.setStyleSheet(_BTN_SUCCESS if is_forward else _BTN_DANGER)
                btn.clicked.connect(lambda _, s=new_status: self._change_status(s))
                self.actions_row.addWidget(btn)

        if edit_ok and req['status'] == 'черновик':
            btn_sub = QPushButton("+ Подтребование")
            btn_sub.setStyleSheet(_BTN_SECONDARY)
            btn_sub.clicked.connect(self._add_sub)
            self.actions_row.addWidget(btn_sub)

        self.actions_row.addStretch()

        if edit_ok:
            btn_del = QPushButton("Удалить")
            btn_del.setStyleSheet(_BTN_DANGER)
            btn_del.clicked.connect(self._delete)
            self.actions_row.addWidget(btn_del)

        # Details tab
        _clear_layout(self.details_layout)

        desc_lbl = QLabel(req['description'] or "Описание не указано")
        desc_lbl.setWordWrap(True)
        desc_lbl.setStyleSheet("color: #4A5568; background: white; padding: 12px; border-radius: 8px;")
        self.details_layout.addWidget(desc_lbl)

        meta_frame = QFrame()
        meta_frame.setObjectName("card")
        meta_frame_layout = QVBoxLayout(meta_frame)
        meta_items = [
            ("Источник", req['source'] or "—"),
            ("Создано", str(req['created_at'])[:16]),
            ("Обновлено", str(req['updated_at'])[:16]),
        ]
        for key, val in meta_items:
            row = QHBoxLayout()
            k = QLabel(key + ":")
            k.setStyleSheet("font-weight: 600; color: #718096; min-width: 100px;")
            v = QLabel(val)
            v.setStyleSheet("color: #2D3748;")
            row.addWidget(k)
            row.addWidget(v)
            row.addStretch()
            meta_frame_layout.addLayout(row)
        self.details_layout.addWidget(meta_frame)
        self.details_layout.addStretch()

        # Sub-requirements tab
        _clear_layout(self.sub_layout)
        subs = db.get_sub_requirements(self.req_id)
        if subs:
            done, total, pct = db.get_requirement_progress(self.req_id)
            pb = QProgressBar()
            pb.setValue(pct)
            pb.setFormat(f"Прогресс: {done}/{total} ({pct}%)")
            pb.setFixedHeight(22)
            self.sub_layout.addWidget(pb)

            for sub in subs:
                self.sub_layout.addWidget(self._make_sub_card(sub))
        else:
            lbl = QLabel("Подтребований нет")
            lbl.setStyleSheet("color: #A0AEC0; font-style: italic; padding: 20px;")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.sub_layout.addWidget(lbl)

        if edit_ok and not req['parent_id']:
            btn_add_sub = QPushButton("+ Добавить подтребование")
            btn_add_sub.setObjectName("btn_secondary")
            btn_add_sub.clicked.connect(self._add_sub)
            self.sub_layout.addWidget(btn_add_sub)
        self.sub_layout.addStretch()

        # Comments tab
        _clear_layout(self.comments_content_layout)
        comments = db.get_comments(self.req_id)
        for c in comments:
            self.comments_content_layout.addWidget(self._make_comment_widget(c))
        if not comments:
            lbl = QLabel("Комментариев нет")
            lbl.setStyleSheet("color: #A0AEC0; font-style: italic; padding: 20px;")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.comments_content_layout.addWidget(lbl)

        # History tab
        _clear_layout(self.history_layout)
        history = db.get_requirement_history(self.req_id)
        for h in history:
            self.history_layout.addWidget(self._make_history_widget(h))
        if not history:
            lbl = QLabel("История изменений пуста")
            lbl.setStyleSheet("color: #A0AEC0; font-style: italic; padding: 20px;")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.history_layout.addWidget(lbl)
        self.history_layout.addStretch()

    def _make_sub_card(self, req):
        frame = QFrame()
        frame.setObjectName("card")
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(12, 8, 12, 8)

        did = QLabel(f"#{req['display_id']}")
        did.setStyleSheet("color: #718096; font-size: 11px; min-width: 60px;")
        title = QLabel(req['title'])
        title.setStyleSheet("font-weight: 600;")
        title.setWordWrap(True)
        status = QLabel(req['status'])
        color = STATUS_COLORS.get(req['status'], '#718096')
        status.setStyleSheet(f"color: {color}; font-size: 12px; font-weight: 600; min-width: 110px;")
        status.setAlignment(Qt.AlignmentFlag.AlignRight)

        btn_open = QPushButton("Открыть")
        btn_open.setObjectName("btn_secondary")
        btn_open.setFixedWidth(80)
        req_id = req['id']
        btn_open.clicked.connect(lambda: self._open_sub(req_id))

        layout.addWidget(did)
        layout.addWidget(title, 1)
        layout.addWidget(status)
        layout.addWidget(btn_open)
        return frame

    def _make_comment_widget(self, comment):
        frame = QFrame()
        frame.setObjectName("card")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(4)

        header = QHBoxLayout()
        author_lbl = QLabel(comment['full_name'] or "Аноним")
        author_lbl.setStyleSheet("font-weight: 600; color: #2B6CB0;")
        date_lbl = QLabel(str(comment['created_at'])[:16])
        date_lbl.setStyleSheet("color: #A0AEC0; font-size: 11px;")
        header.addWidget(author_lbl)
        header.addStretch()
        header.addWidget(date_lbl)
        layout.addLayout(header)

        content = QLabel(comment['content'])
        content.setWordWrap(True)
        content.setStyleSheet("color: #4A5568;")
        layout.addWidget(content)
        return frame

    def _make_history_widget(self, h):
        frame = QFrame()
        frame.setObjectName("card")
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(12, 6, 12, 6)
        layout.setSpacing(8)

        date = QLabel(str(h['created_at'])[:16])
        date.setStyleSheet("color: #A0AEC0; font-size: 11px; min-width: 110px;")
        author = QLabel(h['full_name'] or "")
        author.setStyleSheet("color: #2B6CB0; font-weight: 600; min-width: 140px;")
        action = h['action'] or ''
        field = h['field_name'] or ''
        old_v = h['old_value'] or ''
        new_v = h['new_value'] or ''

        if field:
            desc = f"{action}: {field}: «{old_v}» → «{new_v}»"
        else:
            desc = action
        if h['comment']:
            desc += f" — {h['comment']}"

        desc_lbl = QLabel(desc)
        desc_lbl.setWordWrap(True)
        desc_lbl.setStyleSheet("color: #4A5568;")

        layout.addWidget(date)
        layout.addWidget(author)
        layout.addWidget(desc_lbl, 1)
        return frame

    def _edit(self):
        req = db.get_requirement(self.req_id)
        dlg = RequirementDialog(self, project_id=req['project_id'], req_id=self.req_id)
        if dlg.exec():
            self._load()
            self.requirement_changed.emit()

    def _add_sub(self):
        req = db.get_requirement(self.req_id)
        dlg = RequirementDialog(self, project_id=req['project_id'], parent_req_id=self.req_id)
        if dlg.exec():
            self._load()
            self.requirement_changed.emit()

    def _open_sub(self, req_id):
        dlg = RequirementCard(self, req_id=req_id)
        dlg.requirement_changed.connect(self._load)
        dlg.exec()
        self.requirement_changed.emit()

    def _change_status(self, new_status):
        req = db.get_requirement(self.req_id)
        user = current_user()

        # Check sub-requirements for "реализовано"
        if new_status == 'реализовано':
            subs = db.get_sub_requirements(self.req_id)
            if subs:
                not_done = [s for s in subs if s['status'] not in ('реализовано', 'проверено')]
                if not_done:
                    QMessageBox.warning(
                        self, "Не все требования реализованы",
                        f"Нельзя отметить как реализованное — есть нереализованные подтребования ({len(not_done)} шт.)"
                    )
                    return

        db.change_requirement_status(self.req_id, new_status, user['id'])
        self._load()
        self.requirement_changed.emit()

    def _delete(self):
        req = db.get_requirement(self.req_id)
        subs = db.get_sub_requirements(self.req_id)
        msg = f"Удалить требование «{req['title']}»?"
        if subs:
            msg += f"\n\nВнимание: также будут удалены {len(subs)} подтребований."
        reply = QMessageBox.question(self, "Подтверждение удаления", msg)
        if reply == QMessageBox.StandardButton.Yes:
            db.delete_requirement(self.req_id, current_user()['id'])
            self.requirement_changed.emit()
            self.accept()

    def _add_comment(self):
        content = self.te_comment.toPlainText().strip()
        if not content:
            return
        user = current_user()
        db.add_comment(self.req_id, user['id'], content)
        self.te_comment.clear()
        self._load()
        self.tabs.setCurrentIndex(2)


def _clear_layout(layout):
    while layout.count():
        item = layout.takeAt(0)
        if item.widget():
            item.widget().deleteLater()
