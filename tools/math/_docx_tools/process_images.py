"""
Process all images for the paper:
1. Auto-crop excessive white margins
2. Downscale oversized images
3. Add thin black border (ref paper style)
4. Save as clean RGB PNG
"""
from PIL import Image, ImageOps
import os, shutil

MEDIA_DIR = r"d:\GIT\public\数模\_unpacked_论文1.5\word\media"
OUTPUT_DIR = r"d:\GIT\public\数模\_unpacked_论文1.5\word\media"
BACKUP_DIR = r"d:\GIT\public\数模\_docx_tools\media_backup"

# Backup originals
if not os.path.exists(BACKUP_DIR):
    os.makedirs(BACKUP_DIR)
    for f in os.listdir(MEDIA_DIR):
        shutil.copy2(os.path.join(MEDIA_DIR, f), os.path.join(BACKUP_DIR, f))
    print(f"Backed up {len(os.listdir(MEDIA_DIR))} images to {BACKUP_DIR}")

# Process each image
WHITE_THRESHOLD = 240  # pixels above this are considered white
TARGET_MAX_WIDTH = 1400  # max pixel width for very large images
BORDER_PX = 1  # border width in pixels

processed = []
for fname in sorted(os.listdir(MEDIA_DIR)):
    if not fname.lower().endswith(('.png', '.jpg', '.jpeg')):
        continue

    path = os.path.join(MEDIA_DIR, fname)
    img = Image.open(path)

    # Convert to RGB
    if img.mode == 'RGBA':
        # Create white background
        bg = Image.new('RGB', img.size, (255, 255, 255))
        bg.paste(img, mask=img.split()[3])
        img = bg
    elif img.mode != 'RGB':
        img = img.convert('RGB')

    orig_size = img.size

    # Step 1: Auto-crop white margins
    # Find content bounds more aggressively
    w, h = img.size
    pixels = img.load()

    def has_content_row(y, step=2):
        for x in range(0, w, step):
            r, g, b = pixels[x, y]
            if r < WHITE_THRESHOLD or g < WHITE_THRESHOLD or b < WHITE_THRESHOLD:
                return True
        return False

    def has_content_col(x, step=2):
        for y in range(0, h, step):
            r, g, b = pixels[x, y]
            if r < WHITE_THRESHOLD or g < WHITE_THRESHOLD or b < WHITE_THRESHOLD:
                return True
        return False

    # Find content boundaries
    top = 0
    for y in range(h):
        if has_content_row(y):
            top = y
            break

    bottom = h - 1
    for y in range(h - 1, -1, -1):
        if has_content_row(y):
            bottom = y
            break

    left = 0
    for x in range(w):
        if has_content_col(x):
            left = x
            break

    right = w - 1
    for x in range(w - 1, -1, -1):
        if has_content_col(x):
            right = x
            break

    # Add a small padding (5px) after crop to prevent tight cutting
    pad = 5
    top = max(0, top - pad)
    bottom = min(h - 1, bottom + pad)
    left = max(0, left - pad)
    right = min(w - 1, right + pad)

    cropped = img.crop((left, top, right + 1, bottom + 1))
    crop_waste = 100 * (1 - cropped.size[0] * cropped.size[1] / (w * h))

    # Step 2: Downscale if oversized
    cw, ch = cropped.size
    if cw > TARGET_MAX_WIDTH:
        ratio = TARGET_MAX_WIDTH / cw
        new_w = TARGET_MAX_WIDTH
        new_h = int(ch * ratio)
        cropped = cropped.resize((new_w, new_h), Image.LANCZOS)

    # Step 3: Add thin black border
    bordered = ImageOps.expand(cropped, border=BORDER_PX, fill=(0, 0, 0))

    # Step 4: Save as PNG
    bordered.save(path, 'PNG')

    new_size = bordered.size
    file_size_kb = os.path.getsize(path) // 1024
    issues = []
    if crop_waste > 5:
        issues.append(f"裁剪{crop_waste:.0f}%空白")
    if orig_size[0] > TARGET_MAX_WIDTH:
        issues.append(f"从{orig_size[0]}px缩放")
    if issues:
        issue_str = "; ".join(issues)
    else:
        issue_str = "微调"

    print(f"  {fname}: {orig_size} -> {new_size} {file_size_kb}KB [{issue_str}]")
    processed.append(fname)

print(f"\nProcessed {len(processed)} images.")
print(f"Original backups in: {BACKUP_DIR}")
