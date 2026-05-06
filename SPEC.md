# model-fetch v0.1 Specification

## Goal

`model-fetch` is a source-aware wrapper around `safetch` for downloading model files and placing them into the correct ComfyUI model folders.

`model-fetch` does not download files directly. It resolves supported inputs into direct file URLs and delegates the actual transfer to `safetch`.

## Scope

v0.1 includes:

- Direct URL downloads
- CivitAI numeric IDs and URLs
- Hugging Face direct file URLs
- Batch input files with mixed entries
- `.env` configuration
- File classification and ComfyUI placement
- JSON output
- Low-confidence fallback to `unknown/`

v0.1 excludes:

- Hugging Face repo-only inputs
- ModelScope
- Parallel downloads
- Browser-cookie auth handling
- Async networking

## Inputs

Supported single-item inputs:

- Generic direct URL
- CivitAI model page URL
- CivitAI API download URL
- CivitAI numeric version or model ID, using `civitai <id>`
- Hugging Face direct file URL

Batch file rules:

- One item per line
- Ignore blank lines
- Ignore lines beginning with `#`
- Mixed formats allowed

## Configuration

Default config path:

`~/.config/model-fetch/.env`

Defaults are loaded first, then `.env`, then CLI overrides.

## Download backend

`safetch` is required and is called as a subprocess.

`model-fetch` relies on `safetch` for:

- Proxy-safe downloads
- Auth headers
- Output directory placement
- Dry-run support
- JSON result reporting
- Resume support

`model-fetch` must not assume `safetch` returns final path or size metadata. It must determine the downloaded file by inspecting the temp directory before and after the download.

## Classification

Classification order:

1. Source metadata
2. Filename patterns
3. Safetensors header inspection
4. File size heuristics
5. Fallback to `unknown`

Confidence score range:

- `0.0` to `1.0`

If confidence is below the threshold in auto mode, the file is placed in `unknown/`.

## Placement

Base path defaults to:

`/mnt/ai-share/image-models`

Supported destination folders:

- `checkpoints`
- `clip`
- `clip_vision`
- `configs`
- `controlnet`
- `diffusion_models`
- `embeddings`
- `gligen`
- `hypernetworks`
- `loras`
- `photomaker`
- `style_models`
- `text_encoders`
- `unet`
- `unknown`
- `upscalers`
- `vae`
- `vae_approx`

Files are moved, not copied.

If a destination already exists, `model-fetch` appends `_1`, `_2`, and so on.

## Exit behavior

- `0` if all items succeed
- Non-zero if any item fails
- Batch mode continues on partial failures
