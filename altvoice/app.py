"""Application controller: hotkey -> record -> pipeline -> UI callback.

This module has no Qt dependency so it can be tested headlessly. The tray UI in
``altvoice.ui.tray`` is a thin adapter over this controller.
"""

from __future__ import annotations

import os
import tempfile
import threading
import time
from pathlib import Path
from typing import Callable

from .asr import create_engine
from .audio import AudioRecorder, trim_silence, write_wav
from .config import AppConfig, normalize_language
from .context import ContextStore
from .correct import LLMCorrector, NullCorrector
from .history import HistoryStore, default_history_path
from .inject import InjectionError, get_injector
from .models import detect_vram_gb, select_profile
from .pipeline import PipelineResult, VoicePipeline
from .servers import ServerManager
from .translate import IndexTranslateTranslator, NullTranslator


class VoiceAppController:
    def __init__(
        self,
        config: AppConfig | None = None,
        config_path: str | Path | None = None,
        on_status: Callable[[str], None] | None = None,
        on_result: Callable[[PipelineResult], None] | None = None,
        on_error: Callable[[str], None] | None = None,
        on_audio_level: Callable[[float], None] | None = None,
        recorder=None,
        pipeline: VoicePipeline | None = None,
        temp_dir: str | None = None,
    ) -> None:
        self.config = config or AppConfig.load(config_path)
        self._config_path = str(config_path) if config_path else None
        self.profile = select_profile(detect_vram_gb(), self.config.profile)
        self.target_lang = normalize_language(self.config.translator.target_language) or "zh"
        self.mode = "translate"
        self.on_status = on_status or (lambda _msg: None)
        self.on_result = on_result or (lambda _result: None)
        self.on_error = on_error or (lambda _msg: None)
        self.on_audio_level = on_audio_level or (lambda _level: None)
        self._recorder = recorder
        self._pipeline = pipeline
        self._pipeline_lock = threading.RLock()
        self._warming = False
        self._servers: ServerManager | None = None
        self._temp_dir = temp_dir
        self._lock = threading.RLock()
        self._bootstrap_model_paths(config_provided=config is not None)
        self._recording = False
        self._cancelled = False
        self._stop_event: threading.Event | None = None
        self._pending_stop: threading.Timer | None = None
        self._thread: threading.Thread | None = None
        self._last_result: PipelineResult | None = None
        self._target_hwnd = 0
        self.history: HistoryStore | None = None
        if self.config.history.enabled:
            try:
                self.history = HistoryStore(
                    self.config.history.path or default_history_path(),
                    retention_days=self.config.history.retention_days,
                    max_entries=self.config.history.max_entries,
                )
            except Exception as exc:
                self.on_error(f"历史记录不可用：{exc}")
        self._cleanup_temp_audio()

    def _bootstrap_model_paths(self, config_provided: bool = False) -> None:
        """Fill omitted model paths for a fresh installed build."""
        if config_provided:
            return
        cfg = self.config
        if cfg.asr.model_path and cfg.corrector.model_path and cfg.translator.model_path:
            return
        from .setup_wizard import build_config

        try:
            fresh = build_config(self.profile, cfg.models_dir, self.target_lang)
        except Exception as exc:
            self.on_error(f"模型配置初始化失败：{exc}")
            return
        fresh.hotkey = cfg.hotkey
        fresh.ui = cfg.ui
        fresh.injection = cfg.injection
        fresh.history = cfg.history
        fresh.servers.binary = cfg.servers.binary
        fresh.servers.host = cfg.servers.host
        fresh.servers.log_dir = cfg.servers.log_dir
        self.config = fresh
        self.target_lang = normalize_language(fresh.translator.target_language) or "zh"
        if self._config_path:
            try:
                fresh.save(self._config_path)
            except OSError:
                pass

    def _cleanup_temp_audio(self) -> None:
        """Remove orphaned WAV files left by a crash or forced shutdown."""
        cutoff = time.time() - 3600
        directory = Path(self._temp_dir or tempfile.gettempdir())
        try:
            for path in directory.glob("altvoice_*.wav"):
                try:
                    if path.stat().st_mtime < cutoff:
                        path.unlink()
                except OSError:
                    pass
        except OSError:
            pass

    @property
    def recording(self) -> bool:
        return self._recording

    @property
    def last_result(self) -> PipelineResult | None:
        return self._last_result

    def ensure_pipeline(self) -> VoicePipeline:
        with self._pipeline_lock:
            if self._pipeline is not None:
                return self._pipeline
            cfg = self.config
            self.on_status(f"加载 ASR（{cfg.asr.engine}）…")
            engine = create_engine(
                cfg.asr.engine,
                model_path=cfg.asr.model_path,
                device=cfg.asr.device,
                language=cfg.asr.language,
                beam_size=cfg.asr.beam_size,
            )
            self.on_status("预热 ASR…")
            engine.load()
            if cfg.servers.enabled:
                self._servers = ServerManager.from_config(cfg, self.profile)
                self.on_status("预热中…")
                for error in self._servers.start_all(on_status=self.on_status):
                    self.on_error(error)
            failed_servers = self._servers.failed if self._servers is not None else set()
            corrector = NullCorrector()
            if (
                cfg.corrector.enabled
                and self.profile != "cpu-safe"
                and "corrector" not in failed_servers
            ):
                corrector = LLMCorrector(
                    base_url=cfg.corrector.base_url,
                    model=cfg.corrector.model,
                    api_key=cfg.corrector.api_key,
                    timeout_s=cfg.corrector.timeout_s,
                    max_edit_ratio=cfg.corrector.max_edit_ratio,
                    max_tokens=cfg.corrector.max_tokens,
                )
            translator = NullTranslator()
            if cfg.translator.enabled and "translator" not in failed_servers:
                translator = IndexTranslateTranslator(
                    base_url=cfg.translator.base_url,
                    model=cfg.translator.model,
                    api_key=cfg.translator.api_key,
                    timeout_s=cfg.translator.timeout_s,
                    max_tokens=cfg.translator.max_tokens,
                )
            injector = get_injector(
                cfg.injection.method,
                restore_clipboard=cfg.injection.restore_clipboard,
            )
            context = ContextStore(scene="daily")
            if self.history is not None:
                context.set_glossary(self.history.get_glossary())
                for item in self.history.recent(5):
                    context.add(
                        source=item["source"],
                        corrected=item["corrected"],
                        translation=item["translation"],
                        app=item["app"],
                        scene=item["scene"],
                    )
            self._pipeline = VoicePipeline(
                asr=engine,
                corrector=corrector,
                translator=translator,
                injector=injector,
                context=context,
                style=cfg.translator.style,
                source_language=cfg.asr.language,
            )
            self.on_status("加载完毕，可以开始输入")
            return self._pipeline

    def warm_up(self) -> None:
        """Load the ASR pipeline in the background.

        The low-level keyboard hook must never block on a multi-second model
        load, so the tray starts this before the user presses Alt.
        """
        with self._pipeline_lock:
            if self._pipeline is not None or self._warming:
                return
            self._warming = True

        def worker() -> None:
            try:
                self.ensure_pipeline()
            except Exception as exc:
                self.on_error(f"模型加载失败：{exc}")
            finally:
                self._warming = False

        threading.Thread(target=worker, name="altvoice-warmup", daemon=True).start()

    def reload_profile(self, profile: str) -> None:
        """Stop the old models, rebuild model paths, and warm the new profile."""
        from .setup_wizard import build_config

        with self._pipeline_lock:
            self.cancel_recording()
            if self._thread is not None:
                self._thread.join(timeout=2.0)
            if self._pipeline is not None:
                try:
                    self._pipeline.close()
                except Exception:
                    pass
                self._pipeline = None
            if self._servers is not None:
                try:
                    self._servers.stop_all()
                except Exception:
                    pass
                self._servers = None
            old = self.config
            try:
                new = build_config(profile, old.models_dir, old.translator.target_language)
            except Exception as exc:
                self.on_error(f"切换模型档位失败：{exc}")
                return
            new.hotkey = old.hotkey
            old_audio = old.audio
            new.audio.samplerate = old_audio.samplerate
            new.audio.channels = old_audio.channels
            new.audio.device = old_audio.device
            new.audio.trim_silence = old_audio.trim_silence
            new.audio.silence_threshold = old_audio.silence_threshold
            new.audio.padding_ms = old_audio.padding_ms
            new.ui = old.ui
            new.injection = old.injection
            new.history = old.history
            old_servers = old.servers
            new.servers.binary = old_servers.binary
            new.servers.host = old_servers.host
            new.servers.startup_timeout_s = old_servers.startup_timeout_s
            new.servers.log_dir = old_servers.log_dir
            new.servers.extra_args = old_servers.extra_args
            new.servers.context_size = old_servers.context_size
            self.config = new
            self.profile = profile
            self.target_lang = normalize_language(new.translator.target_language) or "zh"
            if self._config_path:
                try:
                    new.save(self._config_path)
                except OSError:
                    pass
            self.on_status(f"已切换 {profile}，正在清理并加载模型…")
        self.warm_up()

    def _ensure_recorder(self) -> AudioRecorder:
        if self._recorder is None:
            self._recorder = AudioRecorder(
                samplerate=self.config.audio.samplerate,
                channels=self.config.audio.channels,
                device=self.config.audio.device,
                on_level=self.on_audio_level,
            )
        return self._recorder

    def toggle_recording(self) -> None:
        if self._recording:
            self.stop_recording()
        else:
            self.start_recording()

    def start_recording(self) -> None:
        with self._lock:
            if self._recording:
                return
            if self._pipeline is None:
                if self._warming:
                    self.on_error("模型加载中，请稍候再按 Alt")
                else:
                    self.on_error("模型未就绪，请运行 altvoice health 检查环境")
                return
            try:
                self._ensure_recorder()
            except Exception as exc:
                self.on_error(str(exc))
                return
            self._cancelled = False
            if self._pending_stop is not None:
                self._pending_stop.cancel()
                self._pending_stop = None
            self._target_hwnd = (
                self._foreground_window() if self.config.ui.focus_guard else 0
            )
            self._stop_event = threading.Event()
            self._recording = True
            self._thread = threading.Thread(
                target=self._record_worker,
                name="altvoice-record",
                daemon=True,
            )
            self._thread.start()
            self.on_status(
                "录音中…再按 Alt 结束"
                if self.config.hotkey.mode == "toggle_alt"
                else "录音中…松开 Alt 结束"
            )

    def stop_recording(self, delay_s: float = 0.0) -> None:
        """Stop capture now, or after a short tail so final words are kept."""
        if delay_s > 0:
            with self._lock:
                if self._pending_stop is not None or self._stop_event is None:
                    return
                self.on_status(f"收尾 {delay_s:.2f} 秒…")
                timer = threading.Timer(delay_s, self._finish_stop)
                timer.daemon = True
                self._pending_stop = timer
                timer.start()
            return
        self._finish_stop()

    def _finish_stop(self) -> None:
        with self._lock:
            self._pending_stop = None
            if self._stop_event is not None:
                self._stop_event.set()
                self.on_status("识别中…")

    def cancel_recording(self) -> None:
        with self._lock:
            self._cancelled = True
            if self._pending_stop is not None:
                self._pending_stop.cancel()
                self._pending_stop = None
            if self._stop_event is not None:
                self._stop_event.set()
            self.on_status("已取消")

    def _record_worker(self) -> None:
        stop_event = self._stop_event
        assert stop_event is not None
        temp_path: str | None = None
        try:
            samples, sample_rate = self._recorder.record_push_to_talk(
                stop_event,
                max_seconds=self.config.audio.max_seconds,
            )
            if self._cancelled:
                return
            if len(samples) == 0:
                self.on_error("没有录到声音，请检查麦克风")
                return
            if self.config.audio.trim_silence:
                samples = trim_silence(
                    samples,
                    sample_rate,
                    threshold=self.config.audio.silence_threshold,
                    padding_ms=self.config.audio.padding_ms,
                )
            if len(samples) < sample_rate * 0.15:
                self.on_error("语音太短，请再说一次")
                return
            fd, temp_path = tempfile.mkstemp(
                prefix="altvoice_",
                suffix=".wav",
                dir=self._temp_dir,
            )
            os.close(fd)
            write_wav(temp_path, samples, sample_rate)
            assert self._pipeline is not None
            result = self._pipeline.process_audio(
                temp_path,
                target_lang=self._effective_target(),
                inject=False,
                on_status=self.on_status,
            )
            if self._cancelled:
                return
            self._last_result = result
            if self.history is not None:
                try:
                    self.history.add_utterance(
                        source=result.raw_text,
                        corrected=result.corrected_text,
                        translation=result.translation if result.target_lang != result.source_lang else "",
                        target_lang=result.target_lang,
                        source_lang=result.source_lang,
                    )
                except Exception as exc:
                    self.on_error(f"写入历史失败：{exc}")
            if result.error:
                self.on_error(result.error)
            # Always paste at the caret; the preview setting only controls whether
            # the main window is brought forward with the two result panels.
            if self.config.ui.focus_guard:
                self.restore_target_focus()
            self._deliver(result, result.output_text)
            self.on_result(result)
        except Exception as exc:
            if not self._cancelled:
                self.on_error(f"识别失败：{exc}")
        finally:
            if temp_path:
                try:
                    os.unlink(temp_path)
                except OSError:
                    pass
            with self._lock:
                self._recording = False
                self._stop_event = None
                self._thread = None

    def _effective_target(self) -> str:
        if self.mode == "transcribe":
            return self.config.asr.language or "zh"
        return self.target_lang

    def commit(self, result: PipelineResult | None = None, text: str | None = None) -> None:
        result = result or self._last_result
        if result is None:
            return
        payload = (text if text is not None else result.output_text).strip()
        if not payload:
            self.on_error("没有可插入的文本")
            return
        self._deliver(result, payload)

    def _deliver(self, result: PipelineResult, payload: str) -> None:
        if (
            self.config.ui.focus_guard
            and self._target_hwnd
            and self._foreground_window() not in (0, self._target_hwnd)
        ):
            try:
                self._copy_to_clipboard(payload)
                self.on_error("焦点已切换，文本已复制到剪贴板，未自动插入")
            except Exception as exc:
                self.on_error(f"焦点已切换，无法自动插入：{exc}")
            return
        assert self._pipeline is not None
        try:
            self._pipeline.injector.inject(payload)
        except InjectionError as exc:
            self.on_error(f"无法插入文本：{exc}")
            return
        result.injected = True
        self.on_status("已插入")

    @staticmethod
    def _foreground_window() -> int:
        if os.name != "nt":
            return 0
        try:
            from .inject.windows import get_foreground_window

            return get_foreground_window()
        except Exception:
            return 0

    @staticmethod
    def _copy_to_clipboard(text: str) -> None:
        if os.name != "nt":
            raise InjectionError("clipboard fallback is Windows-only")
        from .inject.windows import set_clipboard_text

        set_clipboard_text(text)

    def restore_target_focus(self) -> bool:
        """Best-effort refocus of the window captured at recording start."""
        if os.name != "nt" or not self._target_hwnd:
            return False
        try:
            from .inject.windows import set_foreground_window

            return set_foreground_window(self._target_hwnd)
        except Exception:
            return False

    def set_target_lang(self, code: str) -> None:
        code = normalize_language(code)
        if code:
            self.target_lang = code
            self.mode = "translate"
            self.config.translator.target_language = code
            if self._config_path:
                try:
                    self.config.save(self._config_path)
                except OSError:
                    pass
            self.on_status(f"输出语言：{code}")

    def set_mode(self, mode: str) -> None:
        if mode not in {"translate", "transcribe"}:
            raise ValueError(f"unknown mode: {mode}")
        self.mode = mode
        self.on_status("模式：中文转写" if mode == "transcribe" else "模式：翻译")

    def close(self) -> None:
        self.cancel_recording()
        if self._pipeline is not None:
            self._pipeline.close()
        if self._servers is not None:
            self._servers.stop_all()
        if self.history is not None:
            self.history.close()

