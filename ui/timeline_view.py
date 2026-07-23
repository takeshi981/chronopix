import calendar
from PySide6.QtWidgets import (
    QWidget, QScrollArea, QVBoxLayout, QLabel, QPushButton, QFrame
)
from PySide6.QtCore import QPoint, QPropertyAnimation, QEasingCurve, QTimer, QSize, Qt
from PySide6.QtGui import QIcon, QPixmap
from core.database import get_session
from core.models import Photo
from theme_manager import themed_icon
from ui.photo_widget import PhotoWidget
from ui.flow_layout import FlowLayout
from sqlmodel import select


class CollapsibleMonth(QWidget):
    def __init__(self, year, month, photos, thumb_size=220):
        super().__init__()
        self.setObjectName("CollapsibleMonth")
        self.year = year
        self.month = month
        self.photos = photos
        self.expanded = True
        self.thumb_size = thumb_size

        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(5)
        self.layout.setContentsMargins(0, 0, 0, 0)

        # Month header
        header = QWidget()
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(10, 5, 10, 5)

        month_name = calendar.month_name[month]
        title = QLabel(f"{month_name}")
        title.setObjectName("MonthHeader")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")

        self.toggle_btn = QPushButton()
        self.toggle_btn.setIcon(themed_icon("down.png"))
 
        self.toggle_btn.setFixedWidth(100)
        self.toggle_btn.clicked.connect(self.toggle)
        
        header_layout.addWidget(title)
        header_layout.addWidget(self.toggle_btn)
        self.layout.addWidget(header)

        # Separator line
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("color: #888;")
        self.layout.addWidget(sep)

        # Content area (FlowLayout)
        self.content = QWidget()
        self.flow = FlowLayout(self.content, spacing=12)
        
        # Popoliamo con la dimensione iniziale desiderata
        for p in photos:
            self.flow.addWidget(PhotoWidget(p, initial_size=self.thumb_size))

        self.layout.addWidget(self.content)

        # Animation
        self.anim = QPropertyAnimation(self.content, b"maximumHeight")
        self.anim.setDuration(250)
        self.anim.setEasingCurve(QEasingCurve.InOutQuad)

        # Calcola l'altezza reale iniziale dopo il rendering del layout
        QTimer.singleShot(0, self.initialize_height)

    def initialize_height(self):
        self.content.adjustSize()
        h = self.content.sizeHint().height()

        if h < 1:
            h = 1

        self.content.setMaximumHeight(h)
        self.full_height = h


    def update_layout_height(self):
        """Ricalcola l'altezza se le foto cambiano dimensione tramite lo slider"""
        self.content.adjustSize()
        h = self.content.sizeHint().height()

        if h < 1:
            h = 1

        self.full_height = h

        if self.expanded:
            self.content.setMaximumHeight(h)


    def toggle(self):
        if self.expanded:
            self.toggle_btn.setIcon(themed_icon("up.png"))
            self.anim.setStartValue(self.full_height)
            self.anim.setEndValue(0)
            self.anim.start()
            self.expanded = False
        else:
            self.toggle_btn.setIcon(themed_icon("down.png"))
            self.anim.setStartValue(0)
            self.anim.setEndValue(self.full_height)
            self.anim.start()
            self.expanded = True
    def refresh_icons(self):
        self.toggle_btn.setIcon(themed_icon("down.png"))
class TimelineView(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("TimelineView")

        # Dimensione di default delle miniature
        self.current_thumb_size = 220
        self.month_positions = {}

        # Scroll area principale
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)

        # Contenitore interno
        self.container = QWidget()
        self.main_layout = QVBoxLayout(self.container)
        self.main_layout.setContentsMargins(15, 15, 15, 15)
        self.main_layout.setSpacing(20)

        self.scroll.setWidget(self.container)

        # Layout principale del TimelineView
        layout = QVBoxLayout(self)
        layout.addWidget(self.scroll)

        # Carica le foto
        self.load_photos()


    def change_photos_size(self, new_size: int):
        """Aggiorna le dimensioni delle foto in tempo reale riarrangiando la griglia"""
        self.current_thumb_size = new_size
        
        # 1. Modifica la dimensione di tutti i PhotoWidget
        photo_widgets = self.findChildren(PhotoWidget)
        for widget in photo_widgets:
            widget.set_thumbnail_size(new_size)
            
        # 2. Chiedi ai blocchi dei mesi di aggiornare le loro altezze di animazione
        months = self.findChildren(CollapsibleMonth)
        for month in months:
            month.flow.invalidate() # Sblocca e forza il FlowLayout a riorganizzarsi
            month.update_layout_height() # Aggiorna le altezze massime
            
        self.update()

    def reload(self):
        self.clear()
        self.load_photos()

    def load_photos(self):
        session = get_session()
        self.clear()
        self.month_positions = {}
        
        photos = session.exec(
            select(Photo).order_by(Photo.exif_date)
        ).all()

        groups = self.group_by_month(photos)
        current_year = None
        y_offset = 0

        for (year, month), items in groups.items():
            # Intestazione Anno (Year Header)
            if year != current_year:
                year_label = QLabel(f"{year}")
                year_label.setObjectName("YearHeader")
                self.main_layout.addWidget(year_label)
                
                # Calcola l'offset per lo scrubber
                y_offset += year_label.sizeHint().height() + 20
                current_year = year

            # Sezione del mese collassabile (Passando la dimensione corrente dello slider)
            month_section = CollapsibleMonth(year, month, items, thumb_size=self.current_thumb_size)
            self.main_layout.addWidget(month_section)

            # Salva la coordinata Y per lo Scrubber laterale
            self.month_positions[(year, month)] = y_offset
            y_offset += month_section.sizeHint().height() + 30

    def group_by_month(self, photos):
        groups = {}
        for p in photos:
            d = p.exif_date or p.created_at
            key = (d.year, d.month)
            groups.setdefault(key, []).append(p)
        return groups

    def scroll_to_month(self, year, month):
        for m in self.findChildren(CollapsibleMonth):
            if m.year == year and m.month == month:
                pos = m.mapTo(self.scroll.widget(), QPoint(0, 0))
                self.scroll.verticalScrollBar().setValue(pos.y())
                return


    def clear(self):
        """Svuota in modo pulito il layout distruggendo i vecchi widget"""
        while self.main_layout.count():
            item = self.main_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

