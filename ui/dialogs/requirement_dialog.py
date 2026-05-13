from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel,
    QLineEdit, QTextEdit, QComboBox, QPushButton, QMessageBox
)
from PyQt6.QtCore import Qt
from db import database as db
from logic.auth import current_user

REQ_TYPES = ['бизнес', 'пользовательское', 'функциональное', 'нефункциональное']
REQ_PRIORITIES = ['высокий', 'средний', 'низкий']
REQ_STATUSES = ['черновик', 'на рассмотрении', 'утверждено', 'реализовано', 'проверено']
REQ_SOURCES = ['заказчик', 'аналитик', 'регулятор', 'команда', 'другое', '']


class RequirementDialog(QDialog):
    def __init__(self, parent=None, project_id=None, req_id=None, parent_req_id=None):
        super().__init__(parent)
        self.project_id = project_id
        self.req_id = req_id
        self.parent_req_id = parent_req_id
        self.setMinimumWidth(520)
        self.setModal(True)

        if req_id:
            self.setWindowTitle("Редактировать требование")
        elif parent_req_id:
            self.setWindowTitle("Новое подтребование")
        else:
            self.setWindowTitle("Новое требование")

        self._build_ui()
        if req_id:
            self._load_requirement()
        elif parent_req_id:
            self._inherit_from_parent()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(24, 24, 24, 24)

        heading = self.windowTitle()
        lbl = QLabel(heading)
        lbl.setStyleSheet("font-size: 16px; font-weight: 700; color: #2B6CB0;")
        layout.addWidget(lbl)

        form = QFormLayout()
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.le_title = QLineEdit()
        self.le_title.setPlaceholderText("Краткое название требования")
        form.addRow("Название *", self.le_title)

        self.te_desc = QTextEdit()
        self.te_desc.setPlaceholderText("Подробное описание требования")
        self.te_desc.setMaximumHeight(110)
        form.addRow("Описание", self.te_desc)

        self.cb_type = QComboBox()
        self.cb_type.addItems(REQ_TYPES)
        form.addRow("Тип", self.cb_type)

        self.cb_priority = QComboBox()
        self.cb_priority.addItems(REQ_PRIORITIES)
        self.cb_priority.setCurrentText('средний')
        form.addRow("Приоритет", self.cb_priority)

        self.cb_source = QComboBox()
        self.cb_source.addItems(REQ_SOURCES)
        form.addRow("Источник", self.cb_source)

        self.cb_status = QComboBox()
        self.cb_status.addItems(REQ_STATUSES)
        form.addRow("Статус", self.cb_status)

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

    def _load_requirement(self):
        r = db.get_requirement(self.req_id)
        if not r:
            return
        self.le_title.setText(r['title'])
        self.te_desc.setPlainText(r['description'] or '')
        self.cb_type.setCurrentText(r['type'])
        self.cb_priority.setCurrentText(r['priority'])
        self.cb_source.setCurrentText(r['source'] or '')
        self.cb_status.setCurrentText(r['status'])

    def _inherit_from_parent(self):
        parent = db.get_requirement(self.parent_req_id)
        if parent:
            self.cb_type.setCurrentText(parent['type'])
            self.cb_source.setCurrentText(parent['source'] or '')

    def _save(self):
        title = self.le_title.text().strip()
        if not title:
            QMessageBox.warning(self, "Ошибка", "Название требования не может быть пустым")
            return

        user = current_user()
        desc = self.te_desc.toPlainText().strip()
        req_type = self.cb_type.currentText()
        priority = self.cb_priority.currentText()
        source = self.cb_source.currentText()
        status = self.cb_status.currentText()

        if self.req_id:
            db.update_requirement(
                self.req_id, title, desc, req_type, priority, source, user['id']
            )
            # Change status separately so history is logged correctly
            current_req = db.get_requirement(self.req_id)
            if current_req and current_req['status'] != status:
                db.change_requirement_status(self.req_id, status, user['id'])
        else:
            # Check parent nesting level
            if self.parent_req_id:
                parent = db.get_requirement(self.parent_req_id)
                if parent and parent['parent_id']:
                    QMessageBox.warning(self, "Ошибка",
                                        "Нельзя создать подтребование подтребования (максимум один уровень вложенности)")
                    return
            self.req_id = db.create_requirement(
                self.project_id, self.parent_req_id, title, desc,
                req_type, priority, 'черновик', source, user['id']
            )
        self.accept()
