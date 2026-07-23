import os
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, 
                                QStackedWidget, QProgressBar, QPushButton, QDialog, QLabel, QSlider)
from PySide6.QtCore import QPoint, QSettings, Qt
from sqlalchemy import label
from ui.photo_widget import PhotoWidget
from theme_manager import ThemeManager
from ui.timeline_view import TimelineView
from ui.sidebar import Sidebar
from core.scanner import extract_exif_date, scan_folder
from PySide6.QtWidgets import QFileDialog
from ui.timeline_scrubber import TimelineScrubber
from PySide6.QtCore import QThread, Qt
from PySide6.QtGui import QAction, QIcon
from core.scanner_worker import ScannerWorker
from core.database import get_session
from sqlmodel import select
from core.models import Photo
from ui.favorites_page import FavoritesPage
from ui.settings_page import SettingsPage
from ui.sidebar import Sidebar
from typing import Optional
from theme_manager import apply_theme

import hashlib


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # 1. IMPOSTAZIONI E TEMA (Caricati subito per evitare glitch visivi)
        self.settings = QSettings("ChronopixApp", "Chronopix")

        saved_theme = self.settings.value("theme", "light")
        apply_theme(saved_theme, f"styles/{saved_theme}.qss")

        # 2. GEOMETRIA FINESTRA PRINCIPALE
        self.setWindowTitle("Chronopix")
        self.resize(1200, 800)

        # 3. CONTENITORE CENTRALE (Impostato subito)
        container = QWidget()
        self.main_layout = QHBoxLayout(container)
        self.setCentralWidget(container)

        # 4. SIDEBAR
        self.sidebar = Sidebar()
        self.main_layout.addWidget(self.sidebar)

        # 5. STACKED WIDGET (Pagine principali)
        self.stack = QStackedWidget()
        self.main_layout.addWidget(self.stack, stretch=1)

        # --- CONFIGURAZIONE PAGINE (In ordine logico) ---
        
        # Pagina 1: Timeline Page
        self.timeline_page = QWidget()
        timeline_layout = QVBoxLayout(self.timeline_page)
        
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        timeline_layout.addWidget(self.progress)

        self.scan_btn = QPushButton("Scan Folder")
        self.scan_btn.setObjectName("ScanButton")
        self.scan_btn.clicked.connect(self.scan_folder)
   

        self.timeline = TimelineView()
        timeline_layout.addWidget(self.timeline)
        
        # Aggiungiamo la timeline allo stack (Indice 0)
        self.stack.addWidget(self.timeline_page)

        # Pagina 2: Settings Page
        self.settings_page = SettingsPage(self)
        self.stack.addWidget(self.settings_page) # (Indice 1)

        # Pagina 3: Favorites Page
        self.favorites_page = FavoritesPage()
        self.stack.addWidget(self.favorites_page) # (Indice 2)

        # Forziamo lo stack a mostrare la timeline all'avvio
        self.stack.setCurrentWidget(self.timeline_page)

        # --- SCRUBBER (Barra di navigazione temporale destra) ---
        session = get_session()
        photos = session.exec(select(Photo)).all()
        groups = self.timeline.group_by_month(photos)

        self.scrubber = TimelineScrubber(groups)
        self.scrubber.monthSelected.connect(self.timeline.scroll_to_month)
        self.main_layout.addWidget(self.scrubber)

        # --- CONNESSIONI SIDEBAR ---
        self.sidebar.timeline_btn.clicked.connect(self.show_timeline)
        self.sidebar.favorites_btn.clicked.connect(self.show_favorites)
        self.sidebar.tags_btn.clicked.connect(self.show_tags)
        self.sidebar.folders_btn.clicked.connect(self.show_folders)
        self.sidebar.settings_btn.clicked.connect(self.show_settings)
        self.sidebar.scan_btn.clicked.connect(self.scan_folder)

        # 6. INIZIALIZZAZIONE MENU (Chiamata solo ora che la finestra è strutturata)
        self.setup_menu_bar()
        # Dentro il costruttore della tua MainWindow o della Timeline Page:
        self.zoom_slider = QSlider(Qt.Horizontal)
        self.zoom_slider.setMinimum(100)  # Dimensione minima della foto (100x100)
        self.zoom_slider.setMaximum(400)  # Dimensione massima della foto (400x400)
        self.zoom_slider.setValue(220)    # Valore iniziale coerente con il default

        # Connettiamo lo spostamento dello slider al metodo della timeline
        self.zoom_slider.valueChanged.connect(self.timeline.change_photos_size)

        # Ricordati di aggiungere lo slider al layout (es. in cima alla timeline_layout)
        timeline_layout.addWidget(self.zoom_slider)

    def setup_menu_bar(self):
        """Inizializza e configura la barra dei menu della finestra"""
        menu_bar = self.menuBar()

        # FILE MENU
        file_menu = menu_bar.addMenu("File")
        
        open_action = QAction("Open Folder...", self)
        open_action.triggered.connect(self.scan_folder)
        file_menu.addAction(open_action)

        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # VIEW MENU
        view_menu = menu_bar.addMenu("View")

        timeline_action = QAction("Timeline", self)
        timeline_action.triggered.connect(self.show_timeline)
        view_menu.addAction(timeline_action)

        favorites_action = QAction("Favorites", self)
        favorites_action.triggered.connect(self.show_favorites)
        view_menu.addAction(favorites_action)

        tags_action = QAction("Tags", self)
        tags_action.triggered.connect(self.show_tags)
        view_menu.addAction(tags_action)

        folders_action = QAction("Folders", self)
        folders_action.triggered.connect(self.show_folders)
        view_menu.addAction(folders_action)

        settings_action = QAction("Settings", self)
        settings_action.triggered.connect(self.show_settings)
        view_menu.addAction(settings_action)

        # EDIT MENU
        edit_menu = menu_bar.addMenu("Edit")

        undo_action = QAction("Undo", self)
        undo_action.triggered.connect(self.edit_undo)
        edit_menu.addAction(undo_action)

        redo_action = QAction("Redo", self)
        redo_action.triggered.connect(self.edit_redo)
        edit_menu.addAction(redo_action)

        # TOOLS MENU
        tools_menu = menu_bar.addMenu("Tools")

        scan_action = QAction("Scan Folder", self)
        scan_action.triggered.connect(self.scan_folder)
        tools_menu.addAction(scan_action)

        rebuild_action = QAction("Rebuild Thumbnails", self)
        rebuild_action.triggered.connect(self.rebuild_thumbnails)
        tools_menu.addAction(rebuild_action)

        clean_action = QAction("Clean Database", self)
        clean_action.triggered.connect(self.clean_database)
        tools_menu.addAction(clean_action)

        export_action = QAction("Export Favorites", self)
        export_action.triggered.connect(self.export_favorites)
        tools_menu.addAction(export_action)

        exif_action = QAction("Rebuild EXIF Cache", self)
        exif_action.triggered.connect(self.rebuild_exif_cache)
        tools_menu.addAction(exif_action)

        dup_action = QAction("Find Duplicates (hash)", self)
        dup_action.triggered.connect(self.find_duplicates_hash)
        tools_menu.addAction(dup_action)            

        # HELP MENU
        help_menu = menu_bar.addMenu("Help")

        about_action = QAction("About Chronopix", self)
        about_action.triggered.connect(self.show_about_dialog)
        help_menu.addAction(about_action)


    def refresh_theme(self):
        app = QApplication.instance()

        for w in app.allWidgets():
            if hasattr(w, "refresh_icons"):
                w.refresh_icons()


        
    def scan_folder(self):
        folder =  QFileDialog.getExistingDirectory(self, "Select Photo Folder", "")
        if not folder:
            return

        # Show progress bar
        self.progress.setVisible(True)
        self.progress.setValue(0)

        # Thread + worker
        self.thread = QThread()
        self.worker = ScannerWorker(folder)
        self.worker.moveToThread(self.thread)

        # Connect signals
        self.thread.started.connect(self.worker.run)
        self.worker.progress.connect(self.progress.setValue)
        self.worker.finished.connect(self.scan_finished)

        # Cleanup
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        self.thread.start()

    def scan_finished(self):
        self.progress.setVisible(False)
        self.progress.setValue(0)

        # Reload timeline
        session = get_session()
        photos = session.exec(select(Photo)).all()
        result = getattr(self.worker, "result", None)
        self.timeline.load_photos()
        if not result:
            print("Scan finished but no result")
            groups = []
        else:
            groups = getattr(result, "groups", [])
        self.rebuild_scrubber(groups)
        self.timeline.reload()
        # Rebuild scrubber
        groups = self.timeline.group_by_month(photos)
        self.scrubber.setParent(None)
        self.scrubber = TimelineScrubber(groups)
        self.main_layout.addWidget(self.scrubber)
        self.scrubber.monthSelected.connect(self.timeline.scroll_to_month)
        self.main_layout.addWidget(self.scrubber)
    def show_timeline(self):
        self.stack.setCurrentWidget(self.timeline_page)

    def show_favorites(self):
        self.favorites_page.refresh()
        self.stack.setCurrentWidget(self.favorites_page)

    def show_tags(self):
        print("Tags clicked")

    def show_folders(self):
        print("Folders clicked")

    def show_settings(self):
        print("Settings clicked")
    
    def rebuild_scrubber(self, groups):
        # Rimuovi scrubber precedente in modo sicuro
        if self.scrubber:
            try:
                self.scrubber.monthSelected.disconnect()
            except:
                pass

            self.main_layout.removeWidget(self.scrubber)
            self.scrubber.deleteLater()
            self.scrubber = None

        # Crea nuovo scrubber
        self.scrubber = TimelineScrubber(groups)
        self.scrubber.monthSelected.connect(self.timeline.scroll_to_month)

        self.main_layout.addWidget(self.scrubber)



    def show_about_dialog(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("About Chronopix")
        dlg.resize(400, 200)

        layout = QVBoxLayout(dlg)
        label = QLabel("Chronopix\nPhoto Manager\nMade by Aureliano")
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)

        dlg.exec()
    def edit_undo(self):
        print("Undo not implemented yet")

    def edit_redo(self):
        print("Redo not implemented yet")
    def rebuild_thumbnails(self):
        from core.scanner import rebuild_all_thumbnails
        rebuild_all_thumbnails()
        self.timeline.reload()
        print("Thumbnails rebuilt")
    def clean_database(self):
        session = get_session()
        photos = session.exec(select(Photo)).all()

        removed = 0
        for p in photos:
            if not os.path.exists(p.path):
                session.delete(p)
                removed += 1

        session.commit()
        self.timeline.reload()
        print(f"Removed {removed} missing files")

    def export_favorites(self):
        from PySide6.QtWidgets import QFileDialog
        import shutil

        target = QFileDialog.getExistingDirectory(self, "Export Favorites")
        if not target:
            return

        session = get_session()
        photos = session.exec(select(Photo).where(Photo.favorite == True)).all()

        for p in photos:
            name = os.path.basename(p.path)
            shutil.copy2(p.path, os.path.join(target, name))

        print(f"Exported {len(photos)} favorites to {target}")
    def rebuild_exif_cache(self):


        session = get_session()
        photos = session.exec(select(Photo)).all()

        updated = 0
        for p in photos:
            try:
                new_date = extract_exif_date(p.path)
                if new_date:
                    p.exif_date = new_date
                    session.add(p)
                    updated += 1
            except Exception as e:
                print(f"EXIF error on {p.path}: {e}")

        session.commit()
        print(f"EXIF cache rebuilt for {updated} photos")

        self.timeline.reload()
    def find_duplicates_hash(self):

        session = get_session()
        photos = session.exec(select(Photo)).all()

        # Compute hash if missing
        for p in photos:
            if not p.hash:
                try:
                    with open(p.path, "rb") as f:
                        p.hash = hashlib.sha256(f.read()).hexdigest()
                    session.add(p)
                except Exception as e:
                    print(f"Hash error on {p.path}: {e}")

        session.commit()

        # Group by hash
        hash_map = {}
        for p in photos:
            hash_map.setdefault(p.hash, []).append(p)

        # Find duplicates
        duplicates = {h: items for h, items in hash_map.items() if len(items) > 1}

        if not duplicates:
            print("No duplicates found")
            return

        print("Duplicates found:")
        for h, items in duplicates.items():
            print(f"\nHash: {h}")
            for p in items:
                print(f" - {p.path}")

        # Optional: show a dialog
        dlg = QDialog(self)
        dlg.setWindowTitle("Duplicate Photos")
        dlg.resize(600, 400)

        layout = QVBoxLayout(dlg)
        label = QLabel("Duplicates found:")
        layout.addWidget(label)

        for h, items in duplicates.items():
            group_label = QLabel(f"<b>{h}</b>")
            layout.addWidget(group_label)
            for p in items:
                layout.addWidget(QLabel(p.path))

        dlg.exec()

    def clear_thumbnail_cache(self):

        session = get_session()
        photos = session.exec(select(Photo)).all()

        removed = 0
        for p in photos:
            if p.thumbnail_path and os.path.exists(p.thumbnail_path):
                try:
                    os.remove(p.thumbnail_path)
                    removed += 1
                except:
                    pass

            p.thumbnail_path = ""
            session.add(p)

        session.commit()

        print(f"Cleared {removed} thumbnails")
        self.timeline.reload()


    def show_settings(self):
        self.stack.setCurrentWidget(self.settings_page)
        

