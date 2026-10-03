#!/usr/bin/env python3
"""
Color Inverter - Desktop Application
Drag-and-drop image color inverter built with PyQt6 and Pillow.
"""

import sys
import os
import io
from typing import Optional

from PIL import Image, ImageOps
from PyQt6.QtCore import Qt, QSize, QTimer
from PyQt6.QtGui import (
    QAction,
    QColor,
    QDragEnterEvent,
    QDropEvent,
    QIcon,
    QImage,
    QKeySequence,
    QPainter,
    QPaintEvent,
    QPixmap,
)
from PyQt6.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)


def pil_to_qpixmap(pil_img: Image.Image) -> QPixmap:
    """Converts a PIL Image to a QPixmap via memory buffer for robustness."""
    buffer = io.BytesIO()
    # Save as PNG to preserve all color depths and alpha channel
    pil_img.save(buffer, format="PNG")
    pixmap = QPixmap()
    pixmap.loadFromData(buffer.getvalue(), "PNG")
    return pixmap


def qimage_to_pil(qimg: QImage) -> Image.Image:
    """Converts a QImage to a PIL Image."""
    buffer = io.BytesIO()
    qimg.save(buffer, "PNG")
    buffer.seek(0)
    return Image.open(buffer).convert("RGBA")


def invert_colors(img: Image.Image) -> Image.Image:
    """
    Inverts colors while preserving alpha (transparency) channels.
    Supports RGBA, RGB, Grayscale (L), Grayscale+Alpha (LA), and Palette (P).
    """
    if img.mode == "RGBA":
        r, g, b, a = img.split()
        return Image.merge("RGBA", (ImageOps.invert(r), ImageOps.invert(g), ImageOps.invert(b), a))
    elif img.mode == "LA":
        l, a = img.split()
        return Image.merge("LA", (ImageOps.invert(l), a))
    elif img.mode == "RGB":
        return ImageOps.invert(img)
    elif img.mode == "L":
        return ImageOps.invert(img)
    elif img.mode == "1":
        # 1-bit monochrome
        return ImageOps.invert(img.convert("L"))
    else:
        # Palette or other formats: convert based on transparency presence
        if "transparency" in img.info or img.mode == "P":
            rgba = img.convert("RGBA")
            r, g, b, a = rgba.split()
            return Image.merge("RGBA", (ImageOps.invert(r), ImageOps.invert(g), ImageOps.invert(b), a))
        else:
            return ImageOps.invert(img.convert("RGB"))


