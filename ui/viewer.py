from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QGraphicsView, QGraphicsScene, QPushButton, QWidget, QHBoxLayout, QSlider
from PySide6.QtGui import QPixmap, QWheelEvent, QMouseEvent, QTransform, QPainter
from PySide6.QtCore import Qt, QPointF
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtCore import QUrl
from PIL import Image
from PIL.ImageQt import ImageQt
import os
  
def load_pixmap(path):
    try:
        img = Image.open(path)
        img = img.convert("RGB")
        qimage = ImageQt(img)
        return QPixmap.fromImage(qimage)
    except Exception as e:
        print("HEIC load error:", e)
        return QPixmap(path)
    
class ImageViewer(QGraphicsView):
    def __init__(self, pixmap):
        super().__init__()

        self.setRenderHints(self.renderHints() |
                            QPainter.Antialiasing |
                            QPainter.SmoothPixmapTransform)

        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)

        # Scene
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)

        # Pixmap item
        self.pix_item = self.scene.addPixmap(pixmap)

        # Fit-to-window iniziale
        self.fitInView(self.pix_item, Qt.KeepAspectRatio)

    def resizeEvent(self, event):
        # Mantiene l’aspect ratio quando la finestra cambia dimensione
        self.fitInView(self.pix_item, Qt.KeepAspectRatio)
        super().resizeEvent(event)

    def wheelEvent(self, event):
        zoom_in_factor = 1.25
        zoom_out_factor = 1 / zoom_in_factor

        if event.angleDelta().y() > 0:
            zoom_factor = zoom_in_factor
        else:
            zoom_factor = zoom_out_factor

        # Zoom verso il punto del mouse
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.scale(zoom_factor, zoom_factor)


    # Pan con mouse drag (già gestito da ScrollHandDrag)
    def mousePressEvent(self, event: QMouseEvent):
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        super().mouseReleaseEvent(event)


class Viewer(QDialog):
    def __init__(self, photo):
        super().__init__()
        self.photo = photo

        self.setWindowTitle("Viewer")
        self.resize(1000, 800)

        layout = QVBoxLayout(self)

        # Detect Live Photo
        base = os.path.splitext(photo.path)[0]
        live_mov = base + ".MOV"
        self.live_mov_exists = os.path.exists(live_mov)

        if photo.is_video:
            self.show_video(photo.path, layout)

        else:
            pix = load_pixmap(photo.path)
            viewer = ImageViewer(pix)
            layout.addWidget(viewer)

            if self.live_mov_exists:
                btn = QPushButton("Play Live Photo")
                btn.clicked.connect(lambda: self.show_video(live_mov, layout))
                layout.addWidget(btn)

    def show_video(self, path, layout):
        # Remove previous widgets (image viewer or previous video)
        while layout.count():
            item = layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        # --- Video widget ---
        video_widget = QVideoWidget()
        video_widget.setMinimumSize(800, 600)
        layout.addWidget(video_widget)

        # --- Media player ---
        self.player = QMediaPlayer(self)
        self.player.setVideoOutput(video_widget)

        # Enable hardware decoding when available
        self.player.setPlaybackRate(1.0)

        # --- Audio ---
        self.audio = QAudioOutput(self)
        self.audio.setVolume(0.8)
        self.player.setAudioOutput(self.audio)

        # --- Load source AFTER binding outputs ---
        self.player.setSource(QUrl.fromLocalFile(path))

        # --- Controls ---
        controls = VideoControls(self.player, self.audio)
        layout.addWidget(controls)

        # Start playback only when ready
        self.player.mediaStatusChanged.connect(self._autoplay_when_ready)

    def _autoplay_when_ready(self, status):
        if status == QMediaPlayer.LoadedMedia:
            self.player.play()

class VideoControls(QWidget):
    def __init__(self, player, audio):
        super().__init__()
        self.player = player
        self.audio = audio

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Play/Pause
        self.play_btn = QPushButton("⏵")
        self.play_btn.clicked.connect(self.toggle_play)
        layout.addWidget(self.play_btn)

        # Seek bar
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(0, 0)
        self.slider.sliderMoved.connect(self.seek)
        layout.addWidget(self.slider)

        # Time label
        self.time_label = QLabel("00:00 / 00:00")
        layout.addWidget(self.time_label)

        # Volume
        self.volume = QSlider(Qt.Horizontal)
        self.volume.setRange(0, 100)
        self.volume.setValue(80)
        self.volume.valueChanged.connect(self.audio.setVolume)
        layout.addWidget(self.volume)

        # Signals
        player.positionChanged.connect(self.update_position)
        player.durationChanged.connect(self.update_duration)

    def toggle_play(self):
        if self.player.playbackState() == QMediaPlayer.PlayingState:
            self.player.pause()
            self.play_btn.setText("⏵")
        else:
            self.player.play()
            self.play_btn.setText("⏸")

    def seek(self, pos):
        self.player.setPosition(pos)

    def update_position(self, pos):
        self.slider.setValue(pos)
        self.update_time_label()

    def update_duration(self, dur):
        self.slider.setRange(0, dur)
        self.update_time_label()

    def update_time_label(self):
        pos = self.player.position() // 1000
        dur = self.player.duration() // 1000

        def fmt(t):
            m = t // 60
            s = t % 60
            return f"{m:02d}:{s:02d}"

        self.time_label.setText(f"{fmt(pos)} / {fmt(dur)}")
