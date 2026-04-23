import os
import re
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import griddata


class HeatmapGenerator:
    def __init__(self, csv_path=None, output_dir=None):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.csv_path = csv_path or os.path.join(base_dir, "data", "raw", "wifi_scan_aggregated.csv")
        self.output_dir = output_dir or os.path.join(base_dir, "results", "heatmaps")
        self.chart_dir = os.path.join(base_dir, "results", "charts")

        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.chart_dir, exist_ok=True)

    @staticmethod
    def safe_filename(text: str) -> str:
        return re.sub(r"[^A-Za-z0-9._-]+", "-", str(text))

    def load_data(self) -> pd.DataFrame:
        if not os.path.exists(self.csv_path):
            raise FileNotFoundError(f"CSV not found: {self.csv_path}")

        # 兼容有表头/无表头两种情况
        try:
            df = pd.read_csv(self.csv_path)
            required_cols = {"x", "y", "ssid", "bssid", "signal_avg"}
            if not required_cols.issubset(df.columns):
                raise ValueError("CSV header not recognized, fallback to header=None.")
        except Exception:
            df = pd.read_csv(self.csv_path, header=None)

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

        df["x"] = pd.to_numeric(df["x"], errors="coerce")
        df["y"] = pd.to_numeric(df["y"], errors="coerce")
        df["signal_avg"] = pd.to_numeric(df["signal_avg"], errors="coerce")
        df["signal_min"] = pd.to_numeric(df["signal_min"], errors="coerce")
        df["signal_max"] = pd.to_numeric(df["signal_max"], errors="coerce")
        df["scan_count"] = pd.to_numeric(df["scan_count"], errors="coerce")

        if "signal_std" in df.columns:
            df["signal_std"] = pd.to_numeric(df["signal_std"], errors="coerce")
        else:
            df["signal_std"] = 0.0

        df = df.dropna(subset=["x", "y", "ssid", "bssid", "signal_avg"]).copy()
        return df

    def print_summary(self, ssid_filter=None):
        df = self.load_data()
        if ssid_filter:
            df = df[df["ssid"] == ssid_filter]

        if df.empty:
            print("[ERROR] No matching data found.")
            return

        summary = (
            df.groupby(["ssid", "bssid"])
            .agg(
                point_count=("signal_avg", "count"),
                avg_signal=("signal_avg", "mean"),
                min_signal=("signal_avg", "min"),
                max_signal=("signal_avg", "max"),
                avg_std=("signal_std", "mean")
            )
            .reset_index()
            .sort_values(by=["ssid", "avg_signal"], ascending=[True, False])
        )

        print("\n[INFO] BSSID Summary")
        print(summary.to_string(index=False))

    def _draw_heatmap(self, df: pd.DataFrame, title: str, output_path: str):
        grouped = df.groupby(["x", "y"], as_index=False)["signal_avg"].mean()

        if grouped.empty:
            print(f"[WARNING] No data to draw: {title}")
            return

        x = grouped["x"].values
        y = grouped["y"].values
        z = grouped["signal_avg"].values

        plt.figure(figsize=(8, 6))

        try:
            xi = np.linspace(x.min(), x.max(), 100)
            yi = np.linspace(y.min(), y.max(), 100)
            xi, yi = np.meshgrid(xi, yi)

            zi = griddata((x, y), z, (xi, yi), method="linear")

            if zi is None or np.all(np.isnan(zi)):
                raise ValueError("Interpolation result is empty.")

            heatmap = plt.imshow(
                zi,
                extent=(x.min(), x.max(), y.min(), y.max()),
                origin="lower",
                cmap="viridis",
                aspect="auto"
            )
            plt.colorbar(heatmap, label="Average Signal Strength (%)")
            plt.scatter(x, y, c="black", s=30)
            print(f"[INFO] Interpolated heatmap generated: {title}")

        except Exception as e:
            print(f"[WARNING] Interpolation failed, fallback to scatter plot: {e}")
            scatter = plt.scatter(
                x, y,
                c=z,
                cmap="viridis",
                s=300,
                edgecolors="black"
            )
            plt.colorbar(scatter, label="Average Signal Strength (%)")
            print(f"[INFO] Scatter plot generated: {title}")

        plt.xlabel("X Position")
        plt.ylabel("Y Position")
        plt.title(title)
        plt.grid(True)
        plt.savefig(output_path, dpi=300, bbox_inches="tight")
        plt.close()

        print(f"[INFO] Saved: {output_path}")

    def generate_single_bssid_heatmap(self, ssid: str, bssid: str):
        df = self.load_data()
        df = df[(df["ssid"] == ssid) & (df["bssid"] == bssid)]

        if df.empty:
            print(f"[ERROR] No data found for SSID={ssid}, BSSID={bssid}")
            return

        safe_ssid = self.safe_filename(ssid)
        safe_bssid = self.safe_filename(bssid)

        title = f"Wi-Fi Signal Heatmap\nSSID: {ssid}\nBSSID: {bssid}"
        output_path = os.path.join(
            self.output_dir,
            f"heatmap_{safe_ssid}_{safe_bssid}.png"
        )

        self._draw_heatmap(df, title, output_path)

    def generate_per_bssid_heatmaps(self, ssid_filter: str):
        df = self.load_data()
        df = df[df["ssid"] == ssid_filter]

        if df.empty:
            print(f"[ERROR] No data found for SSID={ssid_filter}")
            return

        bssid_list = sorted(df["bssid"].unique())
        print(f"[INFO] Found {len(bssid_list)} BSSID(s) under SSID={ssid_filter}")

        for bssid in bssid_list:
            sub_df = df[df["bssid"] == bssid]

            if sub_df["signal_avg"].nunique() <= 1:
                print(f"[INFO] Skip flat BSSID: {bssid}")
                continue

            self.generate_single_bssid_heatmap(ssid_filter, bssid)

    def generate_ssid_combined_heatmap(self, ssid_filter: str, mode="max"):
        df = self.load_data()
        df = df[df["ssid"] == ssid_filter]

        if df.empty:
            print(f"[ERROR] No data found for SSID={ssid_filter}")
            return

        if mode == "max":
            combined = df.groupby(["x", "y"], as_index=False)["signal_avg"].max()
        elif mode == "mean":
            combined = df.groupby(["x", "y"], as_index=False)["signal_avg"].mean()
        else:
            print("[ERROR] mode must be 'max' or 'mean'")
            return

        safe_ssid = self.safe_filename(ssid_filter)
        title = f"Wi-Fi Signal Heatmap\nSSID: {ssid_filter}\nCombined mode: {mode}"
        output_path = os.path.join(
            self.output_dir,
            f"heatmap_{safe_ssid}_combined_{mode}.png"
        )

        self._draw_heatmap(combined, title, output_path)

    def generate_sampling_points_plot(self, ssid_filter=None):
        df = self.load_data()
        if ssid_filter:
            df = df[df["ssid"] == ssid_filter]

        if df.empty:
            print("[WARNING] No data for sampling points plot.")
            return

        point_df = df.groupby(["x", "y"], as_index=False)["signal_avg"].max()

        plt.figure(figsize=(8, 6))
        plt.scatter(point_df["x"], point_df["y"], s=120, edgecolors="black")
        for _, row in point_df.iterrows():
            plt.text(row["x"], row["y"], f'({int(row["x"])},{int(row["y"])})', fontsize=8)

        plt.xlabel("X Position")
        plt.ylabel("Y Position")
        plt.title(f"Sampling Points {'- ' + ssid_filter if ssid_filter else ''}")
        plt.grid(True)

        out_path = os.path.join(self.chart_dir, "sampling_points.png")
        plt.savefig(out_path, dpi=300, bbox_inches="tight")
        plt.close()
        print(f"[INFO] Saved: {out_path}")

    def generate_signal_distribution_chart(self, ssid_filter=None):
        df = self.load_data()
        if ssid_filter:
            df = df[df["ssid"] == ssid_filter]

        if df.empty:
            print("[WARNING] No data for signal distribution chart.")
            return

        point_df = df.groupby(["x", "y"], as_index=False)["signal_avg"].max()

        plt.figure(figsize=(8, 6))
        plt.hist(point_df["signal_avg"], bins=10, edgecolor="black")
        plt.xlabel("Signal Strength (%)")
        plt.ylabel("Number of Points")
        plt.title(f"Signal Distribution {'- ' + ssid_filter if ssid_filter else ''}")
        plt.grid(True, axis="y")

        out_path = os.path.join(self.chart_dir, "signal_distribution.png")
        plt.savefig(out_path, dpi=300, bbox_inches="tight")
        plt.close()
        print(f"[INFO] Saved: {out_path}")

    def generate_blind_spot_plot(self, ssid_filter=None, weak_threshold=60, blind_threshold=40):
        df = self.load_data()
        if ssid_filter:
            df = df[df["ssid"] == ssid_filter]

        if df.empty:
            print("[WARNING] No data for blind spot plot.")
            return

        point_df = df.groupby(["x", "y"], as_index=False)["signal_avg"].max()

        normal_df = point_df[point_df["signal_avg"] >= weak_threshold]
        weak_df = point_df[(point_df["signal_avg"] < weak_threshold) & (point_df["signal_avg"] >= blind_threshold)]
        blind_df = point_df[point_df["signal_avg"] < blind_threshold]

        plt.figure(figsize=(8, 6))

        if not normal_df.empty:
            plt.scatter(normal_df["x"], normal_df["y"], s=120, label="Normal", edgecolors="black")
        if not weak_df.empty:
            plt.scatter(weak_df["x"], weak_df["y"], s=120, label="Weak", edgecolors="black")
        if not blind_df.empty:
            plt.scatter(blind_df["x"], blind_df["y"], s=120, label="Blind Spot", edgecolors="black")

        plt.xlabel("X Position")
        plt.ylabel("Y Position")
        plt.title(f"Blind Spot Detection {'- ' + ssid_filter if ssid_filter else ''}")
        plt.legend()
        plt.grid(True)

        out_path = os.path.join(self.chart_dir, "blind_spots.png")
        plt.savefig(out_path, dpi=300, bbox_inches="tight")
        plt.close()
        print(f"[INFO] Saved: {out_path}")

    def generate_ap_comparison_chart(self, ssid_filter=None):
        df = self.load_data()
        if ssid_filter:
            df = df[df["ssid"] == ssid_filter]

        if df.empty:
            print("[WARNING] No data for AP comparison chart.")
            return

        summary = (
            df.groupby("bssid", as_index=False)
            .agg(avg_signal=("signal_avg", "mean"))
            .sort_values(by="avg_signal", ascending=False)
        )

        plt.figure(figsize=(10, 6))
        plt.bar(summary["bssid"], summary["avg_signal"], edgecolor="black")
        plt.xlabel("BSSID")
        plt.ylabel("Average Signal (%)")
        plt.title(f"AP Comparison {'- ' + ssid_filter if ssid_filter else ''}")
        plt.xticks(rotation=45, ha="right")
        plt.grid(True, axis="y")

        out_path = os.path.join(self.chart_dir, "ap_comparison.png")
        plt.savefig(out_path, dpi=300, bbox_inches="tight")
        plt.close()
        print(f"[INFO] Saved: {out_path}")