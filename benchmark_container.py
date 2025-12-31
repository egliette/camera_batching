import argparse
import csv
import re
import subprocess
import time
from datetime import datetime

import numpy as np


def convert_to_mb(value):
    match = re.match(r"([\d.]+)([A-Za-z]+)", value)
    if not match:
        return 0

    num, unit = float(match.group(1)), match.group(2).upper()

    conversions = {
        "B": 1 / (1024 * 1024),
        "KIB": 1 / 1024,
        "MIB": 1,
        "GIB": 1024,
        "KB": 1 / 1024,
        "MB": 1,
        "GB": 1024,
    }

    return num * conversions.get(unit, 1)


def parse_gpu_stats():
    """Parse GPU utilization and memory usage from nvidia-smi"""
    try:
        cmd = "nvidia-smi --query-gpu=utilization.gpu,memory.used,memory.total --format=csv,noheader,nounits"
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=5
        )

        if result.returncode != 0:
            return None, None, None

        output = result.stdout.strip()
        if not output:
            return None, None, None

        parts = output.split("\n")[0].split(", ")
        if len(parts) < 3:
            return None, None, None

        gpu_util = float(parts[0])
        gpu_mem_used_mb = float(parts[1])
        gpu_mem_total_mb = float(parts[2])

        return gpu_util, gpu_mem_used_mb, gpu_mem_total_mb

    except Exception as e:
        return None, None, None


def parse_docker_stats(container_name):
    try:
        cmd = f"docker stats {container_name} --no-stream --format '{{{{.CPUPerc}}}} {{{{.MemUsage}}}}'"
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=5
        )

        if result.returncode != 0:
            return None, None

        output = result.stdout.strip()
        parts = output.split()

        cpu_percent = float(parts[0].rstrip("%"))
        mem_usage = parts[1]

        mem_usage_mb = convert_to_mb(mem_usage)

        return cpu_percent, mem_usage_mb

    except Exception as e:
        return None, None


def collect_stats(
    container_name, duration_seconds, interval_seconds=10, csv_file="docker_stats.csv"
):
    data = []

    with open(csv_file, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "timestamp",
                "cpu_percent",
                "memory_mb",
                "gpu_util_percent",
                "gpu_memory_mb",
                "gpu_memory_total_mb",
            ]
        )

        end_time = time.time() + duration_seconds

        while time.time() < end_time:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cpu, mem_mb = parse_docker_stats(container_name)
            gpu_util, gpu_mem_mb, gpu_mem_total_mb = parse_gpu_stats()

            if cpu is not None:
                row = [timestamp, cpu, mem_mb]
                if gpu_util is not None:
                    row.extend([gpu_util, gpu_mem_mb, gpu_mem_total_mb])
                else:
                    row.extend([None, None, None])

                writer.writerow(row)

                stats_dict = {"cpu": cpu, "memory_mb": mem_mb}
                if gpu_util is not None:
                    stats_dict["gpu_util"] = gpu_util
                    stats_dict["gpu_memory_mb"] = gpu_mem_mb
                    stats_dict["gpu_memory_total_mb"] = gpu_mem_total_mb

                data.append(stats_dict)

                gpu_info = (
                    f", GPU Memory: {gpu_mem_mb:.2f}/{gpu_mem_total_mb:.2f}MB"
                    if gpu_util is not None
                    else ", GPU: N/A"
                )
                print(
                    f"{timestamp} - CPU: {cpu:.2f}%, Memory: {mem_mb:.2f}MB{gpu_info}"
                )

            time.sleep(interval_seconds)

    return data


def analyze_stats(data):
    if not data:
        return

    cpu_values = [d["cpu"] for d in data]
    mem_mb_values = [d["memory_mb"] for d in data]

    gpu_mem_values = [
        d.get("gpu_memory_mb") for d in data if d.get("gpu_memory_mb") is not None
    ]

    print("\n" + "=" * 60)
    print("STATISTICAL ANALYSIS")
    print("=" * 60)

    metrics = {"CPU Usage (%)": cpu_values, "Memory Usage (MB)": mem_mb_values}

    if gpu_mem_values:
        metrics["GPU Memory Usage (MB)"] = gpu_mem_values

    for metric_name, values in metrics.items():
        if not values:
            continue

        p50 = np.percentile(values, 50)
        p95 = np.percentile(values, 95)
        p99 = np.percentile(values, 99)
        mean = np.mean(values)

        print(f"\n{metric_name}:")
        print(f"  Mean: {mean:.2f}")
        print(f"  P50: {p50:.2f}")
        print(f"  P95: {p95:.2f}")
        print(f"  P99: {p99:.2f}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Docker container stats collector and analyzer"
    )
    parser.add_argument("container", help="Container name or ID")
    parser.add_argument(
        "-d", "--duration", type=int, default=120, help="Total duration in seconds"
    )
    parser.add_argument(
        "-i", "--interval", type=int, default=10, help="Sampling interval in seconds"
    )
    parser.add_argument(
        "-o", "--output", default="docker_stats.csv", help="Output CSV file"
    )

    args = parser.parse_args()

    data = collect_stats(args.container, args.duration, args.interval, args.output)
    analyze_stats(data)
