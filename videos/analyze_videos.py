import json
from pathlib import Path

import cv2


def get_video_metadata(video_path: Path):
    cap = cv2.VideoCapture(str(video_path))

    if not cap.isOpened():
        return {"filename": video_path.name, "error": "Could not open video file"}

    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    duration = frame_count / fps if fps > 0 else 0

    cap.release()

    return {
        "filename": video_path.name,
        "fps": round(fps, 2),
        "duration": round(duration, 2),
        "width": width,
        "height": height,
    }


def main() -> None:
    script_dir = Path(__file__).parent
    mp4_files = sorted(script_dir.glob("*.mp4"))

    if not mp4_files:
        print(json.dumps({"message": "No .mp4 files found in the directory"}, indent=2))
        return

    results = []
    for video_file in mp4_files:
        metadata = get_video_metadata(video_file)
        results.append(metadata)

    output = {"videos": results, "total_count": len(results)}

    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
