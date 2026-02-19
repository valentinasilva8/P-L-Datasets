# Data Dictionary: covenant_pl v1.0.0

Human-readable schema documentation for the covenant/portfolio learning dataset.

---

## bank_txn_summary_monthly.csv

Monthly aggregated bank transaction summaries per customer.

| Column | Type | Description |
|--------|------|-------------|
| customer_id | string | Unique customer identifier |
| snapshot_month | date | Month of snapshot (YYYY-MM-DD, first of month) |
| ach_outflow_count | int | Number of ACH outflows in the month |
| wire_outflow_count | int | Number of wire outflows in the month |
| external_outflow_count | int | Number of external (e.g., crypto) outflows |
| ach_outflow_amount_usd | float | Total ACH outflow amount in USD |
| wire_outflow_amount_usd | float | Total wire outflow amount in USD |
| external_outflow_amount_usd | float | Total external outflow amount in USD |
| inbound_transfer_count | int | Number of inbound transfers |
| inbound_transfer_amount_usd | float | Total inbound transfer amount in USD |
| total_txn_count | int | Total transaction count for the month |

---

## customer_snapshot_monthly.csv

Monthly customer profile snapshots: product holdings, balances, and engagement metrics.

| Column | Type | Description |
|--------|------|-------------|
| customer_id | string | Unique customer identifier |
| snapshot_month | date | Month of snapshot |
| product_count | int | Number of products held |
| has_checking | bool | Whether customer has checking account |
| has_savings | bool | Whether customer has savings account |
| has_investment | bool | Whether customer has investment account |
| has_mortgage | bool | Whether customer has mortgage |
| has_credit_card | bool | Whether customer has credit card |
| total_deposits_usd | float | Total deposit balance in USD |
| total_investments_usd | float | Total investment balance in USD |
| monthly_login_count | float | Average logins per month |
| mobile_login_pct | float | Fraction of logins from mobile (0–1) |
| days_since_last_login | int | Days since last login |
| avg_monthly_transactions | float | Average monthly transaction count |
| volatile_equity_flag | bool | Flag for volatile equity exposure |
| relationship_tenure_months | int | Months since account opening |

---

## customers.csv

Master customer table: demographics, segment, and churn risk.

| Column | Type | Description |
|--------|------|-------------|
| customer_id | string | Unique customer identifier (primary key) |
| account_open_date | date | Date account was opened |
| age_band | string | Age band (e.g., 25-34) |
| income_band | string | Income band (e.g., 150-200K) |
| state | string | US state code |
| segment | string | Customer segment (Retail, Affluent, Wealth Management) |
| advisor_assigned | bool | Whether an advisor is assigned |
| churn_risk_score | float | Model-derived churn risk (0–1) |

---

## labels.csv

Labels for customers who exhibited outflow behavior (churn/outflow events).

| Column | Type | Description |
|--------|------|-------------|
| customer_id | string | Unique customer identifier |
| first_outflow_date | date | Date of first outflow event |
| count_outflows_total | int | Total number of outflows |

---

## market_conditions.csv

Time-series market data: asset prices, volatility, liquidity, and regime.

| Column | Type | Description |
|--------|------|-------------|
| timestamp | datetime | Observation timestamp |
| asset | string | Asset symbol (e.g., BTC, ETH) |
| price_usd | float | Price in USD |
| price_change_1h_pct | float | 1-hour price change (decimal) |
| price_change_24h_pct | float | 24-hour price change (decimal) |
| volatility_1h_ann | float | 1-hour annualized volatility |
| volatility_24h_ann | float | 24-hour annualized volatility |
| bid_ask_spread_bps | float | Bid-ask spread in basis points |
| order_book_depth_usd | float | Order book depth in USD |
| liquidity_score | float | Liquidity score |
| avg_confirmation_time_min | float | Average confirmation time (minutes) |
| mempool_pending_tx | float | Mempool pending transactions (nullable for non-BTC) |
| gas_price_gwei | float | Gas price in gwei (nullable for non-ETH) |
| regime | string | Market regime (e.g., normal) |

---

## model1_dataset.csv

Pre-joined modeling dataset: combines customer snapshots, bank txns, customer attributes, labels, and target variable.

