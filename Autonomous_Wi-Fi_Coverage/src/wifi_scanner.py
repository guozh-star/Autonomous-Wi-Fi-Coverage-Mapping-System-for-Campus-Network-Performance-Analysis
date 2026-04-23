import subprocess
import re
from datetime import datetime
from typing import List, Dict, Optional


class WiFiScanner:
    def scan_wifi(self) -> List[Dict]:
        """
        Scan Wi-Fi networks on Windows using:
        netsh wlan show networks mode=bssid

        Supports both English and Chinese Windows output.
        """
        try:
            result = subprocess.run(
                ["netsh", "wlan", "show", "networks", "mode=bssid"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="ignore"
            )

            output = result.stdout
            return self._parse_netsh_output(output)

        except Exception as e:
            print(f"[ERROR] Wi-Fi scan failed: {e}")
            return []

    def _parse_netsh_output(self, output: str) -> List[Dict]:
        networks: List[Dict] = []
        lines = output.splitlines()

        current_ssid: Optional[str] = None
        current_bssid: Optional[str] = None
        current_signal: Optional[str] = None
        current_channel: Optional[str] = None
        current_radio: Optional[str] = None

        def save_current():
            if current_ssid and current_bssid:
                networks.append({
                    "timestamp": datetime.now().isoformat(),
                    "ssid": current_ssid,
                    "bssid": current_bssid,
                    "signal": current_signal,
                    "channel": current_channel,
                    "radio_type": current_radio
                })

        for raw_line in lines:
            line = raw_line.strip()
            if not line:
                continue

            # ---------- SSID ----------
            # English/Chinese:
            # SSID 1 : WKU-VPN
            ssid_match = re.match(r"SSID\s+\d+\s*:\s*(.*)", line)
            if ssid_match:
                current_ssid = ssid_match.group(1).strip()
                continue

            # ---------- BSSID ----------
            # English/Chinese:
            # BSSID 1 : xx:xx:xx:xx:xx:xx
            bssid_match = re.match(r"BSSID\s+\d+\s*:\s*(.*)", line)
            if bssid_match:
                # 进入新 BSSID 前，先保存上一个 AP
                save_current()

                current_bssid = bssid_match.group(1).strip()
                current_signal = None
                current_channel = None
                current_radio = None
                continue

            # ---------- Signal ----------
            # English: Signal : 78%
            # Chinese: 信号 : 78%
            signal_match = re.match(r"(Signal|信号)\s*:\s*(.*)", line)
            if signal_match:
                current_signal = signal_match.group(2).strip()
                continue

            # ---------- Channel ----------
            # English: Channel : 6
            # Chinese: 信道 : 6 / 频道 : 6 / 信道号 : 6
            channel_match = re.match(r"(Channel|信道|频道|信道号)\s*:\s*(.*)", line)
            if channel_match:
                current_channel = channel_match.group(2).strip()
                continue

            # ---------- Radio type ----------
            # English: Radio type : 802.11n
            # Chinese: 无线电类型 : 802.11n
            radio_match = re.match(r"(Radio type|无线电类型)\s*:\s*(.*)", line)
            if radio_match:
                current_radio = radio_match.group(2).strip()
                continue

        # 保存最后一个 AP
        save_current()
        return networks


if __name__ == "__main__":
    scanner = WiFiScanner()
    wifi_list = scanner.scan_wifi()
    for item in wifi_list:
        print(item)