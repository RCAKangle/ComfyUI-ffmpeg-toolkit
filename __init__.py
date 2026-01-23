from .nodes import FFmpegMergeFrames, FFmpegSplitVideo, InterleaveFrames

NODE_CLASS_MAPPINGS = {
    "FFmpegSplitVideo": FFmpegSplitVideo,
    "FFmpegMergeFrames": FFmpegMergeFrames,
    "InterleaveFrames": InterleaveFrames,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "FFmpegSplitVideo": "FFmpeg Split Video",
    "FFmpegMergeFrames": "FFmpeg Merge Frames",
    "InterleaveFrames": "Interleave Frames",
}
