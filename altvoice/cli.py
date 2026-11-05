"""Command line entry points for AltVoice."""

from __future__ import annotations

import argparse
import importlib.util
import json
import platform
import shutil
import sys
from pathlib import Path

from . import __version__
from .bakeoff import load_manifest, run_bakeoff, write_report
from .config import AppConfig, TARGET_LANGUAGES, language_display, normalize_language
from .models import PROFILES, detect_vram_gb, estimate_vram, profile_models, select_profile


def _config(args: argparse.Namespace) -> AppConfig:
    return AppConfig.load(args.config)


def cmd_doctor(args: argparse.Namespace) -> int:
    cfg = _config(args)
    vram = detect_vram_gb()
    profile = select_profile(vram, cfg.profile)
    print(f"AltVoice {__version__}")
    print(f"Python:        {sys.version.split()[0]}")
    print(f"Platform:      {platform.platform()}")
    print(f"Config:        {args.config or '(default)'}")
    print(f"Models dir:    {cfg.models_dir}")
    print(f"ffmpeg:        {shutil.which('ffmpeg') or 'NOT FOUND'}")
    print(f"nvidia-smi:    {shutil.which('nvidia-smi') or 'NOT FOUND'}")
    print(f"VRAM:          {f'{vram:.1f} GB' if vram else 'not detected'}")
    print(f"Profile:       {profile}")
    for spec in profile_models(profile).values():
        print(f"  {spec.role:10} {spec.display_name:28} ~{spec.vram_gb:.1f} GB  {spec.license}")
    print("Optional packages:")
    for module in ("numpy", "sounddevice", "PySide6", "torch", "qwen_asr", "sherpa_onnx", "fireredasr"):
        print(f"  {module:14} {'yes' if importlib.util.find_spec(module) else 'no'}")
    print("ASR engines:")
    from .asr import available_engines

    for name, available in available_engines().items():
        print(f"  {name:10} {'available' if available else 'not installed'}")
    return 0


def cmd_profiles(args: argparse.Namespace) -> int:
    vram = detect_vram_gb()
    active = select_profile(vram, "auto")
    print(f"Detected VRAM: {f'{vram:.1f} GB' if vram else 'none'} -> auto profile: {active}")
    print(f"{'profile':16} {'weights':>8}  components")
    for name in PROFILES:
        models = profile_models(name)
        comps = ", ".join(f"{role}={spec.display_name}" for role, spec in models.items())
        print(f"{name:16} {estimate_vram(name):7.1f}G  {comps}")
    return 0


def cmd_bakeoff(args: argparse.Namespace) -> int:
    cases = load_manifest(args.manifest)
    if args.limit:
        cases = cases[: args.limit]
    engines = [e.strip() for e in args.engine.split(",") if e.strip()]
    if engines == ["all"]:
        engines = ["firered", "qwen3", "sherpa"]
    if args.dry_run:
        print(f"manifest: {args.manifest}")
        print(f"cases:    {len(cases)}")
        print(f"engines:  {', '.join(engines)}")
        missing = [str(c.audio) for c in cases if not c.audio.exists()]
        if missing:
            print(f"missing audio files: {len(missing)}")
            for path in missing[:5]:
                print(f"  {path}")
        return 0

    report = run_bakeoff(
        cases,
        engines,
        model_path=args.model_path,
        device=args.device,
        limit=args.limit,
    )
    out_dir = Path(args.out)
    json_path, csv_path = write_report(report, out_dir)
    for name, data in report["engines"].items():
        summary = data["summary"]
        if not data.get("loaded"):
            print(f"{name}: NOT LOADED — {data.get('error', '')}")
            continue
        cer = summary["cer_mean"]
        cer_text = f"{cer:.4f}" if cer is not None else "n/a"
        print(
            f"{name}: CER mean={cer_text} "
            f"p50={summary['latency_p50_ms']:.0f}ms "
            f"p95={summary['latency_p95_ms']:.0f}ms "
            f"ok={summary['ok']}/{summary['total']}"
        )
    print(f"report: {json_path}")
    print(f"csv:    {csv_path}")
    return 0


