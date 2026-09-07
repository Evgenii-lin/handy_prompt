"""Background worker thread for LLM inference and model download."""
import requests
from PySide6.QtCore import QThread, Signal, QMutex

from huggingface_hub.utils import tqdm as hf_tqdm

from config import REPO_ID, MODEL_FILENAME, MODEL_PATH

DOWNLOAD_URL = (
    f"https://huggingface.co/{REPO_ID}/resolve/main/{MODEL_FILENAME}"
)

try:
    from llama_cpp import Llama
except ImportError:
    Llama = None


# ---------------------------------------------------------------------------
# Progress helpers
# ---------------------------------------------------------------------------
class ProgressEmitter:
    """Thread-safe progress emitter bridging download thread and Qt."""

    def __init__(self, progress_signal):
        self.signal = progress_signal
        self.last_pct = -1
        self.mutex = QMutex()

    def emit_progress(self, pct: int) -> None:
        if pct - self.last_pct >= 1 or pct == 100:
            self.last_pct = pct
            self.signal.emit(pct)


class QThreadTqdm(hf_tqdm):
    """tqdm subclass that emits Qt signals for download progress."""

    def __init__(self, progress_emitter: ProgressEmitter, *args, **kwargs):
        self.progress_emitter = progress_emitter
        super().__init__(*args, **kwargs)

    def update(self, n=1):
        super().update(n)
        if hasattr(self, "n") and hasattr(self, "total") and self.total > 0:
            pct = int((self.n / self.total) * 100)
            self.progress_emitter.emit_progress(pct)


# ---------------------------------------------------------------------------
# Worker
# ---------------------------------------------------------------------------
class LlamaWorker(QThread):
    token_generated = Signal(str)
    finished_generation = Signal()
    error_occurred = Signal(str)
    progress_changed = Signal(int)

    def __init__(self, prompt: str):
        super().__init__()
        self.prompt = prompt
        self.role = (
            "You are an expert prompt engineer specializing in writing instructions "
            "for Claude Code, a terminal-based coding assistant.\n"
            f"I need you to write a detailed, high-performance prompt for Claude Code "
            f"to perform the following task: {self.prompt}.\n"
            "The prompt you generate for me must include:\n"
            "1. A clear, concise objective statement.\n"
            "2. Specific file paths or components to focus on.\n"
            "3. Explicit constraints.\n"
            "4. Expected output format or testing steps.\n"
            "Provide only the final prompt wrapped in a markdown code block."
        )

        if not MODEL_PATH.is_file():
            self.needs_download = True
            self.llm = None
        else:
            self.needs_download = False
            if Llama:
                self.llm = Llama(model_path=str(MODEL_PATH), n_ctx=2048)
            else:
                self.llm = None

    # ------------------------------------------------------------------
    def run(self) -> None:
        # -- Download if needed --
        if self.needs_download:
            self.progress_changed.emit(0)
            try:
                self.progress_changed.emit(5)
                emitter = ProgressEmitter(self.progress_changed)

                tmp_path = MODEL_PATH.with_suffix(".part")

                with requests.get(
                    DOWNLOAD_URL,
                    stream=True,
                    headers={"User-Agent": "HandyPrompt/1.0"},
                ) as resp:
                    resp.raise_for_status()
                    total = int(resp.headers.get("content-length", 0))

                    downloaded = 0
                    with open(tmp_path, "wb") as f:
                        for chunk in resp.iter_content(chunk_size=8 * 1024 * 1024):
                            f.write(chunk)
                            downloaded += len(chunk)
                            if total > 0:
                                pct = int(downloaded / total * 100)
                                emitter.emit_progress(pct)

                tmp_path.rename(MODEL_PATH)
                self.progress_changed.emit(100)

                if Llama:
                    self.llm = Llama(model_path=str(MODEL_PATH), n_ctx=2048)

            except Exception as e:
                self.error_occurred.emit(f"Download error: {e}")
                self.finished_generation.emit()
                return

        # -- Generate (or mock) --
        if not Llama:
            self.token_generated.emit("[Mock Output: ")
            self.token_generated.emit(f"Prompt generated based on: {self.prompt}]")
            self.finished_generation.emit()
            return

        if self.llm is None:
            self.error_occurred.emit("Model not loaded.")
            self.finished_generation.emit()
            return

        try:
            output = self.llm(
                f"user\n{self.prompt}\n\n{self.role}\n##assistant\n",
                max_tokens=512,
                stream=True,
            )
            for chunk in output:
                if "choices" in chunk and chunk["choices"]:
                    self.token_generated.emit(chunk["choices"][0]["text"])
            self.finished_generation.emit()
        except Exception as e:
            self.error_occurred.emit(str(e))
