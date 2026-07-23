from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
import weakref

class ThemeManager:
    current_theme = "light"
    # Use weak references so widgets can be garbage collected when closed
    _listeners = []

    @classmethod
    def register_widget(cls, widget):
        """Allows a widget to subscribe to theme change notifications."""
        cls._listeners.append(weakref.ref(widget))

    @classmethod
    def notify_listeners(cls):
        """Triggers icon refreshes on all alive registered widgets."""
        active_listeners = []
        for ref in cls._listeners:
            widget = ref()
            if widget is not None:
                active_listeners.append(ref)
                # Safeguard check to ensure the widget has the method
                if hasattr(widget, "refresh_icons"):
                    widget.refresh_icons()
        cls._listeners = active_listeners


def themed_icon(name: str) -> QIcon:
    path = f"assets/icons/{ThemeManager.current_theme}/{name}"
    return QIcon(path)


def apply_theme(theme_name: str, qss_path: str):
    # Standardize to lowercase for asset paths
    ThemeManager.current_theme = theme_name.lower() 

    app = QApplication.instance()
    if app:
        with open(qss_path, "r") as f:
            app.setStyleSheet(f.read())

    ThemeManager.notify_listeners()