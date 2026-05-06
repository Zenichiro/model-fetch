# model-fetch

`model-fetch` is a small source-aware wrapper around `safetch` for downloading model files and placing them into the correct ComfyUI model folders.

It resolves supported inputs into direct downloadable URLs, downloads them safely via `safetch`, classifies the resulting file, and moves it into the appropriate folder under a configured model base directory.

## v0.1 Scope

- Uses `safetch` as the download backend
- Supports:
  - CivitAI model page URLs
  - CivitAI API download URLs
  - CivitAI numeric IDs
  - Hugging Face direct file URLs
  - Generic direct URLs
- Batch mode with mixed inputs
- `.env` configuration
- Type detection for ComfyUI placement
- `unknown/` fallback for low-confidence placement

## Install

```bash
python -m pip install .
```

Requirements:

- Python 3.10+
- `safetch` installed and available on `PATH`

## Usage

Direct URL:

```bash
model-fetch https://huggingface.co/org/repo/resolve/main/model.safetensors
```

CivitAI numeric input:

```bash
model-fetch civitai 2807896
```

Batch mode:

```bash
model-fetch --input models.txt
```

Prompt before placing files:

```bash
model-fetch --confirm https://civitai.com/api/download/models/2807896
```

JSON output:

```bash
model-fetch --json --input models.txt
```

## Configuration

Default config path:

```text
~/.config/model-fetch/.env
```

Example:

```env
MODEL_BASE_DIR=/mnt/ai-share/image-models
TEMP_DOWNLOAD_DIR=/tmp/model-fetch

SAFETCH_PATH=safetch
SAFETCH_NO_RESUME=false

CIVITAI_API_KEY=
CIVITAI_USE_MIRROR=false
CIVITAI_USE_PROXY=true
CIVITAI_GLUETUN_ENABLED=false

HUGGINGFACE_API_TOKEN=
HUGGINGFACE_USE_PROXY=false
HUGGINGFACE_GLUETUN_ENABLED=false
```

## Detection

Classification priority:

1. Source metadata
2. Filename patterns
3. Safetensors header inspection
4. File size heuristics
5. Fallback to `unknown`

Important note: `.safetensors` header inspection is efficient. The format stores a small JSON header at the start of the file, so `model-fetch` only needs to read the beginning of the file rather than the full multi-GB payload.

## Development

```bash
python -m pip install -e .[dev]
python -m pytest
```
