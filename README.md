# DataLab 13 · Interview Portfolio

A professional dark-themed **Streamlit dashboard with 13 interactive data applications** by Diego Allan Alves. The Machine Learning Prediction Studio is the flagship module with a fully working synthetic customer churn classifier.

## Run

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Applications

1. **Machine Learning Prediction Studio:** Random Forest / Logistic Regression, model metrics, ROC curve, confusion matrix, feature importance, PCA, probability distribution and interactive what-if inference.
2. **Business Insights Explorer:** regional filters, revenue visualization and CSV export.
3. **Data Pipeline Builder:** configurable extract/transform/load demo.
4. **Database Management Console:** read-only SQL over isolated in-memory SQLite.
5. **KPI Performance Command Center:** KPI cards, segment revenue, customer mix and monthly trend.
6. **Customer Behaviour Analytics:** segment conversion rates and behavioral scatterplots.
7. **Web Data Collection Platform:** safe example.com allowlisted heading extraction.
8. **Smart Data Importer:** upload CSV/JSON and profile quality.
9. **Interactive Visualization Studio:** configurable charts and axis controls.
10. **Data Quality Monitoring Platform:** nulls, duplicates, cardinality, null heatmap and CSV export.
11. **ETL Pipeline Orchestrator:** extraction, transformation and temporary SQLite load.
12. **Data Enrichment & Augmentation Lab:** derived customer features and K-Means clusters.
13. **Statistical Experimentation Lab:** test/control uplift metrics and comparison visualization.

## Testing

```bash
python -m pytest -q tests
python -m py_compile app.py core.py
```

## Important

- All default customer data is **synthetic**; no dashboard metrics are real-world results.
- This is a **portfolio MVP**, not a production-grade cloud deployment or enterprise data platform.
- The example.com scraper intentionally uses a strict allowlist.
- The SQL console is an educational read-only demo and should not be exposed to untrusted users or privileged databases.
- Uploaded datasets can have different columns; some modules require the default schema. Use the import module's reset button to restore it.
- The UI is styled with custom CSS; minor visual differences may occur across Streamlit versions.

## Studio UI upgrade (October 2026)

- Larger, easier-to-read sidebar and stronger dashboard typography.
- Every application now includes a short description and learning goals.
- Web scraping supports **only** the two purpose-built educational domains `books.toscrape.com` and `quotes.toscrape.com` (not arbitrary URLs).
- Scraper provides a 1–5 page limit, 0.5–5 second delay, CSV export, results preview and visualizations based on the collected data.
- Internet connectivity is required for live scraping; other modules run on synthetic local data.
- Before using any website for scraping, review its terms and robots.txt, avoid high request rates, and do not scrape private data.

To run:

```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

To test:

```bash
python -m pytest -q
```

The sample data is synthetic. This release is a functional Streamlit implementation, not an exact pixel-for-pixel reproduction of the concept image.
