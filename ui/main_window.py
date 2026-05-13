from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QListWidget, QListWidgetItem, QTabWidget,
    QFrame, QSplitter, QStatusBar, QToolBar, QComboBox,
    QMessageBox, QLineEdit, QDialog, QScrollArea
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QSize
from PyQt6.QtGui import QFont, QAction, QIcon

from db import database as db
from logic.auth import current_user, logout, can_edit
from ui.styles import STATUS_COLORS
from ui.app_icon import make_icon
from ui.dialogs.project_dialog import ProjectDialog
from ui.dialogs.member_dialog import MemberDialog
from ui.widgets.requirements_panel import RequirementsPanel
from ui.widgets.activity_widget import ActivityWidget
from ui.widgets.reports_widget import ReportsWidget
from ui.widgets.notifications_panel import NotificationsPanel


class MainWindow(QMainWindow):
    logout_requested = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.current_project_id = None
        self.notif_timer = QTimer(self)
        self.notif_timer.timeout.connect(self._update_notif_badge)
        self.notif_timer.start(15000)

        self.setWindowTitle("До-документация — Система управления требованиями")
        self.setWindowIcon(make_icon())
        self.setMinimumSize(1100, 720)
        self._build_ui()
        self._load_projects()
        self._update_notif_badge()

    def _build_ui(self):
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ── Sidebar ────────────────────────────────────────────────────────
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(240)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(12, 16, 12, 16)
        sidebar_layout.setSpacing(8)

        app_lbl = QLabel("До-документация")
        app_lbl.setFont(QFont("Segoe UI", 15, QFont.Weight.Bold))
        app_lbl.setStyleSheet("color: #63B3ED; padding: 4px 0 8px 4px;")
        sidebar_layout.addWidget(app_lbl)

        # User info
        user = current_user()
        self.lbl_user = QLabel(user['full_name'] if user else "")
        self.lbl_user.setStyleSheet("color: #BEE3F8; font-size: 12px; padding: 0 4px;")
        self.lbl_user.setWordWrap(True)
        sidebar_layout.addWidget(self.lbl_user)

        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("border: 1px solid #2D3F55;")
        sidebar_layout.addWidget(separator)

        # Projects section
        proj_header = QHBoxLayout()
        proj_lbl = QLabel("ПРОЕКТЫ")
        proj_lbl.setStyleSheet("color: #718096; font-size: 11px; font-weight: 700; letter-spacing: 1px;")
        btn_new_proj = QPushButton("+")
        btn_new_proj.setFixedSize(24, 24)
        btn_new_proj.setToolTip("Создать проект")
        btn_new_proj.setStyleSheet(
            "QPushButton { background: #2D3F55; color: #63B3ED; border-radius: 4px; "
            "font-weight: bold; padding: 0px; font-size: 16px; text-align: center; }"
            "QPushButton:hover { background: #3A5068; }"
        )
        btn_new_proj.clicked.connect(self._new_project)
        proj_header.addWidget(proj_lbl)
        proj_header.addStretch()
        proj_header.addWidget(btn_new_proj)
        sidebar_layout.addLayout(proj_header)

        self.project_list = QListWidget()
        self.project_list.setStyleSheet(
            "QListWidget { background: transparent; border: none; }"
            "QListWidget::item { color: #CBD5E0; padding: 8px 10px; border-radius: 6px; margin: 1px 0; }"
            "QListWidget::item:selected { background: #4A7FA5; color: white; }"
            "QListWidget::item:hover { background: #2D3F55; }"
        )
        self.project_list.currentItemChanged.connect(self._on_project_selected)
        sidebar_layout.addWidget(self.project_list, 1)

        # Project actions
        self.btn_edit_proj = QPushButton("Редактировать проект")
        self.btn_edit_proj.clicked.connect(self._edit_project)
        self.btn_edit_proj.setEnabled(False)
        sidebar_layout.addWidget(self.btn_edit_proj)

        self.btn_members = QPushButton("Участники")
        self.btn_members.clicked.connect(self._manage_members)
        self.btn_members.setEnabled(False)
        sidebar_layout.addWidget(self.btn_members)

        self.btn_delete_proj = QPushButton("Удалить проект")
        self.btn_delete_proj.setStyleSheet(
            "QPushButton { background: #2D3F55; color: #FC8181; border: none; "
            "padding: 8px; border-radius: 6px; text-align: left; }"
            "QPushButton:hover { background: #3A2020; }"
            "QPushButton:disabled { color: #4A5568; }"
        )
        self.btn_delete_proj.clicked.connect(self._delete_project)
        self.btn_delete_proj.setEnabled(False)
        sidebar_layout.addWidget(self.btn_delete_proj)

        separator2 = QFrame()
        separator2.setFrameShape(QFrame.Shape.HLine)
        separator2.setStyleSheet("border: 1px solid #2D3F55;")
        sidebar_layout.addWidget(separator2)

        # Notification & logout
        self.btn_notif = QPushButton("🔔 Уведомления")
        self.btn_notif.setObjectName("btn_notif")
        self.btn_notif.clicked.connect(self._open_notifications)
        sidebar_layout.addWidget(self.btn_notif)

        btn_logout = QPushButton("Выйти")
        btn_logout.setStyleSheet(
            "QPushButton { background: #2D3F55; color: #FC8181; border: none; padding: 8px; border-radius: 6px; }"
            "QPushButton:hover { background: #3A2020; }"
        )
        btn_logout.clicked.connect(self._logout)
        sidebar_layout.addWidget(btn_logout)

        main_layout.addWidget(sidebar)

        # ── Main area ──────────────────────────────────────────────────────
        right_area = QWidget()
        right_area.setObjectName("main_right_area")
        right_area.setStyleSheet("#main_right_area { background: #F5F6FA; }")
        right_layout = QVBoxLayout(right_area)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        # Header bar
        self.header_bar = QFrame()
        self.header_bar.setObjectName("header")
        hdr_layout = QHBoxLayout(self.header_bar)
        hdr_layout.setContentsMargins(16, 8, 16, 8)

        self.lbl_project_name = QLabel("Выберите проект")
        self.lbl_project_name.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        self.lbl_project_name.setStyleSheet("color: #2B6CB0;")

        self.lbl_project_meta = QLabel("")
        self.lbl_project_meta.setStyleSheet("color: #718096; font-size: 12px;")

        hdr_layout.addWidget(self.lbl_project_name)
        hdr_layout.addWidget(self.lbl_project_meta)
        hdr_layout.addStretch()

        right_layout.addWidget(self.header_bar)

        # Tab widget
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("QTabWidget::pane { border: none; border-radius: 0; }")
        right_layout.addWidget(self.tabs)

        # Tab: Requirements
        self.req_panel = RequirementsPanel()
        self.req_panel.data_changed.connect(self._on_data_changed)
        self.tabs.addTab(self.req_panel, "Требования")

        # Tab: Activity
        self.activity_widget = ActivityWidget()
        self.tabs.addTab(self.activity_widget, "Активность")

        # Tab: Reports
        self.reports_widget = ReportsWidget()
        self.tabs.addTab(self.reports_widget, "Отчёты")

        self.tabs.currentChanged.connect(self._on_tab_changed)

        main_layout.addWidget(right_area, 1)

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Готово")

    # ── Projects ────────────────────────────────────────────────────────────

    def _load_projects(self):
        self.project_list.clear()
        user = current_user()
        if not user:
            return
        projects = db.get_projects_for_user(user['id'])
        for p in projects:
            item = QListWidgetItem(p['name'])
            item.setData(Qt.ItemDataRole.UserRole, p['id'])
            item.setToolTip(f"Статус: {p['status']}\nРоль: {p['role']}")
            self.project_list.addItem(item)

    def _on_project_selected(self, current, previous):
        if not current:
            return
        project_id = current.data(Qt.ItemDataRole.UserRole)
        self.current_project_id = project_id

        project = db.get_project(project_id)
        user = current_user()
        role = db.get_user_role_in_project(project_id, user['id'])

        self.lbl_project_name.setText(project['name'])
        meta = f"Статус: {project['status']}  |  Ваша роль: {role}"
        if project['start_date']:
            meta += f"  |  {project['start_date']} – {project['end_date'] or '...'}"
        self.lbl_project_meta.setText(meta)

        self.btn_edit_proj.setEnabled(can_edit(project_id))
        self.btn_members.setEnabled(True)
        self.btn_delete_proj.setEnabled(role == 'руководитель')

        self.req_panel.set_project(project_id)
        self.activity_widget.set_project(project_id)
        self.reports_widget.set_project(project_id)
        self.status_bar.showMessage(f"Проект: {project['name']}  |  Роль: {role}")

    def _new_project(self):
        dlg = ProjectDialog(self)
        if dlg.exec():
            self._load_projects()

    def _edit_project(self):
        if not self.current_project_id:
            return
        dlg = ProjectDialog(self, project_id=self.current_project_id)
        if dlg.exec():
            self._load_projects()
            # Reselect current project
            for i in range(self.project_list.count()):
                item = self.project_list.item(i)
                if item.data(Qt.ItemDataRole.UserRole) == self.current_project_id:
                    self.project_list.setCurrentItem(item)
                    break

    def _delete_project(self):
        if not self.current_project_id:
            return
        project = db.get_project(self.current_project_id)
        reply = QMessageBox.question(
            self, "Удаление проекта",
            f"Удалить проект «{project['name']}»?\n\n"
            "Будут удалены все требования, комментарии и история изменений.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        db.delete_project(self.current_project_id)
        self.current_project_id = None
        self.lbl_project_name.setText("Выберите проект")
        self.lbl_project_meta.setText("")
        self.btn_edit_proj.setEnabled(False)
        self.btn_members.setEnabled(False)
        self.btn_delete_proj.setEnabled(False)
        self.req_panel.set_project(None)
        self.activity_widget.set_project(None)
        self.reports_widget.set_project(None)
        self._load_projects()

    def _manage_members(self):
        if not self.current_project_id:
            return
        dlg = MemberDialog(self, project_id=self.current_project_id)
        dlg.exec()

    # ── Tabs ────────────────────────────────────────────────────────────────

    def _on_tab_changed(self, index):
        if index == 1:
            self.activity_widget.refresh()
        elif index == 2:
            self.reports_widget.refresh()

    def _on_data_changed(self):
        if self.tabs.currentIndex() == 1:
            self.activity_widget.refresh()

    # ── Notifications ────────────────────────────────────────────────────────

    def _open_notifications(self):
        dlg = NotificationsPanel(self)
        dlg.exec()
        self._update_notif_badge()

    def _update_notif_badge(self):
        user = current_user()
        if not user:
            return
        count = db.count_unread_notifications(user['id'])
        if count > 0:
            self.btn_notif.setText(f"🔔 Уведомления ({count})")
            self.btn_notif.setStyleSheet(
                "QPushButton { background: #3B82F6; color: white; border: none; "
                "padding: 8px 12px; border-radius: 6px; font-weight: 600; }"
            )
        else:
            self.btn_notif.setText("🔔 Уведомления")
            self.btn_notif.setStyleSheet("")
            self.btn_notif.setObjectName("btn_notif")

    # ── Auth ────────────────────────────────────────────────────────────────

    def _logout(self):
        self.notif_timer.stop()
        logout()
        self.logout_requested.emit()
