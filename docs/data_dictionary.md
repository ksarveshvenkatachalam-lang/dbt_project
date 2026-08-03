# Data dictionary and methodology

| Field | Layer | Definition |
|---|---|---|
| `ocid` | Fact | Open Contracting Data Standard identifier |
| `award_id` | Fact | Identifier of the award within a release |
| `award_value` | Fact | Published award amount in the stated currency |
| `buyer_sk` | Fact | Surrogate key for the contracting authority |
| `supplier_sk` | Fact | Surrogate key for the awarded organisation |
| `category_sk` | Fact | Surrogate key for the procurement classification |
| `value_anomaly_flag` | Fact | Award exceeds category mean plus two population standard deviations |
| `dependency_ratio` | Mart | Supplier value from its largest buyer divided by total supplier value |
| `market_share_pct` | Mart | Supplier value divided by total analysed value |
| `risk_score` | Mart | Weighted 0–100 indicator combining dependency, anomalies, and market share |

## Interpretation

High values identify records for review; they do not imply misconduct. Published notices may contain amendments, duplicated releases, missing classifications, multi-supplier awards, or inconsistent currencies. Production use should add release-version deduplication, GBP conversion, and procurement-policy thresholds.

