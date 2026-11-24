"""A deliberately small SQL subset for academic read queries."""

from __future__ import annotations

from dataclasses import dataclass

import sqlglot
from sqlglot import exp
from sqlglot.errors import ParseError


MAX_ROWS = 100
MAX_SQL_LENGTH = 6000
TABLE_COLUMNS: dict[str, frozenset[str]] = {
    "students": frozenset({"student_id", "full_name", "registration_number", "semester"}),
    "courses": frozenset({"course_id", "course_code", "course_name", "credit_hours"}),
    "marks": frozenset({"record_id", "student_id", "course_id", "obtained_marks", "total_marks"}),
    "attendance": frozenset({"record_id", "student_id", "course_id", "total_classes", "attended_classes"}),
}

ALLOWED_NODES = {
    exp.Select, exp.Alias, exp.Table, exp.TableAlias, exp.Column, exp.Identifier,
    exp.From, exp.Join, exp.Where, exp.Group, exp.Having, exp.Order, exp.Ordered,
    exp.Limit, exp.Literal, exp.Count, exp.Avg, exp.Sum, exp.Min, exp.Max,
    exp.Round, exp.Coalesce, exp.Nullif, exp.Distinct, exp.Star, exp.EQ,
    exp.NEQ, exp.GT, exp.GTE, exp.LT, exp.LTE, exp.And, exp.Or, exp.Not,
    exp.Add, exp.Sub, exp.Mul, exp.Div, exp.Mod, exp.Between, exp.In,
    exp.Is, exp.Like, exp.Paren, exp.Null, exp.Boolean, exp.Neg,
}


class UnsafeQueryError(Exception):
    """Generated SQL is outside the allowed read-only subset."""


@dataclass(frozen=True)
class SafeQuery:
    sql: str
    row_limit: int
    was_capped: bool


def _clean_sql(raw_sql: str) -> str:
    sql = raw_sql.strip()
    if sql.startswith("```") and sql.endswith("```"):
        lines = sql.splitlines()
        sql = "\n".join(lines[1:-1]).strip()
    if sql.lower().startswith("sql:"):
        sql = sql[4:].strip()
    return sql


def validate_sql(raw_sql: str, max_rows: int = MAX_ROWS) -> SafeQuery:
    """Parse SQL, validate every AST node, and enforce a hard row cap."""
    if not isinstance(raw_sql, str) or not 1 <= max_rows <= MAX_ROWS:
        raise UnsafeQueryError("Invalid query or result limit.")
    sql = _clean_sql(raw_sql)
    if not sql or len(sql) > MAX_SQL_LENGTH or any(marker in sql for marker in ("--", "/*", "#")):
        raise UnsafeQueryError("The query is empty, too long, or contains comments.")
    try:
        statements = sqlglot.parse(sql, read="mysql", error_level="RAISE")
    except (ParseError, ValueError) as exc:
        raise UnsafeQueryError("The generated SQL could not be parsed.") from exc
    if len(statements) != 1 or type(statements[0]) is not exp.Select:
        raise UnsafeQueryError("Only one SELECT statement is allowed.")

    tree = statements[0]
    tables = list(tree.find_all(exp.Table))
    if not tables or len(tables) > 5:
        raise UnsafeQueryError("The query must use authorized academic tables.")
    aliases: dict[str, str] = {}
    for table in tables:
        name = table.name.lower()
        if table.db or table.catalog or name not in TABLE_COLUMNS:
            raise UnsafeQueryError("The query references an unauthorized table.")
        alias = table.alias_or_name.lower()
        if alias in aliases:
            raise UnsafeQueryError("Duplicate table aliases are not allowed.")
        aliases[alias] = name

    projection_aliases = {item.alias.lower() for item in tree.expressions if item.alias}
    for node in tree.walk():
        if type(node) not in ALLOWED_NODES:
            raise UnsafeQueryError("The query contains an unsupported operation or function.")
        if isinstance(node, exp.Join):
            if node.args.get("on") is None or node.args.get("using") is not None:
                raise UnsafeQueryError("Every join must use an explicit ON condition.")
            if str(node.args.get("kind") or "").upper() in {"CROSS", "NATURAL"}:
                raise UnsafeQueryError("Cartesian joins are not allowed.")
        if isinstance(node, exp.Star) and not isinstance(node.parent, exp.Count):
            raise UnsafeQueryError("SELECT * is not allowed.")
        if isinstance(node, exp.Column):
            name = node.name.lower()
            if node.table:
                table_name = aliases.get(node.table.lower())
                if table_name is None or name not in TABLE_COLUMNS[table_name]:
                    raise UnsafeQueryError("The query references an unauthorized column.")
            elif name not in projection_aliases and not any(name in TABLE_COLUMNS[t] for t in aliases.values()):
                raise UnsafeQueryError("The query references an unauthorized column.")

    for projection in tree.expressions:
        source = projection.this if isinstance(projection, exp.Alias) else projection
        if not any(isinstance(node, exp.Column) for node in source.walk()) and not isinstance(source, exp.Count):
            raise UnsafeQueryError("Selected values must come from academic records.")
        if any(isinstance(node, exp.Literal) and node.is_string for node in source.walk()):
            raise UnsafeQueryError("String constants cannot be presented as academic records.")

    requested_limit = tree.args.get("limit")
    if requested_limit is not None:
        value = requested_limit.expression
        if not isinstance(value, exp.Literal) or value.is_string or not value.this.isdigit():
            raise UnsafeQueryError("LIMIT must be a positive integer.")
        requested = int(value.this)
        if requested < 1:
            raise UnsafeQueryError("LIMIT must be a positive integer.")
        capped = requested > max_rows
        row_limit = min(requested, max_rows)
    else:
        capped = True
        row_limit = max_rows
    tree.set("limit", exp.Limit(expression=exp.Literal.number(row_limit)))
    return SafeQuery(sql=tree.sql(dialect="mysql"), row_limit=row_limit, was_capped=capped)
