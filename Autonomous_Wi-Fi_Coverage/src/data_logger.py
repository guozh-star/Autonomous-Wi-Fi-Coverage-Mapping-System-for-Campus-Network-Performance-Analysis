import csv
import os
from typing import List, Dict


class DataLogger:
    def __init__(self, file_path: str = "data/raw/wifi_scan_aggregated.csv"):
        self.file_path = file_path
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)

    def log_aggregated(self, x: float, y: float, wifi_data: List[Dict]) -> None:
        need_header = (
                not os.path.exists(self.file_path)
                or os.path.getsize(self.file_path) == 0
        )

        with open(self.file_path, mode="a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)

            if need_header:
                writer.writerow([
                    "x", "y", "ssid", "bssid",
                    "signal_avg", "signal_min", "signal_max", "signal_std",
                    "scan_count", "channel", "radio_type"
                ])

            for item in wifi_data:
                writer.writerow([
                    x,
                    y,
                    item.get("ssid", ""),
                    item.get("bssid", ""),
                    item.get("signal_avg", ""),
                    item.get("signal_min", ""),
                    item.get("signal_max", ""),
                    item.get("signal_std", 0),
                    item.get("scan_count", ""),
                    item.get("channel", ""),
                    item.get("radio_type", "")
                ])