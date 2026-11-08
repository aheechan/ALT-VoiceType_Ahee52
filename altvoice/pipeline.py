"""Pipeline orchestration: ASR -> correction -> translation -> injection."""

from __future__ import annotations

import time
from dataclasses import dataclass, field

from .asr import ASREngine, ASRResult
from .config import normalize_language
from .context import ContextStore
from .correct import CorrectionResult, Corrector, NullCorrector
from .inject import InjectionError, Injector, NullInjector
from .numerals import normalize_numbers
from .translate import NullTranslator, TranslationError, Translator


@dataclass
class PipelineResult:
    raw_text: str
    corrected_text: str
    translation: str
    target_lang: str
    source_lang: str = "zh"
    engine: str = ""
    asr_latency_ms: float = 0.0
    correct_latency_ms: float = 0.0
    translate_latency_ms: float = 0.0
    total_latency_ms: float = 0.0
    correction_risk: float = 0.0
    injected: bool = False
    error: str = ""
    context: list[dict[str, str]] = field(default_factory=list)

    @property
    def output_text(self) -> str:
        return self.translation if self.translation else self.corrected_text


class VoicePipeline:
    def __init__(
        self,
        asr: ASREngine,
        corrector: Corrector | None = None,
        translator: Translator | None = None,
        injector: Injector | None = None,
        context: ContextStore | None = None,
        style: str = "daily",
        glossary: dict[str, str] | None = None,
        source_language: str = "zh",
    ) -> None:
        self.asr = asr
        self.corrector = corrector or NullCorrector()
        self.translator = translator or NullTranslator()
        self.injector = injector or NullInjector()
        self.context = context or ContextStore()
        self.style = style
        self.source_language = source_language or "zh"
        if glossary:
            self.context.set_glossary(glossary)

    def process_audio(
        self,
        audio_path: str,
        target_lang: str = "zh",
        inject: bool = True,
        scene: str | None = None,
        on_status=None,
    ) -> PipelineResult:
        status = on_status or (lambda _message: None)
        start = time.perf_counter()
        status("识别中…")
        asr_result: ASRResult = self.asr.transcribe(audio_path, language=self.source_language)
        elapsed = (time.perf_counter() - start) * 1000.0
        result = self.process_text(
            asr_result.text,
            target_lang=target_lang,
            inject=inject,
            scene=scene,
            source_lang=asr_result.language or "zh",
            on_status=status,
        )
        result.engine = asr_result.engine
        result.asr_latency_ms = asr_result.latency_ms or elapsed
        result.total_latency_ms = (time.perf_counter() - start) * 1000.0
        return result

    def process_text(
        self,
        raw_text: str,
        target_lang: str = "zh",
        inject: bool = True,
        scene: str | None = None,
        source_lang: str = "zh",
        app: str = "",
        on_status=None,
    ) -> PipelineResult:
        status = on_status or (lambda _message: None)
        start = time.perf_counter()
        raw_text = (raw_text or "").strip()
        target = normalize_language(target_lang) or "zh"
        source = normalize_language(source_lang) or "zh"
        active_scene = scene or self.context.scene

        status("纠错中…")
        correct_start = time.perf_counter()
        correction: CorrectionResult = self.corrector.correct(
            raw_text,
            context=self.context.recent(5),
            glossary=self.context.glossary,
            scene=active_scene,
        )
        correct_ms = (time.perf_counter() - correct_start) * 1000.0
        corrected = correction.text.strip() or raw_text
        corrected = normalize_numbers(corrected)

        translation = corrected
        translate_ms = 0.0
        error = ""
        if target != source:
            status("翻译中…")
            translate_start = time.perf_counter()
            try:
                translation = self.translator.translate(
                    corrected,
                    target_lang=target,
                    context=self.context.recent(3),
                    style=self.style,
                    glossary=self.context.glossary,
                    source_lang=source,
                )
            except TranslationError as exc:
                # Keep the corrected source text and report the failure; the UI
                # can show it in the preview instead of blocking dictation.
                translation = corrected
                error = str(exc)
            translate_ms = (time.perf_counter() - translate_start) * 1000.0

        injected = False
        if inject:
            try:
                self.injector.inject(translation)
                injected = True
            except InjectionError as exc:
                error = f"{error}; injection: {exc}".strip("; ")

        self.context.add(
            source=raw_text,
            corrected=corrected,
            translation=translation if target != source else "",
            app=app,
            scene=active_scene,
        )

        return PipelineResult(
            raw_text=raw_text,
            corrected_text=corrected,
            translation=translation,
            target_lang=target,
            source_lang=source,
            correct_latency_ms=correct_ms,
            translate_latency_ms=translate_ms,
            total_latency_ms=(time.perf_counter() - start) * 1000.0,
            correction_risk=correction.risk,
            injected=injected,
            error=error,
            context=self.context.recent(5),
        )

    def close(self) -> None:
        for obj in (self.asr, self.corrector, self.translator):
            close = getattr(obj, "close", None)
            if callable(close):
                close()

