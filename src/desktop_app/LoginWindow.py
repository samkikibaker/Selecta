import httpx
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QMainWindow,
    QLabel,
    QLineEdit,
    QPushButton,
    QWidget,
    QVBoxLayout,
    QMessageBox,
)

from selecta.logger import generate_logger
from desktop_app.MainWindow import MainWindow
from selecta.utils import API_URL

# Logger
logger = generate_logger()


class LoginWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Selecta")
        self.setFixedSize(300, 200)

        # Dashboard window will be populated after login
        self.dashboard = None

        # Create the central widget and layout
        central_widget = QWidget()
        layout = QVBoxLayout()

        # Login title
        title = QLabel("Login")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 30px; font-weight: bold;")
        layout.addWidget(title)

        # Email input
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Email")
        layout.addWidget(self.email_input)

        # Password input
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.Password)  # Hide password
        layout.addWidget(self.password_input)

        # Login button
        login_button = QPushButton("Login")
        login_button.clicked.connect(self.handle_login)
        layout.addWidget(login_button)

        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

    def handle_login(self):
        # Get inputs
        email = self.email_input.text().strip()
        password = self.password_input.text().strip()
        if not email or not password:
            QMessageBox.warning(None, "Missing Fields", "Email and password are required.")
            return

        # Post to /login endpoint to get access token
        with httpx.Client() as client:
            response = client.post(f"{API_URL}/login", json={"email": email, "password": password})
            if response.status_code == 200:
                access_token = response.json()["access_token"]
                self.dashboard = MainWindow(email=email, access_token=access_token)
                self.dashboard.show()
                self.close()
            else:
                error_message = response.json().get("detail", "Login failed.")
                QMessageBox.warning(None, "Login Failed", error_message)
