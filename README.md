Handy Prompt

A lightweight, local AI assistant powered by Qwen and llama-cpp-python, featuring a modern graphical user interface built with PySide6 and chat history persistence via SQLite.

## Features

- 100% Local & Private: Your data never leaves your machine.
- Powered by Qwen: Seamless text generation using advanced LLM capabilities.
- Fast Inference: Optimized performance via llama-cpp-python (GGUF format support).
- Chat History: Automatically saves and loads your past conversations using an SQLite database.
- Modern UI: Clean and responsive interface built with PySide6 (Qt for Python).

## Installation

### Prerequisites

- Python 3.10 or higher
- Git

### Setup

1. Clone the repository:
   git clone https://github.com/Evgenii-lin/handy_prompt.git
   cd handy_prompt

2. Create and activate a virtual environment:
   python -m venv .venv
   # On Windows:
   .venv\Scripts\activate
   # On macOS/Linux:
   source .venv/bin/activate

3. Install the dependencies:
   pip install -r requirements.txt

## Getting Started

1. Download a Model:
   When generating prompt for the first time, Qwen model (e.g., Qwen2.5-7B-Instruct-GGUF) from Hugging Face  will be                                             downloaded to models/ folder.
3. Run the Application:
   python main.py

## Third-Party Components & Licenses

This project is open-source under the MIT License. However, it relies on several excellent third-party libraries and models with their own respective licenses:

* Python — PSF License (https://python.org)
* PySide6 (Qt for Python) — GNU LGPLv3 (https://gnu.org) | Copyright The Qt Company
* llama-cpp-python — MIT License (https://github.comabetlen/llama-cpp-python) | Copyright Andrei Betlen
* Hugging Face Transformers — Apache 2.0 License (https://github.comhuggingface/transformers) | Copyright Hugging Face, Inc.
* Qwen Model Series — Apache 2.0 / Qwen License (https://github.comQwenLM/Qwen2.5) | Copyright Alibaba Cloud
* SQLite — Public Domain (https://sqlite.org)

## License

This project is licensed under the MIT License - see the LICENSE file for details.
