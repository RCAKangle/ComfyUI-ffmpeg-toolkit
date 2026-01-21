# ComfyUI-ffmpeg-toolkit

FFmpeg-based custom nodes for ComfyUI that convert between videos and frame
batches. The focus is reliability and compatibility with real-world workflows.

## Features

- Split videos into ComfyUI IMAGE batches using FFmpeg
- Merge IMAGE batches into MP4 (H.264) videos using FFmpeg
- Accept VIDEO or IMAGE inputs to tolerate type inconsistencies
- Optional FPS override for both split and merge
- Outputs are compatible with Preview Image, VAE Encode, Save Image, and Save Video

## Nodes

### FFmpeg Split Video

Inputs:
- `video` (VIDEO or IMAGE)
- `fps` (FLOAT, default 0)

Outputs:
- `frames` (IMAGE)

Behavior:
- `fps = 0` keeps the source frame rate
- `fps > 0` resamples using `-vf fps=<value>`

### FFmpeg Merge Frames

Inputs:
- `frames` (IMAGE or VIDEO)
- `fps` (FLOAT, default 30)

Outputs:
- `video` (VIDEO)
- `frames` (IMAGE)

Notes:
- The `frames` output is provided so you can connect to nodes that only accept
  IMAGE inputs (for example, VHS Video Combine).
- If a VIDEO input is provided, it is passed through as `video` and its decoded
  frames are returned on `frames`.

## Requirements

- FFmpeg installed and available on PATH
- Python environment from ComfyUI (torch is already included)
- Python packages in `requirements.txt`

## Installation

1. Clone or download this repo into `ComfyUI/custom_nodes/ComfyUI-ffmpeg-toolkit`
2. Restart ComfyUI

## Usage Examples

- Video to frames:
  - `Load Video` -> `FFmpeg Split Video` -> `Preview Image` / `VAE Encode` / `Save Image`

- Frames to video:
  - `IMAGE batch` -> `FFmpeg Merge Frames` -> `Save Video`

- Frames to VHS Video Combine:
  - `IMAGE batch` -> `FFmpeg Merge Frames` -> `frames` -> `VHS Video Combine`

## Troubleshooting

- "FFmpeg not found": install FFmpeg and make sure `ffmpeg` is in PATH.
