# Environmental Monitoring Coverage and Bias Auditor for PM2.5 in Illinois

Authors: Allen Wang and Daniel Duan

## I. Introduction and Background

This project examines PM2.5 monitoring coverage and data quality in Illinois, with particular attention to the Chicago-DeKalb corridor. PM2.5 is an appropriate focus for a geoscience data project because concentrations can vary substantially across short distances, while monitor coverage is still spatially uneven. That combination makes PM2.5 a useful case for studying how different monitoring systems represent environmental conditions and where important gaps may remain.

Our original proposal attempted to cover monitor coverage, data-quality checks, and more advanced calibration or bias-correction ideas at the same time. After revising the scope, we narrowed the project to a more realistic undergraduate workflow centered on three questions: how to collect PM2.5 data from multiple sources, how to standardize those records into one shared structure, and how to generate basic coverage and quality diagnostics in a reproducible way. This direction remains well supported by the literature on incomplete PM2.5 monitoring coverage, environmental justice, and the challenges of comparing low-cost and regulatory observations.

## II. Data and Methods

The project uses two main PM2.5 data sources:

1. EPA AQS daily PM2.5 observations
2. OpenAQ PM2.5 observations and metadata

The workflow is built around a reproducible notebook that supports both sample data and API-driven runs. The current baseline method has four main stages:

1. Read sample data or request PM2.5 observations from AQS and OpenAQ
2. Standardize records into one shared schema with source, station ID, timestamps, coordinates, units, and PM2.5 values
3. Compute basic station-level quality metrics such as missingness, temporal coverage, and outlier rates
4. Generate summary tables and figures for coverage diagnostics, data quality, and a simple paired-modeling experiment

The code is intentionally focused on a manageable toolkit for the course project. The primary libraries are `requests`, `pandas`, `numpy`, `matplotlib`, and `scikit-learn`, with notebook-based execution as the main project entry point.

## III. Current Project Status

The current repository reflects a narrowed and more reproducible version of the original plan.

- Scope, schema, and API access decisions are complete
- Data ingestion and harmonization are implemented in the notebook workflow
- Sample-data mode is available for reproducibility without private API keys
- API mode is available for direct AQS and OpenAQ requests
- Coverage diagnostics, station-level quality summaries, and baseline model outputs are written to disk

More advanced spatial equity analysis and calibration remain secondary extensions rather than the project core. This is consistent with the revised project plan in our report draft, where the main goal is to establish a stable, honest workflow before attempting more ambitious modeling.

## IV. Repository Structure

The most important files in the repository are:

- [notebooks/PM25_Auditor_Workflow.ipynb](notebooks/PM25_Auditor_Workflow.ipynb): main reproducible notebook
- [src/pm25_auditor/pipeline.py](src/pm25_auditor/pipeline.py): shared processing utilities used by the workflow
- [config.yaml](config.yaml): study settings and output paths
- [docs/data_dictionary.md](docs/data_dictionary.md): internal schema documentation
- [data/sample/](data/sample): included sample datasets for reproducible runs without API access

## V. How to Run the Project

Install the required packages:

```bash
pip install -r requirements.txt
```

### Default Reproducible Mode

1. Open [PM25_Auditor_Workflow.ipynb](notebooks/PM25_Auditor_Workflow.ipynb)
2. Leave `USE_SAMPLE_DATA = True`
3. Run the notebook from top to bottom

This mode is the easiest way for instructors or classmates to reproduce the workflow because it does not require API credentials.

### API Mode

To run the notebook with live AQS and OpenAQ data:

1. Create a `.env` file in the repository root based on `.env.example`
2. Add your credentials in this format:

```env
AQS_EMAIL=your_email_here
AQS_KEY=your_aqs_key_here
OPENAQ_KEY=your_openaq_key_here
```

3. Open the notebook and set:

```python
USE_SAMPLE_DATA = False
```

4. Run the notebook from the beginning

### Colab Notes

The notebook also supports running in Google Colab. When opened from GitHub, the first code cell will locate the repository and clone it into `/content` if needed. If Colab is still using an older cached copy of the repository, delete `/content/EAE-483-Group-Project`, restart the runtime, and rerun the notebook from the top.

## VI. Expected Outputs

After a successful run, the project writes the following outputs:

- `data/processed/aqs_clean.csv`
- `data/processed/openaq_clean.csv`
- `data/processed/audit_table.csv`
- `reports/station_quality_metrics.csv`
- `reports/coverage_summary.csv`
- `reports/data_quality_summary.csv`
- `reports/model_metrics.csv`
- `figures/monthly_mean_by_provider.png`
- `figures/station_map.png`

These files are the main evidence that the workflow has completed successfully.

## VII. Summary

This repository documents a revised PM2.5 monitoring audit project for Illinois. The project now emphasizes a reproducible workflow over overly ambitious scope, and the current implementation supports that goal well. The notebook can be rerun in a sample-data mode for reproducibility or in an API mode for direct data collection. The main deliverables are harmonized PM2.5 tables, station-level quality summaries, coverage diagnostics, and baseline modeling outputs. This version of the project is more modest than the original proposal, but it is also more realistic, more reproducible, and better aligned with the course expectations.

## VIII. Selected References

Hua, J., Y. Zhang, B. de Foy, X. Mei, J. Shang, Y. Zhang, I. D. Sulaymon, and D. Zhou, 2021: Improved PM2.5 concentration estimates from low-cost sensors using calibration models categorized by relative humidity. *Aerosol Science and Technology*, 55, 600-613. https://doi.org/10.1080/02786826.2021.1873911

Kelly, B. C., T. J. Cova, M. P. Debbink, T. Onega, and S. C. Brewer, 2024: Racial and ethnic disparities in regulatory air quality monitor locations in the US. *JAMA Network Open*, 7, e2449005. https://doi.org/10.1001/jamanetworkopen.2024.49005

Kelp, M. M., T. C. Fargiano, S. Lin, T. Liu, J. R. Turner, J. N. Kutz, and L. J. Mickley, 2023: Data-driven placement of PM2.5 air quality sensors in the United States: An approach to target urban environmental injustice. *GeoHealth*, 7, e2023GH000834. https://doi.org/10.1029/2023GH000834

Rosales, C., J. R. Bratburd, S. Diez, S. Duncan, C. Malings, and P. Pant, 2025: Open air quality data platforms for environmental health research and action. *Current Environmental Health Reports*, 12, 27. https://doi.org/10.1007/s40572-025-00487-6

Wang, Y., J. D. Marshall, and J. S. Apte, 2024: U.S. ambient air monitoring network has inadequate coverage under new PM2.5 standard. *Environmental Science & Technology Letters*, 11, 1220-1226. https://doi.org/10.1021/acs.estlett.4c00605

## IX. License

This project is released under the MIT License. See [LICENSE](LICENSE).
