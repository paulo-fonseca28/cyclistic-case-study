from __future__ import annotations

import pandas as pd

from bikeshare_analysis import MONTHS, PROCESSED_DATA_DIR, validate_project_outputs


def main() -> None:
    errors = validate_project_outputs(raise_on_error=False)
    if errors:
        print("Validation failed:")
        for error in errors:
            print(f"- {error}")
        raise SystemExit(1)

    quality = pd.read_csv(PROCESSED_DATA_DIR / "data_quality_summary.csv")
    print("Validation passed.")
    print(f"Raw files checked: {len(MONTHS)}")
    print(f"Rows read: {int(quality['rows_read'].sum()):,}")
    print(f"Valid rows: {int(quality['valid_rows'].sum()):,}")
    print(f"Rows removed: {int(quality['rows_removed'].sum()):,}")


if __name__ == "__main__":
    main()
