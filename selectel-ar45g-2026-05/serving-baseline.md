# Selectel AR45G — LLM serving baseline (Phase B)

_Single RTX PRO 6000 96 GB. Each model served via llama.cpp / vLLM; ЛИИ-Спорт-Bench-RU re-run on
local serving must match OpenRouter within ±0.2. **TEMPLATE — fill during the window.**_

## Per-model serving

| Model | Format | Cold-start (s) | VRAM peak (GB) | tok/s @1 | @4 | @16 | @32 | 32K ctx tok/s | RU vs EN Δ |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Gemma 4 31B Instruct | Q4_K_XL GGUF | | | | | | | | |
| Gemma 4 31B Instruct | BF16 | | | | | | | | |
| Qwen 3.6 27B | BF16 | | | | | | | | |
| EduLLM-Chuvash-27B | GGUF | | | | | | | | |
| gpt-oss-120b (optional) | MXFP4 | | | | | | | | |

## Gemma 4 31B — MTP drafter A/B (lossless speculative decode)

| Config | tok/s @1 | @16 | draft-accept % | VRAM Δ | output distribution-identical? |
|---|---:|---:|---:|---:|---|
| base, no drafter | | | — | — | — |
| base + MTP drafter | | | | | |

Speedup factor: __FILL__× . Feeds `production-economics.md` + the Habr throughput headline + the
July Selectel partner-commission tokens/sec number.

## Bench-harness validation (local serving vs OpenRouter)

| Model | Tier-1 sport | local mean | OpenRouter mean | Δ (must be ≤0.2) |
|---|---|---:|---:|---:|
| Gemma 4 31B base | basketball | | 7.45 (overall ref) | |

_If Δ > 0.2: investigate chat template / quant degradation / tokenizer skew before trusting Phase C._
