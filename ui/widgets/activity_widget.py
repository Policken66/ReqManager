from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea,
    QFrame, QPushButton
)
from PyQt6.QtCore import Qt
from db import database as db

ACTION_ICONS = {
    'создано': '✦',
    'изменено': '✎',
    'статус': '⇄',
    'удалено': '✕',
    'комментарий': '💬',
}


class ActivityWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.project_id = None
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(12, 12, 12, 12)

        header = QHBoxLayout()
        lbl = QLabel("Лента активности")
        lbl.setStyleSheet("font-size: 15px; font-weight: 700; color: #2B6CB0;")
        btn_refresh = QPushButton("Обновить")
        btn_refresh.setObjectName("btn_secondary")
        btn_refresh.clicked.connect(self.refresh)
        header.addWidget(lbl)
        header.addStretch()
        header.addWidget(btn_refresh)
        layout.addLayout(header)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.content = QWidget()
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.content_layout.setSpacing(6)
        self.scroll.setWidget(self.content)
        layout.addWidget(self.scroll)

    def set_project(self, project_id: int):
        self.project_id = project_id
        self.refresh()

    def refresh(self):
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not self.project_id:
            lbl = QLabel("Выберите проект для просмотра активности")
            lbl.setStyleSheet("color: #A0AEC0; font-style: italic;")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.content_layout.addWidget(lbl)
            return

        entries = db.get_activity_log(self.project_id)
        if not entries:
            lbl = QLabel("Активности нет")
            lbl.setStyleSheet("color: #A0AEC0; font-style: italic; padding: 30px;")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.content_layout.addWidget(lbl)
            return

        for entry in entries:
            self.content_layout.addWidget(self._make_entry(entry))

    def _make_entry(self, entry):
        frame = QFrame()
        frame.setObjectName("card")
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(12)

        icon_text = ACTION_ICONS.get(entry['action_type'], '•')
        icon = QLabel(icon_text)
        icon.setStyleSheet("font-size: 16px; color: #3B82F6; min-width: 24px;")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon)

        info = QVBoxLayout()
        info.setSpacing(2)

        desc = QLabel(entry['description'] or entry['action_type'])
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #2D3748;")

        meta_row = QHBoxLayout()
        author = QLabel(entry['full_name'] or "Система")
        author.setStyleSheet("color: #2B6CB0; font-weight: 600; font-size: 12px;")
        date = QLabel(str(entry['created_at'])[:16])
        date.setStyleSheet("color: #A0AEC0; font-size: 11px;")
        meta_row.addWidget(author)
        meta_row.addWidget(QLabel("·"))
        meta_row.addWidget(date)
        meta_row.addStretch()

        info.addWidget(desc)
        info.addLayout(meta_row)
        layout.addLayout(info, 1)
        return frame
