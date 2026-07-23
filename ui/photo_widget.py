import os
from PySide6.QtWidgets import (
    QSizePolicy, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QStackedLayout
)
from PySide6.QtGui import QPixmap, QIcon
from PySide6.QtCore import Qt, QSize

from core.database import get_session
from core.models import Photo
from PIL import Image
from theme_manager import themed_icon, ThemeManager

from ui.viewer import Viewer


def asset(path: str) -> str:
    base = os.path.dirname(__file__)  # folder of photo_widget.py
    return os.path.join(base, "..", "assets", "icons", path).replace("\\", "/")

img = Image.open("assets/icons/dark/down.png")
img.save("assets/icons/dark/down_fixed.png", optimize=True, quality=85)

class PhotoWidget(QWidget):
    def __init__(self, photo, initial_size=220):
        super().__init__()
        self.photo = photo
        self.setObjectName("PhotoWidget")
        ThemeManager.register_widget(self)
        self.setFixedSize(initial_size, initial_size)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # FOTO
        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.label)

        pix = QPixmap(photo.thumbnail_path)
        self.original_pixmap = pix
        self.update_thumbnail()

        # Overlay
        self.overlay = QWidget(self.label)
        self.overlay.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        self.overlay.setStyleSheet("background: transparent; border: none;")
        self.overlay_layout = QHBoxLayout(self.overlay)
        self.overlay_layout.setContentsMargins(0, 0, 0, 0)
        self.overlay_layout.setSpacing(4)

        # --- LIVE PHOTO ICON ---
        self.live_btn = QPushButton()
        self.live_btn.setObjectName("liveBadge")


        self.live_btn.setFixedSize(32, 32)
        self.live_btn.setIconSize(QSize(24, 24))
        self.live_btn.setFlat(True)
        self.live_btn.setIcon(themed_icon("live_photo.png"))      # <--- THEMED
        self.live_btn.setProperty("iconName", "live_photo.png") 
        self.live_btn.setIcon(themed_icon("live_photo.png"))    
        if not getattr(self.photo, "is_live", False):
            self.live_btn.hide()

        self.overlay_layout.addWidget(self.live_btn)

        # --- FAVORITE ICON ---
        self.favorite_btn = QPushButton()
        self.favorite_btn.setObjectName("favoriteBadge")


        self.favorite_btn.setFixedSize(32, 32)
        self.favorite_btn.setIconSize(QSize(24, 24))
        self.favorite_btn.setFlat(True)
        self.favorite_btn.clicked.connect(self.toggle_favorite)
        self.favorite_btn.setProperty("iconName", "live_photo.png") 
        self.favorite_btn.setIcon(themed_icon("live_photo.png"))  
        self.update_favorite_icon()  # Set the correct icon based on the photo's favorite status

        self.overlay_layout.addWidget(self.favorite_btn)

        self.overlay.move(initial_size - self.overlay.sizeHint().width() - 5, 5)
        self.overlay.raise_()

        self.label.mousePressEvent = self.open_viewer
        

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.overlay.move(self.width() - self.overlay.sizeHint().width() - 5, 5)


    def set_thumbnail_size(self, new_size):
        """Called dynamically when the timeline grid slider resizes the items."""
        # 1. Update the widget's overall dimensions
        self.setFixedSize(new_size, new_size)
        
        # 2. Reposition the Top-Right Favorite badge securely
        if hasattr(self, 'favorite_btn'):
            self.favorite_btn.move(new_size - 32 - 5, 5)
            
        # 3. Reposition the Top-Left Live badge (optional, but keeps logic explicit)
        if hasattr(self, 'live_btn'):
            self.live_btn.move(5, 5)

        # 4. Trigger your internal pixel re-rendering logic
        self.update_thumbnail()
        self.overlay.move(self.width() - self.overlay.sizeHint().width() - 5, 5)

    def update_thumbnail(self):
        """Mantiene aspect ratio perfetto per portrait e landscape."""
        if self.original_pixmap.isNull():
            return

        w = self.width()
        h = self.height()

        scaled = self.original_pixmap.scaled(
            w, h,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )

        self.label.setPixmap(scaled)

    def open_viewer(self, event):
        viewer = Viewer(self.photo)
        viewer.exec()

    def toggle_favorite(self):
        session = get_session()
        db_photo = session.get(Photo, self.photo.id)
        db_photo.favorite = not db_photo.favorite
        session.add(db_photo)
        session.commit()

        self.photo.favorite = db_photo.favorite
        self.update_favorite_icon()

        parent = self.parent()
        if hasattr(parent, "refresh"):
            parent.refresh()

    def update_favorite_icon(self):
        if self.photo.favorite:
            self.favorite_btn.setIcon(themed_icon("heart_filled.png"))
        else:
            self.favorite_btn.setIcon(themed_icon("heart_empty.png"))

    
    def refresh_icons(self):
        # If the widget is already deleted, do nothing
        if not self.live_btn or not self.favorite_btn:
            return

        # Live photo icon
        try:
            if self.live_btn.isVisible():
                icon_name = self.live_btn.property("iconName")
                self.live_btn.setIcon(themed_icon(icon_name))
        except RuntimeError:
            return  # C++ object deleted

        # Favorite icon
        try:
            self.update_favorite_icon()
        except RuntimeError:
            return


