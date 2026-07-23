import sys
import time # Opzionale: solo se vuoi forzare una durata minima
from PySide6.QtWidgets import QApplication, QSplashScreen
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt
from ui.main_window import MainWindow
from core.database import init_db
if __name__ == "__main__":
    app = QApplication(sys.argv)
    init_db()
    # 1. CREA LO SPLASH SCREEN
    # Sostituisci "assets/splash.png" con il percorso di una tua immagine
    pixmap = QPixmap("assets/splash.png") 
    splash = QSplashScreen(pixmap, Qt.WindowStaysOnTopHint)
    
    # Mostra un messaggio di testo sopra l'immagine (opzionale)
    splash.showMessage("Caricamento di Chronopix...", Qt.AlignBottom | Qt.AlignCenter, Qt.white)
    splash.show()
    
    # Permette a Qt di processare i primi eventi grafici e mostrare lo splash
    app.processEvents()

    # 2. INIZIALIZZA LA FINESTRA PRINCIPALE
    # Durante questa fase, la MainWindow leggerà il database e caricherà i temi
    window = MainWindow()

    # Opzionale: se il caricamento è troppo veloce e vuoi far vedere lo splash per almeno 2 secondi
    # time.sleep(2) 

    # 3. MOSTRA LA FINESTRA E CHIUDI LO SPLASH SCREEN
    window.show()
    
    # Questo comando fa scomparire lo splash screen AUTOMATICAMENTE 
    # nel momento esatto in cui la finestra principale viene disegnata a schermo
    splash.finish(window)

    sys.exit(app.exec())