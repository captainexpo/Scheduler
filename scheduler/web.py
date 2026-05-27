from __future__ import annotations

import csv
import io
import tempfile
import uuid
from pathlib import Path

from flask import Flask, Response, abort, render_template, request, send_file

from scheduler.main import run_scheduler


app = Flask(__name__)

_RESULTS: dict[str, dict[str, object]] = {}


def _temp_file_from_upload(upload) -> str:
    with tempfile.NamedTemporaryFile(
        delete=False, suffix=Path(upload.filename or "upload.csv").suffix or ".csv"
    ) as tmp:
        upload.save(tmp)
        return tmp.name


def _build_score_dist(meta: dict[str, object]) -> list[dict[str, object]]:
    raw_dist = meta.get("score_dist", [])
    labels = [
        "1st choice",
        "2nd choice",
        "3rd choice",
        "4th choice",
        "5th choice",
        "Unsorted",
    ]
    values: list[float] = []
    for item in raw_dist if isinstance(raw_dist, list) else []:
        if isinstance(item, (int, float)):
            values.append(float(item))
        else:
            values.append(0.0)
    max_value = max(values) if values else 0.0
    result: list[dict[str, object]] = []
    for index, label in enumerate(labels):
        value = values[index] if index < len(values) else 0.0
        width = 0 if max_value == 0 else round((value / max_value) * 100, 1)
        result.append({"label": label, "value": value, "width": width})
    return result


def _build_preview(csv_output: str) -> tuple[list[str], list[dict[str, str]]]:
    reader = csv.DictReader(io.StringIO(csv_output))
    columns = list(reader.fieldnames or [])
    rows: list[dict[str, str]] = []
    for row in reader:
        rows.append(row)
        # if len(rows) >= 25:
        # break
    return columns, rows


def _render_page(
    *, error: str | None = None, result: dict[str, object] | None = None
) -> str:
    return render_template("index.html", error=error, result=result)


@app.get("/")
def index() -> str:
    return _render_page()


@app.post("/")
def run_schedule() -> str:
    students_upload = request.files.get("students")
    classes_upload = request.files.get("classes")

    # desired grade mixing weight
    mixing_weight = request.form.get("mixing_weight", "1.0")
    print(f"Received mixing weight: {mixing_weight}")

    algorithm = request.form.get("algorithm", "lp")

    if not students_upload or not students_upload.filename:
        return _render_page(error="Please choose a student CSV file.")
    if not classes_upload or not classes_upload.filename:
        return _render_page(error="Please choose a class CSV file.")

    student_path = _temp_file_from_upload(students_upload)
    class_path = _temp_file_from_upload(classes_upload)

    try:
        solved_data, csv_output = run_scheduler(
            student_path,
            class_path,
            algorithm=algorithm,
            lp_opts={"grade_mixing_weight": float(mixing_weight)},
        )
        token = uuid.uuid4().hex
        preview_columns, preview_rows = _build_preview(csv_output)
        result = {
            "token": token,
            "meta": solved_data.meta,
            "score_dist": _build_score_dist(solved_data.meta),
            "preview_columns": preview_columns,
            "preview_rows": preview_rows,
        }
        _RESULTS[token] = {"csv": csv_output, "filename": "scheduled_students.csv"}
        return _render_page(result=result)
    except Exception as exc:  # pragma: no cover - surfaced to the user in the UI
        return _render_page(error=f"Scheduling failed: {exc}")
    finally:
        Path(student_path).unlink(missing_ok=True)
        Path(class_path).unlink(missing_ok=True)


@app.get("/download/<token>")
def download(token: str) -> Response:
    result = _RESULTS.get(token)
    if result is None:
        abort(404)

    csv_output = result["csv"]
    filename = result["filename"]
    return send_file(
        io.BytesIO(str(csv_output).encode("utf-8")),
        mimetype="text/csv",
        as_attachment=True,
        download_name=str(filename),
    )


def main() -> None:
    app.run(host="127.0.0.1", port=8000, debug=True)


if __name__ == "__main__":
    main()

