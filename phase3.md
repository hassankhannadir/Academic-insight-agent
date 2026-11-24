Act as a senior Python developer, data analyst, and UI/UX engineer.

Phase 1 (Academic Database Setup) and Phase 2 (Read-Only Academic Insight Agent) have been completed. Now implement **Phase 3: Academic Analytics Dashboard**.

## Technology Stack

- Programming Language: Python
- Frontend: Streamlit
- Database: MySQL/MariaDB through XAMPP
- Database Connector: mysql-connector-python
- Data Analysis: Pandas
- Data Visualization: Plotly
- Environment Management: python-dotenv
- Existing AI Integration: Groq SDK
- SQL Validation: SQLGlot
- Testing: Pytest

## 1. Dashboard Integration

Create Tab #4 in the existing Streamlit application named **Academic Analytics**.

Inspect the existing architecture before implementation. Preserve all existing tabs, features, database records, and AI agent functionality.

## 2. Dashboard Summary Metrics

Display KPI cards for:

- Total students.
- Total courses.
- Average marks percentage.
- Average attendance percentage.
- Number of students with attendance below 75%.

Calculate all metrics dynamically from actual database records.

## 3. Course-wise Student Marks

Create interactive Plotly visualizations that include:

- Individual student marks for each course.
- Average marks by course.
- Highest and lowest scoring students.
- Student performance comparison.
- Course and student selection filters.
- Hover information showing relevant academic details.

Normalize marks into percentages when total marks differ.

## 4. Attendance Comparison

Create interactive Plotly visualizations that include:

- Student-wise attendance comparison.
- Course-wise average attendance.
- A clearly visible 75% attendance threshold.
- Highlight students with attendance below 75%.
- Course and student selection filters.
- Attendance percentages calculated from attended and total classes.

Handle zero total classes safely.

## 5. UI/UX Requirements

- Professional, modern academic dashboard.
- Clear visual hierarchy and consistent spacing.
- Responsive charts and layouts.
- Consistent typography and color palette.
- Interactive filters.
- Loading indicators and empty-state handling.
- Supporting data tables.
- CSV export for filtered academic records.
- Avoid excessive gradients, unnecessary decorations, and generic AI-generated styling.

## 6. Database and Security

- Reuse the existing database connectivity module.
- Use exclusively the SELECT-only database account.
- Use parameterized SQL queries wherever applicable.
- Never hardcode academic data or credentials.
- Handle database connection errors gracefully.
- Use efficient queries and appropriate Streamlit caching.
- Provide a refresh option to retrieve updated records.
- The dashboard must work independently of the Groq API.

## 7. Testing and Final Verification

- Verify all calculations against database records.
- Test filters, charts, and CSV exports.
- Test missing data and database connection failures.
- Verify that all existing tabs remain functional.
- Verify that the database account remains read-only.
- Launch the Streamlit application and inspect the dashboard.
- Fix discovered bugs and visual inconsistencies.
- Install missing dependencies and update requirements.txt.

## 8. Execution Requirements

Implement everything directly within the existing project rather than providing instructions.

After implementation:

- Conduct a complete audit of all three phases.
- Update README.md with setup and execution instructions.
- Document environment configuration and database setup.
- Report actual test results and unresolved issues.
- Do not claim successful live Groq verification unless it was actually performed.

The final application must satisfy all three original assignment requirements: academic database, read-only academic insight AI agent, and Tab #4 Academic Analytics with course-wise student marks and attendance comparison.