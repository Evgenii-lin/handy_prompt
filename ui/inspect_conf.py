import sys
import requests

from pathlib import Path

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QComboBox, QVBoxLayout, QWidget,
    QLabel, QTextEdit, QPushButton, QHBoxLayout, QMessageBox, QFileDialog, QProgressBar,
)
from PySide6.QtCore import QThread, Signal


OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL_14B = "qwen2.5:14b"


DEEP_INSPECT_PROMPT = """
You are a senior infrastructure auditor with deep expertise across
Cisco IOS/NX-OS, Linux networking (iptables/nftables, iproute2),
Docker/container orchestration, nginx/Apache, and systemd.

Analyze the configuration below. Every non-empty line or logical
block gets its own entry. Skip nothing.

==========================================================
## PER-LINE ANALYSIS
==========================================================

For each line or block in the input, output exactly this structure:

---
**Line <N>:** `<exact text from config>`

**Does:**
2–4 sentences explaining what this line does technically.
Not just "permits TCP" — explain the mechanism:
what the parameters mean, what the mask/wildcard covers,
what protocol/port implies, how this interacts with the
surrounding context.
Write for a junior engineer who knows networking basics
but has never seen this specific syntax.
If the line belongs to a block (ACL, server block, service
unit, compose service), briefly state what that block is
for before explaining the line within it.

**Risk:**
CRITICAL / HIGH / MEDIUM / LOW / OK
Followed by: what can go wrong, what is missing,
what dependency this line has on another line.
If the line is correct and complete, write "OK — no issues."
If you are not certain, prefix the concern with "Possible:"
Do NOT invent problems. If it is fine, say it is fine.

**Fix:**
Exact replacement line, missing companion line,
or "OK."
One or two concrete lines of config. Not a paragraph.
If a fix requires a command on a DIFFERENT device or
in a different file, say so explicitly:
"Fix: On the router, apply with: ip access-group WEB-FILTER in"

---

==========================================================
## NOTES & RECOMMENDATIONS
==========================================================

After all lines are covered, list cross-line observations
that do not belong to any single line:

- **Redundancy:** lines that duplicate implicit behavior
  (e.g., explicit `deny ip any any` after Cisco's implicit deny).
  Note whether the redundancy is harmful or intentional
  (e.g., for match counters).
- **Application / Context:** things that must be done OUTSIDE
  this config for it to take effect (apply ACL to interface,
  reload service, restart container, run `ip link set up`).
- **Ordering:** lines whose effect depends on sequence
  (ACL evaluation order, iptables chain order, nginx server
  block match order, systemd After=/Requires=).
- **Best practice gaps:** missing hardening, missing logging,
  missing rate limiting, missing failover — things that are
  not "broken" but should be there in production.
- **Dependencies between blocks:** e.g., "the route in block X
  references the interface defined in block Y; if Y changes,
  X silently breaks."

Each note: one bold label + 2–3 sentences. Be specific.
Reference line numbers.

==========================================================
## SUMMARY
==========================================================

- Total lines/blocks analyzed: <N>
- CRITICAL: <n>   HIGH: <n>   MEDIUM: <n>   LOW: <n>   OK: <n>
- Verdict: <production-ready / needs fixes before deploy / critical gaps>
  (one sentence, name the top issue)

==========================================================
## FINAL CORRECTED CONFIGURATION
==========================================================

Output the complete configuration with all fixes applied.
Rules:
- Every original line is present (corrected or unchanged).
- Changed lines: prefix with `# CHANGED` (or `! CHANGED` for Cisco).
- Added lines:   prefix with `# ADDED`   (or `! ADDED` for Cisco).
- Removed lines: list in a `## REMOVED` block at the very end,
  each with a one-line reason.
- The output must be syntactically valid and paste-ready.
- Do NOT reformat or reorganize lines that do not need changing.
  Preserve the original structure and order.
- If there were zero issues, write:
  "No changes required. Configuration is correct as-is."
  and output the original unchanged.

==========================================================
## HARD RULES
==========================================================

1. Do NOT invent directives, IPs, ports, or features not in the input.
2. Do NOT skip a line because it "looks fine." Write the entry.
   "Risk: OK — no issues." and "Fix: OK." is a valid entry.
3. Do NOT repeat the same explanation for identical lines.
   First occurrence: full explanation.
   Subsequent: "Identical to line <N>. Risk: OK. Fix: OK."
4. Every "Fix" must be a concrete line of config or command.
   Never "consider improving this" or "review this setting."
5. If the config is from a vendor you are less familiar with,
   analyze the syntax you can verify and mark the rest:
   "Risk: [UNCLEAR — vendor-specific directive, verify against
   vendor documentation]"
6. Severity definitions:
   CRITICAL — data loss, full exposure, auth bypass, DoS
   HIGH     — privilege escalation, missing hardening, broken failover
   MEDIUM   — suboptimal, missing best practice, minor exposure
   LOW      — style, naming, missing comment, redundant line
   OK       — correct, complete, no action needed

==========================================================
## INPUT
==========================================================
"""