def cmd_transcribe(args: argparse.Namespace) -> int:
    from .asr import EngineUnavailable, create_engine

    cfg = _config(args)
    engine = None
    try:
        engine = create_engine(
            args.engine,
            model_path=args.model_path or cfg.asr.model_path,
            device=args.device or cfg.asr.device,
            language=args.language or cfg.asr.language,
            beam_size=cfg.asr.beam_size,
        )
        result = engine.transcribe(args.audio, language=args.language or cfg.asr.language)
    except EngineUnavailable as exc:
        print(f"ASR unavailable: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:
        print(f"transcription failed: {exc}", file=sys.stderr)
        return 1
    finally:
        if engine is not None:
            engine.close()
    if args.json:
        print(
            json.dumps(
                {
                    "text": result.text,
                    "language": result.language,
                    "engine": result.engine,
                    "latency_ms": result.latency_ms,
                },
                ensure_ascii=False,
            )
        )
    else:
        print(result.text)
    return 0


def cmd_translate(args: argparse.Namespace) -> int:
    from .translate import IndexTranslateTranslator, TranslationError

    cfg = _config(args)
    target = normalize_language(args.target or cfg.translator.target_language)
    if target not in TARGET_LANGUAGES:
        print(f"unknown target language: {target}", file=sys.stderr)
        return 2
    translator = IndexTranslateTranslator(
        base_url=args.base_url or cfg.translator.base_url,
        model=args.model or cfg.translator.model,
        api_key=cfg.translator.api_key,
        timeout_s=cfg.translator.timeout_s,
        max_tokens=cfg.translator.max_tokens,
    )
    try:
        print(
            translator.translate(
                args.text,
                target_lang=target,
                style=args.style or cfg.translator.style,
            )
        )
    except TranslationError as exc:
        print(f"translation failed: {exc}", file=sys.stderr)
        return 1
    finally:
        translator.close()
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="altvoice", description="Offline voice input")
    parser.add_argument("--config", default=None, help="path to config.json")
    sub = parser.add_subparsers(dest="command", required=True)

    doctor = sub.add_parser("doctor", help="show environment and model status")
    doctor.set_defaults(func=cmd_doctor)

    profiles = sub.add_parser("profiles", help="list VRAM/model profiles")
    profiles.set_defaults(func=cmd_profiles)

    bakeoff = sub.add_parser("bakeoff", help="compare ASR engines on a JSONL manifest")
    bakeoff.add_argument("--manifest", required=True)
    bakeoff.add_argument("--engine", default="all", help="all, firered, qwen3, sherpa")
    bakeoff.add_argument("--model-path", default=None)
    bakeoff.add_argument("--device", default="cuda")
    bakeoff.add_argument("--limit", type=int, default=0)
    bakeoff.add_argument("--out", default="benchmarks/results")
    bakeoff.add_argument("--dry-run", action="store_true")
    bakeoff.set_defaults(func=cmd_bakeoff)

    transcribe = sub.add_parser("transcribe", help="transcribe one audio file")
    transcribe.add_argument("audio")
    transcribe.add_argument("--engine", default="auto")
    transcribe.add_argument("--model-path", default=None)
    transcribe.add_argument("--device", default=None)
    transcribe.add_argument("--language", default=None)
    transcribe.add_argument("--json", action="store_true")
    transcribe.set_defaults(func=cmd_transcribe)

    translate = sub.add_parser("translate", help="translate one text via a local LLM")
    translate.add_argument("text")
    translate.add_argument("--target", "-t", default=None)
    translate.add_argument("--base-url", default=None)
    translate.add_argument("--model", "-m", default=None)
    translate.add_argument("--style", default=None)
    translate.set_defaults(func=cmd_translate)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
