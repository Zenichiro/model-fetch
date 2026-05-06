from __future__ import annotations

PATTERN_RULES: list[tuple[tuple[str, ...], str, float, str]] = [
    (("lora",), "loras", 0.85, "filename_pattern"),
    (("vae",), "vae", 0.85, "filename_pattern"),
    (("controlnet",), "controlnet", 0.9, "filename_pattern"),
    (("upscal", "realesrgan", "4x"), "upscalers", 0.75, "filename_pattern"),
    (("embedding", "textual"), "embeddings", 0.8, "filename_pattern"),
    (("clip", "umt5", "text_encoder"), "text_encoders", 0.75, "filename_pattern"),
    (("gligen",), "gligen", 0.85, "filename_pattern"),
    (("photomaker",), "photomaker", 0.9, "filename_pattern"),
    (("hypernetwork",), "hypernetworks", 0.85, "filename_pattern"),
    (("unet",), "unet", 0.75, "filename_pattern"),
    (("diffusion",), "diffusion_models", 0.75, "filename_pattern"),
]