# ─────────────────────────────────────────────────────────────
# File reading: text files and PDF documents
# ─────────────────────────────────────────────────────────────
def read_document(file_path: str) -> str:
    """Return the text content of a .txt/.conf or a .pdf file.

    Raises a ValueError with a user-friendly message on failure.
    """
    path = Path(file_path)
    if path.suffix.lower() == ".pdf":
        return _extract_pdf_text(path)

    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="latin-1")


def _extract_pdf_text(path: Path) -> str:
    """Extract text from a PDF, page by page, using pypdf."""
    try:
        from pypdf import PdfReader
    except ImportError as e:
        raise ValueError(
            "pypdf is not installed, so PDF files cannot be opened.\n"
            "Install it with:  pip install pypdf"
        ) from e

    reader = PdfReader(str(path))
    if reader.is_encrypted:
        if not reader.decrypt(""):
            raise ValueError("This PDF is password-protected. Remove the password and try again.")

    pages = []
    for i, page in enumerate(reader.pages, start=1):
        text = (page.extract_text() or "").strip()
        if text:
            pages.append(f"[Page {i}]\n{text}" if len(reader.pages) > 1 else text)

    content = "\n\n".join(pages).strip()
    if not content:
        raise ValueError(
            "No selectable text found in this PDF.\n"
            "If it is a scanned image, convert it to a text PDF (OCR) first."
        )
    return content


class DeepInspectWorker(QThread):
    progress = Signal(str)
    finished_ok = Signal(str)
    finished_err = Signal(str)

    def __init__(self, file_contents: str):
        super().__init__()
        self.file_contents = file_contents

    def run(self):
        try:
            self.progress.emit("Analyzing with 14B...")
            response = requests.post(
                OLLAMA_URL,
                json={
                    "model": MODEL_14B,
                    "messages": [
                        {"role": "system", "content": DEEP_INSPECT_PROMPT},
                        {"role": "user", "content":
                             f"Analyze this config:\n\n```\n{self.file_contents}\n```"},
                    ],
                    "stream": False,
                    "options": {"num_ctx": 16384, "temperature": 0.0},
                },
                timeout=300,
            )
            response.raise_for_status()
            text = response.json()["message"]["content"]
            self.finished_ok.emit(text)

        except requests.exceptions.ConnectionError:
            self.finished_err.emit(
                "Could not connect to Ollama at http://localhost:11434.\n\n"
                "1. Install Ollama from https://ollama.com/download\n"
                "   and make sure it is running (check the system tray).\n"
                "2. Install the model with command in CMD:\n"
                "     ollama pull qwen2.5:14b\n"
                "Then press Upload again to analyze."
            )
        except requests.exceptions.HTTPError as e:
            detail = ""
            if e.response is not None:
                try:
                    detail = e.response.json().get("error", "")
                except Exception:
                    detail = e.response.text
            if e.response is not None and e.response.status_code == 404 or "not found" in detail.lower():
                self.finished_err.emit(
                    "Ollama is running, but the model 'qwen2.5:14b' is not installed.\n"
                    "Install it by running this command in CMD:\n"
                    "     ollama pull qwen2.5:14b\n"
                    "Then press Upload again to analyze."
                )
            else:
                self.finished_err.emit(f"Ollama error: {detail or e}")
        except Exception as e:
            self.finished_err.emit(str(e))


