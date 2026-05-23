"""Model defaults for corpus construction.

Gemini 3.5 Flash is the May 2026 default for extraction, translation, and
quality filtering. Gemma 4 remains the trainable base model, not the bulk
corpus-generation judge.
"""

DEFAULT_MODELS = {
    "agy_default": "antigravity-default-gemini-3.5-flash",
    "gemini_direct": "gemini-3.5-flash",
    "openrouter_bulk": "google/gemini-3.5-flash",
    "openrouter_cheap_smoke": "qwen/qwen3.6-flash",
    "trainable_base": "google/gemma-4-31b-it",
}
