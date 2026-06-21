from __future__ import annotations

from bikeshare_analysis import PROCESSED_DATA_DIR, ROOT_DIR, process_raw_data


def main() -> None:
    key_metrics = process_raw_data()
    totals = key_metrics["quality_totals"]
    print("Bike-share processed data generated.")
    print(f"Input rows: {int(totals['rows_read']):,}")
    print(f"Valid rows: {int(totals['valid_rows']):,}")
    print(f"Rows removed: {int(totals['rows_removed']):,}")
    print(f"Output directory: {PROCESSED_DATA_DIR.relative_to(ROOT_DIR)}")


if __name__ == "__main__":
    main()
