from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox
)
from PyQt6.QtCore import Qt
from db import database as db
from logic.auth import ALL_ROLES, current_user


class MemberDialog(QDialog):
    def __init__(self, parent=None, project_id=None):
        super().__init__(parent)
        self.project_id = project_id
        self.setWindowTitle("Участники проекта")
        self.setMinimumSize(600, 420)
        self.setModal(True)
        self._build_ui()
        self._load_members()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        lbl = QLabel("Управление участниками проекта")
        lbl.setStyleSheet("font-size: 15px; font-weight: 700; color: #2B6CB0;")
        layout.addWidget(lbl)

        # Add member row
        add_row = QHBoxLayout()
        self.cb_users = QComboBox()
        self.cb_users.setMinimumWidth(200)
        self._fill_users_combo()

        self.cb_role = QComboBox()
        self.cb_role.addItems(ALL_ROLES)

        btn_add = QPushButton("Добавить")
        btn_add.clicked.connect(self._add_member)
        add_row.addWidget(QLabel("Пользователь:"))
        add_row.addWidget(self.cb_users, 1)
        add_row.addWidget(QLabel("Роль:"))
        add_row.addWidget(self.cb_role)
        add_row.addWidget(btn_add)
        layout.addLayout(add_row)

        # Members table
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["ФИО", "Email", "Роль", "Действие"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(2, 160)
        self.table.setColumnWidth(3, 90)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setDefaultSectionSize(36)
        layout.addWidget(self.table)

        btn_close = QPushButton("Закрыть")
        btn_close.setObjectName("btn_secondary")
        btn_close.clicked.connect(self.accept)
        row = QHBoxLayout()
        row.addStretch()
        row.addWidget(btn_close)
        layout.addLayout(row)

    def _fill_users_combo(self):
        self.cb_users.clear()
        all_users = db.get_all_users()
        members = db.get_project_members(self.project_id)
        member_ids = {m['id'] for m in members}
        self._all_users = []
        for u in all_users:
            if u['id'] not in member_ids:
                self.cb_users.addItem(f"{u['full_name']} ({u['email']})", u['id'])
                self._all_users.append(u)

    def _load_members(self):
        self.table.setRowCount(0)
        members = db.get_project_members(self.project_id)
        current = current_user()
        for m in members:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(m['full_name']))
            self.table.setItem(row, 1, QTableWidgetItem(m['email']))

            cb = QComboBox()
            cb.addItems(ALL_ROLES)
            cb.setCurrentText(m['role'])
            cb.setStyleSheet(
                "QComboBox { padding: 4px 8px; border: 1px solid #CBD5E0; border-radius: 4px; background: white; }"
                "QComboBox::drop-down { border: none; width: 20px; }"
            )
            user_id = m['id']
            cb.currentTextChanged.connect(
                lambda role, uid=user_id: db.update_member_role(self.project_id, uid, role)
            )
            self.table.setCellWidget(row, 2, cb)

            if m['id'] != current['id']:
                btn_rm = QPushButton("Удалить")
                btn_rm.setStyleSheet(
                    "QPushButton { background: #FC8181; color: white; border: none; "
                    "padding: 4px 10px; border-radius: 4px; font-weight: 500; }"
                    "QPushButton:hover { background: #F56565; }"
                )
                btn_rm.clicked.connect(lambda _, uid=m['id']: self._remove_member(uid))
                self.table.setCellWidget(row, 3, btn_rm)

    def _add_member(self):
        uid = self.cb_users.currentData()
        if uid is None:
            QMessageBox.information(self, "Нет пользователей", "Все пользователи уже добавлены в проект.")
            return
        role = self.cb_role.currentText()
        db.add_project_member(self.project_id, uid, role)
        self._refresh()

    def _remove_member(self, user_id):
        db.remove_project_member(self.project_id, user_id)
        self._refresh()

    def _refresh(self):
        self._fill_users_combo()
        self._load_members()
