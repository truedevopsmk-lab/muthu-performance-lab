from __future__ import annotations

import argparse
from pathlib import Path

from muthu_performance_lab.pwa_export import (
    detect_default_garmin_path,
    export_pwa_json,
    refresh_database_from_garmin,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Export Garmin dashboard data for the PWA.")
    parser.add_argument(
        "--garmin-path",
        type=str,
        default=None,
        help="Path to your GARMIN folder (contains Activity/, Sleep/, etc).",
    )
    parser.add_argument(
        "--skip-refresh",
        action="store_true",
        help="Skip reading FIT files and export from current SQLite database only.",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="pwa/data/dashboard_data.json",
        help="Output JSON file for PWA.",
    )
    args = parser.parse_args()

    if not args.skip_refresh:
        if args.garmin_path:
            garmin_root = Path(args.garmin_path).expanduser().resolve()
        else:
            detected = detect_default_garmin_path()
            if detected is None:
                raise FileNotFoundError(
                    "Could not find GARMIN folder automatically. Use --garmin-path."
                )
            garmin_root = detected

        upserted, parsed = refresh_database_from_garmin(garmin_root)
        print(f"Refresh complete. Parsed {parsed} FIT files and updated {upserted} rows.")

    payload = export_pwa_json(Path(args.output))
    print(f"Exported PWA JSON: {args.output}")
    print(f"Data available: {payload.get('has_data')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
