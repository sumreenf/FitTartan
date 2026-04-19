"""SQLite + SQLAlchemy models for FitTartan."""

from __future__ import annotations

from datetime import date, datetime
from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
    inspect,
    text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    weight_kg: Mapped[float] = mapped_column(Float, nullable=False)
    goal: Mapped[str] = mapped_column(String(32), nullable=False)
    activity_level: Mapped[str] = mapped_column(String(32), nullable=False)
    dietary_restrictions: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    # Biometrics for Mifflin–St Jeor BMR / TDEE (nullable for legacy DB rows).
    age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    height_cm: Mapped[float | None] = mapped_column(Float, nullable=True)
    sex: Mapped[str | None] = mapped_column(String(16), nullable=True)  # male | female | other
    training_split: Mapped[str | None] = mapped_column(String(32), nullable=True)

    workouts: Mapped[list["WorkoutLog"]] = relationship(back_populates="user")
    weights: Mapped[list["WeightLog"]] = relationship(back_populates="user")
    foods: Mapped[list["FoodLog"]] = relationship(back_populates="user")
    checkins: Mapped[list["GymCheckin"]] = relationship(back_populates="user")


class WorkoutLog(Base):
    __tablename__ = "workout_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    exercise: Mapped[str] = mapped_column(String(256), nullable=False)
    sets: Mapped[int] = mapped_column(Integer, nullable=False)
    reps: Mapped[int] = mapped_column(Integer, nullable=False)
    weight_kg: Mapped[float | None] = mapped_column(Float, nullable=True)

    user: Mapped["User"] = relationship(back_populates="workouts")


class WeightLog(Base):
    __tablename__ = "weight_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    weight_kg: Mapped[float] = mapped_column(Float, nullable=False)

    user: Mapped["User"] = relationship(back_populates="weights")


class FoodLog(Base):
    __tablename__ = "food_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    item_name: Mapped[str] = mapped_column(String(512), nullable=False)
    calories: Mapped[float] = mapped_column(Float, nullable=False)
    protein: Mapped[float] = mapped_column(Float, nullable=False)
    carbs: Mapped[float] = mapped_column(Float, nullable=False)
    fat: Mapped[float] = mapped_column(Float, nullable=False)

    user: Mapped["User"] = relationship(back_populates="foods")


class GymCheckin(Base):
    __tablename__ = "gym_checkins"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    gym_location: Mapped[str] = mapped_column(String(128), nullable=False, index=True)

    user: Mapped["User"] = relationship(back_populates="checkins")


class DiningMenuItem(Base):
    __tablename__ = "dining_menu_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(512), nullable=False, index=True)
    calories: Mapped[float] = mapped_column(Float, nullable=False)
    protein: Mapped[float] = mapped_column(Float, nullable=False)
    carbs: Mapped[float] = mapped_column(Float, nullable=False)
    fat: Mapped[float] = mapped_column(Float, nullable=False)
    location: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    meal_period: Mapped[str] = mapped_column(String(64), nullable=False)
    date_scraped: Mapped[date] = mapped_column(Date, nullable=False, index=True)


class GuardrailLog(Base):
    __tablename__ = "guardrail_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    trigger_type: Mapped[str] = mapped_column(String(64), nullable=False)
    message_snippet: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class MealSuggestionRating(Base):
    __tablename__ = "meal_suggestion_ratings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    suggestion_text: Mapped[str] = mapped_column(Text, nullable=False)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)  # 1 up, -1 down
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class OverloadSuggestionLog(Base):
    """Tracks progressive overload suggestions for eval (vs next workout)."""

    __tablename__ = "overload_suggestion_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    exercise: Mapped[str] = mapped_column(String(256), nullable=False)
    suggested_weight_kg: Mapped[float] = mapped_column(Float, nullable=False)
    session_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    next_session_weight_kg: Mapped[float | None] = mapped_column(Float, nullable=True)
    matched: Mapped[bool | None] = mapped_column(Boolean, nullable=True)


class CrowdPredictionEval(Base):
    """Stores snapshot of predicted quiet windows vs actual density for eval."""

    __tablename__ = "crowd_prediction_eval"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    gym: Mapped[str] = mapped_column(String(128), nullable=False)
    day_of_week: Mapped[int] = mapped_column(Integer, nullable=False)
    predicted_quiet_hours: Mapped[str] = mapped_column(Text, nullable=False)  # JSON list
    actual_peak_hour: Mapped[int | None] = mapped_column(Integer, nullable=True)
    checkin_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


DATABASE_URL = "sqlite:///./fittartan.db"
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def _migrate_sqlite_workout_weight_nullable() -> None:
    """Allow NULL workout weight_kg (SQLite cannot flip NOT NULL with a simple ALTER)."""
    try:
        insp = inspect(engine)
        names = insp.get_table_names() or []
        if "workout_logs" not in names:
            return
        cols = {c["name"]: c for c in insp.get_columns("workout_logs")}
        w = cols.get("weight_kg")
        if not w or w.get("nullable", True):
            return
    except Exception:
        return
    stmts = [
        """
        CREATE TABLE workout_logs__new (
            id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            date DATE NOT NULL,
            exercise VARCHAR(256) NOT NULL,
            sets INTEGER NOT NULL,
            reps INTEGER NOT NULL,
            weight_kg FLOAT,
            FOREIGN KEY(user_id) REFERENCES users (id)
        )
        """,
        """
        INSERT INTO workout_logs__new (id, user_id, date, exercise, sets, reps, weight_kg)
        SELECT id, user_id, date, exercise, sets, reps, weight_kg FROM workout_logs
        """,
        "DROP TABLE workout_logs",
        "ALTER TABLE workout_logs__new RENAME TO workout_logs",
        "CREATE INDEX IF NOT EXISTS ix_workout_logs_user_id ON workout_logs (user_id)",
        "CREATE INDEX IF NOT EXISTS ix_workout_logs_date ON workout_logs (date)",
    ]
    with engine.begin() as conn:
        for stmt in stmts:
            conn.execute(text(stmt))


def _migrate_sqlite_users_columns() -> None:
    """Add columns introduced after first deploy (SQLite has no ALTER in create_all)."""
    try:
        insp = inspect(engine)
        if insp.get_table_names() is None or "users" not in insp.get_table_names():
            return
        existing = {c["name"] for c in insp.get_columns("users")}
    except Exception:
        return
    alters: list[str] = []
    if "age" not in existing:
        alters.append("ALTER TABLE users ADD COLUMN age INTEGER")
    if "height_cm" not in existing:
        alters.append("ALTER TABLE users ADD COLUMN height_cm FLOAT")
    if "sex" not in existing:
        alters.append("ALTER TABLE users ADD COLUMN sex VARCHAR(16)")
    if "training_split" not in existing:
        alters.append("ALTER TABLE users ADD COLUMN training_split VARCHAR(32)")
    if not alters:
        return
    with engine.begin() as conn:
        for stmt in alters:
            conn.execute(text(stmt))


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    if str(engine.url).startswith("sqlite"):
        _migrate_sqlite_workout_weight_nullable()
        _migrate_sqlite_users_columns()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
