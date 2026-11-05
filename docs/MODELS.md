# Models, sizes and licenses

AltVoice does not ship model weights. Download them from the official repositories and place them
under `%LOCALAPPDATA%\AltVoice\models` (or set `models_dir` in `config.json`).

## Catalog

| Key | Role | Params | Quant | Disk | VRAM | License | Source |
|---|---|---:|---|---:|---:|---|---|
| `firered_asr_aed` | ASR | 1.1B | FP16 | ~2.2 GB | ~2.5 GB | Apache-2.0 | [FireRedASR2S](https://github.com/FireRedTeam/FireRedASR2S) |
| `qwen3_asr_1_7b` | ASR | 1.7B | BF16 | ~3.4 GB | ~3.6 GB | Apache-2.0 | [Qwen3-ASR](https://github.com/QwenLM/Qwen3-ASR) |
| `qwen3_asr_0_6b` | ASR | 0.6B | BF16 | ~1.2 GB | ~1.5 GB | Apache-2.0 | [Qwen3-ASR](https://github.com/QwenLM/Qwen3-ASR) |
| `sensevoice_small` | ASR | 234M | FP32/ONNX | ~0.3 GB | ~0.5 GB | Apache-2.0 | [SenseVoice](https://github.com/FunAudioLLM/SenseVoice) |
| `qwen3_1_7b_instruct_q4` | Corrector | 1.7B | Q4_K_M | ~1.2 GB | ~1.3 GB | Apache-2.0 | Qwen3 |
| `qwen3_4b_instruct_q4` | Corrector | 4B | Q4_K_M | ~2.5 GB | ~2.6 GB | Apache-2.0 | Qwen3 |
| `rules_only` | Corrector | — | rules | 0 | 0 | Apache-2.0 | built-in (CPU profile) |
| `index_translate_9b_q4` | Translator | 9B | Q4_K_M | ~5.5 GB | ~5.7 GB | check model card | [Index-Translate](https://github.com/bilibili/Index-Translate) |
| `index_translate_2b_q4` | Translator | 2B | Q4_K_M | ~1.5 GB | ~1.6 GB | check model card | Index-Translate |

Sizes are approximate and vary by quantizer/revision. Always verify the SHA256 of downloaded files.

## Recommended 12 GB setup (RTX 3070)

1. **ASR:** FireRedASR2-AED, FP16.
2. **Corrector:** Qwen3-1.7B-Instruct, Q4_K_M, served by llama.cpp on `127.0.0.1:8091`.
3. **Translator:** Index-Translate-9B, Q4_K_M, served by llama.cpp on `127.0.0.1:8092`.

If the translator OOMs while all three are resident, either:

- enable lazy loading (`lazy_load: true`), or
- switch to `12gb-safe` (Qwen3-ASR-0.6B + 2B translator), or
- unload the translator after 5 idle minutes.

## Download notes

FireRedASR2S:

```bash
git clone https://github.com/FireRedTeam/FireRedASR2S.git
# follow its README to download FireRedASR2-AED weights into pretrained_models/
```

Qwen3-ASR:

```bash
pip install -U qwen-asr
# weights download on first from_pretrained, or:
modelscope download --model Qwen/Qwen3-ASR-1.7B --local_dir ./models/Qwen3-ASR-1.7B
```

SenseVoice / sherpa-onnx:

```bash
pip install -U sherpa-onnx
# download the sherpa-onnx SenseVoice int8 model bundle from the official releases
```

Index-Translate GGUF:

```bash
# from https://huggingface.co/IndexTeam/Index-Translate-9B-GGUF
# use the Q4_K_M file and start llama-server with an OpenAI-compatible /v1 endpoint
```

## License checklist before distribution

- [ ] FireRedASR2S code and weights: Apache-2.0 (keep NOTICE).
- [ ] Qwen3-ASR code/weights: Apache-2.0.
- [ ] SenseVoice: Apache-2.0; FunASR toolkit is MIT with a separate model license.
- [ ] Qwen3 LLMs: Apache-2.0 for the listed open models; verify the exact checkpoint.
- [ ] Index-Translate repository code: Apache-2.0; **weights may have separate terms** — read the
  Hugging Face model card.
- [ ] PySide6: LGPL-3.0; dynamic linking and license notice required.
- [ ] llama.cpp: MIT.
- [ ] Do not commit weights, audio samples, or user data to git.
