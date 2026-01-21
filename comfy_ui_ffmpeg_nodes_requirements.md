# ComfyUI-FFmpeg-Nodes

## Requirements Specification (English)

---

## 1. Project Overview

This project aims to develop a **ComfyUI custom node repository based on FFmpeg**, focusing on robust and flexible conversion between **video files** and **image frame batches** within ComfyUI workflows.

The repository is intended to serve as a low-level infrastructure layer for video processing in ComfyUI, addressing common limitations in existing nodes and enabling seamless integration with diffusion, VAE, and preview pipelines.

Core goals:

- Provide reliable **video → frames** and **frames → video** conversion
- Handle real-world ComfyUI data-type inconsistencies (Video vs Image ports)
- Leverage FFmpeg for performance, format compatibility, and encoding control
- Maintain minimal scope with strong extensibility

---

## 2. Design Principles

1. **FFmpeg-Centric Architecture**
   - All video encoding and decoding is handled via FFmpeg CLI
   - Python code is responsible only for:
     - Parameter assembly
     - Temporary file / directory management
     - Adapting FFmpeg I/O to ComfyUI tensor formats

2. **Type Compatibility over Type Purity**
   - Nodes must tolerate situations where:
     - Video data is passed through an `IMAGE` port
     - Image batches represent sequential video frames
   - Nodes must internally detect and normalize input formats

3. **Seamless ComfyUI Integration**
   - Outputs must directly connect to:
     - `Preview Image`
     - `VAE Encode (pixels)`
     - `Save Image` / `Save Image Extended`

4. **Minimal Core, Future Expansion**
   - Initial release focuses on two essential nodes
   - Architecture should support future nodes, such as:
     - Audio extraction / merging
     - FPS resampling
     - Resolution scaling
     - Codec / bitrate presets

---

## 3. Node 1: Split Video (Video → Frames)

### 3.1 Node Name (Working Title)

`FFmpeg Split Video`

---

### 3.2 Functionality

This node takes a video input and splits it into individual frames using FFmpeg. The frames are returned as a ComfyUI-compatible **image batch**.

---

### 3.3 Input Ports

| Port Name | Type   | Description |
|---------|--------|-------------|
| `video` | VIDEO / IMAGE | Video source. May come from `Load Video` or be transmitted via an `IMAGE` port. Must be auto-detected and handled internally. |

Optional (future):
- Start frame / time
- End frame / time
- Target FPS

---

### 3.4 Internal Processing

1. Detect input type:
   - Native video path
   - Video encapsulated as image sequence or tensor
2. If necessary, normalize input to a temporary video file
3. Execute FFmpeg command, e.g.:
   ```bash
   ffmpeg -i input.mp4 frame_%06d.png
   ```
4. Load generated frames into a ComfyUI image batch
5. Preserve correct frame order

---

### 3.5 Output Ports

| Port Name | Type  | Description |
|---------|-------|-------------|
| `frames` | IMAGE | Batch of frames as images, ordered sequentially. |

---

### 3.6 Compatibility Requirements

The `frames` output must be directly compatible with:

- `Preview Image` (frame-by-frame preview)
- `VAE Encode (pixels)`
- Any node expecting standard ComfyUI image batches

---

## 4. Node 2: Merge Frames (Frames → Video)

### 4.1 Node Name (Working Title)

`FFmpeg Merge Frames`

---

### 4.2 Functionality

This node takes an ordered batch of images (frames) and merges them into a video file using FFmpeg.

---

### 4.3 Input Ports

| Port Name | Type  | Description |
|---------|-------|-------------|
| `frames` | IMAGE | Ordered image batch representing video frames. Typically produced by `Save Image Extended` or diffusion pipelines. |

Optional (future):
- FPS
- Codec
- Bitrate
- Pixel format

---

### 4.4 Internal Processing

1. Receive image batch and validate ordering
2. Export frames to a temporary directory using sequential filenames
3. Execute FFmpeg command, e.g.:
   ```bash
   ffmpeg -framerate 24 -i frame_%06d.png -c:v libx264 output.mp4
   ```
4. Generate video file
5. Prepare output for ComfyUI consumption

---

### 4.5 Output Ports

| Port Name | Type | Description |
|---------|------|-------------|
| `video` | VIDEO / IMAGE | Generated video. Must support saving and previewing in ComfyUI. |

---

### 4.6 Compatibility Requirements

The output video must:

- Be savable via ComfyUI save nodes
- Be previewable if connected to video/image preview nodes
- Remain compatible with workflows that treat video as an `IMAGE`-type object

---

## 5. Error Handling & Stability

- Graceful failure if FFmpeg is not installed or not found
- Clear error messages for:
  - Unsupported input formats
  - Empty frame batches
  - Frame ordering issues
- Automatic cleanup of temporary files and directories

---

## 6. Environment & Dependencies

- **Required**:
  - FFmpeg (system-installed and accessible via CLI)
  - Python version compatible with ComfyUI

- **Optional**:
  - CUDA-enabled FFmpeg build (future optimization)

---

## 7. Future Roadmap (Non-Blocking)

- Audio track extraction and reintegration
- Multi-video batch processing
- Timeline-aware frame merging
- Metadata preservation (FPS, duration, codec info)
- Preset system for common video targets (web, exhibition, archive)

---

## 8. Summary

This repository defines a **clean, FFmpeg-backed video I/O layer for ComfyUI**, prioritizing real-world workflow compatibility over strict typing. By focusing on two core nodes—**Split Video** and **Merge Frames**—it establishes a stable foundation for advanced video-based generative pipelines.

