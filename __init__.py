from .nodes import FFmpegMergeFrames, FFmpegSplitVideo

NODE_CLASS_MAPPINGS = {
    "FFmpegSplitVideo": FFmpegSplitVideo,
    "FFmpegMergeFrames": FFmpegMergeFrames,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "FFmpegSplitVideo": "FFmpeg Split Video",
    "FFmpegMergeFrames": "FFmpeg Merge Frames",
}
