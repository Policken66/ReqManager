from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QWidget, QFrame
)
from PyQt6.QtCore import Qt
from db import database as db
from logic.auth import current_user
from ui.styles import STATUS_COLORS

TYPE_ICONS = {
    'status_change': '⇄',
    'mention': '@',
    'review': '✓',
}


class NotificationsPanel(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Уведомления")
        self.setMinimumSize(460, 500)
        self.setModal(True)
        self._build_ui()
        self._load()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(16, 16, 16, 16)

        header = QHBoxLayout()
        lbl = QLabel("Уведомления")
        lbl.setStyleSheet("font-size: 16px; font-weight: 700; color: #2B6CB0;")
        btn_read_all = QPushButton("Прочитать все")
        btn_read_all.setObjectName("btn_secondary")
        btn_read_all.clicked.connect(self._mark_all_read)
        header.addWidget(lbl)
        header.addStretch()
        header.addWidget(btn_read_all)
        layout.addLayout(header)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.content = QWidget()
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.content_layout.setSpacing(6)
        self.scroll.setWidget(self.content)
        layout.addWidget(self.scroll)

        btn_close = QPushButton("Закрыть")
        btn_close.setObjectName("btn_secondary")
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close)

    def _load(self):
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        user = current_user()
        notifications = db.get_notifications(user['id'])

        if not notifications:
            lbl = QLabel("Уведомлений нет")
            lbl.setStyleSheet("color: #A0AEC0; font-style: italic; padding: 30px;")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.content_layout.addWidget(lbl)
            return

        for n in notifications:
            self.content_layout.addWidget(self._make_notif(n))

    def _make_notif(self, n):
        frame = QFrame()
        frame.setObjectName("card")
        bg = "#EBF8FF" if not n['is_read'] else "white"
        frame.setStyleSheet(f"QFrame#card {{ background: {bg}; }}")
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(12)

        icon = QLabel(TYPE_ICONS.get(n['type'], '•'))
        icon.setStyleSheet("font-size: 18px; color: #3B82F6; min-width: 24px;")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon)

        info = QVBoxLayout()
        info.setSpacing(2)
        msg = QLabel(n['message'])
        msg.setWordWrap(True)
        msg.setStyleSheet("color: #2D3748;" + (" font-weight: 600;" if not n['is_read'] else ""))

        req_info = ""
        if n['display_id']:
            req_info = f"Требование #{n['display_id']}"
        date = str(n['created_at'])[:16]
        meta = QLabel(f"{req_info}  {date}".strip())
        meta.setStyleSheet("color: #A0AEC0; font-size: 11px;")

        info.addWidget(msg)
        info.addWidget(meta)
        layout.addLayout(info, 1)

        if not n['is_read']:
            dot = QLabel("●")
            dot.setStyleSheet("color: #3B82F6; font-size: 10px;")
            layout.addWidget(dot)

        return frame

    def _mark_all_read(self):
        user = current_user()
        db.mark_notifications_read(user['id'])
        self._load()
