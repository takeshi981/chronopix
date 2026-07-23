from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QScrollArea
import calendar
from functools import partial

class TimelineScrubber(QWidget):
    monthSelected = Signal(int, int)  # year, month

    def __init__(self, groups):
        super().__init__()

        self.setObjectName("ScrubberContainer")
        # 1. Changed from setFixedWidth to a safer minimum width to prevent font clipping
        self.setMinimumWidth(120) 

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Setup Scroll Area
        self.scroll = QScrollArea()
        self.scroll.setObjectName("ScrubberScrollArea")
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        self.scroll.setStyleSheet("""
            QScrollArea { border: none; }
            QScrollBar:vertical { width: 4px; margin: 0px; }
            QScrollBar::handle:vertical { min-height: 20px; border-radius: 2px; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { border: none; background: none; }
        """)

        self.content_widget = QWidget()
        self.content_widget.setObjectName("ScrubberContent")
        
        layout = QVBoxLayout(self.content_widget)
        layout.setAlignment(Qt.AlignTop)
        layout.setSpacing(2)
        # 2. Optimized padding: keeping left/right compact so text doesn't squeeze out
        layout.setContentsMargins(6, 10, 6, 10)

        year_map = {}
        for (year, month) in groups:
            year_map.setdefault(year, []).append(month)

        for year in sorted(year_map.keys(), reverse=True):
            year_label = QLabel(str(year))
            year_label.setProperty("class", "scrubber-year")
            year_label.setStyleSheet("""
                font-size: 13px; font-weight: 600; 
                margin-top: 12px; margin-bottom: 2px; padding-left: 6px; 
            """)
            layout.addWidget(year_label)

            for month in sorted(year_map[year]):
                btn = QPushButton(self.month_name(month))
                btn.setFixedHeight(24)
                btn.setProperty("class", "scrubber-month")
                
                # 3. Explicitly setting text alignment to left inside the layout
                btn.setStyleSheet("""
                    QPushButton {
                        text-align: left; 
                        padding-left: 6px;
                        padding-right: 2px;
                        border: none; 
                        border-radius: 4px; 
                        font-size: 12px; 
                        font-weight: 500;
                    }
                """)
                
                btn.clicked.connect(partial(self._on_month_clicked, btn, year, month))

                layout.addWidget(btn)

        layout.addStretch()
        
        self.scroll.setWidget(self.content_widget)
        main_layout.addWidget(self.scroll)

    def _on_month_clicked(self, button, year, month):
        self.monthSelected.emit(year, month)


    def month_name(self, m):
        return calendar.month_abbr[m]
    


