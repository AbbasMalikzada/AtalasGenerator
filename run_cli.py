"""CLI: прогнать pipeline по директории с материалами.

    python run_cli.py sample_data
    DOCGEN_FAKE=1 python run_cli.py sample_data   # без сети/ключа

Печатает результат в формате ТЗ.
"""
from __future__ import annotations

import json
import sys

from app.ingest import load_dir
from app.pipeline import generate_document


def main() -> None:
    # Принудительно настраиваем вывод в UTF-8 для Windows, чтобы избежать UnicodeEncodeError
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    if len(sys.argv) < 2:
        print("usage: python run_cli.py <dir_with_materials>")
        sys.exit(1)
    files = load_dir(sys.argv[1])
    result = generate_document(files)
    print(json.dumps(result.model_dump(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
