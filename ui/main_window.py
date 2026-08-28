"""Main application window – prompt browser and toolbar."""
from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QComboBox, QVBoxLayout, QWidget,
    QLabel, QTextEdit, QPushButton, QHBoxLayout, QMessageBox, QFileDialog,
)
from PyQt6.QtGui import QIcon

from database import PromptDatabase
from ui.add_prompt import AddPromptWindow
from ui.edit_prompt import EditPromptWindow


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Handy Prompt")
        self.resize(1280, 720)
        self.current_choice = ""
        self.db = PromptDatabase()

        self._set_icon()
        self._init_ui()

    # ------------------------------------------------------------------
    # Icon
    # ------------------------------------------------------------------
    def _set_icon(self):
        icon_path = Path(__file__).parent.parent / "assets" / "icon.png"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------
    def _init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)

        # -- Top bar --
        top = QWidget()
        top_layout = QHBoxLayout(top)
        std_h = 55

        self.combo = QComboBox()
        self.combo.setMinimumWidth(200)
        self.combo.setFixedHeight(std_h)
        top_layout.addWidget(self.combo)

        self.label = QLabel("")
        self.label.setObjectName("status_label")
        top_layout.addWidget(self.label)

        self.about_btn = QPushButton("About")
        self.about_btn.setFixedHeight(std_h)
        self.about_btn.clicked.connect(self._show_about)
        top_layout.addWidget(self.about_btn)

        top_layout.addStretch()

        self.copy_btn = QPushButton("Copy"); self.copy_btn.setObjectName("copy_button")
        self.add_btn = QPushButton("Add New Prompt"); self.add_btn.setObjectName("add_button")
        self.save_btn = QPushButton("Save"); self.save_btn.setObjectName("save_button")
        self.edit_btn = QPushButton("Edit"); self.edit_btn.setObjectName("edit_button")
        self.del_btn = QPushButton("Delete"); self.del_btn.setObjectName("del_button")

        self.add_btn.clicked.connect(self._open_add)
        self.save_btn.clicked.connect(self._save_to_file)
        self.copy_btn.clicked.connect(self._copy_to_clipboard)
        self.edit_btn.clicked.connect(self._open_edit)
        self.del_btn.clicked.connect(self._delete_prompt)

        top_layout.addWidget(self.copy_btn)
        top_layout.addWidget(self.add_btn)
        self.save_btn.setFixedHeight(std_h)
        top_layout.addWidget(self.save_btn)
        top_layout.addWidget(self.edit_btn)
        top_layout.addWidget(self.del_btn)

        layout.addWidget(top)

        # -- Display --
        self.chat_display = QTextEdit()
        self.chat_display.setObjectName("output_display")
        self.chat_display.setReadOnly(True)
        self.chat_display.setPlaceholderText("Select a prompt to view its content...")
        layout.addWidget(self.chat_display)
        layout.setStretchFactor(self.chat_display, 1)

        # -- Signals --
        self.combo.currentIndexChanged.connect(self._on_combo_change)
        self._load_prompts()

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------
    def _on_combo_change(self, _index: int):
        name = self.combo.currentText()
        self.current_choice = name
        self.label.setText(f"Selected: {name}")
        content = self.db.get_content(name)
        self.chat_display.setText(content or "")

    def _open_add(self):
        self._child = AddPromptWindow(parent=self, db=self.db)
        self._child.show()

    def _open_edit(self):
        if not self.current_choice:
            QMessageBox.warning(self, "Warning", "Please select a prompt first.")
            return
        self._child = EditPromptWindow(choice=self.current_choice, parent=self, db=self.db)
        self._child.show()

    def _save_to_file(self):
        if not self.current_choice:
            QMessageBox.warning(self, "Warning", "Please select a prompt first.")
            return
        content = self.db.get_content(self.current_choice)
        if not content:
            QMessageBox.warning(self, "Warning", "No content to save.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Prompt", f"{self.current_choice}.txt",
            "Text Files (*.txt);;All Files (*)",
        )
        if path:
            Path(path).write_text(content, encoding="utf-8")
            QMessageBox.information(self, "Success", f"Saved to {path}")

    def _copy_to_clipboard(self):
        if not self.current_choice:
            QMessageBox.warning(self, "Warning", "Please select a prompt first.")
            return
        content = self.db.get_content(self.current_choice)
        if not content:
            QMessageBox.warning(self, "Warning", "No content to copy.")
            return
        QApplication.clipboard().setText(content)
        QMessageBox.information(self, "Success", "Copied to clipboard!")

    def _delete_prompt(self):
        if not self.current_choice:
            QMessageBox.warning(self, "Warning", "Please select a prompt first.")
            return
        reply = QMessageBox.question(
            self, "Confirm", f'Delete "{self.current_choice}"?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.db.delete_prompt(self.current_choice)
            idx = self.combo.findText(self.current_choice)
            if idx != -1:
                self.combo.removeItem(idx)
            self.chat_display.clear()
            self.label.setText("Deleted")
            self.current_choice = ""
            QMessageBox.information(self, "Success", "Prompt deleted.")

    def _show_about(self):
        text = (
            "<h3>Handy Prompt</h3>"
            "<p><b>Version:</b> 1.0.0</p>"
            "<p>AI prompt manager</p>"
            "<p><b>Author:</b> Evgenii Savenkov</p>"
            "<p><b>License:</b> MIT</p>"
        )
        QMessageBox.about(self, "About", text)

    # ------------------------------------------------------------------
    # Helpers called by child windows
    # ------------------------------------------------------------------
    def refresh_combo(self, new_name: str):
        if self.combo.findText(new_name) == -1:
            self.combo.addItem(new_name)

    def rename_combo_item(self, old: str, new: str):
        idx = self.combo.findText(old)
        if idx != -1:
            self.combo.removeItem(idx)
        self.combo.addItem(new)
        self.combo.setCurrentText(new)
        self.current_choice = new

    def _load_prompts(self):
        self.combo.clear()
        for name in self.db.get_all_prompt_names():
            self.combo.addItem(name)