# ==========================================
# How to run it all together:
# ==========================================

"""Main application window – prompt browser and toolbar."""


class InspectWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Inspect configuration")
        self.resize(1280, 720)
        self.current_choice = ""

        self.worker = None
        self._pending_contents = None

        self._init_ui()

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
        #top_layout.addWidget(self.combo)

        self.label = QLabel("")
        self.label.setObjectName("status_label")
        #top_layout.addWidget(self.label)

        top_layout.addStretch()

        self.upload_btn = QPushButton("Upload")
        self.upload_btn.setObjectName("upload_button")
        self.upload_btn.setFixedHeight(std_h)
        self.save_btn = QPushButton("Save")
        self.save_btn.setObjectName("save_button")
        self.save_btn.setFixedHeight(std_h)

        self.upload_btn.clicked.connect(self._open_add)
        self.save_btn.clicked.connect(self._save_to_file)

        top_layout.addWidget(self.upload_btn)
        top_layout.addWidget(self.save_btn)

        layout.addWidget(top)

        # -- Display --
        self.chat_display = QTextEdit()
        self.chat_display.setObjectName("output_display")
        self.chat_display.setReadOnly(True)
        self.chat_display.setPlaceholderText("Choose a config or PDF document for analysis")
        layout.addWidget(self.chat_display)
        layout.setStretchFactor(self.chat_display, 1)

        # -- Signals --
        self.combo.currentIndexChanged.connect(self._on_combo_change)

    # ------------------------------------------------------------------
    def _on_combo_change(self, _index: int):
        name = self.combo.currentText()
        self.current_choice = name
        self.label.setText(f"Selected: {name}")
        content = self.db.get_content(name)
        self.chat_display.setText(content or "")

    # ------------------------------------------------------------------
    # Upload flow: file dialog (txt or pdf) → DeepInspectWorker
    # ------------------------------------------------------------------
    def _busy(self) -> bool:
        return self.worker is not None and self.worker.isRunning()

    def _open_add(self):
        if self._busy():
            return

        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Document", "",
            "Config/Text Files (*.txt *.conf *.cfg *.ini *.yml *.yaml *.xml *.log);;"
            "PDF Documents (*.pdf);;"
            "All Files (*)",
        )
        if not file_path:
            return

        try:
            file_contents = read_document(file_path)
        except Exception as e:
            self.chat_display.setText(f"Read error: {e}")
            return

        if not file_contents.strip():
            self.chat_display.setText("The file appears to be empty.")
            return

        self._start_analysis(file_contents)

    def _start_analysis(self, file_contents: str):
        self.chat_display.setText("Analyzing...")
        self.upload_btn.setEnabled(False)

        self.worker = DeepInspectWorker(file_contents)
        self.worker.progress.connect(self._on_worker_progress)
        self.worker.finished_ok.connect(self._on_worker_done)
        self.worker.finished_err.connect(self._on_worker_error)
        self.worker.start()

    def _on_worker_progress(self, text: str):
        self.chat_display.setText(text)

    def _on_worker_done(self, result: str):
        self.chat_display.setText(result)
        self.upload_btn.setEnabled(True)

    def _on_worker_error(self, err: str):
        self.chat_display.setText(f"Error: {err}")
        self.upload_btn.setEnabled(True)

    # ------------------------------------------------------------------
    def closeEvent(self, event):
        # Avoid "QThread: Destroyed while thread is still running" on exit.
        if self._busy():
            reply = QMessageBox.question(
                self, "Quit",
                "An analysis is still running. Quit anyway?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                event.ignore()
                return
            if self.worker.isRunning():
                self.worker.wait(5000)
        super().closeEvent(event)

    def _save_to_file(self):
        content = self.chat_display.toPlainText()
        if not content:
            QMessageBox.warning(self, "Warning", "Nothing to save.")
            return

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Analysis",
            "analysis.txt",
            "Text Files (*.txt);;All Files (*)",
        )
        if path:
            Path(path).write_text(content, encoding="utf-8")
            QMessageBox.information(self, "Success", f"Saved to {path}")


def main():
    app = QApplication(sys.argv)

    window = InspectWindow()
    window.show()

    sys.exit(app.exec())
