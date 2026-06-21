from __future__ import annotations

from bikeshare_analysis import FIGURES_DIR, REPORTS_DIR, ROOT_DIR, TABLES_DIR, create_report_assets


def main() -> None:
    create_report_assets(close_figures=True)
    print("Bike-share report tables and figures generated.")
    print(f"Tables directory: {TABLES_DIR.relative_to(ROOT_DIR)}")
    print(f"Figures directory: {FIGURES_DIR.relative_to(ROOT_DIR)}")
    print(f"Summary report: {(REPORTS_DIR / 'final_summary.md').relative_to(ROOT_DIR)}")


if __name__ == "__main__":
    main()
