"""Persistence service for result JSON files."""
import json, re
from pathlib import Path
from .processing import _safe_result_filename

class ResultManager:
    """Persist and retrieve per-student classification results."""
    def result_filename(self, filename: str, raw_text: str) -> str:
        return _safe_result_filename(filename, raw_text)

    def save(self, result: dict, output_folder: Path) -> Path:
        output_folder = Path(output_folder); output_folder.mkdir(parents=True, exist_ok=True)
        student = re.sub(r"[^A-Za-z0-9_.-]+", "_", result.get("student_id", "UnknownStudent"))
        path = output_folder / f"{student}.json"
        path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
        return path

    def load(self, path: Path) -> dict:
        return json.loads(Path(path).read_text(encoding="utf-8"))

__all__ = ["ResultManager"]
