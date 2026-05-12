from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame, QStackedWidget, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from logic.auth import login, register


class LoginWindow(QWidget):
    login_successful = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("До-документация — Вход")
        self.setMinimumSize(440, 520)
        self.setObjectName("login_bg")

        outer = QVBoxLayout(self)
        outer.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.stack = QStackedWidget()
        outer.addWidget(self.stack)

        self.stack.addWidget(self._build_login_page())
        self.stack.addWidget(self._build_register_page())

    # ── Login page ─────────────────────────────────────────────────────────────

    def _build_login_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        card = QFrame()
        card.setObjectName("login_card")
        card.setFixedWidth(380)
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(16)
        card_layout.setContentsMargins(32, 32, 32, 32)

        title = QLabel("До-документация")
        title.setFont(QFont("Segoe UI", 22, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #2B6CB0;")

        subtitle = QLabel("Система управления требованиями")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color: #718096; font-size: 12px;")

        lbl_email = QLabel("Email")
        lbl_email.setStyleSheet("font-weight: 600;")
        self.le_login_email = QLineEdit()
        self.le_login_email.setPlaceholderText("you@example.com")

        lbl_pass = QLabel("Пароль")
        lbl_pass.setStyleSheet("font-weight: 600;")
        self.le_login_pass = QLineEdit()
        self.le_login_pass.setPlaceholderText("••••••••")
        self.le_login_pass.setEchoMode(QLineEdit.EchoMode.Password)

        self.lbl_login_error = QLabel("")
        self.lbl_login_error.setStyleSheet("color: #E53E3E; font-size: 12px;")
        self.lbl_login_error.setAlignment(Qt.AlignmentFlag.AlignCenter)

        btn_login = QPushButton("Войти")
        btn_login.setMinimumHeight(42)
        btn_login.clicked.connect(self._do_login)

        sep = QLabel("— или —")
        sep.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sep.setStyleSheet("color: #A0AEC0; font-size: 12px;")

        btn_go_register = QPushButton("Зарегистрироваться")
        btn_go_register.setObjectName("btn_secondary")
        btn_go_register.setMinimumHeight(38)
        btn_go_register.clicked.connect(lambda: self.stack.setCurrentIndex(1))

        self.le_login_pass.returnPressed.connect(self._do_login)
        self.le_login_email.returnPressed.connect(self.le_login_pass.setFocus)

        for w in [title, subtitle, lbl_email, self.le_login_email,
                  lbl_pass, self.le_login_pass, self.lbl_login_error,
                  btn_login, sep, btn_go_register]:
            card_layout.addWidget(w)

        layout.addWidget(card)
        return page

    def _do_login(self):
        ok, msg = login(self.le_login_email.text(), self.le_login_pass.text())
        if ok:
            self.login_successful.emit()
        else:
            self.lbl_login_error.setText(msg)

    # ── Register page ──────────────────────────────────────────────────────────

    def _build_register_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        card = QFrame()
        card.setObjectName("login_card")
        card.setFixedWidth(380)
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(14)
        card_layout.setContentsMargins(32, 32, 32, 32)

        title = QLabel("Регистрация")
        title.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #2B6CB0;")

        lbl_name = QLabel("ФИО")
        lbl_name.setStyleSheet("font-weight: 600;")
        self.le_reg_name = QLineEdit()
        self.le_reg_name.setPlaceholderText("Иванов Иван Иванович")

        lbl_email = QLabel("Email")
        lbl_email.setStyleSheet("font-weight: 600;")
        self.le_reg_email = QLineEdit()
        self.le_reg_email.setPlaceholderText("you@example.com")

        lbl_pass = QLabel("Пароль")
        lbl_pass.setStyleSheet("font-weight: 600;")
        self.le_reg_pass = QLineEdit()
        self.le_reg_pass.setPlaceholderText("не менее 6 символов")
        self.le_reg_pass.setEchoMode(QLineEdit.EchoMode.Password)

        lbl_pass2 = QLabel("Повторите пароль")
        lbl_pass2.setStyleSheet("font-weight: 600;")
        self.le_reg_pass2 = QLineEdit()
        self.le_reg_pass2.setPlaceholderText("••••••••")
        self.le_reg_pass2.setEchoMode(QLineEdit.EchoMode.Password)

        self.lbl_reg_error = QLabel("")
        self.lbl_reg_error.setStyleSheet("color: #E53E3E; font-size: 12px;")
        self.lbl_reg_error.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_reg_error.setWordWrap(True)

        btn_register = QPushButton("Создать аккаунт")
        btn_register.setMinimumHeight(42)
        btn_register.clicked.connect(self._do_register)

        btn_back = QPushButton("← Назад к входу")
        btn_back.setObjectName("btn_secondary")
        btn_back.setMinimumHeight(38)
        btn_back.clicked.connect(lambda: self.stack.setCurrentIndex(0))

        for w in [title, lbl_name, self.le_reg_name, lbl_email, self.le_reg_email,
                  lbl_pass, self.le_reg_pass, lbl_pass2, self.le_reg_pass2,
                  self.lbl_reg_error, btn_register, btn_back]:
            card_layout.addWidget(w)

        layout.addWidget(card)
        return page

    def _do_register(self):
        self.lbl_reg_error.setText("")
        if self.le_reg_pass.text() != self.le_reg_pass2.text():
            self.lbl_reg_error.setText("Пароли не совпадают")
            return
        ok, msg = register(
            self.le_reg_email.text(),
            self.le_reg_pass.text(),
            self.le_reg_name.text()
        )
        if ok:
            QMessageBox.information(self, "Готово", "Аккаунт создан! Войдите в систему.")
            self.stack.setCurrentIndex(0)
            self.le_login_email.setText(self.le_reg_email.text())
        else:
            self.lbl_reg_error.setText(msg)
