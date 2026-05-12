from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel,
    QLineEdit, QTextEdit, QComboBox, QDateEdit, QPushButton,
    QMessageBox, QFrame
)
from PyQt6.QtCore import Qt, QDate
from db import database as db
from logic.auth import current_user

PROJECT_STATUSES = ['активный', 'архивный', 'завершён']


class ProjectDialog(QDialog):
    def __init__(self, parent=None, project_id=None):
        super().__init__(parent)
        self.project_id = project_id
        self.setWindowTitle("Новый проект" if not project_id else "Редактировать проект")
        self.setMinimumWidth(480)
        self.setModal(True)
        self._build_ui()
        if project_id:
            self._load_project()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        title_lbl = QLabel("Новый проект" if not self.project_id else "Редактировать проект")
        title_lbl.setStyleSheet("font-size: 16px; font-weight: 700; color: #2B6CB0;")
        layout.addWidget(title_lbl)

        form = QFormLayout()
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.le_name = QLineEdit()
        self.le_name.setPlaceholderText("Название проекта")
        form.addRow("Название *", self.le_name)

        self.te_desc = QTextEdit()
        self.te_desc.setPlaceholderText("Краткое описание проекта")
        self.te_desc.setMaximumHeight(90)
        form.addRow("Описание", self.te_desc)

        self.cb_status = QComboBox()
        self.cb_status.addItems(PROJECT_STATUSES)
        form.addRow("Статус", self.cb_status)

        self.de_start = QDateEdit()
        self.de_start.setCalendarPopup(True)
        self.de_start.setDate(QDate.currentDate())
        self.de_start.setDisplayFormat("dd.MM.yyyy")
        form.addRow("Дата начала", self.de_start)

        self.de_end = QDateEdit()
        self.de_end.setCalendarPopup(True)
        self.de_end.setDate(QDate.currentDate().addMonths(6))
        self.de_end.setDisplayFormat("dd.MM.yyyy")
        form.addRow("Дата окончания", self.de_end)

        layout.addLayout(form)

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_cancel = QPushButton("Отмена")
        btn_cancel.setObjectName("btn_secondary")
        btn_cancel.clicked.connect(self.reject)
        btn_save = QPushButton("Сохранить")
        btn_save.clicked.connect(self._save)
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_save)
        layout.addLayout(btn_row)

    def _load_project(self):
        p = db.get_project(self.project_id)
        if not p:
            return
        self.le_name.setText(p['name'])
        self.te_desc.setPlainText(p['description'] or '')
        idx = self.cb_status.findText(p['status'])
        if idx >= 0:
            self.cb_status.setCurrentIndex(idx)
        if p['start_date']:
            d = QDate.fromString(str(p['start_date'])[:10], "yyyy-MM-dd")
            self.de_start.setDate(d)
        if p['end_date']:
            d = QDate.fromString(str(p['end_date'])[:10], "yyyy-MM-dd")
            self.de_end.setDate(d)

    def _save(self):
        name = self.le_name.text().strip()
        if not name:
            QMessageBox.warning(self, "Ошибка", "Название проекта не может быть пустым")
            return
        desc = self.te_desc.toPlainText().strip()
        status = self.cb_status.currentText()
        start = self.de_start.date().toString("yyyy-MM-dd")
        end = self.de_end.date().toString("yyyy-MM-dd")

        user = current_user()
        if self.project_id:
            db.update_project(self.project_id, name, desc, status, start, end)
        else:
            self.project_id = db.create_project(name, desc, status, start, end, user['id'])
        self.accept()
