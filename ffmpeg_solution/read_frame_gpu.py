import json
import shlex
import subprocess
import time
from contextlib import contextmanager

import cv2
import numpy as np


def get_stream_metadata(rtsp_url):
    cmd_str = f"""
        ffprobe -v quiet \
        -show_entries stream=width,height,r_frame_rate \
        -of json \
        {rtsp_url}
    """
    cmd = shlex.split(cmd_str)
    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        text=True,
    )

    metadata = json.loads(result.stdout)
    if not metadata:
        print(f"Cannot connect to {rtsp_url}. FFprobe returned nothing")
        return None
    metadata = metadata["streams"][0]
    metadata["rtsp"] = rtsp_url
    return metadata


@contextmanager
def ffmpeg_process(cmd):
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    try:
        yield process
    finally:
        process.terminate()

        try:
            stdout, stderr = process.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            stdout, stderr = process.communicate()

        if stderr:
            print(f"FFmpeg stderr (final): {stderr.decode('utf-8')}")


def read_frames_bgr24(rtsp_url, metadata):
    # -rtsp_transport tcp: use TCP transport for RTSP (more reliable than UDP)
    # -c:v h264_cuvid: GPU-accelerated H.264 decoder using NVIDIA CUVID
    # -i: input source URL
    # -pix_fmt bgr24: output pixel format as BGR24 (3 bytes per pixel, compatible with OpenCV)
    # -f rawvideo: output raw uncompressed video frames
    # -: output to stdout
    cmd_str = f"""
        ffmpeg -rtsp_transport tcp \
        -c:v h264_cuvid \
        -i {rtsp_url} \
        -pix_fmt bgr24 \
        -f rawvideo \
        -
    """
    cmd = shlex.split(cmd_str)
    width = metadata["width"]
    height = metadata["height"]
    frame_size = width * height * 3
    frame_count = 0
    fps_start = time.time()
    last_print_time = time.time()

    with ffmpeg_process(cmd) as process:
        while True:
            frame_buffer = process.stdout.read(frame_size)
            if len(frame_buffer) != frame_size:
                break

            frame = np.frombuffer(frame_buffer, dtype=np.uint8).reshape(
                (height, width, 3)
            )

            frame_count += 1
            current_time = time.time()
            elapsed = current_time - fps_start

            if current_time - last_print_time >= 10.0:
                fps = frame_count / elapsed
                print(f"FPS: {fps:.2f}")
                last_print_time = current_time


def read_frames_yuv420p(rtsp_url, metadata):
    # -rtsp_transport tcp: use TCP transport for RTSP (more reliable than UDP)
    # -c:v h264_cuvid: GPU-accelerated H.264 decoder using NVIDIA CUVID
    # -i: input source URL
    # -pix_fmt yuv420p: output pixel format as YUV420p (1.5 bytes per pixel, more memory efficient than BGR)
    # -f rawvideo: output raw uncompressed video frames
    # -: output to stdout
    cmd_str = f"""
        ffmpeg -rtsp_transport tcp \
        -c:v h264_cuvid \
        -i {rtsp_url} \
        -pix_fmt yuv420p \
        -f rawvideo \
        -
    """
    cmd = shlex.split(cmd_str)
    width = metadata["width"]
    height = metadata["height"]
    frame_size = width * height * 3 // 2
    frame_count = 0
    fps_start = time.time()
    last_print_time = time.time()

    with ffmpeg_process(cmd) as process:
        while True:
            frame_buffer = process.stdout.read(frame_size)
            if len(frame_buffer) != frame_size:
                break

            yuv_array = np.frombuffer(frame_buffer, dtype=np.uint8)
            yuv_frame = yuv_array.reshape((height * 3 // 2, width))

            frame_count += 1
            current_time = time.time()
            elapsed = current_time - fps_start

            if current_time - last_print_time >= 10.0:
                cv2.cvtColor(yuv_frame, cv2.COLOR_YUV2BGR_I420)
                fps = frame_count / elapsed
                print(f"FPS: {fps:.2f}")
                last_print_time = current_time


def main():
    rtsp_url = "rtsp://media_service:8554/camera_1"

    metadata = get_stream_metadata(rtsp_url)
    if not metadata:
        return

    print(json.dumps(metadata, indent=2))

    # read_frames_bgr24(rtsp_url, metadata)
    read_frames_yuv420p(rtsp_url, metadata)


if __name__ == "__main__":
    main()
