# Synthetic analytics delivery method

Customer usage features use observation periods of November and December 2025. ClientPulse joins this historical usage with customer attributes to predict synthetic churn in the following month.

Rows with negative active days, unknown customer references or future usage periods are rejected before feature construction.

Customer identifiers and outcome labels are excluded from model input features. Imputation and encoding are fitted only on training data.

ROC AUC measures ranking discrimination. Compare the trained model against a baseline and report uncertainty before interpreting model quality.
