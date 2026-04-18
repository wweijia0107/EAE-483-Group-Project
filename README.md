# PM2.5 Monitoring Audit Project

This repository is our EAE 483 group project on PM2.5 monitoring coverage and data quality in Illinois, with emphasis on the Chicago-DeKalb corridor.

The project focuses on three main outputs:

- coverage diagnostics
- data-quality summaries
- baseline machine learning results

To make the project easy to review, the repository includes a sample dataset so the main notebook can be rerun without private API keys.

## Main Files

- [PM25_Auditor_Workflow.ipynb](notebooks/PM25_Auditor_Workflow.ipynb): main notebook for the final reproducible workflow
- [config.yaml](config.yaml): project settings
- [data_dictionary.md](docs/data_dictionary.md): internal data schema

## Setup

Install the required packages:

```bash
pip install -r requirements.txt
```

If you want to extend the project to real API downloads later, copy `.env.example` to `.env` and add your own API keys.

## How To Run

1. Open [PM25_Auditor_Workflow.ipynb](notebooks/PM25_Auditor_Workflow.ipynb).
2. Run the notebook from top to bottom.
3. Review the tables, figures, and saved output files.

The current configuration uses sample data by default, so the notebook is easier for others to reproduce.

For Colab:

- Open the notebook from the GitHub repository.
- Run the first code cell first.
- The notebook will automatically locate the project files, and in Colab it will clone the repository into `/content` if needed.

## Expected Outputs

After running the notebook, the project should generate:

- `data/processed/aqs_clean.csv`
- `data/processed/openaq_clean.csv`
- `data/processed/audit_table.csv`
- `reports/station_quality_metrics.csv`
- `reports/coverage_summary.csv`
- `reports/data_quality_summary.csv`
- `reports/model_metrics.csv`
- `figures/monthly_mean_by_provider.png`
- `figures/station_map.png`

## Notes

- Sample data is included so the workflow can be reproduced without API access.
- Raw download folders are not committed to Git.
- Supporting code is stored in `src/pm25_auditor/`, but the main project entry point is the notebook.

## License

This project is released under the MIT License. See [LICENSE](LICENSE).
