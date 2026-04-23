import os
import pandas as pd


class WiFiAnalyzer:
    def __init__(self, csv_path=None, output_dir=None):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.csv_path = csv_path or os.path.join(base_dir, "data", "raw", "wifi_scan_aggregated.csv")
        self.output_dir = output_dir or os.path.join(base_dir, "data", "processed")
        self.report_dir = os.path.join(base_dir, "results", "reports")

        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.report_dir, exist_ok=True)

    def load_data(self) -> pd.DataFrame:
        if not os.path.exists(self.csv_path):
            raise FileNotFoundError(f"CSV not found: {self.csv_path}")

        # 同时兼容“老 CSV（无表头）”和“新 CSV（有表头）”
        try:
            df = pd.read_csv(self.csv_path)

            required_cols = {"x", "y", "ssid", "bssid", "signal_avg"}
            if not required_cols.issubset(df.columns):
                raise ValueError("CSV header not recognized, fallback to header=None.")
        except Exception:
            # 老格式：无表头
            df = pd.read_csv(
                self.csv_path,
                header=None
            )

            if df.shape[1] == 10:
                df.columns = [
                    "x", "y", "ssid", "bssid",
                    "signal_avg", "signal_min", "signal_max",
                    "scan_count", "channel", "radio_type"
                ]
            elif df.shape[1] == 11:
                df.columns = [
                    "x", "y", "ssid", "bssid",
                    "signal_avg", "signal_min", "signal_max",
                    "signal_std", "scan_count", "channel", "radio_type"
                ]
            else:
                raise ValueError(f"Unexpected CSV column count: {df.shape[1]}")

        numeric_cols = ["x", "y", "signal_avg", "signal_min", "signal_max", "scan_count"]
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        if "signal_std" in df.columns:
            df["signal_std"] = pd.to_numeric(df["signal_std"], errors="coerce")
        else:
            df["signal_std"] = 0.0

        df = df.dropna(subset=["x", "y", "ssid", "bssid", "signal_avg"]).copy()

        # coverage level: 你现在是百分比，不是 dBm，所以阈值按百分比定义
        df["coverage_level"] = df["signal_avg"].apply(self.classify_signal)

        return df

    @staticmethod
    def classify_signal(signal: float) -> str:
        if signal >= 90:
            return "Excellent"
        elif signal >= 75:
            return "Good"
        elif signal >= 60:
            return "Fair"
        elif signal >= 40:
            return "Weak"
        else:
            return "Poor"

    def generate_ap_summary(self, ssid_filter=None) -> pd.DataFrame:
        df = self.load_data()

        if ssid_filter:
            df = df[df["ssid"] == ssid_filter]

        if df.empty:
            print("[WARNING] No data for AP summary.")
            return pd.DataFrame()

        summary = (
            df.groupby(["ssid", "bssid"], as_index=False)
            .agg(
                point_count=("signal_avg", "count"),
                avg_signal=("signal_avg", "mean"),
                min_signal=("signal_avg", "min"),
                max_signal=("signal_avg", "max"),
                avg_std=("signal_std", "mean"),
                total_scan_count=("scan_count", "sum"),
                channel=("channel", "first"),
                radio_type=("radio_type", "first")
            )
            .sort_values(by=["ssid", "avg_signal"], ascending=[True, False])
        )

        summary["avg_signal"] = summary["avg_signal"].round(2)
        summary["avg_std"] = summary["avg_std"].round(2)

        out_path = os.path.join(self.output_dir, "ap_summary.csv")
        summary.to_csv(out_path, index=False, encoding="utf-8-sig")
        print(f"[INFO] Saved AP summary: {out_path}")
        return summary

    def generate_blind_spots(self, ssid_filter=None, weak_threshold=60, blind_threshold=40) -> pd.DataFrame:
        df = self.load_data()

        if ssid_filter:
            df = df[df["ssid"] == ssid_filter]

        if df.empty:
            print("[WARNING] No data for blind spot analysis.")
            return pd.DataFrame()

        point_df = (
            df.groupby(["x", "y"], as_index=False)
            .agg(
                signal_avg=("signal_avg", "max"),   # 一个点取当前SSID下最好的覆盖
                signal_std=("signal_std", "mean"),
                ap_count=("bssid", "nunique")
            )
        )

        def label_area(v):
            if v < blind_threshold:
                return "Blind Spot"
            elif v < weak_threshold:
                return "Weak Coverage"
            else:
                return "Normal"

        point_df["area_type"] = point_df["signal_avg"].apply(label_area)

        result = point_df[point_df["area_type"] != "Normal"].copy()
        result = result.sort_values(by=["area_type", "signal_avg"], ascending=[True, True])

        out_path = os.path.join(self.output_dir, "blind_spots.csv")
        result.to_csv(out_path, index=False, encoding="utf-8-sig")
        print(f"[INFO] Saved blind spots: {out_path}")
        return result

    def generate_unstable_areas(self, ssid_filter=None, std_threshold=8) -> pd.DataFrame:
        df = self.load_data()

        if ssid_filter:
            df = df[df["ssid"] == ssid_filter]

        if df.empty:
            print("[WARNING] No data for unstable area analysis.")
            return pd.DataFrame()

        unstable = (
            df.groupby(["x", "y"], as_index=False)
            .agg(
                signal_avg=("signal_avg", "max"),
                signal_std=("signal_std", "mean"),
                ap_count=("bssid", "nunique")
            )
        )

        unstable = unstable[unstable["signal_std"] > std_threshold].copy()
        unstable = unstable.sort_values(by="signal_std", ascending=False)

        out_path = os.path.join(self.output_dir, "unstable_areas.csv")
        unstable.to_csv(out_path, index=False, encoding="utf-8-sig")
        print(f"[INFO] Saved unstable areas: {out_path}")
        return unstable

    def generate_coverage_report(self, ssid_filter=None, weak_threshold=60, blind_threshold=40, std_threshold=8):
        df = self.load_data()

        if ssid_filter:
            df = df[df["ssid"] == ssid_filter]

        if df.empty:
            print("[WARNING] No data for report generation.")
            return

        ap_summary = self.generate_ap_summary(ssid_filter=ssid_filter)
        blind_spots = self.generate_blind_spots(
            ssid_filter=ssid_filter,
            weak_threshold=weak_threshold,
            blind_threshold=blind_threshold
        )
        unstable = self.generate_unstable_areas(
            ssid_filter=ssid_filter,
            std_threshold=std_threshold
        )

        point_df = (
            df.groupby(["x", "y"], as_index=False)
            .agg(
                signal_avg=("signal_avg", "max"),
                signal_std=("signal_std", "mean")
            )
        )

        total_points = len(point_df)
        avg_signal = round(point_df["signal_avg"].mean(), 2) if not point_df.empty else 0
        weak_count = len(point_df[point_df["signal_avg"] < weak_threshold])
        blind_count = len(point_df[point_df["signal_avg"] < blind_threshold])
        unstable_count = len(unstable)

        strongest_ap = "N/A"
        if not ap_summary.empty:
            row = ap_summary.iloc[0]
            strongest_ap = f'{row["ssid"]} / {row["bssid"]} / avg={row["avg_signal"]}'

        weakest_area = "N/A"
        if not point_df.empty:
            row = point_df.sort_values(by="signal_avg", ascending=True).iloc[0]
            weakest_area = f'({int(row["x"])}, {int(row["y"])}) / signal={round(row["signal_avg"], 2)}'

        most_unstable_area = "N/A"
        if not point_df.empty:
            row = point_df.sort_values(by="signal_std", ascending=False).iloc[0]
            most_unstable_area = f'({int(row["x"])}, {int(row["y"])}) / std={round(row["signal_std"], 2)}'

        lines = [
            "WiFi Coverage Analysis Report",
            "=" * 40,
            f"SSID Filter: {ssid_filter if ssid_filter else 'ALL'}",
            f"Total Sampling Points: {total_points}",
            f"Average Signal: {avg_signal}",
            f"Weak Coverage Count (< {weak_threshold}): {weak_count}",
            f"Blind Spot Count (< {blind_threshold}): {blind_count}",
            f"Unstable Area Count (std > {std_threshold}): {unstable_count}",
            f"Strongest AP: {strongest_ap}",
            f"Weakest Area: {weakest_area}",
            f"Most Unstable Area: {most_unstable_area}",
            "",
            "Coverage Level Statistics:",
            df["coverage_level"].value_counts().to_string(),
            ]

        out_path = os.path.join(self.report_dir, "coverage_summary.txt")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        print(f"[INFO] Saved report: {out_path}")