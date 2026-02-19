# P-L-Datasets

---

## Quickstart

### Option A: Download ZIP

1. Click **Code** → **Download ZIP** on GitHub.
2. Extract the archive.
3. Data is in `datasets/covenant_pl/v1.0.0/`.

### Option B: Git Clone

```bash
git clone https://github.com/valentinasilva8/P-L-Datasets.git
cd P-L-Datasets
```

### Option C: Download Release Asset

1. Go to [Releases](https://github.com/valentinasilva8/P-L-Datasets/releases).
2. Download the `covenant_pl-v1.0.0.zip` asset (when available).
3. Unzip and use the CSVs in the extracted folder.

---

## Dataset Catalog

| Dataset ID   | Version | Description                                      | Total Size | Files |
|-------------|---------|--------------------------------------------------|------------|-------|
| covenant_pl | v1.0.0  | Synthetic covenant/portfolio learning dataset for churn prediction and outflow analysis. Includes customer snapshots, bank transaction summaries, outflows, crypto shadow transactions, settlement data, wallet risk scores, and market conditions. | 53.6 MB | 10 CSVs |

**Files in covenant_pl v1.0.0:**

- `bank_txn_summary_monthly.csv` — Monthly bank transaction summaries per customer
- `customer_snapshot_monthly.csv` — Monthly customer profile snapshots
- `customers.csv` — Master customer table
- `labels.csv` — Labels for customers with outflow events
- `market_conditions.csv` — Market data (prices, volatility, regime)
- `model1_dataset.csv` — Pre-joined modeling dataset with target `y`
- `outflows.csv` — Individual outflow transactions
- `settlement_data.csv` — Settlement records for crypto transactions
- `shadow_transactions.csv` — Crypto shadow transactions with fraud labels
- `wallet_scores.csv` — Risk scores for wallet addresses

**How to cite:** If you use this dataset, please cite the repository and version, e.g.:

> P-L-Datasets, covenant_pl v1.0.0. https://github.com/valentinasilva8/P-L-Datasets

---

## Loading the Data

### Python

```python
import pandas as pd

# Base path (adjust if needed)
base = "datasets/covenant_pl/v1.0.0"

# Load key tables
customers = pd.read_csv(f"{base}/customers.csv")
snapshots = pd.read_csv(f"{base}/customer_snapshot_monthly.csv")
model_data = pd.read_csv(f"{base}/model1_dataset.csv")

# Parse dates
customers["account_open_date"] = pd.to_datetime(customers["account_open_date"])
snapshots["snapshot_month"] = pd.to_datetime(snapshots["snapshot_month"])
```

### R

```r
# Base path (adjust if needed)
base <- "datasets/covenant_pl/v1.0.0"

# Load key tables
customers <- read.csv(file.path(base, "customers.csv"))
snapshots <- read.csv(file.path(base, "customer_snapshot_monthly.csv"))
model_data <- read.csv(file.path(base, "model1_dataset.csv"))

# Parse dates
customers$account_open_date <- as.Date(customers$account_open_date)
snapshots$snapshot_month <- as.Date(snapshots$snapshot_month)
```

---

## Versioning Policy

We use **Semantic Versioning** (SemVer) for dataset versions:

- **Major (X.0.0):** Breaking changes (e.g., column renames, removals, schema changes).
- **Minor (1.X.0):** Backward-compatible additions (e.g., new columns, new files).
- **Patch (1.0.X):** Backward-compatible fixes (e.g., typo corrections, small data fixes).

This keeps participants’ code stable across minor/patch updates while signaling when migration is needed.

---

## Synthetic Data Notice

All data in this repository is **synthetic** and generated for educational purposes. It does not represent real customers, transactions, or market events. Use it only for learning, prototyping, and workshops.


---

## Validation

### Run Locally

```bash
pip install pandas pyyaml
python scripts/validate_dataset.py --dataset covenant_pl --version v1.0.0
```

### What the Validator Checks

- **File existence** — All expected CSVs are present
- **Required columns** — No missing required columns
- **Unexpected columns** — Warns if extra columns exist
- **Dtypes** — Warns on type mismatches
- **Nullability** — Fails if non-nullable columns contain nulls
- **Numeric ranges** — Warns if values fall outside schema min/max
- **Primary key uniqueness** — Fails if PK or composite key has duplicates
- **Referential integrity** — Warns on orphans; fails if orphan rate > 0.5%

Reports are written to `artifacts/validation/<dataset>/<version>/`:

- `validation_report.md` — Human-readable summary
- `validation_report.json` — Machine-readable results

---

## Contributing

### Adding a New Dataset Version

1. **Create the data folder:**  
   `datasets/<dataset_id>/<version>/` (e.g. `datasets/covenant_pl/v1.1.0/`).

2. **Add your CSVs** to that folder.

3. **Update the catalog:**  
   Edit `catalog/datasets.yaml` and add a new version entry with:
   - `path`, `row_count`, `column_count`, `file_size_bytes`, `sha256` (compute via script or validator).

4. **Add schema:**  
   Create `schemas/<dataset_id>/<version>/schema.yaml` and `DATA_DICTIONARY.md` (see `schemas/covenant_pl/v1.0.0/` for the format).

5. **Run validation:**
   ```bash
   python scripts/validate_dataset.py --dataset <dataset_id> --version <version>
   ```

6. **Update the GitHub workflow** in `.github/workflows/validate-datasets.yml` if you want CI to validate the new version.

7. **Update this README** with the new dataset/version in the catalog table.
