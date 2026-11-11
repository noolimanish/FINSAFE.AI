"""
SQLite persistence layer for FinSafe.
Defines the 7 core tables:
  1. users
  2. profiles
  3. insurance_policies
  4. investments
  5. expenses
  6. audit_runs
  7. recommendations

Includes SQLAlchemy 2.0 declarative models when SQLAlchemy is installed in the environment,
plus a transparent stdlib sqlite3 repository so the app and test suite run in any Python 3.10+ environment.
"""

from __future__ import annotations

import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Dict, Generator, List, Optional

# Optional SQLAlchemy ORM metadata declaration for production / migrations inspection
try:
    from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text, create_engine
    from sqlalchemy.orm import declarative_base, sessionmaker

    Base = declarative_base()

    class UserORM(Base):
        __tablename__ = "users"
        id = Column(Integer, primary_key=True, index=True)
        alias = Column(String(64), nullable=False, default="Anonymous")
        created_at = Column(String(64), nullable=False)

    class ProfileORM(Base):
        __tablename__ = "profiles"
        id = Column(Integer, primary_key=True, index=True)
        user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
        age = Column(Integer, nullable=False)
        retirement_age = Column(Integer, nullable=False, default=60)
        annual_income = Column(Float, nullable=False)
        dependents = Column(Integer, nullable=False, default=0)
        monthly_retirement_contribution = Column(Float, nullable=False, default=0.0)
        updated_at = Column(String(64), nullable=False)

    class InsurancePolicyORM(Base):
        __tablename__ = "insurance_policies"
        id = Column(Integer, primary_key=True, index=True)
        user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
        policy_type = Column(String(32), nullable=False)
        provider_name = Column(String(128), nullable=False)
        sum_assured = Column(Float, nullable=False)
        annual_premium = Column(Float, nullable=False, default=0.0)

    class InvestmentORM(Base):
        __tablename__ = "investments"
        id = Column(Integer, primary_key=True, index=True)
        user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
        category = Column(String(32), nullable=False)
        instrument_name = Column(String(128), nullable=False)
        current_value = Column(Float, nullable=False)
        is_locked = Column(Boolean, nullable=False, default=False)

    class ExpenseORM(Base):
        __tablename__ = "expenses"
        id = Column(Integer, primary_key=True, index=True)
        user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
        category = Column(String(32), nullable=False)
        label = Column(String(128), nullable=False)
        monthly_amount = Column(Float, nullable=False)

    class AuditRunORM(Base):
        __tablename__ = "audit_runs"
        id = Column(Integer, primary_key=True, index=True)
        user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
        security_score = Column(Integer, nullable=False)
        score_band = Column(String(32), nullable=False)
        metrics_json = Column(Text, nullable=False)
        findings_json = Column(Text, nullable=False)
        llm_used = Column(Boolean, nullable=False, default=False)
        created_at = Column(String(64), nullable=False)

    class RecommendationORM(Base):
        __tablename__ = "recommendations"
        id = Column(Integer, primary_key=True, index=True)
        audit_run_id = Column(Integer, ForeignKey("audit_runs.id"), nullable=False, index=True)
        priority_order = Column(Integer, nullable=False)
        week_bucket = Column(String(32), nullable=False)
        rule_id = Column(String(16), nullable=False)
        title = Column(String(256), nullable=False)
        description = Column(Text, nullable=False)
        is_completed = Column(Boolean, nullable=False, default=False)

