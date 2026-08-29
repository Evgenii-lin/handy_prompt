"""Window for adding a new prompt (with optional AI generation)."""
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTextEdit, QPushButton, QProgressBar, QMessageBox,
)

from database import PromptDatabase
from worker import LlamaWorker


class AddPromptWindow(QMainWindow):
    def __init__(self, parent=None, db: PromptDatabase = None):
        super().__init__()
        self.setWindowTitle("Add New Prompt")
        self.resize(800, 720)
        self.parent_window = parent
        self.db = db or PromptDatabase()
        self.worker: LlamaWorker | None = None
        self._build_ui()

    # ------------------------------------------------------------------
    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        lbl = QLabel("Enter Prompt Name")
        lbl.setObjectName("field_label")
        layout.addWidget(lbl)

        self.name_field = QTextEdit()
        self.name_field.setObjectName("input_field")
        self.name_field.setPlaceholderText("Enter prompt name")
        self.name_field.setMaximumHeight(60)
        layout.addWidget(self.name_field)

        lbl2 = QLabel("Keywords for AI generation")
        lbl2.setObjectName("field_label")
        layout.addWidget(lbl2)

        self.keywords_field = QTextEdit()
        self.keywords_field.setObjectName("input_field")
        self.keywords_field.setPlaceholderText("Enter keywords...")
        self.keywords_field.setMaximumHeight(100)
        layout.addWidget(self.keywords_field)

        self.gen_btn = QPushButton("Generate Prompt")
        self.gen_btn.setObjectName("gen_button")
        self.gen_btn.clicked.connect(self._start_generation)
        layout.addWidget(self.gen_btn)

        self.progress = QProgressBar()
        self.progress.setVisible(False)
        layout.addWidget(self.progress)

        lbl3 = QLabel("Generated Prompt Content")
        lbl3.setObjectName("field_label")
        layout.addWidget(lbl3)

        self.output = QTextEdit()
        self.output.setObjectName("output_display")
        self.output.setPlaceholderText("Generated prompt appears here...")
        layout.addWidget(self.output)

        btn_row = QHBoxLayout()
        self.save_btn = QPushButton("Save Prompt")
        self.save_btn.setObjectName("add_button")
        self.save_btn.clicked.connect(self._save)

        self.back_btn = QPushButton("Back")
        self.back_btn.setObjectName("back_button")
        self.back_btn.clicked.connect(self.close)

        btn_row.addWidget(self.save_btn)
        btn_row.addWidget(self.back_btn)
        layout.addLayout(btn_row)

    # ------------------------------------------------------------------
    def _start_generation(self):
        prompt = self.keywords_field.toPlainText().strip()
        if not prompt:
            return

        self.output.append("<b>Generated Prompt:</b><br>")
        self.gen_btn.setEnabled(False)
        self.progress.setValue(0)
        self.progress.setVisible(True)

        self.worker = LlamaWorker(prompt)
        self.worker.token_generated.connect(self._on_token)
        self.worker.finished_generation.connect(self._on_finished)
        self.worker.error_occurred.connect(self._on_error)
        self.worker.progress_changed.connect(self.progress.setValue)
        self.worker.start()

    def _on_token(self, token: str):
        if token:
            cur = self.output.textCursor()
            cur.movePosition(cur.MoveOperation.End)
            cur.insertText(token)
            self.output.verticalScrollBar().setValue(
                self.output.verticalScrollBar().maximum()
            )

    def _on_finished(self):
        self.gen_btn.setEnabled(True)
        self.progress.setVisible(False)

    def _on_error(self, msg: str):
        self.gen_btn.setEnabled(True)
        self.progress.setVisible(False)
        self.output.append(f"<font color='red'>Error: {msg}</font>")

    # ------------------------------------------------------------------
    def _save(self):
        name = self.name_field.toPlainText().strip()
        content = self.output.toPlainText().strip()
        if not name:
            QMessageBox.warning(self, "Warning", "Prompt name is required.")
            return
        try:
            self.db.insert_prompt(name, content)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Save failed: {e}")
            return
        QMessageBox.information(self, "Success", "Prompt saved!")
        if self.parent_window:
            self.parent_window.refresh_combo(name)
        self.close()

    def closeEvent(self, event):
        if self.parent_window is None:
            self.db.close()
        event.accept()
