from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QScrollArea, QGroupBox,
    QFormLayout, QComboBox, QCheckBox, QPushButton, QFileDialog
)
from PySide6.QtCore import Qt
from PySide6.QtCore import QSettings # Assicurati di importarlo (o da PyQt6 / PyQt5)
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QScrollArea, QGroupBox, QFormLayout, QComboBox, QCheckBox)
from theme_manager import apply_theme, ThemeManager  # Importa la funzione apply_theme e la classe ThemeManager

class SettingsPage(QWidget):
    def __init__(self, mainwindow):
        super().__init__()
        self.setObjectName("SettingsPage")
        self.mainwindow = mainwindow
        
        # Inizializziamo QSettings (usa il nome della tua app)
        self.settings = QSettings("ChronopixApp", "Chronopix")
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Header
        title = QLabel("Settings")
        title.setStyleSheet("font-size: 22px; font-weight: bold; margin-bottom: 10px;")
        main_layout.addWidget(title)

        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        main_layout.addWidget(scroll)

        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setSpacing(20)
        scroll.setWidget(container)

        # ---------------------------------------------------------
        # GENERAL SETTINGS (Aggiornato)
        # ---------------------------------------------------------
        general_box = QGroupBox("General")
        general_layout = QFormLayout(general_box)

        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Dark", "Light"])
        # Legge il tema salvato (default "Dark" se non esiste)
        saved_theme = self.settings.value("theme", "Dark")
        self.theme_combo.setCurrentText(saved_theme)
        # Connette il cambio di index al salvataggio e applicazione tema
        self.theme_combo.currentTextChanged.connect(self.save_and_apply_theme)
        general_layout.addRow("Theme:", self.theme_combo)

        self.startup_scan = QCheckBox("Scan folder at startup")
        # Legge lo stato della checkbox salvata (ritorna una stringa 'true'/'false' da convertire)
        is_checked = self.settings.value("startup_scan", "false") == "true"
        self.startup_scan.setChecked(is_checked)
        self.startup_scan.toggled.connect(self.save_startup_setting)
        general_layout.addRow(self.startup_scan)

        container_layout.addWidget(general_box)

        # ---------------------------------------------------------
        # CACHE SETTINGS
        # ---------------------------------------------------------
        cache_box = QGroupBox("Cache")
        cache_layout = QFormLayout(cache_box)

        clear_thumb_btn = QPushButton("Clear Thumbnail Cache")
        clear_thumb_btn.clicked.connect(self.clear_thumbnail_cache)
        cache_layout.addRow(clear_thumb_btn)

        rebuild_exif_btn = QPushButton("Rebuild EXIF Cache")
        rebuild_exif_btn.clicked.connect(self.rebuild_exif_cache)
        cache_layout.addRow(rebuild_exif_btn)

        container_layout.addWidget(cache_box)

        # ---------------------------------------------------------
        # DATABASE SETTINGS
        # ---------------------------------------------------------
        db_box = QGroupBox("Database")
        db_layout = QFormLayout(db_box)

        clean_db_btn = QPushButton("Clean Database (remove missing files)")
        clean_db_btn.clicked.connect(self.clean_database)
        db_layout.addRow(clean_db_btn)

        export_fav_btn = QPushButton("Export Favorites")
        export_fav_btn.clicked.connect(self.export_favorites)
        db_layout.addRow(export_fav_btn)

        container_layout.addWidget(db_box)

        # ---------------------------------------------------------
        # DUPLICATES
        # ---------------------------------------------------------
        dup_box = QGroupBox("Duplicates")
        dup_layout = QFormLayout(dup_box)

        find_dup_btn = QPushButton("Find Duplicates (hash)")
        find_dup_btn.clicked.connect(self.find_duplicates_hash)
        dup_layout.addRow(find_dup_btn)

        container_layout.addWidget(dup_box)

        container_layout.addStretch()


    # ---------------------------------------------------------
    # NUOVI METODI PER SALVATAGGIO E TEMA
    # ---------------------------------------------------------


    def save_and_apply_theme(self, theme_name):
        # 1. Save setting
        self.settings.setValue("theme", theme_name)

        # 2. Apply stylesheet globally (Pass both the name and the path)
        apply_theme(theme_name, f"styles/{theme_name}.qss")

        # 3. Refresh UI
        self.mainwindow.refresh_theme()


    def save_startup_setting(self, checked):
        # Salva lo stato della checkbox come stringa "true" o "false"
        self.settings.setValue("startup_scan", "true" if checked else "false")


    # ---------------------------------------------------------
    # CALLBACKS (delegano al MainWindow)
    # ---------------------------------------------------------
    def clear_thumbnail_cache(self):
        self.mainwindow.clear_thumbnail_cache()

    def rebuild_exif_cache(self):
        self.mainwindow.rebuild_exif_cache()

    def clean_database(self):
        self.mainwindow.clean_database()

    def export_favorites(self):
        self.mainwindow.export_favorites()

    def find_duplicates_hash(self):
        self.mainwindow.find_duplicates_hash()

