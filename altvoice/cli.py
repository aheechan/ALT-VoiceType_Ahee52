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
    print(f"ALT-VoiceType {__version__}")
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
    from .model_store import locations

    print("Model files:")
    for item in locations(cfg, profile):
        print(f"  [{'OK' if item.exists else 'MISSING':7}] {item.path}")
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


def cmd_history(args: argparse.Namespace) -> int:
    cfg = _config(args)
    if not cfg.history.enabled:
        print("History is disabled in config.json.")
        return 0
    from .history import HistoryStore, default_history_path

    path = cfg.history.path or default_history_path()
    try:
        store = HistoryStore(path)
    except OSError as exc:
        print(f"History unavailable: {exc}", file=sys.stderr)
        return 2
    try:
        if args.clear:
            store.clear()
            print(f"Cleared history: {path}")
            return 0
        items = store.recent(args.limit)
        print(f"History: {path} ({len(items)} shown)")
        for item in items:
            translation = f" -> {item['translation']}" if item["translation"] else ""
            print(f"  {item['corrected']}{translation}")
        return 0
    finally:
        store.close()


def cmd_download(args: argparse.Namespace) -> int:
    cfg = _config(args)
    profile = args.profile or select_profile(detect_vram_gb(), cfg.profile)
    from .downloader import download_profile

    errors = download_profile(cfg, profile, progress=print)
    if errors:
        print("\nDownload errors:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1
    print("Model download complete.")
    return 0


def cmd_audio(args: argparse.Namespace) -> int:
    try:
        import sounddevice as sd
    except ImportError:
        print("sounddevice is not installed; pip install 'altvoice[audio]'", file=sys.stderr)
        return 2

    if args.list:
        default = sd.default.device
        print(f"default devices: {default}")
        for index, device in enumerate(sd.query_devices()):
            if device.get("max_input_channels", 0) <= 0:
                continue
            print(
                f"  [{index}] {device['name']}  "
                f"in={device['max_input_channels']}  "
                f"rate={device.get('default_samplerate')}"
            )
        return 0

    from .audio import AudioRecorder, write_wav

    try:
        recorder = AudioRecorder(
            samplerate=16000,
            channels=1,
            device=args.device,
        )
        samples, rate = recorder.record(max_seconds=args.seconds)
    except Exception as exc:
        print(f"recording failed: {exc}", file=sys.stderr)
        return 1
    if len(samples) == 0:
        print("no audio captured", file=sys.stderr)
        return 1
    write_wav(args.out, samples, rate)
    print(f"wrote {args.out} ({len(samples) / rate:.1f}s at {rate} Hz)")
    return 0


def cmd_health(args: argparse.Namespace) -> int:
    cfg = _config(args)
    from .health import check_health, format_report

    report = check_health(cfg, check_servers=args.servers)
    print(format_report(report, config=cfg, show_commands=not args.no_commands))
    return 0 if report.ready else 1


def cmd_setup(args: argparse.Namespace) -> int:
    from .setup_wizard import run_setup

    return run_setup(
        profile=args.profile,
        models_dir=args.models_dir,
        target_language=args.target,
        config_path=args.config,
        force=args.force,
        print_only=args.print_only,
        show_commands=not args.no_commands,
    )


def cmd_models(args: argparse.Namespace) -> int:
    cfg = _config(args)
    profile = args.profile or select_profile(detect_vram_gb(), cfg.profile)
    from .model_store import all_present, download_commands, locations

    items = locations(cfg, profile)
    print(f"Profile: {profile}")
    for item in items:
        mark = "OK" if item.exists else "MISSING"
        print(f"  [{mark:7}] {item.role:10} {item.display_name:28} {item.path}")
    if args.commands:
        print("\nDownload commands (verify file names on the repository):")
        for command in download_commands(cfg, profile):
            print(command)
    if args.check and not all_present(cfg, profile):
        return 1
    return 0


def cmd_servers(args: argparse.Namespace) -> int:
    cfg = _config(args)
    profile = select_profile(detect_vram_gb(), cfg.profile)
    from .servers import ServerManager

    manager = ServerManager.from_config(cfg, profile)
    if not manager.servers:
        print("No autostart model servers configured.")
        print("Set corrector.model_path / translator.model_path in config.json.")
        return 0
    for server in manager.servers:
        spec = server.spec
        print(
            f"{spec.name:10} {spec.model_path}\n"
            f"           {spec.health_url()}  ready={server.is_ready()}"
        )
        if args.command:
            print("           " + " ".join(spec.command()))
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    try:
        from .ui.tray import run_tray
    except SystemExit as exc:
        print(f"Tray UI unavailable: {exc}", file=sys.stderr)
        return 2
    return run_tray(args.config, smoke_seconds=args.smoke)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="altvoice", description="Offline voice input")
    parser.add_argument("--config", default=None, help="path to config.json")
    sub = parser.add_subparsers(dest="command", required=True)

    doctor = sub.add_parser("doctor", help="show environment and model status")
    doctor.set_defaults(func=cmd_doctor)

    health = sub.add_parser("health", help="check whether the app is ready to run")
    health.add_argument("--servers", action="store_true", help="also probe configured model servers")
    health.add_argument("--no-commands", action="store_true")
    health.set_defaults(func=cmd_health)

    audio = sub.add_parser("audio", help="list microphones or record a test WAV")
    audio.add_argument("--list", action="store_true")
    audio.add_argument("--seconds", type=float, default=3.0)
    audio.add_argument("--out", default="altvoice-test.wav")
    audio.add_argument("--device", type=int, default=None)
    audio.set_defaults(func=cmd_audio)

    history = sub.add_parser("history", help="show or clear local dictation history")
    history.add_argument("--limit", type=int, default=10)
    history.add_argument("--clear", action="store_true")
    history.set_defaults(func=cmd_history)

    profiles = sub.add_parser("profiles", help="list VRAM/model profiles")
    profiles.set_defaults(func=cmd_profiles)

    models = sub.add_parser("models", help="check model files and print download commands")
    models.add_argument("--profile", default=None)
    models.add_argument("--check", action="store_true", help="exit 1 when a model is missing")
    models.add_argument("--commands", action="store_true")
    models.set_defaults(func=cmd_models)

    download = sub.add_parser("download", help="download missing Hugging Face models")
    download.add_argument("--profile", default=None)
    download.set_defaults(func=cmd_download)

    setup = sub.add_parser("setup", help="write a first-run config with model paths")
    setup.add_argument("--profile", default="12gb-balanced")
    setup.add_argument("--models-dir", default=None)
    setup.add_argument("--target", "-t", default="en")
    setup.add_argument("--force", action="store_true")
    setup.add_argument("--print-only", action="store_true")
    setup.add_argument("--no-commands", action="store_true")
    setup.set_defaults(func=cmd_setup)

    run = sub.add_parser("run", help="start the system-tray voice input app")
    run.add_argument(
        "--smoke",
        type=float,
        default=0.0,
        help="start the tray, wait N seconds, then exit (for desktop/package checks)",
    )
    run.set_defaults(func=cmd_run)

    servers = sub.add_parser("servers", help="show configured llama.cpp servers")
    servers.add_argument("--command", action="store_true", help="print the launch command")
    servers.set_defaults(func=cmd_servers)

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
    args_list = sys.argv[1:] if argv is None else list(argv)
    # Double-clicking the windowed exe starts it with no arguments. Start the
    # tray instead of printing an argparse usage error.
    if not args_list:
        args_list = ["run"]
    args = parser.parse_args(args_list)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
