import sys
from PyQt6.QtWidgets import QApplication, QStackedWidget
from PyQt6.QtCore import Qt

from db.database import init_db
from ui.styles import APP_STYLE
from ui.login_window import LoginWindow
from ui.main_window import MainWindow
from ui.app_icon import make_icon


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(APP_STYLE)
    app.setApplicationName("До-документация")
    app.setOrganizationName("NSTU")

    icon = make_icon()
    app.setWindowIcon(icon)

    init_db()

    stack = QStackedWidget()
    stack.setWindowTitle("До-документация")
    stack.setWindowIcon(icon)
    stack.setMinimumSize(440, 520)

    login_win = LoginWindow()
    main_win = None

    def on_login():
        nonlocal main_win
        main_win = MainWindow()

        def on_logout():
            stack.removeWidget(main_win)
            stack.setCurrentIndex(0)
            stack.setMinimumSize(440, 520)
            stack.resize(440, 520)

        main_win.logout_requested.connect(on_logout)
        stack.addWidget(main_win)
        stack.setCurrentWidget(main_win)
        stack.setMinimumSize(1100, 720)
        stack.resize(1200, 760)

    login_win.login_successful.connect(on_login)
    stack.addWidget(login_win)
    stack.setCurrentIndex(0)
    stack.show()

    sys.exit(app.exec())


if __name__ == '__main__':
    main()
