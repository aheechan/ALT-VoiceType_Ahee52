"""Model catalog, VRAM profiles and hardware detection.

The RTX 3070 12 GB is the baseline. Profiles are deliberately conservative:
they account for the CUDA context, KV cache and a normal Windows desktop, not
just the raw weight size.
"""

from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass, replace

from .edition import current_edition


@dataclass(frozen=True)
class ModelSpec:
    key: str
    role: str  # asr | corrector | translator
    display_name: str
    params_b: float
    quant: str
    disk_gb: float
    vram_gb: float
    license: str
    source: str
    notes: str = ""
    repo: str = ""
    filename: str = ""
    kind: str = "file"  # file | dir | none


MODEL_CATALOG: dict[str, ModelSpec] = {
    "firered_asr_aed": ModelSpec(
        key="firered_asr_aed",
        role="asr",
        display_name="FireRedASR2-AED 1.1B",
        params_b=1.1,
        quant="FP16",
        disk_gb=2.2,
        vram_gb=2.5,
        license="Apache-2.0",
        source="https://github.com/FireRedTeam/FireRedASR2S",
        notes="Best Mandarin CER tier; no streaming; <=60 s audio.",
    ),
    "qwen3_asr_1_7b": ModelSpec(
        key="qwen3_asr_1_7b",
        role="asr",
        display_name="Qwen3-ASR-1.7B",
        params_b=1.7,
        quant="BF16",
        disk_gb=3.4,
        vram_gb=3.6,
        license="Apache-2.0",
        source="https://github.com/QwenLM/Qwen3-ASR",
        notes="52 languages/dialects, streaming via vLLM.",
    ),
    "qwen3_asr_1_7b_uncensored": ModelSpec(
        key="qwen3_asr_1_7b_uncensored",
        role="asr",
        display_name="Qwen3-ASR-1.7B-Uncensored",
        params_b=1.7,
        quant="BF16",
        disk_gb=4.5,
        vram_gb=3.6,
        license="Apache-2.0",
        source="https://huggingface.co/freeuser17/Qwen3-ASR-1.7B-Uncensored",
        notes="Uncensored 1.7B ASR; loaded through qwen-asr.",
    ),
    "qwen3_asr_0_6b": ModelSpec(
        key="qwen3_asr_0_6b",
        role="asr",
        display_name="Qwen3-ASR-0.6B",
        params_b=0.6,
        quant="BF16",
        disk_gb=1.2,
        vram_gb=1.5,
        license="Apache-2.0",
        source="https://github.com/QwenLM/Qwen3-ASR",
        notes="Fast 12 GB safe-profile ASR.",
    ),
    "faster_whisper_small_en": ModelSpec(
        key="faster_whisper_small_en",
        role="asr",
        display_name="faster-whisper small.en",
        params_b=0.24,
        quant="int8",
        disk_gb=0.47,
        vram_gb=0.0,
        license="MIT",
        source="https://huggingface.co/Systran/faster-whisper-small.en",
        notes="English-only CPU ASR used by the English edition.",
    ),
    "sensevoice_small": ModelSpec(
        key="sensevoice_small",
        role="asr",
        display_name="SenseVoice-Small",
        params_b=0.234,
        quant="ONNX/FP32",
        disk_gb=0.3,
        vram_gb=0.5,
        license="Apache-2.0",
        source="https://github.com/FunAudioLLM/SenseVoice",
        notes="CPU fallback via sherpa-onnx; no streaming.",
    ),
    "qwen3_1_7b_instruct_q4": ModelSpec(
        key="qwen3_1_7b_instruct_q4",
        role="corrector",
        display_name="Qwen3-1.7B-Instruct Q8",
        params_b=1.7,
        quant="Q8_0",
        disk_gb=1.8,
        vram_gb=1.9,
        license="Apache-2.0",
        source="https://huggingface.co/Qwen",
        notes="Default 12 GB corrector; official repo only ships Q8_0.",
    ),
    "qwen3_1_7b_abliterated_q4": ModelSpec(
        key="qwen3_1_7b_abliterated_q4",
        role="corrector",
        display_name="Qwen3-1.7B-Abliterated Q4",
        params_b=1.7,
        quant="Q4_K_M",
        disk_gb=1.1,
        vram_gb=1.2,
        license="Apache-2.0",
        source="https://huggingface.co/mradermacher/Qwen3-1.7B-abliterated-v2-i1-GGUF",
        notes="Uncensored alternate for the higher profiles.",
    ),
    "qwen3_4b_instruct_q4": ModelSpec(
        key="qwen3_4b_instruct_q4",
        role="corrector",
        display_name="Qwen3-4B-Instruct Q4",
        params_b=4.0,
        quant="Q4_K_M",
        disk_gb=2.5,
        vram_gb=2.6,
        license="Apache-2.0",
        source="https://huggingface.co/Qwen",
        notes="16 GB+ corrector; better names and punctuation.",
    ),
    "qwen3_4b_abliterated_q4": ModelSpec(
        key="qwen3_4b_abliterated_q4",
        role="translator",
        display_name="Qwen3-4B-Abliterated Q4",
        params_b=4.0,
        quant="Q4_K_M",
        disk_gb=2.4,
        vram_gb=2.5,
        license="Apache-2.0",
        source="https://huggingface.co/mradermacher/Huihui-Qwen3-4B-Instruct-2507-abliterated-GGUF",
        notes="Uncensored 4B translation for the 16 GB tier.",
    ),
    "rules_only": ModelSpec(
        key="rules_only",
        role="corrector",
        display_name="Rules only (no LLM)",
        params_b=0.0,
        quant="deterministic rules",
        disk_gb=0.0,
        vram_gb=0.0,
        license="Apache-2.0",
        source="built-in",
        notes="CPU-safe profile: no LLM correction, only punctuation/terms guards.",
    ),
    "index_translate_9b_q4": ModelSpec(
        key="index_translate_9b_q4",
        role="translator",
        display_name="Index-Translate-9B Q4",
        params_b=9.0,
        quant="Q4_K_M",
        disk_gb=5.5,
        vram_gb=5.7,
        license="Check model card",
        source="https://github.com/bilibili/Index-Translate",
        notes="Chinese-centric translation; verify weight license.",
    ),
    "index_translate_2b_q4": ModelSpec(
        key="index_translate_2b_q4",
        role="translator",
        display_name="Index-Translate-2B Q4",
        params_b=2.0,
        quant="Q4_K_M",
        disk_gb=1.5,
        vram_gb=1.6,
        license="Check model card",
        source="https://github.com/bilibili/Index-Translate",
        notes="Fallback for OOM/CPU profiles.",
    ),
}

