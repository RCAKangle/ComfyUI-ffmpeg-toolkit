import io
import logging
import os
import shutil
import tempfile
from typing import Any

import torch
import folder_paths

from .ffmpeg_utils import FFmpegError, run_ffmpeg
from .image_utils import load_frames_from_dir, save_frames_to_dir

try:
    from comfy_api.input_impl import VideoFromFile
except Exception:
    try:
        from comfy_api.latest import InputImpl

        VideoFromFile = InputImpl.VideoFromFile
    except Exception:
        VideoFromFile = None


def _is_video_input(value: Any) -> bool:
    return hasattr(value, "get_stream_source") and hasattr(value, "get_components")


def _interleave_tensors(batch_a: torch.Tensor, batch_b: torch.Tensor) -> torch.Tensor:
    if batch_a.dim() < 1 or batch_b.dim() < 1:
        raise ValueError("Inputs must include a batch dimension.")
    if batch_a.shape[0] != batch_b.shape[0]:
        logging.warning(
            "Interleave Frames: batch sizes differ (%s vs %s); truncating.",
            batch_a.shape[0],
            batch_b.shape[0],
        )
    count = min(batch_a.shape[0], batch_b.shape[0])
    if count == 0:
        raise ValueError("Inputs must contain at least one frame.")
    batch_a = batch_a[:count]
    batch_b = batch_b[:count]
    return torch.stack([batch_a, batch_b], dim=1).reshape(2 * count, *batch_a.shape[1:])


def _detect_batch_type(value: Any) -> str:
    if isinstance(value, dict):
        if "samples" not in value:
            raise ValueError("LATENT input is missing 'samples'.")
        return "LATENT"
    if isinstance(value, torch.Tensor):
        return "IMAGE"
    raise ValueError("Input must be IMAGE or LATENT.")


def _interleave_latents(batch_a: dict, batch_b: dict) -> dict:
    samples_a = batch_a["samples"]
    samples_b = batch_b["samples"]
    if not isinstance(samples_a, torch.Tensor) or not isinstance(samples_b, torch.Tensor):
        raise ValueError("LATENT samples must be torch tensors.")

    output = {"samples": _interleave_tensors(samples_a, samples_b)}
    for key, value_a in batch_a.items():
        if key == "samples" or key not in batch_b:
            continue
        value_b = batch_b[key]
        if not isinstance(value_a, torch.Tensor) or not isinstance(value_b, torch.Tensor):
            continue
        if value_a.shape[0] != samples_a.shape[0] or value_b.shape[0] != samples_b.shape[0]:
            continue
        output[key] = _interleave_tensors(value_a, value_b)
    return output


def _ensure_video_path(video: Any) -> tuple[str, bool]:
    if isinstance(video, str):
        return video, False
    if not _is_video_input(video):
        raise ValueError("Input is not a supported video type.")

    source = video.get_stream_source()
    if isinstance(source, str):
        return source, False
    if isinstance(source, io.BytesIO):
        source.seek(0)
        extension = "mp4"
        if hasattr(video, "get_container_format"):
            try:
                extension = video.get_container_format().split(",")[0] or extension
            except Exception:
                pass
        temp_dir = folder_paths.get_temp_directory()
        os.makedirs(temp_dir, exist_ok=True)
        handle, temp_path = tempfile.mkstemp(
            prefix="ffmpeg_input_", suffix=f".{extension}", dir=temp_dir
        )
        os.close(handle)
        with open(temp_path, "wb") as target:
            target.write(source.read())
        return temp_path, True
    raise ValueError("Unsupported video stream source.")


