# Autonomous Wi-Fi Coverage Mapping System

## Overview

This project presents an autonomous-oriented Wi-Fi coverage mapping and analysis system for campus network performance evaluation. It is designed to automate the workflow of Wi-Fi surveying through structured sampling, repeated scanning, data aggregation, heatmap generation, and diagnostic analysis.

The goal of this project is to reduce the limitations of traditional manual Wi-Fi site surveys, which are often time-consuming, difficult to standardize, and limited in spatial coverage. By transforming repeated wireless measurements into visual and analytical outputs, the system provides a practical and repeatable approach to evaluating campus Wi-Fi conditions.

Although the current implementation does not yet include full deployment on an autonomous robotic platform, it already realizes an automated surveying and analysis workflow at the software level and provides a foundation for future robotic integration.

---

## Features

- Structured grid-based Wi-Fi sampling
- Repeated Wi-Fi scanning at each sampling point
- Aggregation of scan results by SSID and BSSID
- Signal statistics generation:
  - average signal
  - minimum signal
  - maximum signal
  - standard deviation
  - scan count
- Heatmap generation:
  - combined-SSID maximum-based heatmap
  - combined-SSID mean-based heatmap
  - single-BSSID heatmaps
- Access-point comparison analysis
- Weak-coverage / blind-spot detection
- Stability analysis based on repeated-scan variability

---

## Project Structure

```bash
Autonomous_Wi-Fi_Coverage/
├── data/
│   ├── processed/
│   │   ├── ap_summary.csv
│   │   ├── blind_spots.csv
│   │   └── unstable_areas.csv
│   └── raw/
│
├── results/
│   ├── charts/
│   │   ├── ap_comparison.png
│   │   ├── blind_spots.png
│   │   ├── sampling_points.png
│   │   └── signal_distribution.png
│   │
│   ├── heatmaps/
│   │   ├── heatmap_WKU-VPN_52-e3-5a-ab-fd-2c.png
│   │   ├── heatmap_WKU-VPN_54-8a-ba-64-76-c1.png
│   │   ├── heatmap_WKU-VPN_54-8a-ba-64-b3-2e.png
│   │   ├── heatmap_WKU-VPN_54-8a-ba-64-b3-21.png
│   │   ├── heatmap_WKU-VPN_combined_max.png
│   │   └── heatmap_WKU-VPN_combined_mean.png
│   │
│   └── reports/
│
├── src/
│   ├── analysis.py
│   ├── data_logger.py
│   ├── heatmap_generator.py
│   ├── localization.py
│   └── wifi_scanner.py
│
├── main.py
└── README.md