# Upstream repositories and expected artifact names. GGUF names are examples;
# always check the repository file list before downloading.
_MODEL_SOURCES: dict[str, tuple[str, str, str]] = {
    "firered_asr_aed": ("FireRedTeam/FireRedASR2-AED", "", "dir"),
    "qwen3_asr_1_7b": ("Qwen/Qwen3-ASR-1.7B", "", "dir"),
    "qwen3_asr_1_7b_uncensored": ("freeuser17/Qwen3-ASR-1.7B-Uncensored", "", "dir"),
    "qwen3_asr_0_6b": ("Qwen/Qwen3-ASR-0.6B", "", "dir"),
    "sensevoice_small": ("iic/SenseVoiceSmall", "", "dir"),
    "qwen3_1_7b_instruct_q4": (
        "Qwen/Qwen3-1.7B-GGUF",
        "Qwen3-1.7B-Q8_0.gguf",
        "file",
    ),
    "qwen3_1_7b_abliterated_q4": (
        "mradermacher/Qwen3-1.7B-abliterated-v2-i1-GGUF",
        "Qwen3-1.7B-abliterated-v2.i1-Q4_K_M.gguf",
        "file",
    ),
    "qwen3_4b_instruct_q4": (
        "Qwen/Qwen3-4B-GGUF",
        "Qwen3-4B-Q4_K_M.gguf",
        "file",
    ),
    "qwen3_4b_abliterated_q4": (
        "mradermacher/Huihui-Qwen3-4B-Instruct-2507-abliterated-GGUF",
        "Huihui-Qwen3-4B-Instruct-2507-abliterated.Q4_K_M.gguf",
        "file",
    ),
    "rules_only": ("", "", "none"),
    "index_translate_9b_q4": (
        "IndexTeam/Index-Translate-9B-GGUF",
        "Index-Translate-9B.Q4_K_M.gguf",
        "file",
    ),
    "index_translate_2b_q4": (
        "IndexTeam/Index-Translate-2B-GGUF",
        "Index-Translate-2B.Q4_K_M.gguf",
        "file",
    ),
}
for _key, (_repo, _filename, _kind) in _MODEL_SOURCES.items():
    if _key in MODEL_CATALOG:
        MODEL_CATALOG[_key] = replace(
            MODEL_CATALOG[_key], repo=_repo, filename=_filename, kind=_kind
        )


