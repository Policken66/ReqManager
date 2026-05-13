from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTreeWidget, QTreeWidgetItem, QComboBox, QLineEdit,
    QHeaderView, QMenu, QMessageBox, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QAction
from db import database as db
from logic.auth import current_user, can_edit
from ui.styles import STATUS_COLORS, PRIORITY_COLORS
from ui.dialogs.requirement_dialog import RequirementDialog
from ui.widgets.requirement_card import RequirementCard

COLS = ['ID', 'Название', 'Тип', 'Приоритет', 'Статус', 'Прогресс', 'Автор']
COL_ID, COL_TITLE, COL_TYPE, COL_PRI, COL_STATUS, COL_PROG, COL_AUTHOR = range(7)


class RequirementsPanel(QWidget):
    data_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.project_id = None
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(0, 0, 0, 0)

        # Toolbar row
        toolbar = QHBoxLayout()

        self.le_search = QLineEdit()
        self.le_search.setPlaceholderText("Поиск по ID, названию, описанию...")
        self.le_search.setMinimumWidth(200)
        self.le_search.textChanged.connect(self._apply_filters)

        self.cb_type = QComboBox()
        self.cb_type.addItem("Все типы", "")
        for v in ['бизнес', 'пользовательское', 'функциональное', 'нефункциональное']:
            self.cb_type.addItem(v, v)
        self.cb_type.currentIndexChanged.connect(self._apply_filters)

        self.cb_status = QComboBox()
        self.cb_status.addItem("Все статусы", "")
        for v in ['черновик', 'на рассмотрении', 'утверждено', 'реализовано', 'проверено']:
            self.cb_status.addItem(v, v)
        self.cb_status.currentIndexChanged.connect(self._apply_filters)

        self.cb_priority = QComboBox()
        self.cb_priority.addItem("Все приоритеты", "")
        for v in ['высокий', 'средний', 'низкий']:
            self.cb_priority.addItem(v, v)
        self.cb_priority.currentIndexChanged.connect(self._apply_filters)

        self.btn_new = QPushButton("+ Требование")
        self.btn_new.clicked.connect(self._new_requirement)
        self.btn_new.setEnabled(False)

        toolbar.addWidget(QLabel("Поиск:"))
        toolbar.addWidget(self.le_search, 2)
        toolbar.addWidget(self.cb_type)
        toolbar.addWidget(self.cb_status)
        toolbar.addWidget(self.cb_priority)
        toolbar.addStretch()
        toolbar.addWidget(self.btn_new)

        layout.addLayout(toolbar)

        # Tree
        self.tree = QTreeWidget()
        self.tree.setColumnCount(len(COLS))
        self.tree.setHeaderLabels(COLS)
        self.tree.setAlternatingRowColors(True)
        self.tree.setRootIsDecorated(True)
        self.tree.setSelectionBehavior(QTreeWidget.SelectionBehavior.SelectRows)
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._context_menu)
        self.tree.itemDoubleClicked.connect(self._open_card)

        header = self.tree.header()
        header.setSectionResizeMode(COL_TITLE, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(COL_ID, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(COL_TYPE, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(COL_PRI, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(COL_STATUS, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(COL_PROG, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(COL_AUTHOR, QHeaderView.ResizeMode.ResizeToContents)

        layout.addWidget(self.tree)

    def set_project(self, project_id: int):
        self.project_id = project_id
        user = current_user()
        self.btn_new.setEnabled(can_edit(project_id) if project_id else False)
        self.refresh()

    def refresh(self):
        self._apply_filters()

    def _get_filters(self):
        filters = {}
        if self.le_search.text().strip():
            filters['search'] = self.le_search.text().strip()
        t = self.cb_type.currentData()
        if t:
            filters['type'] = t
        s = self.cb_status.currentData()
        if s:
            filters['status'] = s
        p = self.cb_priority.currentData()
        if p:
            filters['priority'] = p
        return filters

    def _apply_filters(self):
        if not self.project_id:
            self.tree.clear()
            return
        filters = self._get_filters()
        reqs = db.get_requirements(self.project_id, filters)
        self._populate_tree(reqs)

    def _populate_tree(self, reqs):
        self.tree.clear()
        root_items = {}
        sub_items = []

        # Separate roots and subs
        for r in reqs:
            if not r['parent_id']:
                item = self._make_item(r)
                root_items[r['id']] = item
                self.tree.addTopLevelItem(item)
            else:
                sub_items.append(r)

        # Add sub-requirements under their parents
        for r in sub_items:
            item = self._make_item(r)
            parent_item = root_items.get(r['parent_id'])
            if parent_item:
                parent_item.addChild(item)
            else:
                # Parent filtered out — show at root with indicator
                item.setText(COL_ID, f"  {r['display_id']}")
                self.tree.addTopLevelItem(item)

        # Update progress column for roots that have subs
        for req_id, item in root_items.items():
            done, total, pct = db.get_requirement_progress(req_id)
            if total > 0:
                item.setText(COL_PROG, f"{pct}%")
            item.setExpanded(True)

    def _make_item(self, r) -> QTreeWidgetItem:
        item = QTreeWidgetItem()
        item.setData(0, Qt.ItemDataRole.UserRole, r['id'])
        item.setText(COL_ID, r['display_id'])
        item.setText(COL_TITLE, r['title'])
        item.setText(COL_TYPE, r['type'])
        item.setText(COL_PRI, r['priority'])
        item.setText(COL_STATUS, r['status'])
        item.setText(COL_AUTHOR, r['author_name'] or '')

        # Color status
        color = STATUS_COLORS.get(r['status'], '#718096')
        item.setForeground(COL_STATUS, QColor(color))

        # Bold roots
        if not r['parent_id']:
            font = QFont()
            font.setBold(True)
            item.setFont(COL_TITLE, font)

        return item

    def _open_card(self, item, col=None):
        req_id = item.data(0, Qt.ItemDataRole.UserRole)
        if req_id:
            dlg = RequirementCard(self, req_id=req_id)
            dlg.requirement_changed.connect(self.refresh)
            dlg.requirement_changed.connect(self.data_changed)
            dlg.exec()

    def _new_requirement(self):
        if not self.project_id:
            return
        dlg = RequirementDialog(self, project_id=self.project_id)
        if dlg.exec():
            self.refresh()
            self.data_changed.emit()

    def _context_menu(self, pos):
        item = self.tree.itemAt(pos)
        if not item:
            return
        req_id = item.data(0, Qt.ItemDataRole.UserRole)
        req = db.get_requirement(req_id)
        if not req:
            return

        menu = QMenu(self)
        act_open = menu.addAction("Открыть карточку")
        act_open.triggered.connect(lambda: self._open_card(item))

        if can_edit(req['project_id']):
            act_edit = menu.addAction("Редактировать")
            act_edit.triggered.connect(lambda: self._edit_req(req_id))

            if not req['parent_id']:
                act_sub = menu.addAction("Добавить подтребование")
                act_sub.triggered.connect(lambda: self._new_sub(req_id))

            menu.addSeparator()
            act_del = menu.addAction("Удалить")
            act_del.triggered.connect(lambda: self._delete_req(req_id))

        menu.exec(self.tree.viewport().mapToGlobal(pos))

    def _edit_req(self, req_id):
        req = db.get_requirement(req_id)
        dlg = RequirementDialog(self, project_id=req['project_id'], req_id=req_id)
        if dlg.exec():
            self.refresh()
            self.data_changed.emit()

    def _new_sub(self, parent_id):
        req = db.get_requirement(parent_id)
        dlg = RequirementDialog(self, project_id=req['project_id'], parent_req_id=parent_id)
        if dlg.exec():
            self.refresh()
            self.data_changed.emit()

    def _delete_req(self, req_id):
        req = db.get_requirement(req_id)
        subs = db.get_sub_requirements(req_id)
        msg = f"Удалить требование «{req['title']}»?"
        if subs:
            msg += f"\n\nТакже будут удалены {len(subs)} подтребований."
        reply = QMessageBox.question(self, "Подтверждение", msg)
        if reply == QMessageBox.StandardButton.Yes:
            db.delete_requirement(req_id, current_user()['id'])
            self.refresh()
            self.data_changed.emit()