class FFmpegSplitVideo:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "video": ("IMAGE,VIDEO", {"tooltip": "Video input or frame batch."}),
                "fps": ("FLOAT", {"default": 0.0, "min": 0.0, "max": 120.0, "step": 1.0}),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("frames",)
    FUNCTION = "split_video"
    CATEGORY = "ffmpeg"

    def split_video(self, video, fps=0.0):
        if isinstance(video, torch.Tensor):
            if video.dim() != 4:
                raise ValueError("IMAGE input must be a 4D tensor [N, H, W, C].")
            return (video,)

        input_path = None
        cleanup_input = False
        frames_dir = None
        try:
            input_path, cleanup_input = _ensure_video_path(video)
            temp_dir = folder_paths.get_temp_directory()
            os.makedirs(temp_dir, exist_ok=True)
            frames_dir = tempfile.mkdtemp(prefix="ffmpeg_split_", dir=temp_dir)
            output_pattern = os.path.join(frames_dir, "frame_%06d.png")

            args = ["-y", "-i", input_path]
            if fps and fps > 0:
                args += ["-vf", f"fps={fps}"]
            args += ["-vsync", "0", output_pattern]
            run_ffmpeg(args)

            frames = load_frames_from_dir(frames_dir)
            return (frames,)
        except FFmpegError as exc:
            raise RuntimeError(str(exc)) from exc
        finally:
            if cleanup_input and input_path and os.path.exists(input_path):
                os.remove(input_path)
            if frames_dir and os.path.isdir(frames_dir):
                shutil.rmtree(frames_dir, ignore_errors=True)


class FFmpegMergeFrames:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "frames": ("IMAGE,VIDEO", {"tooltip": "Frame batch to merge into a video."}),
                "fps": ("FLOAT", {"default": 30.0, "min": 1.0, "max": 120.0, "step": 1.0}),
            }
        }

    RETURN_TYPES = ("VIDEO", "IMAGE")
    RETURN_NAMES = ("video", "frames")
    FUNCTION = "merge_frames"
    CATEGORY = "ffmpeg"

    def merge_frames(self, frames, fps=30.0):
        if _is_video_input(frames):
            components = frames.get_components()
            return (frames, components.images)

        if not isinstance(frames, torch.Tensor) or frames.dim() != 4:
            raise ValueError("Frames input must be a 4D IMAGE tensor [N, H, W, C].")
        if frames.shape[0] == 0:
            raise ValueError("Frames input is empty.")
        if VideoFromFile is None:
            raise RuntimeError("Video output is not available in this ComfyUI build.")

        temp_dir = folder_paths.get_temp_directory()
        os.makedirs(temp_dir, exist_ok=True)
        temp_root = tempfile.mkdtemp(prefix="ffmpeg_merge_", dir=temp_dir)
        frames_dir = os.path.join(temp_root, "frames")
        os.makedirs(frames_dir, exist_ok=True)
        output_path = os.path.join(temp_root, "output.mp4")

        try:
            save_frames_to_dir(frames, frames_dir, "frame_%06d.png")
            input_pattern = os.path.join(frames_dir, "frame_%06d.png")
            args = [
                "-y",
                "-framerate",
                str(float(fps)),
                "-i",
                input_pattern,
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                output_path,
            ]
            run_ffmpeg(args)
            if not os.path.exists(output_path):
                raise RuntimeError("FFmpeg did not produce an output video.")
            return (VideoFromFile(output_path), frames)
        except FFmpegError as exc:
            raise RuntimeError(str(exc)) from exc
        finally:
            if os.path.isdir(frames_dir):
                shutil.rmtree(frames_dir, ignore_errors=True)


class InterleaveFrames:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "batch_a": ("IMAGE,LATENT", {"tooltip": "First batch to interleave."}),
                "batch_b": ("IMAGE,LATENT", {"tooltip": "Second batch to interleave."}),
            }
        }

    RETURN_TYPES = ("IMAGE,LATENT",)
    RETURN_NAMES = ("batch",)
    FUNCTION = "interleave"
    CATEGORY = "ffmpeg"

    def interleave(self, batch_a, batch_b):
        type_a = _detect_batch_type(batch_a)
        type_b = _detect_batch_type(batch_b)
        if type_a != type_b:
            raise ValueError("Input types must match (IMAGE+IMAGE or LATENT+LATENT).")

        if type_a == "IMAGE":
            if not isinstance(batch_a, torch.Tensor) or not isinstance(batch_b, torch.Tensor):
                raise ValueError("IMAGE inputs must be torch tensors.")
            return (_interleave_tensors(batch_a, batch_b),)

        if not isinstance(batch_a, dict) or not isinstance(batch_b, dict):
            raise ValueError("LATENT inputs must be dicts.")
        return (_interleave_latents(batch_a, batch_b),)
