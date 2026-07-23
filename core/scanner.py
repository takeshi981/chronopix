import os
from datetime import datetime
from sqlmodel import select
from PIL import Image, ExifTags
import imagehash
import ffmpeg
from core.database import get_session
from core.models import Photo
from core.thumbnails import ensure_thumb_dir, THUMB_DIR
from core.thumbnails import generate_thumbnail
from pillow_heif import register_heif_opener
register_heif_opener()


SUPPORTED_IMAGE_EXT = (".jpg", ".jpeg", ".png", ".gif", ".heic")
SUPPORTED_VIDEO_EXT = (".mp4", ".mov", ".mkv", ".webm")


def extract_exif_date(path: str) -> datetime:
    """Try to extract EXIF DateTimeOriginal. Fallback to file timestamp so it NEVER returns None."""
    try:
        img = Image.open(path)
        img.seek(0)
        exif = img.getexif()

        if exif:
            # Find EXIF tag for DateTimeOriginal
            for tag_id, value in exif.items():
                tag = ExifTags.TAGS.get(tag_id, tag_id)
                if tag == "DateTimeOriginal":
                    try:
                        return datetime.strptime(value, "%Y:%m:%d %H:%M:%S")
                    except Exception:
                        pass # Fallback below if parsing fails
    except Exception:
        pass

    # Safe Fallback: Use file modification time if EXIF doesn't exist or errors out
    return datetime.fromtimestamp(os.path.getmtime(path))


def scan_folder(folder: str):
    if not folder or not os.path.isdir(folder):
        print(f"[scanner] Invalid folder: {folder}")
        return

    print(f"[scanner] Scanning folder: {folder}")
    session = get_session()

    for root, _, files in os.walk(folder):
        # Create a quick-lookup set of all lowercase filenames in this specific directory
        # This prevents slow disk I/O checks during the loop
        files_in_dir = {f.lower() for f in files}

        for filename in files:
            path = os.path.join(root, filename)
            filename_lower = filename.lower()

            # Foto
            if filename_lower.endswith(SUPPORTED_IMAGE_EXT):
                process_image(path, files_in_dir, session)

            # Video
            elif filename_lower.endswith(SUPPORTED_VIDEO_EXT):
                process_video(path, session)


def process_image(path: str, files_in_dir: set, session):
    norm_path = normalize_path(path)
    
    dir_name = os.path.dirname(path)
    base_name, _ = os.path.splitext(os.path.basename(path))
    base_name_lower = base_name.lower()

    # Check if a matching video file exists in the current directory listing
    is_live_photo = False
    for ext in SUPPORTED_VIDEO_EXT:
        if f"{base_name_lower}{ext}" in files_in_dir:
            is_live_photo = True
            break

    # Check if the photo already exists in DB using the normalized path
    existing = session.exec(select(Photo).where(Photo.path == norm_path)).first()
    if not existing:
        # Extract date safely (guaranteed to return a datetime object)
        photo_date = extract_exif_date(path)

        photo = Photo(
            path=norm_path,
            thumbnail_path=generate_thumbnail(path), 
            created_at=photo_date,          
            exif_date=photo_date,
            is_video=False,
            is_live=is_live_photo  
        )
        session.add(photo)
        session.commit()


def process_video(path, session):
    norm = normalize_path(path)
    
    # 1. Check if this video path is already indexed in the DB
    exists = session.exec(select(Photo).where(Photo.path == norm)).first()
    if exists:
        return

    # 2. Check immediately if this video belongs to a Live Photo.
    base_name, _ = os.path.splitext(path)
    for ext in SUPPORTED_IMAGE_EXT:
        if os.path.exists(base_name + ext) or os.path.exists(base_name + ext.upper()):
            print(f"[scanner] Skipping standalone video import for Live Photo component: {path}")
            return

    # 3. If it's a standalone video, proceed with processing
    print("[scanner] VIDEO:", path)
    created = datetime.fromtimestamp(os.path.getmtime(path))
    
    thumb = generate_video_thumbnail(path) 
        
    photo = Photo(
        path=norm,
        created_at=created,
        exif_date=created,
        favorite=False,
        hash=None,
        thumbnail_path=thumb,
        is_video=True,
        is_live=False 
    )

    session.add(photo)
    session.commit()


def generate_video_thumbnail(src_path: str) -> str:
    ensure_thumb_dir()
    filename = os.path.basename(src_path) + ".jpg"
    dst_path = os.path.abspath(os.path.join(THUMB_DIR, filename))

    try:
        (
            ffmpeg
            .input(src_path, ss=1)  # frame at second 1
            .filter('scale', 512, -1)
            .output(dst_path, vframes=1)
            .run(quiet=True, overwrite_output=True)
        )
    except Exception as e:
        print(f"[scanner] Failed to generate video thumbnail for {src_path}: {e}")
        
    return dst_path


def generate_thumbnail(src_path: str) -> str:
    ensure_thumb_dir()
    filename = os.path.basename(src_path)
    dst_path = os.path.abspath(os.path.join(THUMB_DIR, filename + ".jpg"))

    img = Image.open(src_path)

    # GIF / PNG / HEIC fix
    if img.mode in ("P", "RGBA"):
        img = img.convert("RGB")

    img.thumbnail((512, 512))
    img.save(dst_path, "JPEG", quality=85)

    return dst_path


def normalize_path(path: str) -> str:
    return os.path.abspath(path).replace("\\", "/").lower()


def rebuild_all_thumbnails():
    session = get_session()
    photos = session.exec(select(Photo)).all()

    for p in photos:
        thumb = generate_thumbnail(p.path)
        p.thumbnail_path = thumb
        session.add(p)

    session.commit()


def check_if_live_by_filename(image_path: str) -> bool:
    base, _ = os.path.splitext(image_path)
    for ext in ['.mov', '.MOV', '.mp4', '.MP4']:
        if os.path.exists(base + ext):
            return True
    return False