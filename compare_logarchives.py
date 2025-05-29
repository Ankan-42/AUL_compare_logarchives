# compare_logarchives_multi.py
import argparse
import os
import tarfile
import tempfile
import shutil
import subprocess
from datetime import datetime
from collections import defaultdict
from dateutil import parser
import csv
import plotly.graph_objects as go

VERBOSE = True

def vprint(*args):
    if VERBOSE:
        print("[INFO]", *args)

def extract_tar_gz(tar_path):
    temp_dir = tempfile.mkdtemp(prefix="sysdiag_extract_")
    with tarfile.open(tar_path, "r:gz") as tar:
        tar.extractall(path=temp_dir)
    return temp_dir

def find_logarchive(base_dir):
    for root, dirs, files in os.walk(base_dir):
        for d in dirs:
            if d.endswith(".logarchive"):
                return os.path.join(root, d)
    return None

def parse_time(t):
    try:
        return parser.parse(t)
    except:
        return None

def extract_log_output(path):
    try:
        result = subprocess.run([
            "log", "show", "--archive", path,
            "--style", "syslog", "--info", "--debug"
        ], capture_output=True, text=True, timeout=900)
        return result.stdout.splitlines()
    except subprocess.TimeoutExpired:
        print(f"[ERROR] Timeout on {path}")
        return []

def get_time_range(lines):
    valid_lines = [l for l in lines if l and l[0].isdigit()]
    if not valid_lines:
        return None, None
    return valid_lines[0], valid_lines[-1]

def count_lines(lines):
    return len([l for l in lines if l and l[0].isdigit()])

def count_processes(lines):
    counter = defaultdict(int)
    for line in lines:
        parts = line.split()
        if len(parts) > 2:
            for part in parts:
                if '[' in part and ']' in part and ':' in part:
                    proc = part.split('[')[0]
                    counter[proc] += 1
                    break
    return counter

def get_dir_size_kb(path):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if os.path.isfile(fp):
                total_size += os.path.getsize(fp)
    return round(total_size / 1024, 2)

def process_logarchive(input_path):
    temp_dir = None
    if input_path.endswith(".tar.gz"):
        temp_dir = extract_tar_gz(input_path)
        input_path = find_logarchive(temp_dir)
    elif os.path.isdir(input_path):
        input_path = find_logarchive(input_path) or input_path

    lines = extract_log_output(input_path)
    if not lines:
        return None, temp_dir

    start_line, end_line = get_time_range(lines)
    if not start_line or not end_line:
        return None, temp_dir

    start_time = parse_time(start_line.split()[0])
    end_time = parse_time(end_line.split()[0])
    ttl_min = round((end_time - start_time).total_seconds() / 60, 2)
    ttl_hr = round(ttl_min / 60, 2)
    ttl_day = round(ttl_min / 1440, 2)
    size_kb = get_dir_size_kb(input_path)
    size_mb = round(size_kb / 1024, 2)
    size_gb = round(size_kb / (1024 * 1024), 2)
    lines_count = count_lines(lines)
    processes = count_processes(lines)

    return {
        "file": os.path.basename(input_path),
        "size_kb": size_kb,
        "size_mb": size_mb,
        "size_gb": size_gb,
        "ttl_min": ttl_min,
        "ttl_hr": ttl_hr,
        "ttl_day": ttl_day,
        "events": lines_count,
        "unique_processes": len(processes)
    }, temp_dir

def generate_csv(results, output):
    with open(output, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["File", "Size (MB)", "Size (GB)", "TTL (hr)", "TTL (days)", "Total Events", "Unique Processes"])
        for r in results:
            writer.writerow([r['file'], r['size_mb'], r['size_gb'], r['ttl_hr'], r['ttl_day'], r['events'], r['unique_processes']])

def generate_html(results, output):
    files = [r['file'] for r in results]

    bar = go.Figure()
    bar.add_trace(go.Bar(name="TTL (days)", x=files, y=[r['ttl_day'] for r in results]))
    bar.add_trace(go.Bar(name="Size (GB)", x=files, y=[r['size_gb'] for r in results]))
    bar.add_trace(go.Bar(name="Total Events", x=files, y=[r['events'] for r in results]))
    bar.add_trace(go.Bar(name="Unique Processes", x=files, y=[r['unique_processes'] for r in results]))
    bar.update_layout(barmode='group', title="Logarchive Comparison", xaxis_title="Logarchives", template="plotly_white")

    with open(output, "w") as f:
        f.write("""
        <html><head>
        <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
        <style>body{font-family:sans-serif;margin:20px;}</style>
        </head><body>
        <h1>Logarchive Comparison Dashboard</h1>
        """)
        f.write(bar.to_html(full_html=False, include_plotlyjs=False))
        f.write("</body></html>")

def main():
    parser = argparse.ArgumentParser(description="Compare multiple logarchives or sysdiagnose archives")
    parser.add_argument("inputs", nargs='+', help="Paths to .logarchive or .tar.gz sysdiagnose")
    args = parser.parse_args()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results = []
    temp_dirs = []

    for path in args.inputs:
        vprint(f"Processing: {path}")
        data, temp_dir = process_logarchive(path)
        if data:
            results.append(data)
        if temp_dir:
            temp_dirs.append(temp_dir)

    csv_out = f"logarchive_comparison_{timestamp}.csv"
    html_out = f"logarchive_comparison_{timestamp}.html"

    generate_csv(results, csv_out)
    generate_html(results, html_out)

    print(f"✅ CSV saved: {csv_out}")
    print(f"✅ HTML saved: {html_out}")

    for t in temp_dirs:
        answer = input(f"❓ Delete temporary folder {t}? (y/n): ").strip().lower()
        if answer == 'y':
            shutil.rmtree(t)
            vprint(f"🧹 Deleted: {t}")
        else:
            vprint(f"📁 Kept: {t}")

if __name__ == "__main__":
    main()