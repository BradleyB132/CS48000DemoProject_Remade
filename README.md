# CS48000 Demo Project (Remade)

Project description
-------------------
This repository implements a Streamlit-based dashboard and a modular service
layer for consolidating production, quality, and shipping spreadsheets into
consolidated datasets and summary metrics. The architecture follows a
modular-monolith layered approach: `app.py` (Streamlit UI) calls into the
`src.services` layer, which uses `src.models` and `src.database` for persistence
and ETL.

How to run / build
------------------
This project uses Poetry to manage dependencies. If you prefer pip, install the
packages listed in `pyproject.toml`.

Using Poetry:
1. Install Poetry: https://python-poetry.org/docs/
2. Install dependencies:
   ```bash
   poetry install
   ```
3. Run the Streamlit app:
   ```bash
   poetry run streamlit run app.py
   ```

Using pip:
1. Create a virtualenv and activate it.
2. Install dependencies:
   ```bash
   pip install streamlit SQLAlchemy psycopg2-binary pandas
   ```
3. Run the app:
   ```bash
   streamlit run app.py
   ```

Usage examples
--------------
- Open the Streamlit app and view the list of production logs.
- Use the select box to view details for a specific production log and its
  inspections.

How to run tests
----------------
Tests are written with `pytest`.

Using Poetry:
```bash
poetry run pytest -q
```
Using pip (with pytest installed):
```bash
pytest -q
```

Test coverage of Acceptance Criteria (ACs)
----------------------------------------
The `test/test_etl_and_services.py` file maps tests to ACs as follows:
- `test_consolidation_and_alignment` -> AC1, AC2, AC3, AC4
- `test_summary_metrics_and_flags` -> AC5, AC6, AC7, AC8
- `test_discrepancy_detection` -> AC9, AC10
- `test_efficiency_and_session_cleanup` -> AC11, AC12

Files / environment variables to update to complete the project
--------------------------------------------------------------
- `src/database/connection.py`: replace the hard-coded `_RENDER_CONNECTION` with
  your real Render connection string or modify the constructor to read from an
  environment variable. Example environment variable name: `DATABASE_URL`.
- `pyproject.toml`: update `authors` or project metadata as needed.
- `README.md`: adjust usage instructions if you use a different deployment
  method.
- Optionally add a `.env` file (not committed) and update the code to read
  database credentials from environment variables for production safety.

Recommended next steps
----------------------
- Add Alembic for database migrations and a script to create tables from the
  SQLAlchemy models.
- Replace hard-coded secrets with environment variables or a secrets manager.
- Add more unit tests for edge-cases and integrate CI (GitHub Actions) to run
  tests on push.

Notes
-----
- Secrets are currently hard-coded by request. Move them to environment
  variables before deploying.
- Database migration tooling (Alembic) is not included but recommended if you
  plan to evolve the schema.
