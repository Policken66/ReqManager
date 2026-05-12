from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem, QHeaderView, QPushButton, QFrame,
    QGroupBox, QGridLayout, QFileDialog
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from db import database as db
from logic import csv_handler
from logic.auth import current_user


class ReportsWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.project_id = None
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(12, 12, 12, 12)

        header = QHBoxLayout()
        lbl = QLabel("Отчёты по проекту")
        lbl.setStyleSheet("font-size: 15px; font-weight: 700; color: #2B6CB0;")

        self.btn_export = QPushButton("Экспорт в CSV")
        self.btn_export.setObjectName("btn_secondary")
        self.btn_export.clicked.connect(self._export_csv)
        self.btn_export.setEnabled(False)

        self.btn_import = QPushButton("Импорт из CSV")
        self.btn_import.setObjectName("btn_secondary")
        self.btn_import.clicked.connect(self._import_csv)
        self.btn_import.setEnabled(False)

        header.addWidget(lbl)
        header.addStretch()
        header.addWidget(self.btn_export)
        header.addWidget(self.btn_import)
        layout.addLayout(header)

        # Summary cards row
        self.summary_row = QHBoxLayout()
        layout.addLayout(self.summary_row)

        # By status group
        status_group = QGroupBox("По статусам")
        self.status_layout = QGridLayout(status_group)
        layout.addWidget(status_group)

        # By type / priority row
        tp_row = QHBoxLayout()
        type_group = QGroupBox("По типам")
        self.type_layout = QGridLayout(type_group)
        pri_group = QGroupBox("По приоритетам")
        self.pri_layout = QGridLayout(pri_group)
        tp_row.addWidget(type_group)
        tp_row.addWidget(pri_group)
        layout.addLayout(tp_row)

        # Members table
        members_group = QGroupBox("Сводка по участникам")
        members_v = QVBoxLayout(members_group)
        self.members_table = QTableWidget(0, 5)
        self.members_table.setHorizontalHeaderLabels(
            ["Участник", "Роль", "Требований", "Рецензий", "Комментариев"]
        )
        self.members_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.members_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.members_table.setAlternatingRowColors(True)
        members_v.addWidget(self.members_table)
        layout.addWidget(members_group)

        self._show_placeholder()

    def set_project(self, project_id: int):
        self.project_id = project_id
        self.btn_export.setEnabled(project_id is not None)
        self.btn_import.setEnabled(project_id is not None)
        self.refresh()

    def refresh(self):
        _clear_layout(self.summary_row)
        _clear_grid(self.status_layout)
        _clear_grid(self.type_layout)
        _clear_grid(self.pri_layout)
        self.members_table.setRowCount(0)

        if not self.project_id:
            self._show_placeholder()
            return

        summary = db.get_project_summary(self.project_id)
        self._show_summary_cards(summary)
        self._show_status_breakdown(summary['by_status'])
        self._show_type_breakdown(summary['by_type'])
        self._show_priority_breakdown(summary['by_priority'])
        self._show_members_table()

    def _show_placeholder(self):
        _clear_layout(self.summary_row)
        lbl = QLabel("Выберите проект для отображения отчётов")
        lbl.setStyleSheet("color: #A0AEC0; font-style: italic;")
        self.summary_row.addWidget(lbl)

    def _show_summary_cards(self, summary):
        cards = [
            ("Всего требований", str(summary['total']), "#3B82F6"),
            ("Реализовано", str(summary['done']), "#48BB78"),
            ("Прогресс", f"{summary['percent']}%", "#D69E2E"),
        ]
        for title, value, color in cards:
            card = QFrame()
            card.setObjectName("card")
            card.setMinimumWidth(140)
            cv = QVBoxLayout(card)
            cv.setContentsMargins(16, 12, 16, 12)
            val_lbl = QLabel(value)
            val_lbl.setStyleSheet(f"font-size: 28px; font-weight: 700; color: {color};")
            val_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            tit_lbl = QLabel(title)
            tit_lbl.setStyleSheet("font-size: 12px; color: #718096;")
            tit_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            cv.addWidget(val_lbl)
            cv.addWidget(tit_lbl)
            self.summary_row.addWidget(card)
        self.summary_row.addStretch()

    def _show_status_breakdown(self, by_status):
        STATUS_COLORS_MAP = {
            'черновик': '#718096', 'на рассмотрении': '#D69E2E',
            'утверждено': '#38A169', 'реализовано': '#3B82F6', 'проверено': '#805AD5'
        }
        # Use a card-per-status layout for perfect alignment
        h_layout = QHBoxLayout()
        h_layout.setSpacing(8)
        for status, count in by_status.items():
            color = STATUS_COLORS_MAP.get(status, '#4A5568')
            card = QFrame()
            card.setStyleSheet(
                f"QFrame {{ border: 1px solid {color}; border-radius: 8px; "
                f"background: white; padding: 4px; }}"
            )
            cv = QVBoxLayout(card)
            cv.setContentsMargins(10, 8, 10, 8)
            cv.setSpacing(4)
            lbl_n = QLabel(str(count))
            lbl_n.setStyleSheet(f"font-size: 22px; font-weight: 700; color: {color}; border: none;")
            lbl_n.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl_s = QLabel(status.capitalize())
            lbl_s.setStyleSheet(f"font-size: 11px; font-weight: 600; color: {color}; border: none;")
            lbl_s.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl_s.setWordWrap(True)
            cv.addWidget(lbl_n)
            cv.addWidget(lbl_s)
            h_layout.addWidget(card)
        h_layout.addStretch()
        self.status_layout.addLayout(h_layout, 0, 0)

    def _show_type_breakdown(self, by_type):
        row = 0
        for t, count in by_type.items():
            lbl_t = QLabel(t.capitalize())
            lbl_t.setStyleSheet("padding: 4px 8px; qproperty-alignment: AlignVCenter;")
            lbl_n = QLabel(str(count))
            lbl_n.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            lbl_n.setStyleSheet("font-weight: 700; font-size: 15px; padding: 4px 8px;")
            self.type_layout.addWidget(lbl_t, row, 0)
            self.type_layout.addWidget(lbl_n, row, 1)
            row += 1

    def _show_priority_breakdown(self, by_priority):
        COLORS = {'высокий': '#FC8181', 'средний': '#F6AD55', 'низкий': '#68D391'}
        row = 0
        for p, count in by_priority.items():
            color = COLORS.get(p, '#4A5568')
            lbl_p = QLabel(p.capitalize())
            lbl_p.setStyleSheet(
                f"color: {color}; font-weight: 600; "
                f"padding: 4px 8px; qproperty-alignment: AlignVCenter;"
            )
            lbl_n = QLabel(str(count))
            lbl_n.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            lbl_n.setStyleSheet("font-weight: 700; font-size: 15px; padding: 4px 8px;")
            self.pri_layout.addWidget(lbl_p, row, 0)
            self.pri_layout.addWidget(lbl_n, row, 1)
            row += 1

    def _show_members_table(self):
        members = db.get_members_summary(self.project_id)
        self.members_table.setRowCount(0)
        for m in members:
            row = self.members_table.rowCount()
            self.members_table.insertRow(row)
            self.members_table.setItem(row, 0, QTableWidgetItem(m['full_name']))
            self.members_table.setItem(row, 1, QTableWidgetItem(m['role']))
            self.members_table.setItem(row, 2, QTableWidgetItem(str(m['requirements'])))
            self.members_table.setItem(row, 3, QTableWidgetItem(str(m['reviewed'])))
            self.members_table.setItem(row, 4, QTableWidgetItem(str(m['comments'])))

    def _export_csv(self):
        if not self.project_id:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Экспорт требований", "requirements.csv", "CSV (*.csv)"
        )
        if path:
            content = csv_handler.export_to_csv(self.project_id)
            with open(path, 'w', encoding='utf-8-sig', newline='') as f:
                f.write(content)
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.information(self, "Экспорт", f"Файл сохранён:\n{path}")

    def _import_csv(self):
        if not self.project_id:
            return
        path, _ = QFileDialog.getOpenFileName(
            self, "Импорт требований", "", "CSV (*.csv)"
        )
        if path:
            with open(path, 'r', encoding='utf-8-sig') as f:
                content = f.read()
            user = current_user()
            result = csv_handler.import_from_csv(self.project_id, content, user['id'])
            from PyQt6.QtWidgets import QMessageBox
            msg = f"Создано: {result['created']}\nПропущено: {result['skipped']}"
            if result['errors']:
                msg += "\n\nОшибки:\n" + "\n".join(result['errors'][:10])
            QMessageBox.information(self, "Импорт завершён", msg)
            self.refresh()


def _clear_layout(layout):
    while layout.count():
        item = layout.takeAt(0)
        if item.widget():
            item.widget().deleteLater()


def _clear_grid(layout):
    while layout.count():
        item = layout.takeAt(0)
        if item.widget():
            item.widget().deleteLater()