| Column | Type | Description |
|--------|------|-------------|
| customer_id | string | Unique customer identifier |
| snapshot_month | date | Snapshot month |
| product_count | int | Number of products |
| has_checking | bool | Has checking account |
| has_savings | bool | Has savings account |
| has_investment | bool | Has investment account |
| has_mortgage | bool | Has mortgage |
| has_credit_card | bool | Has credit card |
| total_deposits_usd | float | Total deposits |
| total_investments_usd | float | Total investments |
| monthly_login_count | float | Monthly logins |
| mobile_login_pct | float | Mobile login fraction |
| days_since_last_login | int | Days since last login |
| avg_monthly_transactions | float | Avg monthly transactions |
| volatile_equity_flag | bool | Volatile equity flag |
| relationship_tenure_months | int | Tenure in months |
| ach_outflow_count | int | ACH outflow count |
| wire_outflow_count | int | Wire outflow count |
| external_outflow_count | int | External outflow count |
| ach_outflow_amount_usd | float | ACH outflow amount |
| wire_outflow_amount_usd | float | Wire outflow amount |
| external_outflow_amount_usd | float | External outflow amount |
| inbound_transfer_count | int | Inbound transfer count |
| inbound_transfer_amount_usd | float | Inbound transfer amount |
| total_txn_count | int | Total transaction count |
| account_open_date | date | Account open date |
| age_band | string | Age band |
| income_band | string | Income band |
| state | string | State |
| segment | string | Segment |
| advisor_assigned | bool | Advisor assigned |
| churn_risk_score | float | Churn risk score |
| first_outflow_date | date | First outflow date (nullable for non-churners) |
| T | date | Observation date |
| T_plus_h | date | Horizon date |
| y | int | Binary target (0/1) |

---

## outflows.csv

Individual outflow transactions (ACH, wire, external).

| Column | Type | Description |
|--------|------|-------------|
| outflow_id | string | Unique outflow identifier (primary key) |
| customer_id | string | Customer who initiated the outflow |
| transaction_date | date | Date of transaction |
| amount_usd | float | Amount in USD |
| descriptor | string | Transaction descriptor (e.g., exchange name) |
| transaction_type | string | Type (ACH, wire, etc.) |

---

## settlement_data.csv

Settlement records for crypto/blockchain transactions.

| Column | Type | Description |
|--------|------|-------------|
| transaction_id | string | Unique transaction identifier (primary key) |
| asset_type | string | Asset (BTC, ETH, etc.) |
| initiated_timestamp | datetime | When transaction was initiated |
| expected_confirmation_min | float | Expected confirmation time (minutes) |
| actual_confirmation_min | float | Actual confirmation time |
| confirmations_required | int | Required confirmations |
| confirmations_received | int | Confirmations received |
| final_settlement_timestamp | datetime | When settlement completed |
| settlement_status | string | Status (e.g., confirmed) |
| delay_flag | bool | Whether there was a delay |
| delay_reason | string | Reason for delay (nullable) |

---

## shadow_transactions.csv

Crypto/blockchain shadow transactions: buy/sell, execution details, fraud labels.

| Column | Type | Description |
|--------|------|-------------|
| transaction_id | string | Unique transaction identifier (primary key) |
| customer_id | string | Customer who initiated |
| timestamp | datetime | Transaction timestamp |
| asset_type | string | Asset (BTC, ETH, etc.) |
| direction | string | buy or sell |
| amount_usd | float | Amount in USD |
| quantity | float | Quantity of asset |
| execution_price | float | Execution price |
| base_spread_bps | int | Base spread in bps |
| dynamic_spread_bps | float | Dynamic spread component |
| total_spread_bps | float | Total spread |
| dest_wallet | string | Destination wallet address |
| device_fingerprint | string | Device fingerprint |
| device_type | string | Device type (desktop_web, mobile_app, etc.) |
| is_new_device | bool | Whether device is new |
| session_duration_sec | int | Session duration in seconds |
| ip_country | string | Country of IP |
| model_score | float | Fraud model score |
| model_decision | string | Model decision (approve, etc.) |
| volatility_regime | string | Volatility regime at time of tx |
| fraud_label | string | Fraud label (nullable) |
| label_date | date | Label date (nullable) |
| fraud_type | string | Type of fraud (nullable) |
| loss_amount_usd | float | Loss amount if fraud (nullable) |

---

## wallet_scores.csv

Risk scores for wallet addresses.

| Column | Type | Description |
|--------|------|-------------|
| wallet_address | string | Wallet address (primary key) |
| risk_score | int | Risk score (0–100) |
| risk_category | string | Category (low, medium, high) |
| first_seen_date | date | First observed date |
| total_transaction_count | int | Total transactions |
| known_entity | string | Known entity (nullable) |
| sanctioned_flag | bool | Whether wallet is sanctioned |
| score_date | date | Date of score |

---

## Joins & Relationships

```
customers (customer_id) [master]
    ├── bank_txn_summary_monthly.customer_id
    ├── customer_snapshot_monthly.customer_id
    ├── labels.customer_id
    ├── model1_dataset.customer_id
    ├── outflows.customer_id
    └── shadow_transactions.customer_id

shadow_transactions (transaction_id)
    └── settlement_data.transaction_id

wallet_scores (wallet_address)
    └── shadow_transactions.dest_wallet (many dest_wallets may not be in wallet_scores)
```

- **customers** is the central dimension table; all customer_id references should resolve to it.
- **shadow_transactions** and **settlement_data** share transaction_id; settlement_data is a subset.
- **wallet_scores** contains risk scores for a subset of wallets; shadow_transactions.dest_wallet may reference external wallets not in wallet_scores.
