from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit,
    QPushButton, QMessageBox, QFrame
)
from PyQt6.QtCore import Qt
from db import database as db
from logic.auth import current_user, can_review, is_valid_status_transition


class ReviewDialog(QDialog):
    def __init__(self, parent=None, req_id=None):
        super().__init__(parent)
        self.req_id = req_id
        self.setWindowTitle("Рецензирование требования")
        self.setMinimumWidth(480)
        self.setModal(True)
        self._build_ui()

    def _build_ui(self):
        req = db.get_requirement(self.req_id)
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(24, 24, 24, 24)

        lbl = QLabel("Рецензирование требования")
        lbl.setStyleSheet("font-size: 16px; font-weight: 700; color: #2B6CB0;")
        layout.addWidget(lbl)

        info = QFrame()
        info.setObjectName("card")
        info_layout = QVBoxLayout(info)
        info_layout.setSpacing(4)
        lbl_id = QLabel(f"ID: {req['display_id']}")
        lbl_id.setStyleSheet("font-size: 12px; color: #718096;")
        lbl_title = QLabel(req['title'])
        lbl_title.setStyleSheet("font-weight: 600; font-size: 14px;")
        lbl_title.setWordWrap(True)
        lbl_status = QLabel(f"Текущий статус: {req['status']}")
        lbl_status.setStyleSheet("color: #D69E2E;")
        info_layout.addWidget(lbl_id)
        info_layout.addWidget(lbl_title)
        info_layout.addWidget(lbl_status)
        layout.addWidget(info)

        lbl_comment = QLabel("Комментарий (обязателен при отклонении):")
        lbl_comment.setStyleSheet("font-weight: 600;")
        layout.addWidget(lbl_comment)

        self.te_comment = QTextEdit()
        self.te_comment.setPlaceholderText("Укажите причину или замечания...")
        self.te_comment.setMaximumHeight(100)
        layout.addWidget(self.te_comment)

        btn_row = QHBoxLayout()
        btn_row.addStretch()

        btn_cancel = QPushButton("Отмена")
        btn_cancel.setObjectName("btn_secondary")
        btn_cancel.clicked.connect(self.reject)

        btn_reject = QPushButton("Отклонить (вернуть в черновик)")
        btn_reject.setObjectName("btn_danger")
        btn_reject.clicked.connect(self._reject)

        btn_approve = QPushButton("Утвердить")
        btn_approve.setObjectName("btn_success")
        btn_approve.clicked.connect(self._approve)

        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_reject)
        btn_row.addWidget(btn_approve)
        layout.addLayout(btn_row)

    def _approve(self):
        req = db.get_requirement(self.req_id)
        user = current_user()

        if not can_review(req['project_id'], req['author_id']):
            QMessageBox.warning(self, "Нет доступа",
                                "Вы не можете рецензировать это требование. "
                                "Рецензент не может быть автором и должен иметь роль руководителя или исполнителя.")
            return

        comment = self.te_comment.toPlainText().strip()
        db.change_requirement_status(self.req_id, 'утверждено', user['id'], comment)
        # Log review action
        conn = db.get_connection()
        conn.execute(
            "INSERT INTO requirement_history (requirement_id, user_id, action, comment) VALUES (?, ?, 'утверждено', ?)",
            (self.req_id, user['id'], comment)
        )
        conn.commit()
        conn.close()
        self.accept()

    def _reject(self):
        req = db.get_requirement(self.req_id)
        user = current_user()

        if not can_review(req['project_id'], req['author_id']):
            QMessageBox.warning(self, "Нет доступа",
                                "Вы не можете рецензировать это требование.")
            return

        comment = self.te_comment.toPlainText().strip()
        if not comment:
            QMessageBox.warning(self, "Комментарий обязателен",
                                "При отклонении требования необходимо указать комментарий.")
            return

        db.change_requirement_status(self.req_id, 'черновик', user['id'], comment)
        conn = db.get_connection()
        conn.execute(
            "INSERT INTO requirement_history (requirement_id, user_id, action, comment) VALUES (?, ?, 'отклонено', ?)",
            (self.req_id, user['id'], comment)
        )
        conn.commit()
        conn.close()
        self.accept()
