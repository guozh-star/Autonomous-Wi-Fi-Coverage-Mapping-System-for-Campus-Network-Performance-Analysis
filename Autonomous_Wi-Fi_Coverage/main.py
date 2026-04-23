import time
import numpy as np
from src.wifi_scanner import WiFiScanner
from src.data_logger import DataLogger
from src.localization import Localization
from src.heatmap_generator import HeatmapGenerator
from src.analysis import WiFiAnalyzer


def aggregate_wifi_data(wifi_records):
    grouped = {}

    for item in wifi_records:
        ssid = item.get("ssid", "").strip()
        bssid = item.get("bssid", "").strip()

        if not ssid or not bssid:
            continue

        key = (ssid, bssid)

        signal_str = str(item.get("signal", "")).replace("%", "").strip()
        try:
            signal_value = float(signal_str)
        except ValueError:
            continue

        if key not in grouped:
            grouped[key] = {
                "ssid": ssid,
                "bssid": bssid,
                "signals": [],
                "channel": item.get("channel", ""),
                "radio_type": item.get("radio_type", "")
            }

        grouped[key]["signals"].append(signal_value)

    aggregated = []
    for _, value in grouped.items():
        signals = value["signals"]

        aggregated.append({
            "ssid": value["ssid"],
            "bssid": value["bssid"],
            "signal_avg": round(float(np.mean(signals)), 2),
            "signal_min": round(float(np.min(signals)), 2),
            "signal_max": round(float(np.max(signals)), 2),
            "signal_std": round(float(np.std(signals)), 2),
            "scan_count": len(signals),
            "channel": value["channel"],
            "radio_type": value["radio_type"]
        })

    return aggregated


def run_survey():
    scanner = WiFiScanner()
    logger = DataLogger("data/raw/wifi_scan_aggregated.csv")
    localization = Localization()

    num_samples = 25
    settle_time = 2
    repeat_scans = 5
    scan_interval = 1

    for sample_idx in range(num_samples):
        x, y = localization.get_position()
        print(f"[INFO] [{sample_idx + 1}/{num_samples}] Arrived at ({x}, {y}), stabilizing...")
        time.sleep(settle_time)

        all_wifi_data = []

        for i in range(repeat_scans):
            wifi_data = scanner.scan_wifi()
            if wifi_data:
                all_wifi_data.extend(wifi_data)
                print(f"[INFO] Scan {i + 1}/{repeat_scans} captured {len(wifi_data)} records at ({x}, {y})")
            else:
                print(f"[WARNING] No Wi-Fi data captured on scan {i + 1} at ({x}, {y})")
            time.sleep(scan_interval)

        aggregated_data = aggregate_wifi_data(all_wifi_data)

        if aggregated_data:
            logger.log_aggregated(x, y, aggregated_data)
            print(f"[INFO] Logged {len(aggregated_data)} aggregated BSSID records at ({x}, {y})")
        else:
            print(f"[WARNING] No aggregated data at ({x}, {y})")

    print("[INFO] Survey finished.")


def run_analysis_and_visualization(ssid_filter="WKU-VPN"):
    print("[INFO] Starting analysis and visualization...")

    generator = HeatmapGenerator()
    analyzer = WiFiAnalyzer()

    # 控制台输出摘要
    generator.print_summary(ssid_filter=ssid_filter)

    # 热力图
    generator.generate_per_bssid_heatmaps(ssid_filter=ssid_filter)
    generator.generate_ssid_combined_heatmap(ssid_filter=ssid_filter, mode="max")
    generator.generate_ssid_combined_heatmap(ssid_filter=ssid_filter, mode="mean")

    # 图表
    generator.generate_sampling_points_plot(ssid_filter=ssid_filter)
    generator.generate_signal_distribution_chart(ssid_filter=ssid_filter)
    generator.generate_blind_spot_plot(ssid_filter=ssid_filter, weak_threshold=60, blind_threshold=40)
    generator.generate_ap_comparison_chart(ssid_filter=ssid_filter)

    # 分析输出
    analyzer.generate_ap_summary(ssid_filter=ssid_filter)
    analyzer.generate_blind_spots(ssid_filter=ssid_filter, weak_threshold=60, blind_threshold=40)
    analyzer.generate_unstable_areas(ssid_filter=ssid_filter, std_threshold=8)
    analyzer.generate_coverage_report(
        ssid_filter=ssid_filter,
        weak_threshold=60,
        blind_threshold=40,
        std_threshold=8
    )

    print("[INFO] Analysis and visualization completed.")


def main():
    # 按需要切换
    RUN_SURVEY = False
    RUN_ANALYSIS = True
    SSID_FILTER = "WKU-VPN"

    if RUN_SURVEY:
        run_survey()

    if RUN_ANALYSIS:
        run_analysis_and_visualization(ssid_filter=SSID_FILTER)


if __name__ == "__main__":
    main()