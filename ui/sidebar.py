from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel
from PySide6.QtCore import Qt

class Sidebar(QWidget):
    def __init__(self):
        super().__init__()

        self.setFixedWidth(200)
        self.setObjectName("Sidebar")

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignTop)

        # Title
        title = QLabel("Library")
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title)

        # Buttons
        self.timeline_btn = QPushButton("Timeline")
        self.favorites_btn = QPushButton("Favorites")
        self.tags_btn = QPushButton("Tags")
        self.folders_btn = QPushButton("Folders")
        self.settings_btn = QPushButton("Settings")
        self.scan_btn = QPushButton("Scan Folder")
        for btn in [
            self.timeline_btn,
            self.favorites_btn,
            self.tags_btn,
            self.folders_btn,
            self.settings_btn,
            self.scan_btn
        ]:
            btn.setFixedHeight(40)
            btn.setStyleSheet("""
                QPushButton {
                    text-align: left;
                    padding-left: 10px;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background-color: #e0e0e0;
                }
            """)
            layout.addWidget(btn)

        layout.addStretch()

