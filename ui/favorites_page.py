from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QScrollArea, QGridLayout, QFrame
from sqlmodel import select, col
from datetime import datetime
from core.database import get_session
from core.models import Photo
from ui.photo_widget import PhotoWidget

class FavoritesPage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        title = QLabel("Favorites")
        title.setObjectName("FavoritesHeader")
        layout.addWidget(title)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        layout.addWidget(self.scroll)

        # Main container for all groups
        self.container = QWidget()
        self.main_layout = QVBoxLayout(self.container)
        self.main_layout.setSpacing(20)
        self.main_layout.addStretch() # Keeps everything at the top
        self.scroll.setWidget(self.container)

        self.refresh()

    def refresh(self):
        # 1. Clear previous content
        while self.main_layout.count() > 1: # Keep the stretch at the end
            item = self.main_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # 2. Query photos sorted by date (newest first)
        session = get_session()
        statement = select(Photo).where(Photo.favorite == True).order_by(Photo.created_at.desc())
        photos = session.exec(statement).all()

        current_date_str = None
        current_grid = None
        col_count = 0
        max_columns = 4

        for photo in photos:
            # Assumes photo.created_at is a datetime object
            date_label = photo.created_at.strftime("%Y - %B %d") 

            # 3. If date changes, create a new section
            if date_label != current_date_str:
                current_date_str = date_label
                
                # Header for the group
                header = QLabel(date_label)
                header.setStyleSheet("font-weight: bold; font-size: 14px; margin-top: 10px;")
                self.main_layout.insertWidget(self.main_layout.count() - 1, header)

                # Grid for this specific group
                group_widget = QWidget()
                current_grid = QGridLayout(group_widget)
                current_grid.setSpacing(10)
                current_grid.setContentsMargins(0, 0, 0, 0)
                self.main_layout.insertWidget(self.main_layout.count() - 1, group_widget)
                
                col_count = 0

            # 4. Add photo to the current grid
            row = col_count // max_columns
            col = col_count % max_columns
            
            photo_widget = PhotoWidget(photo)
            current_grid.addWidget(photo_widget, row, col)
            col_count += 1
