# ComfyUI-ffmpeg-toolkit

FFmpeg-based custom nodes for ComfyUI that convert between videos and frame batches.

## Nodes

- FFmpeg Split Video (video → frames)
- FFmpeg Merge Frames (frames → video, plus frames pass-through)
- Interleave Frames (interleave 2–6 IMAGE/LATENT batches)

## Requirements

- FFmpeg installed and available on PATH
- Python environment from ComfyUI (torch is already included)
- Python packages in `requirements.txt`

## Installation

1. Clone or download this repo into `ComfyUI/custom_nodes/ComfyUI-ffmpeg-toolkit`
2. Restart ComfyUI

## Troubleshooting

- "FFmpeg not found": install FFmpeg and ensure `ffmpeg` is in PATH.
