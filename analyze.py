import sys
import requests

from pathlib import Path

from llama_cpp import Llama

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QComboBox, QVBoxLayout, QWidget,
    QLabel, QTextEdit, QPushButton, QHBoxLayout, QMessageBox, QFileDialog, QProgressBar,
)
from PySide6.QtCore import QThread, Signal

# Use the frozen-aware paths from config so the model lives next to the
# .exe (or in the project folder in dev) — never relative to the CWD.
from config import (
    MODELS_DIR,
    MODEL_PATH as MODEL_7B_PATH,
    REPO_ID,
    MODEL_FILENAME as MODEL_7B_FILENAME,
)
MODEL_7B_URL = (
    f"https://huggingface.co/{REPO_ID}/resolve/main/{MODEL_7B_FILENAME}"
)

EXPLAIN_PROMPT = (
    """
You are a senior network/systems engineer explaining a configuration
to a junior engineer. Your job: make them understand WHAT it does,
WHY it exists, and WHAT could go wrong.

RULES
- Plain language. If you use a jargon term, add a 3-word gloss in
parentheses. Example: "native VLAN (the default untagged VLAN on a trunk)".
- Explain intent, not just syntax. "This permits HTTPS" is wrong.
"This lets the app subnet reach the web-tier subnet on port 443
and nothing else" is right.
- If a setting looks risky, non-standard, or missing a recommended
companion command, flag it: ⚠️ <one-line reason>.
- If a line is unclear or context-dependent, say so. Do NOT guess.
- Never invent a keyword, port, IP, or directive that is not in the
input. If you are unsure, write "unclear from this fragment."
- Repeated blocks: analyze the first instance fully, then for the
rest write one line: "Identical to [first block name]."

OUTPUT FORMAT
Start directly with ### 1. No preamble, no "Sure, here is…".
Omit any section that does not apply to the config provided.

### 1. Overview
- **Platform / syntax:** <e.g. Cisco IOS-XE, nftables, sshd_config>
- **Role in the network:** <1 sentence: what this device/service does
and who/what talks to it>
- **Key risk or note:** <1 line if any ⚠️ applies, else "None.">

### 2. Global / system-wide settings
For each global line or setting (outside any named block):
- `exact command or directive`
→ **Does:** <what it does, 1 sentence>
→ **Why:** <why an engineer writes it, 1 sentence>
→ ⚠️ <only if applicable>

### 3. Per-block / per-interface / per-rule breakdown
For each named block, interface, ACL, zone, table, stanza:

#### <Block name> <e.g. "GigabitEthernet0/1", "table inet filter",
"Host *", "route 10.10.0.0/16">
- `directive`
→ **Does:** …
→ **Why:** …
→ ⚠️ …

If multiple blocks are identical, after the first:
> Blocks X, Y, Z: identical to <first block>. (list names)

### 4. Operational summary
3–6 bullet points, no headers, no sub-bullets. Cover:
- What traffic / connections are allowed or blocked (if applicable)
- Which ports / VLANs / subnets / users are affected
- Logging / audit trail: what gets logged, where
- Performance or resource impact if notable
- Any interaction between blocks (e.g. ACL applied on interface
that a route-map also references)

"""
)


# ─────────────────────────────────────────────────────────────
# Model: load the GGUF once, reuse it for every analysis
# ─────────────────────────────────────────────────────────────
_LLM_CACHE = {}



def get_llm(n_ctx: int = 4096, n_gpu_layers: int = -1) -> Llama:
    key = (str(MODEL_7B_PATH), n_ctx, n_gpu_layers)
    if key not in _LLM_CACHE:
        _LLM_CACHE[key] = Llama(
            model_path=str(MODEL_7B_PATH),
            n_ctx=n_ctx,
            n_gpu_layers=n_gpu_layers,
        )
    return _LLM_CACHE[key]


