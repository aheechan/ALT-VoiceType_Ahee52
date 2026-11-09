# Third-party models and licenses

This project's own source code is licensed under **Apache-2.0**.  
Model weights are **not** part of the Git repository, but the Windows installers
published in GitHub Releases **do bundle** model weights so the app works
offline.

This file is informational. It does not replace the upstream license text or
the model card. Before commercial redistribution, verify the exact checkpoint
and its current upstream terms.

## Models bundled by the Chinese installer

| Model | Role | Upstream | License note |
|---|---|---|---|
| Qwen3-ASR-0.6B | ASR | https://huggingface.co/Qwen/Qwen3-ASR-0.6B | Apache-2.0 (verify the checkpoint card) |
| Qwen3-1.7B-Abliterated Q4 | Correction | https://huggingface.co/mradermacher/Qwen3-1.7B-abliterated-v2-i1-GGUF | Based on Qwen3-1.7B (Apache-2.0); verify the derivative model card |
| Index-Translate-2B Q4 | Translation | https://huggingface.co/IndexTeam/Index-Translate-2B-GGUF | Repository code is Apache-2.0; model weights may have separate terms — check the model card |

## Models bundled by the English installer

| Model | Role | Upstream | License note |
|---|---|---|---|
| faster-whisper small.en | ASR | https://huggingface.co/Systran/faster-whisper-small.en | faster-whisper code is MIT; model card terms apply |
| Qwen3-1.7B-Abliterated Q4 | Correction | https://huggingface.co/mradermacher/Qwen3-1.7B-abliterated-v2-i1-GGUF | Based on Qwen3-1.7B (Apache-2.0); verify the derivative model card |
| Index-Translate-2B Q4 | Translation | https://huggingface.co/IndexTeam/Index-Translate-2B-GGUF | Repository code is Apache-2.0; model weights may have separate terms — check the model card |

## Runtime components

| Component | License |
|---|---|
| PySide6 / Qt | LGPL-3.0 (dynamic linking) |
| PyTorch | BSD-3-Clause |
| Transformers, tokenizers, huggingface_hub, safetensors, accelerate | Apache-2.0 |
| faster-whisper | MIT |
| CTranslate2 | MIT |
| onnxruntime | MIT |
| PyAV / FFmpeg | BSD-style / LGPL or GPL depending on the FFmpeg build |
| NumPy | BSD-3-Clause |
| librosa | ISC |
| numba / llvmlite | BSD-2-Clause / BSD-3-Clause |
| sounddevice | MIT |
| llama.cpp | MIT |
| sherpa-onnx | Apache-2.0 |
| qwen-asr | Apache-2.0 |

## Redistribution checklist

If you redistribute an installer that contains model weights:

1. Keep `LICENSE` and `NOTICE`.
2. Keep this file and the upstream model links.
3. Include the upstream license text if the model card requires it.
4. Do not imply that the model weights are Apache-2.0 merely because the
   application code is Apache-2.0.
5. For commercial use, verify each model card and, where relevant, the
   training-data and use restrictions.

The source repository intentionally does not contain model files. Only the
Release installers contain the bundled weights.
