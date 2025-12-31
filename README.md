# Camera Batching

This repository compares different approaches to decoding camera streams and batching them using OpenCV, FFmpeg, and GStreamer.

## Preparing Videos

To simulate camera **RTSP** streams, I use MEDIAMTX and FFmpeg to publish looped videos as streams. The videos used in this project were sourced from this [GitHub gist](https://gist.github.com/jsturgis/3b19447b304616f18657):

<details>
<summary>Click to expand video metadata</summary>

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

</details>

## CPU only - Benchmark Results

### FFmpeg output with YUV, convert to BGR_I420 after 10 seconds

This use case applies when you don't need every BGR frame for model inference, but only need to convert frames periodically after a given interval.

```bash
CPU Usage (%):
  Mean: 35.99
  P50: 32.80
  P95: 53.81
  P99: 53.90

Memory Usage (MB):
  Mean: 133.10
  P50: 133.15
  P95: 133.40
```

### FFmpeg output with YUV, convert to BGR_I420 using OpenCV

This use case applies when you need YUV format for memory efficiency, but must convert to BGR immediately to feed frames to a model.

```bash
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
```


### FFmpeg output with BGR format

The FFmpeg pipeline outputs buffers with `pix_fmt bgr24`, which is directly compatible with OpenCV and requires no color space conversion.

```bash
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
```

**CPU Usage**: BGR format has higher CPU usage (54.83%) compared to YUV with delayed conversion (35.99%) because FFmpeg needs to perform an additional color space conversion. Video streams are typically decoded in YUV format, which is the native format for streaming. FFmpeg must convert from YUV to BGR before writing the buffer to stdout, adding computational overhead.

**Memory Usage**: BGR format uses more memory (175.48 MB) compared to YUV (~131 MB) because BGR24 frames require 3 bytes per pixel, while YUV420p frames require only 1.5 bytes per pixel. This results in BGR frames being approximately 2x larger than YUV frames in terms of buffer size.

## Hardware Accelerator - Benchmark Results

Use `ffmpeg -hwaccels` to check supported hardware acceleration methods.

**Note**: Despite using GPU-accelerated decoding (`h264_cuvid`), the results show similar or worse CPU and memory usage compared to CPU-only decoding. This occurs because the decoded frames are transferred back to CPU memory space, adding overhead from CPU-GPU memory transfers. Additionally, GPU memory management and driver overhead contribute to the increased resource usage. The benefits of hardware acceleration are more apparent when processing remains on the GPU or when handling multiple high-resolution streams simultaneously.

### FFmpeg output with YUV, convert to BGR_I420 after 10 seconds (buffer in CPU memory)

This use case applies when you don't need every BGR frame for model inference, but only need to convert frames periodically after a given interval.

```bash
CPU Usage (%):
  Mean: 26.11
  P50: 25.20
  P95: 34.80
  P99: 35.50

Memory Usage (MB):
  Mean: 166.51
  P50: 166.50
  P95: 166.86
  P99: 166.97

GPU Memory Usage (MB):
  Mean: 99.00
  P50: 99.00
  P95: 99.00
  P99: 99.00
```

### FFmpeg output with YUV, convert to BGR_I420 using OpenCV (buffer in CPU memory)

This use case applies when you need YUV format for memory efficiency, but must convert to BGR immediately to feed frames to a model.

```bash
CPU Usage (%):
  Mean: 70.50
  P50: 77.81
  P95: 91.37
  P99: 92.03

Memory Usage (MB):
  Mean: 165.22
  P50: 165.50
  P95: 166.01
  P99: 166.08

GPU Memory Usage (MB):
  Mean: 99.00
  P50: 99.00
  P95: 99.00
  P99: 99.00
```

### FFmpeg output with BGR format (buffer in CPU memory)

The FFmpeg pipeline outputs buffers with `pix_fmt bgr24`, which is directly compatible with OpenCV and requires no color space conversion. There are two approaches to handle GPU-accelerated decoding:

#### Approach 1: Direct decoder output (simpler pipeline)

Uses `-c:v h264_cuvid` decoder with direct BGR24 output. The decoder handles GPU-to-CPU transfer internally, but the conversion pipeline is: **NV12 (GPU) → YUV420p → BGR24** (two conversion steps).

```bash
CPU Usage (%):
  Mean: 60.67
  P50: 66.00
  P95: 74.13
  P99: 75.34

Memory Usage (MB):
  Mean: 245.35
  P50: 245.25
  P95: 245.78
  P99: 245.96

GPU Memory Usage (MB):
  Mean: 99.00
  P50: 99.00
  P95: 99.00
  P99: 99.00
```

**Trade-offs**: Simpler command but higher CPU usage due to the extra YUV420p intermediate conversion step. Lower GPU memory usage.

#### Approach 2: Explicit GPU memory management (optimized pipeline)

Uses `-hwaccel cuda` with `-hwaccel_output_format cuda` to keep frames in GPU memory, then `-vf "hwdownload,format=nv12"` to download and convert to CPU memory. The conversion pipeline is: **NV12 (GPU) → NV12 (CPU) → BGR24** (one direct conversion step, avoiding YUV420p intermediate).

```bash
CPU Usage (%):
  Mean: 45.57
  P50: 45.28
  P95: 61.04
  P99: 64.32

Memory Usage (MB):
  Mean: 232.15
  P50: 232.10
  P95: 232.46
  P99: 232.49

GPU Memory Usage (MB):
  Mean: 133.00
  P50: 133.00
  P95: 133.00
  P99: 133.00
```

**Trade-offs**: Lower CPU usage (~25% reduction) due to eliminating the intermediate YUV420p conversion step, and slightly lower system memory usage. However, higher GPU memory usage (133MB vs 99MB) due to explicit GPU memory buffering. More complex pipeline configuration.