# ─────────────────────────────────────────────────────────────
# Download: resumable, reports progress per chunk
# ─────────────────────────────────────────────────────────────
def download_model(url: str, dest: Path, progress_cb=None):
    """Stream `url` to `dest` (via a .part file), resuming an existing .part.

    progress_cb(downloaded_bytes, total_bytes) is called per chunk.
    """
    tmp = dest.with_suffix(".part")
    headers = {"User-Agent": "HandyPrompt/1.0"}

    start = tmp.stat().st_size if tmp.exists() else 0
    if start > 0:
        headers["Range"] = f"bytes={start}-"

    with requests.get(url, stream=True, timeout=(15, 60), headers=headers) as r:
        resumed = start > 0 and r.status_code == 206
        r.raise_for_status()
        if not resumed:          # server ignored Range → start over
            start = 0
        remaining = int(r.headers.get("content-length", 0))
        total = (start + remaining) if resumed else remaining

        with open(tmp, "ab" if resumed else "wb") as f:
            downloaded = start
            for chunk in r.iter_content(chunk_size=8 * 1024 * 1024):
                if not chunk:
                    continue
                f.write(chunk)
                downloaded += len(chunk)
                if progress_cb:
                    progress_cb(downloaded, total)

    tmp.rename(dest)


class DownloadWorker(QThread):
    """Downloads the model off the GUI thread, emitting percent progress."""

    progress = Signal(int)      # 0..100
    finished_ok = Signal()
    finished_err = Signal(str)

    def __init__(self, url: str, dest: Path):
        super().__init__()
        self.url = url
        self.dest = Path(dest)
        self._last_pct = -1

    def _on_chunk(self, downloaded: int, total: int) -> None:
        if not total:
            return
        pct = max(0, min(100, int(downloaded * 100 / total)))
        if pct != self._last_pct:          # throttle: one emit per 1 % step
            self._last_pct = pct
            self.progress.emit(pct)

    def run(self):
        try:
            download_model(self.url, self.dest, progress_cb=self._on_chunk)
            self.finished_ok.emit()
        except Exception as e:
            self.finished_err.emit(str(e))


class AnalyzeWorker(QThread):
    progress = Signal(str)       # status text
    finished_ok = Signal(str)    # final result
    finished_err = Signal(str)   # error message

    def __init__(self, file_contents: str):
        super().__init__()
        self.file_contents = file_contents

    def run(self):
        if not MODEL_7B_PATH.is_file():
            self.finished_err.emit(
                f"Model file not found: {MODEL_7B_PATH}\n\n"
                "Download it first from the Analyze window (press Upload — "
                "the download starts automatically), or put the .gguf file "
                "in the models/ folder next to the app."
            )
            return

        try:
            first_load = not _LLM_CACHE
            self.progress.emit(
                "Loading model... (first analysis takes a while)" if first_load
                else "Analyzing..."
            )
            try:
                llm = get_llm(n_ctx=8192, n_gpu_layers=-1)
            except Exception as e:
                self.finished_err.emit(
                    f"Could not load the local model: {e}\n\n"
                    f"Expected file: {MODEL_7B_PATH}\n"
                    "If the file is corrupt or incomplete, delete it and "
                    "press Upload again to re-download."
                )
                return

            self.progress.emit("Analyzing...")
            messages = [
                {"role": "system", "content": EXPLAIN_PROMPT},
                {"role": "user", "content": f"Analyze this config:\n\n```\n{self.file_contents}\n```"},
            ]
            response = llm.create_chat_completion(
                messages=messages,
                max_tokens=1500,
                temperature=0.0,
            )
            self.finished_ok.emit(response["choices"][0]["message"]["content"] or "")

        except Exception as e:
            self.finished_err.emit(str(e))


# ==========================================
# How to run it all together:
# ==========================================

"""Main application window – prompt browser and toolbar."""


#from database import PromptDatabase
#from ui.add_prompt import AddPromptWindow
#from ui.edit_prompt import EditPromptWindow


class AnalyzeWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Analyze configuration")
        self.resize(1280, 720)
        self.current_choice = ""
        #self.db = PromptDatabase()

        self.download_worker = None
        self.worker = None
        self._pending_contents = None

        #self._set_icon()
        self._init_ui()

    # ------------------------------------------------------------------
    #def _set_icon(self):
    #    from config import resource_path
    #    icon_path = resource_path("assets/icon.png")
    #    if icon_path.exists():
    #        self.setWindowIcon(QIcon(str(icon_path)))


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

        #self.about_btn = QPushButton("About")
        #self.about_btn.setFixedHeight(std_h)
        #self.about_btn.clicked.connect(self._show_about)
        #top_layout.addWidget(self.about_btn)

        top_layout.addStretch()


        self.upload_btn = QPushButton("Upload")
        self.upload_btn.setObjectName("upload_button")
        self.copy_btn = QPushButton("Copy")
        self.copy_btn.setObjectName("copy_button")
        self.save_btn = QPushButton("Save")
        self.save_btn.setObjectName("save_button")
        self.save_btn.setFixedHeight(std_h)
        #self.edit_btn = QPushButton("Edit")
        #self.edit_btn.setObjectName("edit_button")
        #self.del_btn = QPushButton("Delete")
        #self.del_btn.setObjectName("del_button")
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setVisible(False)
        layout.addWidget(self.progress)

        self.upload_btn.clicked.connect(self._open_add)
        self.save_btn.clicked.connect(self._save_to_file)
        #self.copy_btn.clicked.connect(self._copy_to_clipboard)
        #self.edit_btn.clicked.connect(self._open_edit)
        #self.del_btn.clicked.connect(self._delete_prompt)

        #top_layout.addWidget(self.copy_btn)
        top_layout.addWidget(self.upload_btn)
        top_layout.addWidget(self.save_btn)
        #top_layout.addWidget(self.edit_btn)
        #top_layout.addWidget(self.del_btn)

        layout.addWidget(top)

        # -- Display --
        self.chat_display = QTextEdit()
        self.chat_display.setObjectName("output_display")
        self.chat_display.setReadOnly(True)
        self.chat_display.setPlaceholderText("Choose a file configuration for analysis")
        layout.addWidget(self.chat_display)
        layout.setStretchFactor(self.chat_display, 1)

        # -- Signals --
        self.combo.currentIndexChanged.connect(self._on_combo_change)
        #self._load_prompts()

    # ------------------------------------------------------------------
    def _on_combo_change(self, _index: int):
        name = self.combo.currentText()
        self.current_choice = name
        self.label.setText(f"Selected: {name}")
        content = self.db.get_content(name)
        self.chat_display.setText(content or "")

    # ------------------------------------------------------------------
    # Upload flow: file dialog → (download if needed) → analysis
    # Nothing heavy runs on the GUI thread.
    # ------------------------------------------------------------------
    def _busy(self) -> bool:
        for w in (self.download_worker, self.worker):
            if w is not None and w.isRunning():
                return True
        return False

    def _open_add(self):
        if self._busy():
            return

        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Document", "",
            "Text Files (*.txt);;All Files (*)",
        )
        if not file_path:
            return

        # ── Read file (fast, fine on GUI thread) ──
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                file_contents = f.read()
        except Exception as e:
            self.chat_display.setText(f"Read error: {e}")
            return

        if MODEL_7B_PATH.is_file():
            self._start_analysis(file_contents)
        else:
            self._start_download(file_contents)

    def _start_download(self, file_contents: str):
        self._pending_contents = file_contents
        self.chat_display.setText(
            f"Downloading {MODEL_7B_FILENAME} (~4.7 GB)...\n"
            "Resuming from .part file if one exists — the window stays usable."
        )
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setVisible(True)
        self.upload_btn.setEnabled(False)

        self.download_worker = DownloadWorker(MODEL_7B_URL, MODEL_7B_PATH)
        self.download_worker.progress.connect(self._on_download_progress)
        self.download_worker.finished_ok.connect(self._on_download_done)
        self.download_worker.finished_err.connect(self._on_download_error)
        self.download_worker.start()

    def _on_download_progress(self, pct: int):
        self.progress.setValue(pct)

    def _on_download_done(self):
        self.progress.setValue(100)
        self.progress.setVisible(False)
        contents = self._pending_contents or ""
        self._pending_contents = None
        self._start_analysis(contents)

    def _on_download_error(self, err: str):
        self.progress.setVisible(False)
        self._pending_contents = None
        self.upload_btn.setEnabled(True)
        self.chat_display.setText(
            f"Download failed: {err}\n"
            "Progress is kept in the .part file — press Upload again to resume."
        )

    # ------------------------------------------------------------------
    def _start_analysis(self, file_contents: str):
        self.progress.setVisible(False)
        self.chat_display.setText("Loading model...")
        self.upload_btn.setEnabled(False)

        self.worker = AnalyzeWorker(file_contents)
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
                "A download/analysis is still running. Quit anyway?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                event.ignore()
                return
            for w in (self.download_worker, self.worker):
                if w is not None and w.isRunning():
                    w.wait(5000)
        super().closeEvent(event)


    #def _open_edit(self):
    #    if not self.current_choice:
    #        QMessageBox.warning(self, "Warning", "Please select a prompt first.")
    #        return
    #    self._child = EditPromptWindow(choice=self.current_choice, parent=self, db=self.db)
    #    self._child.show()

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
