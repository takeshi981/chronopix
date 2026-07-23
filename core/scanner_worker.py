from PySide6.QtCore import QObject, Signal
from core.database import get_session
from core.scanner import process_image, process_video, SUPPORTED_IMAGE_EXT, SUPPORTED_VIDEO_EXT
import os

class ScannerWorker(QObject):
    progress = Signal(int)
    finished = Signal()

    def __init__(self, folder):
        super().__init__()
        self.folder = folder

    def run(self):
        session = get_session()

        all_files = []
        # A dictionary mapping dir_path -> set(lowercase_filenames)
        dir_contents_map = {}

        # 1. Collect files and map directory contents simultaneously
        for root, _, files in os.walk(self.folder):
            # Store lowercase filenames for this specific folder context
            dir_contents_map[root] = {f.lower() for f in files}
            
            for f in files:
                all_files.append(os.path.join(root, f))

        total = len(all_files)
        if total == 0:
            self.finished.emit()
            return

        done = 0

        # 2. Process collected files
        for path in all_files:
            lower = path.lower()
            current_dir = os.path.dirname(path)
            
            # Fetch the pre-computed set of sibling files in the current folder
            files_in_dir = dir_contents_map.get(current_dir, set())

            if lower.endswith(SUPPORTED_IMAGE_EXT):
                # Pass files_in_dir down to your updated process_image logic
                process_image(path, files_in_dir, session)
                
            elif lower.endswith(SUPPORTED_VIDEO_EXT):
                process_video(path, session)

            done += 1
            pct = int((done / total) * 100)
            self.progress.emit(pct)

        self.finished.emit()
