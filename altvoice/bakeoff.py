"""ASR bake-off harness: CER, latency and failure reporting."""

from __future__ import annotations

import json
import statistics
import time
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .asr import EngineUnavailable, create_engine
from .correct.guard import levenshtein


@dataclass
class Case:
    case_id: str
    audio: Path
    reference: str = ""
    language: str = "zh"
    tags: list[str] = field(default_factory=list)


@dataclass
class CaseResult:
    case_id: str
    text: str = ""
    reference: str = ""
    cer: float | None = None
    latency_ms: float = 0.0
    error: str = ""
    tags: list[str] = field(default_factory=list)


def load_manifest(path: str | Path) -> list[Case]:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(path)
    text = path.read_text(encoding="utf-8")
    rows: list[dict[str, Any]]
    if path.suffix.lower() == ".jsonl":
        rows = []
        for line_no, line in enumerate(text.splitlines(), 1):
            line = line.strip()
            if not line:
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_no}: invalid JSON: {exc}") from exc
            if not isinstance(item, dict):
                raise ValueError(f"{path}:{line_no}: expected an object")
            rows.append(item)
    else:
        data = json.loads(text)
        if isinstance(data, dict):
            data = data.get("cases", [])
        if not isinstance(data, list):
            raise ValueError("manifest must be a JSON array or {'cases': [...]}")
        rows = data

    cases: list[Case] = []
    base = path.parent
    for index, row in enumerate(rows):
        audio = row.get("audio") or row.get("wav") or row.get("path")
        if not audio:
            raise ValueError(f"{path}: case {index} is missing 'audio'")
        audio_path = Path(str(audio))
        if not audio_path.is_absolute():
            audio_path = (base / audio_path).resolve()
        case_id = str(row.get("id") or f"case-{index:04d}")
        cases.append(
            Case(
                case_id=case_id,
                audio=audio_path,
                reference=str(row.get("reference") or row.get("text") or ""),
                language=str(row.get("language") or "zh"),
                tags=[str(t) for t in (row.get("tags") or [])],
            )
        )
    return cases


def normalize_for_cer(text: str) -> str:
    """Keep letters/digits/CJK, drop punctuation and whitespace, casefold Latin."""
    text = unicodedata.normalize("NFKC", text or "").casefold()
    chars: list[str] = []
    for ch in text:
        if ch.isalnum():
            chars.append(ch)
        elif "\u4e00" <= ch <= "\u9fff":
            chars.append(ch)
    return "".join(chars)


def character_error_rate(reference: str, hypothesis: str) -> float | None:
    ref = normalize_for_cer(reference)
    hyp = normalize_for_cer(hypothesis)
    if not ref:
        return None
    return levenshtein(ref, hyp) / len(ref)


def _percentile(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    rank = (len(ordered) - 1) * p
    low = int(rank)
    high = min(low + 1, len(ordered) - 1)
    weight = rank - low
    return ordered[low] * (1 - weight) + ordered[high] * weight


def _summary(results: list[CaseResult]) -> dict[str, Any]:
    ok = [r for r in results if not r.error]
    scored = [r for r in ok if r.cer is not None]
    latencies = [r.latency_ms for r in ok if r.latency_ms > 0]
    return {
        "total": len(results),
        "ok": len(ok),
        "errors": len(results) - len(ok),
        "cer_cases": len(scored),
        "cer_mean": statistics.fmean(r.cer for r in scored) if scored else None,
        "cer_median": statistics.median(r.cer for r in scored) if scored else None,
        "latency_p50_ms": _percentile(latencies, 0.50),
        "latency_p95_ms": _percentile(latencies, 0.95),
    }


def run_engine(
    engine_name: str,
    cases: list[Case],
    model_path: str | None = None,
    device: str = "cuda",
    limit: int = 0,
) -> dict[str, Any]:
    selected = cases[:limit] if limit else cases
    results: list[CaseResult] = []
    engine = None
    try:
        engine = create_engine(engine_name, model_path=model_path, device=device)
        engine.load()
    except EngineUnavailable as exc:
        return {
            "engine": engine_name,
            "loaded": False,
            "error": str(exc),
            "summary": _summary([]),
            "results": [],
        }
    try:
        for case in selected:
            if not case.audio.exists():
                results.append(
                    CaseResult(
                        case_id=case.case_id,
                        reference=case.reference,
                        error=f"audio not found: {case.audio}",
                        tags=case.tags,
                    )
                )
                continue
            start = time.perf_counter()
            try:
                asr_result = engine.transcribe(str(case.audio), language=case.language)
                elapsed = (time.perf_counter() - start) * 1000.0
                latency = asr_result.latency_ms or elapsed
                results.append(
                    CaseResult(
                        case_id=case.case_id,
                        text=asr_result.text,
                        reference=case.reference,
                        cer=character_error_rate(case.reference, asr_result.text),
                        latency_ms=latency,
                        tags=case.tags,
                    )
                )
            except Exception as exc:  # one bad case should not kill the run
                results.append(
                    CaseResult(
                        case_id=case.case_id,
                        reference=case.reference,
                        latency_ms=(time.perf_counter() - start) * 1000.0,
                        error=str(exc),
                        tags=case.tags,
                    )
                )
    finally:
        if engine is not None:
            engine.close()

    return {
        "engine": engine.name,
        "loaded": True,
        "summary": _summary(results),
        "results": [r.__dict__ for r in results],
    }


def run_bakeoff(
    cases: list[Case],
    engines: list[str],
    model_path: str | None = None,
    device: str = "cuda",
    limit: int = 0,
) -> dict[str, Any]:
    return {
        "cases": len(cases),
        "engines": {
            name: run_engine(name, cases, model_path=model_path, device=device, limit=limit)
            for name in engines
        },
    }


def write_report(report: dict[str, Any], out_dir: str | Path) -> tuple[Path, Path]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "bakeoff.json"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    csv_path = out_dir / "bakeoff.csv"
    lines = ["engine,case_id,cer,latency_ms,error,text"]
    for engine_name, data in report.get("engines", {}).items():
        for row in data.get("results", []):
            text = str(row.get("text", "")).replace('"', '""')
            error = str(row.get("error", "")).replace('"', '""')
            cer = "" if row.get("cer") is None else f"{row['cer']:.6f}"
            lines.append(
                f'{engine_name},{row.get("case_id","")},{cer},'
                f'{row.get("latency_ms",0):.3f},"{error}","{text}"'
            )
    csv_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return json_path, csv_path

