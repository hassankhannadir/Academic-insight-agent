# Academic Insight

A local Streamlit application backed by the XAMPP MariaDB `academic_db` database.
It includes the academic database, a read-only Groq-assisted question-answering
agent, and the Academic Analytics dashboard.

## Set up on Windows

1. Start MySQL in XAMPP. Phase 1 was configured for `127.0.0.1:3306`.
2. From the project root, run the database setup if `academic_db` has not
   already been created:

   ```powershell
   powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\database\setup.ps1
   ```

   The script creates four tables, imports fictional data, creates a random
   password in `.env`, and verifies that `academic_agent_ro@127.0.0.1` can
   read but cannot write. See `database/README.md` for details.

3. Use Python 3.12 and install the pinned dependencies:

   ```powershell
   python -m venv .venv
   .venv\Scripts\python.exe -m pip install -r requirements.txt
   ```

   The current workspace already has a populated `.venv`.

4. Put your Groq API key and chosen model name in `.env.groq` to enable the
   AI tab. `.env.groq.example` shows the two settings. No model is assumed.
   The dashboard and database views work while these fields are empty.

5. Start the application:

   ```powershell
   .venv\Scripts\python.exe -m streamlit run app.py
   ```

Both `.env` and `.env.groq` are ignored by Git. Do not place either password
or API key in source files or a repository.

## Application tabs

1. **Ask Academic Insight:** natural-language questions and follow-up chat.
2. **Students:** a semester-filtered student directory.
3. **Courses:** the current course directory.
4. **Academic Analytics:** five global KPIs; course and student filters;
   individual and average marks; highest and lowest scores; student comparison;
   attendance comparisons and the 75% threshold; supporting tables; and a
   filtered CSV export.

The dashboard refreshes its read-only database snapshot every 60 seconds.
Use **Refresh data** in Tab #4 to reload immediately. Filters update charts,
tables, and CSV export. The KPI cards always describe the full database.

Marks and attendance percentages are calculated per record, then averaged
over valid records. A zero total is excluded from percentage calculations.
The low-attendance KPI counts students whose *combined* attended classes
across courses are below 75% of their combined scheduled classes. The
low-attendance table and heatmap flag individual course records below 75%.

## Security and verification

The app connects only as `academic_agent_ro@127.0.0.1`, whose MariaDB grant
is `SELECT` on `academic_db.*`. Agent-generated SQL must pass a SQLGlot
allowlist: one SELECT over approved tables, explicit joins, approved columns
and functions, no comments or unsafe operations, and at most 100 result rows.
MariaDB also applies a three-second statement limit. Dashboard queries are
fixed in code; user-selected filters are applied to Pandas data, so filter
text is never inserted into SQL.

```powershell
.venv\Scripts\python.exe -m pytest -q
```

The tests cover all three phases, including live local MariaDB reads and
denied writes. Groq responses in automated tests are mocked. A real Groq
request remains to be verified after the API key and model are supplied.
