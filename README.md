# Camera Batching

This repository compares different approaches to decoding camera streams and batching them using OpenCV, FFmpeg, and GStreamer.

## Preparing Videos

To simulate camera **RTSP** streams, I use MEDIAMTX and FFmpeg to publish looped videos as streams. The videos used in this project were sourced from this [GitHub gist](https://gist.github.com/jsturgis/3b19447b304616f18657):
```json
{
  "videos": [
    {
      "filename": "BigBuckBunny.mp4",
      "sources" : [ "http://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4" ],
      "fps": 24.0,
      "duration": 596.46,
      "width": 1280,
      "height": 720
    },
    {
      "filename": "ElephantsDream.mp4",
      "sources" : [ "http://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ElephantsDream.mp4" ],
      "fps": 24.0,
      "duration": 653.79,
      "width": 1280,
      "height": 720
    },
    {
      "filename": "TearsOfSteel.mp4",
      "sources" : [ "http://commondatastorage.googleapis.com/gtv-videos-bucket/sample/TearsOfSteel.mp4" ],
      "fps": 24.0,
      "duration": 734.25,
      "width": 1280,
      "height": 534
    },
    {
      "filename": "WhatCarCanYouGetForAGrand.mp4",
      "sources" : [ "http://commondatastorage.googleapis.com/gtv-videos-bucket/sample/WhatCarCanYouGetForAGrand.mp4" ],
      "fps": 29.97,
      "duration": 567.37,
      "width": 480,
      "height": 270
    }
  ]
}
```
## Benchmark Results

### FFmpeg output with YUV, convert to BGR_I420 after 10 seconds

This use case applies when you don't need every BGR frame for model inference, but only need to convert frames periodically after a given interval.

CPU Usage (%):
  Mean: 35.99
  P50: 32.80
  P95: 53.81
  P99: 53.90

Memory Usage (MB):
  Mean: 133.10
  P50: 133.15
  P95: 133.40

### FFmpeg output with YUV, convert to BGR_I420 using OpenCV

This use case applies when you need YUV format for memory efficiency, but must convert to BGR immediately to feed frames to a model.

CPU Usage (%):
  Mean: 101.36
  P50: 97.94
  P95: 145.35
  P99: 147.97

Memory Usage (MB):
  Mean: 130.98
  P50: 131.00
  P95: 131.51
  P99: 131.58


### FFmpeg output with BGR format

The FFmpeg pipeline outputs buffers with `pix_fmt bgr24`, which is directly compatible with OpenCV and requires no color space conversion.

CPU Usage (%):
  Mean: 54.83
  P50: 57.23
  P95: 69.87
  P99: 71.64

Memory Usage (MB):
  Mean: 175.48
  P50: 175.95
  P95: 176.40
  P99: 176.40

**CPU Usage**: BGR format has higher CPU usage (54.83%) compared to YUV with delayed conversion (35.99%) because FFmpeg needs to perform an additional color space conversion. Video streams are typically decoded in YUV format, which is the native format for streaming. FFmpeg must convert from YUV to BGR before writing the buffer to stdout, adding computational overhead.

**Memory Usage**: BGR format uses more memory (175.48 MB) compared to YUV (~131 MB) because BGR24 frames require 3 bytes per pixel, while YUV420p frames require only 1.5 bytes per pixel. This results in BGR frames being approximately 2x larger than YUV frames in terms of buffer size.
