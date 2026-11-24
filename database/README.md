# Academic database setup

XAMPP's MariaDB client is the only external program this phase needs. The
PowerShell script uses it to create the schema, load fictional data, provision
the local agent account, and verify both reads and rejected writes.

Run from the project root:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\database\setup.ps1
```

The script creates `.env` with a random agent password if it does not exist.
The file is excluded by `.gitignore`; `.env.example` documents its keys.
The account is limited to `SELECT` on `academic_db.*` from `127.0.0.1`.

If the XAMPP root account has a password, set `DB_SETUP_ADMIN_PASSWORD` in
the current shell before running the script, then remove it from that shell.
The script never stores the administrator password in `.env`.

`setup.sql` creates the four tables with keys and checks. `seed.sql` adds
30 fictional students, six courses, and 180 marks and attendance rows each.
`verify.sql` contains sample reporting queries. The SQL files can be rerun;
they do not drop tables or other databases.
