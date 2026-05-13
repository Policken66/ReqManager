APP_STYLE = """
QMainWindow, QDialog {
    background-color: #F5F6FA;
}

QWidget {
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 13px;
    color: #2D3748;
}

/* ── Sidebar ── */
#sidebar {
    background-color: #1E2A3A;
    color: #E2E8F0;
    min-width: 240px;
    max-width: 240px;
}

#sidebar QLabel {
    color: #E2E8F0;
}

#sidebar QPushButton {
    background-color: #2D3F55;
    color: #E2E8F0;
    border: none;
    padding: 8px 12px;
    border-radius: 6px;
    text-align: left;
}

#sidebar QPushButton:hover {
    background-color: #3A5068;
}

#sidebar QPushButton:pressed {
    background-color: #4A7FA5;
}

#sidebar QListWidget {
    background-color: transparent;
    border: none;
    color: #E2E8F0;
}

#sidebar QListWidget::item {
    padding: 8px 12px;
    border-radius: 6px;
    margin: 2px 0;
}

#sidebar QListWidget::item:selected {
    background-color: #4A7FA5;
    color: #FFFFFF;
}

#sidebar QListWidget::item:hover {
    background-color: #2D3F55;
}

/* ── Header ── */
#header {
    background-color: #FFFFFF;
    border-bottom: 1px solid #E2E8F0;
    padding: 8px 16px;
    min-height: 54px;
    max-height: 54px;
}

/* ── Buttons ── */
QPushButton {
    background-color: #3B82F6;
    color: #FFFFFF;
    border: none;
    padding: 8px 18px;
    border-radius: 6px;
    font-weight: 500;
}

QPushButton:hover {
    background-color: #2563EB;
}

QPushButton:pressed {
    background-color: #1D4ED8;
}

QPushButton:disabled {
    background-color: #CBD5E0;
    color: #718096;
}

QPushButton#btn_secondary {
    background-color: #EDF2F7;
    color: #4A5568;
    border: 1px solid #CBD5E0;
}

QPushButton#btn_secondary:hover {
    background-color: #E2E8F0;
}

QPushButton#btn_danger {
    background-color: #FC8181;
    color: #FFFFFF;
}

QPushButton#btn_danger:hover {
    background-color: #F56565;
}

QPushButton#btn_success {
    background-color: #48BB78;
    color: #FFFFFF;
}

QPushButton#btn_success:hover {
    background-color: #38A169;
}

/* ── Inputs ── */
QLineEdit, QTextEdit, QComboBox, QDateEdit {
    background-color: #FFFFFF;
    border: 1px solid #CBD5E0;
    border-radius: 6px;
    padding: 7px 10px;
    color: #2D3748;
}

QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QDateEdit:focus {
    border-color: #3B82F6;
    outline: none;
}

QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: center right;
    width: 20px;
    border-left: 1px solid #CBD5E0;
    background: transparent;
}

QComboBox::down-arrow {
    image: url(ARROW_PATH_PLACEHOLDER);
    width: 10px;
    height: 6px;
}

QComboBox QAbstractItemView {
    background-color: #FFFFFF;
    border: 1px solid #CBD5E0;
    border-radius: 4px;
    selection-background-color: #EBF4FF;
    selection-color: #2B6CB0;
}

/* ── Tables ── */
QTableWidget {
    background-color: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 8px;
    gridline-color: #F0F4F8;
    alternate-background-color: #F7FAFC;
}

QTableWidget::item {
    padding: 6px 10px;
}

QTableWidget::item:selected {
    background-color: #EBF4FF;
    color: #2B6CB0;
}

QHeaderView::section {
    background-color: #F7FAFC;
    border: none;
    border-bottom: 2px solid #E2E8F0;
    padding: 8px 10px;
    font-weight: 600;
    color: #4A5568;
}

/* ── Tree Widget ── */
QTreeWidget {
    background-color: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 8px;
    alternate-background-color: #F7FAFC;
    show-decoration-selected: 1;
}

QTreeWidget::item {
    padding: 5px 4px;
    min-height: 28px;
}

QTreeWidget::item:selected {
    background-color: #EBF4FF;
    color: #2B6CB0;
}

QTreeWidget::item:hover {
    background-color: #F0F7FF;
}

QTreeWidget::branch:has-children:!has-siblings:closed,
QTreeWidget::branch:closed:has-children:has-siblings {
    border-image: none;
}

QTreeWidget::branch:open:has-children:!has-siblings,
QTreeWidget::branch:open:has-children:has-siblings {
    border-image: none;
}

/* ── Tab Widget ── */
QTabWidget::pane {
    border: 1px solid #E2E8F0;
    border-radius: 0 8px 8px 8px;
    background-color: #FFFFFF;
}

QTabBar::tab {
    background-color: #EDF2F7;
    color: #718096;
    padding: 8px 20px;
    border: 1px solid #E2E8F0;
    border-bottom: none;
    border-radius: 6px 6px 0 0;
    margin-right: 2px;
    font-weight: 500;
}

QTabBar::tab:selected {
    background-color: #FFFFFF;
    color: #2B6CB0;
    border-bottom: 2px solid #3B82F6;
}

QTabBar::tab:hover:!selected {
    background-color: #E2E8F0;
}

/* ── Scroll Bars ── */
QScrollBar:vertical {
    background-color: #F7FAFC;
    width: 8px;
    border-radius: 4px;
}

QScrollBar::handle:vertical {
    background-color: #CBD5E0;
    border-radius: 4px;
    min-height: 30px;
}

QScrollBar::handle:vertical:hover {
    background-color: #A0AEC0;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}

/* ── Status Labels ── */
QLabel#status_draft { color: #718096; }
QLabel#status_review { color: #D69E2E; font-weight: 600; }
QLabel#status_approved { color: #38A169; font-weight: 600; }
QLabel#status_implemented { color: #3B82F6; font-weight: 600; }
QLabel#status_verified { color: #805AD5; font-weight: 600; }

/* ── Cards ── */
QFrame#card {
    background-color: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 10px;
    padding: 12px;
}

QFrame#card:hover {
    border-color: #BEE3F8;
}

/* ── Notification Badge ── */
QPushButton#btn_notif {
    background-color: transparent;
    color: #4A5568;
    border: 1px solid #CBD5E0;
    border-radius: 18px;
    padding: 4px 10px;
    font-weight: 600;
}

QPushButton#btn_notif:hover {
    background-color: #EDF2F7;
}

/* ── Group Box ── */
QGroupBox {
    border: 1px solid #E2E8F0;
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 8px;
    font-weight: 600;
    color: #4A5568;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
    background-color: #F5F6FA;
}

/* ── Login Window ── */
QFrame#login_card {
    background-color: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 16px;
    padding: 32px;
}

/* ── Progress Bar ── */
QProgressBar {
    border: 1px solid #E2E8F0;
    border-radius: 4px;
    background-color: #F7FAFC;
    text-align: center;
    height: 16px;
    color: #4A5568;
}

QProgressBar::chunk {
    background-color: #48BB78;
    border-radius: 3px;
}
"""

STATUS_COLORS = {
    'черновик': '#718096',
    'на рассмотрении': '#D69E2E',
    'утверждено': '#38A169',
    'реализовано': '#3B82F6',
    'проверено': '#805AD5',
}

PRIORITY_COLORS = {
    'высокий': '#FC8181',
    'средний': '#F6AD55',
    'низкий': '#68D391',
}

TYPE_ICONS = {
    'бизнес': 'Б',
    'пользовательское': 'П',
    'функциональное': 'Ф',
    'нефункциональное': 'НФ',
}