PROFILE_ORDER: list[str] = [
    "12gb-safe",
    "12gb-balanced",
    "12gb-max",
]
PROFILE_LABELS: dict[str, str] = {
    "12gb-safe": "eco · 20s · CPU",
    "12gb-balanced": "standard · 45s · GPU",
    "12gb-max": "extended · 120s · GPU",
}

PROFILES: dict[str, dict[str, str]] = {
    "12gb-safe": {
        "description": "20s 输入上限 · CPU 全模型 · 最低资源",
        "duration_s": "20",
        "asr": "qwen3_asr_0_6b",
        "corrector": "qwen3_1_7b_abliterated_q4",
        "translator": "index_translate_2b_q4",
    },
    "12gb-balanced": {
        "description": "45s 输入上限 · 全 GPU · 标准速度",
        "duration_s": "45",
        "asr": "qwen3_asr_0_6b",
        "corrector": "qwen3_1_7b_abliterated_q4",
        "translator": "index_translate_2b_q4",
    },
    "12gb-max": {
        "description": "120s 输入上限 · 全 GPU · 高资源",
        "duration_s": "120",
        "asr": "qwen3_asr_0_6b",
        "corrector": "qwen3_1_7b_abliterated_q4",
        "translator": "index_translate_2b_q4",
    },
    "cpu-safe": {
        "description": "CPU-only fallback (hidden)",
        "duration_s": "20",
        "asr": "sensevoice_small",
        "corrector": "rules_only",
        "translator": "index_translate_2b_q4",
    },
}


def detect_vram_gb() -> float | None:
    """Return the largest NVIDIA GPU memory in GB, or None when unavailable."""
    exe = shutil.which("nvidia-smi")
    if not exe:
        return None
    try:
        proc = subprocess.run(
            [
                exe,
                "--query-gpu=memory.total",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    values: list[float] = []
    for line in proc.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            values.append(float(line.split(",")[0].strip()) / 1024.0)
        except ValueError:
            continue
    return max(values) if values else None


def select_profile(vram_gb: float | None = None, requested: str = "auto") -> str:
    if requested and requested != "auto":
        if requested not in PROFILES:
            raise ValueError(f"unknown profile {requested!r}; choose from {', '.join(PROFILES)}")
        return requested
    if vram_gb is None:
        return "cpu-safe"
    if vram_gb < 6:
        return "cpu-safe"
    if vram_gb < 10:
        return "12gb-safe"
    if vram_gb < 16:
        return "12gb-balanced"
    return "12gb-max"


def profile_models(profile: str) -> dict[str, ModelSpec]:
    if profile not in PROFILES:
        raise ValueError(f"unknown profile {profile!r}")
    cfg = PROFILES[profile]
    asr_key = cfg["asr"]
    if current_edition().code == "en":
        asr_key = "faster_whisper_small_en"
    return {
        role: MODEL_CATALOG[key]
        for role, key in (("asr", asr_key), ("corrector", cfg["corrector"]), ("translator", cfg["translator"]))
    }


def estimate_vram(profile: str) -> float:
    return sum(spec.vram_gb for spec in profile_models(profile).values())


def profile_summary(profile: str) -> str:
    models = profile_models(profile)
    return (
        f"{profile}: ASR={models['asr'].display_name}, "
        f"corrector={models['corrector'].display_name}, "
        f"translator={models['translator'].display_name}, "
        f"weights~{estimate_vram(profile):.1f} GB"
    )

