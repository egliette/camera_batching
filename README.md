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
