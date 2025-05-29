# LogArchive Comparison Tool

This Python script allows you to analyze and compare multiple `.logarchive` files or compressed `sysdiagnose` archives from any Apple OS systems. It extracts key forensic metrics such as time span (TTL), file size, total events, and number of unique processes. It generates:

* A CSV summary file
* An interactive HTML dashboard with bar charts for quick visual comparison

## 📦 Requirements

* Python 3.8+
* macOS (uses the built-in `log` command)
* Required Python packages (see `requirements.txt`)

## 🛠 Installation

1. Clone or download this repository
2. Install the required Python packages:

   ```bash
   pip install -r requirements.txt
   ```

> 💡 If you are using an M1/M2 Mac, consider using a virtual environment:
>
> ```bash
> python3 -m venv venv
> source venv/bin/activate
> pip install -r requirements.txt
> ```

## ▶️ Usage

```bash
python3 compare_logarchives.py <path1_> <path2> ...
```

You can provide one or more of the following:

* `.logarchive` directories
* `.tar.gz` sysdiagnose files

### Example

```bash
python3 compare_logarchives_multi.py ~/logs/macos_15.6.logarchive ~/sysdiagnose/sysdiag_15.5.tar.gz
```

After execution:

* A CSV file like `logarchive_comparison_20250529_154500.csv` is created.
* An HTML report like `logarchive_comparison_20250529_154500.html` is created.
* If sysdiagnose archives were used, you're prompted whether to delete extracted temp folders.

## 📊 Output Metrics

Each archive is evaluated on:

* ✅ Size in KB, MB, GB
* ✅ Time span (TTL) in minutes, hours, days
* ✅ Total log events
* ✅ Unique process names

## 📁 Output Files

* `.csv` → summary in tabular format
* `.html` → interactive chart report

## 🩹 Cleanup

Temporary folders are only removed after confirmation.

## 🔒 Note

This tool is designed for forensic or diagnostic purposes. Ensure appropriate permissions and respect privacy when analyzing system logs.