except ImportError:
    Base = None  # type: ignore


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    alias TEXT NOT NULL DEFAULT 'Anonymous',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL UNIQUE,
    age INTEGER NOT NULL,
    retirement_age INTEGER NOT NULL DEFAULT 60,
    annual_income REAL NOT NULL,
    dependents INTEGER NOT NULL DEFAULT 0,
    monthly_retirement_contribution REAL NOT NULL DEFAULT 0.0,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS insurance_policies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    policy_type TEXT NOT NULL,
    provider_name TEXT NOT NULL,
    sum_assured REAL NOT NULL,
    annual_premium REAL NOT NULL DEFAULT 0.0,
    FOREIGN KEY(user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS investments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    category TEXT NOT NULL,
    instrument_name TEXT NOT NULL,
    current_value REAL NOT NULL,
    is_locked INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY(user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    category TEXT NOT NULL,
    label TEXT NOT NULL,
    monthly_amount REAL NOT NULL,
    FOREIGN KEY(user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS audit_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    security_score INTEGER NOT NULL,
    score_band TEXT NOT NULL,
    metrics_json TEXT NOT NULL,
    findings_json TEXT NOT NULL,
    llm_used INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    FOREIGN KEY(user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS recommendations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    audit_run_id INTEGER NOT NULL,
    priority_order INTEGER NOT NULL,
    week_bucket TEXT NOT NULL,
    rule_id TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    is_completed INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY(audit_run_id) REFERENCES audit_runs(id)
);
"""


def get_db_path() -> str:
    db_url = os.getenv("DATABASE_URL", "sqlite:///./finsafe.db")
    if db_url.startswith("sqlite:///"):
        return db_url.replace("sqlite:///", "", 1)
    return "./finsafe.db"


class FinSafeRepository:
    """Clean, deterministic SQLite data access layer."""

    def __init__(self, db_path: Optional[str] = None) -> None:
        self.db_path = db_path or get_db_path()
        self._init_db()

    @contextmanager
    def _connect(self) -> Generator[sqlite3.Connection, None, None]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            with conn:
                yield conn
        finally:
            conn.close()

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.executescript(SCHEMA_SQL)
            conn.commit()

    def ensure_user(self, user_id: int = 1, alias: str = "Aarav") -> Dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
            if not row:
                conn.execute(
                    "INSERT INTO users (id, alias, created_at) VALUES (?, ?, ?)",
                    (user_id, alias, now),
                )
                conn.commit()
            elif alias and row["alias"] != alias:
                conn.execute("UPDATE users SET alias = ? WHERE id = ?", (alias, user_id))
                conn.commit()
            row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
            return dict(row)

    def upsert_profile(self, user_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        alias = data.get("alias", "Aarav")
        user = self.ensure_user(user_id=user_id, alias=alias)
        now = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            existing = conn.execute(
                "SELECT id FROM profiles WHERE user_id = ?", (user_id,)
            ).fetchone()
            if existing:
                conn.execute(
                    """
                    UPDATE profiles
                    SET age = ?, retirement_age = ?, annual_income = ?,
                        dependents = ?, monthly_retirement_contribution = ?, updated_at = ?
                    WHERE user_id = ?
                    """,
                    (
                        data["age"],
                        data.get("retirement_age", 60),
                        data["annual_income"],
                        data.get("dependents", 0),
                        data.get("monthly_retirement_contribution", 0.0),
                        now,
                        user_id,
                    ),
                )
            else:
                conn.execute(
                    """
                    INSERT INTO profiles
                    (user_id, age, retirement_age, annual_income, dependents, monthly_retirement_contribution, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        user_id,
                        data["age"],
                        data.get("retirement_age", 60),
                        data["annual_income"],
                        data.get("dependents", 0),
                        data.get("monthly_retirement_contribution", 0.0),
                        now,
                    ),
                )
            conn.commit()
            row = conn.execute(
                "SELECT * FROM profiles WHERE user_id = ?", (user_id,)
            ).fetchone()
            result = dict(row)
            result["alias"] = user["alias"]
            return result

    def get_profile(self, user_id: int = 1) -> Optional[Dict[str, Any]]:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT p.*, u.alias
                FROM profiles p
                JOIN users u ON u.id = p.user_id
                WHERE p.user_id = ?
                """,
                (user_id,),
            ).fetchone()
            return dict(row) if row else None

    def replace_insurance_policies(
        self, user_id: int, policies: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        self.ensure_user(user_id=user_id)
        with self._connect() as conn:
            conn.execute("DELETE FROM insurance_policies WHERE user_id = ?", (user_id,))
            for p in policies:
                conn.execute(
                    """
                    INSERT INTO insurance_policies (user_id, policy_type, provider_name, sum_assured, annual_premium)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        user_id,
                        p["policy_type"],
                        p["provider_name"],
                        p["sum_assured"],
                        p.get("annual_premium", 0.0),
                    ),
                )
            conn.commit()
        return self.list_insurance_policies(user_id)

    def list_insurance_policies(self, user_id: int = 1) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM insurance_policies WHERE user_id = ? ORDER BY id ASC",
                (user_id,),
            ).fetchall()
            return [dict(r) for r in rows]

    def replace_investments(
        self, user_id: int, investments: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        self.ensure_user(user_id=user_id)
        with self._connect() as conn:
            conn.execute("DELETE FROM investments WHERE user_id = ?", (user_id,))
            for inv in investments:
                is_locked = bool(inv.get("is_locked", inv["category"] in ("lic_endowment_ulip", "retirement_epf_ppf_nps")))
                conn.execute(
                    """
                    INSERT INTO investments (user_id, category, instrument_name, current_value, is_locked)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        user_id,
                        inv["category"],
                        inv["instrument_name"],
                        inv["current_value"],
                        1 if is_locked else 0,
                    ),
                )
            conn.commit()
        return self.list_investments(user_id)

    def list_investments(self, user_id: int = 1) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM investments WHERE user_id = ? ORDER BY id ASC",
                (user_id,),
            ).fetchall()
            out = []
            for r in rows:
                d = dict(r)
                d["is_locked"] = bool(d["is_locked"])
                out.append(d)
            return out

    def replace_expenses(
        self, user_id: int, expenses: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        self.ensure_user(user_id=user_id)
        with self._connect() as conn:
            conn.execute("DELETE FROM expenses WHERE user_id = ?", (user_id,))
            for exp in expenses:
                conn.execute(
                    """
                    INSERT INTO expenses (user_id, category, label, monthly_amount)
                    VALUES (?, ?, ?, ?)
                    """,
                    (user_id, exp["category"], exp["label"], exp["monthly_amount"]),
                )
            conn.commit()
        return self.list_expenses(user_id)

    def list_expenses(self, user_id: int = 1) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM expenses WHERE user_id = ? ORDER BY id ASC",
                (user_id,),
            ).fetchall()
            return [dict(r) for r in rows]

    def save_audit_run(
        self,
        user_id: int,
        security_score: int,
        score_band: str,
        metrics: Dict[str, Any],
        findings: List[Dict[str, Any]],
        action_plan: List[Dict[str, Any]],
        llm_used: bool,
    ) -> Dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO audit_runs
                (user_id, security_score, score_band, metrics_json, findings_json, llm_used, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    security_score,
                    score_band,
                    json.dumps(metrics),
                    json.dumps(findings),
                    1 if llm_used else 0,
                    now,
                ),
            )
            audit_run_id = cursor.lastrowid
            for item in action_plan:
                conn.execute(
                    """
                    INSERT INTO recommendations
                    (audit_run_id, priority_order, week_bucket, rule_id, title, description, is_completed)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        audit_run_id,
                        item["priority_order"],
                        item["week_bucket"],
                        item["rule_id"],
                        item["title"],
                        item["description"],
                        1 if item.get("is_completed", False) else 0,
                    ),
                )
            conn.commit()
        return self.get_latest_audit_run(user_id)  # type: ignore

    def get_latest_audit_run(self, user_id: int = 1) -> Optional[Dict[str, Any]]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM audit_runs WHERE user_id = ? ORDER BY id DESC LIMIT 1",
                (user_id,),
            ).fetchone()
            if not row:
                return None
            audit_id = row["id"]
            rec_rows = conn.execute(
                "SELECT * FROM recommendations WHERE audit_run_id = ? ORDER BY priority_order ASC",
                (audit_id,),
            ).fetchall()
            recs = []
            for r in rec_rows:
                d = dict(r)
                d["is_completed"] = bool(d["is_completed"])
                recs.append(d)

            profile = self.get_profile(user_id)
            return {
                "audit_run_id": audit_id,
                "user_id": user_id,
                "alias": profile["alias"] if profile else "Aarav",
                "security_score": row["security_score"],
                "score_band": row["score_band"],
                "llm_used": bool(row["llm_used"]),
                "created_at": row["created_at"],
                "metrics": json.loads(row["metrics_json"]),
                "findings": json.loads(row["findings_json"]),
                "action_plan": recs,
            }

    def toggle_recommendation(self, item_id: int, is_completed: bool) -> Optional[Dict[str, Any]]:
        with self._connect() as conn:
            conn.execute(
                "UPDATE recommendations SET is_completed = ? WHERE id = ?",
                (1 if is_completed else 0, item_id),
            )
            conn.commit()
            row = conn.execute(
                "SELECT * FROM recommendations WHERE id = ?", (item_id,)
            ).fetchone()
            if not row:
                return None
            d = dict(row)
            d["is_completed"] = bool(d["is_completed"])
            return d
