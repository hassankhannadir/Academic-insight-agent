[CmdletBinding()]
param(
  [string] $MysqlPath,
  [string] $AdminUser = 'root'
)

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$envPath = Join-Path $projectRoot '.env'

if (-not (Test-Path -LiteralPath $envPath)) {
  $randomBytes = [byte[]]::new(32)
  $generator = [System.Security.Cryptography.RandomNumberGenerator]::Create()
  try { $generator.GetBytes($randomBytes) } finally { $generator.Dispose() }
  $generatedPassword = [Convert]::ToBase64String($randomBytes).TrimEnd('=').Replace('+', '-').Replace('/', '_')
  $envText = "DB_HOST=127.0.0.1`nDB_PORT=3306`nDB_NAME=academic_db`nDB_USER=academic_agent_ro`nDB_PASSWORD=$generatedPassword`n"
  [System.IO.File]::WriteAllText($envPath, $envText, [System.Text.UTF8Encoding]::new($false))
  Write-Host 'Created .env with a random password.'
}

$config = @{}
foreach ($line in [System.IO.File]::ReadAllLines($envPath)) {
  if ($line -match '^\s*([A-Za-z_][A-Za-z_0-9]*)=(.*)$') {
    $config[$Matches[1]] = $Matches[2].Trim()
  }
}
foreach ($key in @('DB_HOST', 'DB_PORT', 'DB_NAME', 'DB_USER', 'DB_PASSWORD')) {
  if (-not $config[$key]) { throw "Missing $key in .env." }
}
if ($config.DB_HOST -ne '127.0.0.1' -or $config.DB_NAME -ne 'academic_db' -or
    $config.DB_USER -notmatch '^[A-Za-z_][A-Za-z_0-9]*$' -or
    $config.DB_PORT -notmatch '^\d{1,5}$' -or
    $AdminUser -notmatch '^[A-Za-z_][A-Za-z_0-9]*$') {
  throw 'This setup supports academic_db on local TCP (127.0.0.1) only.'
}

if (-not $MysqlPath) {
  $command = Get-Command mysql.exe -ErrorAction SilentlyContinue
  if ($command) { $MysqlPath = $command.Source }
}
if (-not $MysqlPath) {
  foreach ($candidate in @('F:/programs/xampp/mysql/bin/mysql.exe', 'C:/xampp/mysql/bin/mysql.exe')) {
    if (Test-Path -LiteralPath $candidate) { $MysqlPath = $candidate; break }
  }
}
if (-not $MysqlPath -or -not (Test-Path -LiteralPath $MysqlPath)) {
  throw 'XAMPP mysql.exe was not found. Pass its full path with -MysqlPath.'
}

function Invoke-MySql {
  param(
    [Parameter(Mandatory)] [string] $Sql,
    [Parameter(Mandatory)] [string] $User,
    [string] $Password = '',
    [string] $Database = ''
  )
  $start = [System.Diagnostics.ProcessStartInfo]::new()
  $start.FileName = $MysqlPath
  $arguments = @('--protocol=tcp', '--connect-timeout=5', "--host=$($config.DB_HOST)",
                 "--port=$($config.DB_PORT)", "--user=$User", '--default-character-set=utf8mb4')
  if ($Database) { $arguments += "--database=$Database" }
  $start.Arguments = $arguments -join ' '
  $start.UseShellExecute = $false
  $start.RedirectStandardInput = $true
  $start.RedirectStandardOutput = $true
  $start.RedirectStandardError = $true
  [void] $start.EnvironmentVariables.Remove('MYSQL_PWD')
  if ($Password) { $start.EnvironmentVariables['MYSQL_PWD'] = $Password }

  $process = [System.Diagnostics.Process]::new()
  $process.StartInfo = $start
  try {
    [void] $process.Start()
    $outputTask = $process.StandardOutput.ReadToEndAsync()
    $errorTask = $process.StandardError.ReadToEndAsync()
    $process.StandardInput.Write($Sql)
    $process.StandardInput.Close()
    $process.WaitForExit()
    return [pscustomobject]@{
      ExitCode = $process.ExitCode
      Output = $outputTask.GetAwaiter().GetResult()
      ErrorText = $errorTask.GetAwaiter().GetResult()
    }
  } finally {
    $process.Dispose()
  }
}

function Assert-Success {
  param([string] $Step, $Result)
  if ($Result.ExitCode -ne 0) { throw "$Step failed: $($Result.ErrorText.Trim())" }
  Write-Host "$Step succeeded."
}

$adminPassword = $env:DB_SETUP_ADMIN_PASSWORD
$schemaSql = [System.IO.File]::ReadAllText((Join-Path $PSScriptRoot 'setup.sql'))
Assert-Success 'Schema setup' (Invoke-MySql -Sql $schemaSql -User $AdminUser -Password $adminPassword)
$seedSql = [System.IO.File]::ReadAllText((Join-Path $PSScriptRoot 'seed.sql'))
Assert-Success 'Seed import' (Invoke-MySql -Sql $seedSql -User $AdminUser -Password $adminPassword)

$account = $config.DB_USER
$quotedPassword = $config.DB_PASSWORD.Replace("'", "''")
$userSql = @"
CREATE USER IF NOT EXISTS '$account'@'127.0.0.1' IDENTIFIED BY '$quotedPassword';
ALTER USER '$account'@'127.0.0.1' IDENTIFIED BY '$quotedPassword';
REVOKE ALL PRIVILEGES, GRANT OPTION FROM '$account'@'127.0.0.1';
GRANT SELECT ON academic_db.* TO '$account'@'127.0.0.1';
"@
Assert-Success 'Read-only account provisioning' (Invoke-MySql -Sql $userSql -User $AdminUser -Password $adminPassword)

$verifySql = [System.IO.File]::ReadAllText((Join-Path $PSScriptRoot 'verify.sql'))
$readResult = Invoke-MySql -Sql $verifySql -User $account -Password $config.DB_PASSWORD
Assert-Success 'Read-only SELECT queries' $readResult
Write-Output $readResult.Output.Trim()

$writeProbes = @(
  @{ Name = 'UPDATE'; Sql = 'UPDATE students SET full_name = full_name WHERE student_id = 1;' },
  @{ Name = 'DELETE'; Sql = 'DELETE FROM students WHERE student_id = 4294967295;' },
  @{ Name = 'INSERT'; Sql = "START TRANSACTION; INSERT INTO students (full_name, registration_number, semester) VALUES ('Permission probe', 'RO-PROBE', 1); ROLLBACK;" }
)
foreach ($probe in $writeProbes) {
  $result = Invoke-MySql -Sql $probe.Sql -User $account -Password $config.DB_PASSWORD -Database 'academic_db'
  if ($result.ExitCode -eq 0 -or $result.ErrorText -notmatch '1142|command denied') {
    throw "$($probe.Name) privilege check did not return the expected denial: $($result.ErrorText.Trim())"
  }
  Write-Host "$($probe.Name) denied as expected."
}
