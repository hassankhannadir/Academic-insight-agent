Act as a senior Python, AI agent, and database security engineer.

Phase 1 (Academic Database Setup) has been completed. Now implement **Phase 2: Read-Only Academic Insight Agent**.

## Technology Stack

- Programming Language: Python
- Frontend: Streamlit
- Database: MySQL/MariaDB through XAMPP
- Database Connector: `mysql-connector-python`
- LLM Provider: Groq API
- LLM Integration: Official `groq` Python SDK
- SQL Validation: SQLGlot
- Data Analysis: Pandas
- Data Visualization: Plotly
- Environment Management: `python-dotenv`
- Testing: Pytest

## 1. Environment Configuration

Create a separate `.env.groq` file for Groq configuration containing:

```env
GROQ_API_KEY=
GROQ_MODEL=
```

I will manually provide the API key and model name later.

- Do not hardcode or assume a model.
- Keep Groq configuration separate from database credentials.
- Include `.env.groq` in `.gitignore`.
- Create `.env.groq.example` with empty placeholders.
- Handle missing API keys and model names gracefully.

## 2. Academic Insight Agent

Inspect the existing project structure and academic database schema before implementation.

Build an AI agent that:

- Accepts user-generated natural-language questions.
- Understands database tables, columns, and relationships.
- Converts natural-language questions into safe SQL queries.
- Executes validated queries against the academic database.
- Sends retrieved results to the Groq LLM for interpretation.
- Produces clear, accurate, human-readable answers.
- Supports conversational follow-up questions.
- Never fabricates academic records.

## 3. Read-Only Security

Security is a mandatory requirement.

- Connect exclusively using the dedicated SELECT-only database account created in Phase 1.
- Use SQLGlot to parse and validate generated SQL.
- Allow only safe SELECT queries.
- Block INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, TRUNCATE, GRANT, and other unauthorized operations.
- Reject multiple SQL statements.
- Block unsafe functions, file operations, and unauthorized tables.
- Mitigate SQL injection and prompt injection.
- Treat user input and database content as untrusted data.
- Implement query execution timeouts and result limits.
- Never expose credentials, API keys, or sensitive configuration.
- Reject unauthorized requests regardless of LLM-generated instructions.

## 4. Streamlit Integration

Integrate the academic insight agent into the existing Streamlit application.

Include:

- Clean conversational interface.
- Chat history using Streamlit session state.
- Suggested academic questions.
- Loading indicators.
- Clear, structured answers.
- Retrieved data tables where appropriate.
- Graceful error handling.
- Responsive and professional UI.

Preserve all existing tabs and functionality.

## 5. Example Questions

The agent should support questions such as:

- Who scored the highest marks in each course?
- Which students have attendance below 75%?
- What are the average marks in each course?
- Who are the top five performing students?
- Compare the academic performance of two students.
- Which students have excellent marks but poor attendance?
- Which students require academic improvement?

Malicious requests such as deleting or modifying student records must be rejected.

## 6. Testing and Verification

- Test database connectivity.
- Verify read-only permissions.
- Test SQL generation and validation.
- Test complex academic queries.
- Test SQL injection and prompt injection attempts.
- Test missing or invalid Groq configuration.
- Test empty query results and database connection failures.
- Test the Streamlit integration.
- Use mocked Groq responses for automated testing until real credentials and model configuration are provided.

## 7. Execution Requirements

- Implement everything directly within the existing project.
- Inspect installed dependencies before installing new ones.
- Install missing dependencies and update `requirements.txt`.
- Follow modular architecture and clean coding practices.
- Preserve existing database records and application functionality.
- Execute available tests and fix discovered issues.
- Do not simply provide implementation instructions.
- Report all changes, test results, and unresolved issues.
- Clearly distinguish mocked tests from live Groq API verification.

## Scope Restriction

Complete Phase 2 only.

Do not implement Tab #4 Academic Analytics, course-wise marks charts, or attendance comparison charts yet. These belong to Phase 3.

Stop after implementing and verifying everything possible without the Groq API key and model name.