class CheckerboardWidget(QWidget):
    """Widget that renders a subtle checkerboard pattern for transparent regions."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.tile_size = 14
        self.color1 = QColor(36, 40, 48)
        self.color2 = QColor(48, 54, 64)

    def paintEvent(self, event: QPaintEvent):
        painter = QPainter(self)
        rect = self.rect()
        for x in range(0, rect.width(), self.tile_size):
            for y in range(0, rect.height(), self.tile_size):
                is_even = ((x // self.tile_size) + (y // self.tile_size)) % 2 == 0
                painter.fillRect(
                    x,
                    y,
                    self.tile_size,
                    self.tile_size,
                    self.color1 if is_even else self.color2,
                )


class ImageDisplayArea(QWidget):
    """Central interactive area supporting drag-and-drop, display, and click-to-open."""

    def __init__(self, parent_window: "MainWindow"):
        super().__init__(parent_window)
        self.parent_window = parent_window
        self.setAcceptDrops(True)
        self.setMinimumSize(420, 360)

        # Layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        # Background checkerboard
        self.checkerboard = CheckerboardWidget(self)
        self.checkerboard.lower()

        # Image display label
        self.image_label = QLabel(self)
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setScaledContents(False)
        self.layout.addWidget(self.image_label)

        # Empty state prompt label
        self.placeholder_label = QLabel(
            "<b>Drag & Drop Image Here</b><br><br>"
            "<span style='color: #8c9ba5;'>or click to browse from computer</span><br>"
            "<span style='font-size: 11px; color: #62727e;'>Supports PNG, JPG, WebP, BMP, GIF • Paste with Ctrl+V</span>",
            self,
        )
        self.placeholder_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.placeholder_label.setStyleSheet(
            "QLabel {"
            "  color: #d1d5db;"
            "  font-size: 15px;"
            "  border: 2px dashed #4b5563;"
            "  border-radius: 12px;"
            "  background-color: rgba(31, 41, 55, 0.7);"
            "  padding: 24px;"
            "}"
            "QLabel:hover {"
            "  border-color: #60a5fa;"
            "  background-color: rgba(37, 49, 66, 0.85);"
            "}"
        )
        self.layout.addWidget(self.placeholder_label)

        self.current_pixmap: Optional[QPixmap] = None
        self.update_state()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.checkerboard.setGeometry(self.rect())
        if self.current_pixmap and not self.current_pixmap.isNull():
            self._render_scaled_image()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and not self.current_pixmap:
            self.parent_window.open_file_dialog()

    def set_display_pixmap(self, pixmap: Optional[QPixmap]):
        self.current_pixmap = pixmap
        self.update_state()

    def update_state(self):
        if self.current_pixmap and not self.current_pixmap.isNull():
            self.placeholder_label.hide()
            self.image_label.show()
            self.checkerboard.show()
            self._render_scaled_image()
        else:
            self.image_label.clear()
            self.image_label.hide()
            self.checkerboard.hide()
            self.placeholder_label.show()

    def _render_scaled_image(self):
        if not self.current_pixmap or self.current_pixmap.isNull():
            return
        target_size = self.size() - QSize(20, 20)
        if target_size.width() <= 0 or target_size.height() <= 0:
            return
        scaled = self.current_pixmap.scaled(
            target_size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.image_label.setPixmap(scaled)

    # Drag and Drop handlers
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls() or event.mimeData().hasImage():
            event.acceptProposedAction()
            self.setStyleSheet("border: 2px solid #3b82f6; border-radius: 8px;")
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        self.setStyleSheet("")
        event.accept()

    def dropEvent(self, event: QDropEvent):
        self.setStyleSheet("")
        mime = event.mimeData()

        if mime.hasUrls():
            urls = mime.urls()
            if urls:
                file_path = urls[0].toLocalFile()
                if file_path and os.path.isfile(file_path):
                    self.parent_window.load_image_from_path(file_path)
                    event.acceptProposedAction()
                    return

        if mime.hasImage():
            qimg = mime.imageData()
            if isinstance(qimg, QImage) and not qimg.isNull():
                pil_img = qimage_to_pil(qimg)
                self.parent_window.set_loaded_image(pil_img, source_name="Dropped Image")
                event.acceptProposedAction()
                return

        event.ignore()


class MainWindow(QMainWindow):
    """Main Application Window."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Color Inverter")
        self.resize(860, 680)

        # Image state
        self.original_image: Optional[Image.Image] = None
        self.inverted_image: Optional[Image.Image] = None
        self.original_pixmap: Optional[QPixmap] = None
        self.inverted_pixmap: Optional[QPixmap] = None
        self.source_path: Optional[str] = None
        self.is_showing_inverted = True

        self._setup_ui()
        self._setup_shortcuts()
        self._apply_dark_theme()

    def _setup_ui(self):
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(16, 16, 16, 12)
        main_layout.setSpacing(12)

        # Interactive display & drop area
        self.display_area = ImageDisplayArea(self)
        main_layout.addWidget(self.display_area, stretch=1)

        # Bottom control bar
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(10)

        # View Toggle (Original / Inverted)
        self.toggle_view_btn = QPushButton("Show Original (Space)")
        self.toggle_view_btn.setEnabled(False)
        self.toggle_view_btn.clicked.connect(self.toggle_view)
        controls_layout.addWidget(self.toggle_view_btn)

        controls_layout.addStretch()

        # Open button
        self.open_btn = QPushButton("Open Image...")
        self.open_btn.clicked.connect(self.open_file_dialog)
        controls_layout.addWidget(self.open_btn)

        # Copy button
        self.copy_btn = QPushButton("Copy Inverted (Ctrl+C)")
        self.copy_btn.setEnabled(False)
        self.copy_btn.setStyleSheet(
            "QPushButton:enabled { background-color: #2563eb; color: white; font-weight: bold; }"
            "QPushButton:enabled:hover { background-color: #1d4ed8; }"
        )
        self.copy_btn.clicked.connect(self.copy_to_clipboard)
        controls_layout.addWidget(self.copy_btn)

        # Save button
        self.save_btn = QPushButton("Save As... (Ctrl+S)")
        self.save_btn.setEnabled(False)
        self.save_btn.clicked.connect(self.save_image_dialog)
        controls_layout.addWidget(self.save_btn)

        # Clear button
        self.clear_btn = QPushButton("Clear")
        self.clear_btn.setEnabled(False)
        self.clear_btn.clicked.connect(self.clear_image)
        controls_layout.addWidget(self.clear_btn)

        main_layout.addLayout(controls_layout)

        # Status Bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready. Drag and drop an image or press Ctrl+V to paste.")

    def _setup_shortcuts(self):
        # Open: Ctrl+O
        open_action = QAction(self)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.triggered.connect(self.open_file_dialog)
        self.addAction(open_action)

        # Copy: Ctrl+C
        copy_action = QAction(self)
        copy_action.setShortcut(QKeySequence.StandardKey.Copy)
        copy_action.triggered.connect(self.copy_to_clipboard)
        self.addAction(copy_action)

        # Save: Ctrl+S
        save_action = QAction(self)
        save_action.setShortcut(QKeySequence.StandardKey.Save)
        save_action.triggered.connect(self.save_image_dialog)
        self.addAction(save_action)

        # Paste: Ctrl+V
        paste_action = QAction(self)
        paste_action.setShortcut(QKeySequence.StandardKey.Paste)
        paste_action.triggered.connect(self.paste_from_clipboard)
        self.addAction(paste_action)

        # Toggle view: Space
        toggle_action = QAction(self)
        toggle_action.setShortcut(Qt.Key.Key_Space)
        toggle_action.triggered.connect(self.toggle_view)
        self.addAction(toggle_action)

    def _apply_dark_theme(self):
        self.setStyleSheet(
            """
            QMainWindow {
                background-color: #111827;
            }
            QWidget {
                color: #e5e7eb;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                font-size: 13px;
            }
            QPushButton {
                background-color: #374151;
                border: 1px solid #4b5563;
                border-radius: 6px;
                padding: 7px 16px;
                color: #f9fafb;
            }
            QPushButton:hover {
                background-color: #4b5563;
            }
            QPushButton:pressed {
                background-color: #1f2937;
            }
            QPushButton:disabled {
                background-color: #1f2937;
                color: #6b7280;
                border-color: #374151;
            }
            QStatusBar {
                background-color: #0f172a;
                color: #9ca3af;
                border-top: 1px solid #1f2937;
            }
            """
        )

    def open_file_dialog(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Image",
            "",
            "Images (*.png *.jpg *.jpeg *.webp *.bmp *.gif *.tiff);;All Files (*)",
        )
        if file_path:
            self.load_image_from_path(file_path)

    def load_image_from_path(self, path: str):
        try:
            pil_img = Image.open(path)
            # Fully load image data to allow closing the file descriptor safely
            pil_img.load()
            self.source_path = path
            self.set_loaded_image(pil_img, source_name=os.path.basename(path))
        except Exception as e:
            QMessageBox.critical(self, "Error Loading Image", f"Failed to load image:\n{e}")
            self.status_bar.showMessage(f"Error loading {os.path.basename(path)}", 4000)

    def paste_from_clipboard(self):
        clipboard = QApplication.clipboard()
        mime = clipboard.mimeData()

        # Check for image content in clipboard
        if mime.hasImage():
            qimg = clipboard.image()
            if not qimg.isNull():
                pil_img = qimage_to_pil(qimg)
                self.source_path = None
                self.set_loaded_image(pil_img, source_name="Pasted Image")
                self.status_bar.showMessage("Image pasted from clipboard.", 3000)
                return

        # Check for copied file paths
        if mime.hasUrls():
            urls = mime.urls()
            if urls:
                file_path = urls[0].toLocalFile()
                if file_path and os.path.isfile(file_path):
                    self.load_image_from_path(file_path)
                    return

        self.status_bar.showMessage("No image found in clipboard.", 3000)

    def set_loaded_image(self, pil_img: Image.Image, source_name: str = ""):
        self.original_image = pil_img
        try:
            self.inverted_image = invert_colors(pil_img)
        except Exception as e:
            QMessageBox.critical(self, "Inversion Error", f"Failed to invert image colors:\n{e}")
            return

        self.original_pixmap = pil_to_qpixmap(self.original_image)
        self.inverted_pixmap = pil_to_qpixmap(self.inverted_image)

        # Default to showing inverted
        self.is_showing_inverted = True
        self.toggle_view_btn.setText("Show Original (Space)")
        self.display_area.set_display_pixmap(self.inverted_pixmap)

        # Enable action buttons
        self.toggle_view_btn.setEnabled(True)
        self.copy_btn.setEnabled(True)
        self.save_btn.setEnabled(True)
        self.clear_btn.setEnabled(True)

        # Window title & status
        w, h = pil_img.size
        has_alpha = "Alpha" if pil_img.mode in ("RGBA", "LA") or ("transparency" in pil_img.info) else "Opaque"
        name_info = source_name if source_name else "Image"
        self.setWindowTitle(f"Color Inverter - {name_info} ({w}×{h})")
        self.status_bar.showMessage(
            f"Loaded {name_info} | {w}×{h} px | Mode: {pil_img.mode} ({has_alpha} preserved) | Inverted successfully.",
            5000,
        )

    def toggle_view(self):
        if not self.original_pixmap or not self.inverted_pixmap:
            return

        self.is_showing_inverted = not self.is_showing_inverted
        if self.is_showing_inverted:
            self.display_area.set_display_pixmap(self.inverted_pixmap)
            self.toggle_view_btn.setText("Show Original (Space)")
            self.status_bar.showMessage("Viewing Inverted image.", 2000)
        else:
            self.display_area.set_display_pixmap(self.original_pixmap)
            self.toggle_view_btn.setText("Show Inverted (Space)")
            self.status_bar.showMessage("Viewing Original image.", 2000)

    def copy_to_clipboard(self):
        if not self.inverted_image:
            return

        clipboard = QApplication.clipboard()
        # Convert inverted PIL image directly to QImage to set in clipboard
        buffer = io.BytesIO()
        self.inverted_image.save(buffer, format="PNG")
        qimg = QImage()
        qimg.loadFromData(buffer.getvalue(), "PNG")

        clipboard.setImage(qimg)
        self.status_bar.showMessage("Inverted image copied to clipboard!", 3500)

        # Temporary button text feedback
        original_btn_text = self.copy_btn.text()
        self.copy_btn.setText("Copied!")
        QTimer.singleShot(1500, lambda: self.copy_btn.setText(original_btn_text))

    def save_image_dialog(self):
        if not self.inverted_image:
            return

        default_dir = os.path.dirname(self.source_path) if self.source_path else ""
        if self.source_path:
            base, ext = os.path.splitext(os.path.basename(self.source_path))
            default_name = f"{base}_inverted{ext if ext else '.png'}"
        else:
            default_name = "inverted_image.png"

        default_path = os.path.join(default_dir, default_name)

        save_path, selected_filter = QFileDialog.getSaveFileName(
            self,
            "Save Inverted Image",
            default_path,
            "PNG (*.png);;JPEG (*.jpg *.jpeg);;WebP (*.webp);;BMP (*.bmp);;All Files (*)",
        )

        if not save_path:
            return

        try:
            # Handle format specifics (e.g. JPEG doesn't support RGBA)
            out_img = self.inverted_image
            ext = os.path.splitext(save_path)[1].lower()
            if ext in (".jpg", ".jpeg") and out_img.mode in ("RGBA", "LA"):
                # Blend with white background if saving transparent image as JPEG
                background = Image.new("RGB", out_img.size, (255, 255, 255))
                if out_img.mode == "RGBA":
                    background.paste(out_img, mask=out_img.split()[3])
                else:
                    background.paste(out_img, mask=out_img.split()[1])
                out_img = background

            out_img.save(save_path)
            self.status_bar.showMessage(f"Saved: {os.path.basename(save_path)}", 4000)
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Failed to save image:\n{e}")

    def clear_image(self):
        self.original_image = None
        self.inverted_image = None
        self.original_pixmap = None
        self.inverted_pixmap = None
        self.source_path = None
        self.is_showing_inverted = True

        self.display_area.set_display_pixmap(None)
        self.toggle_view_btn.setEnabled(False)
        self.toggle_view_btn.setText("Show Original (Space)")
        self.copy_btn.setEnabled(False)
        self.save_btn.setEnabled(False)
        self.clear_btn.setEnabled(False)
        self.setWindowTitle("Color Inverter")
        self.status_bar.showMessage("Cleared. Ready for next image.", 3000)


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Color Inverter")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
