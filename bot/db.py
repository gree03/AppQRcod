"""Database helpers for the Telegram bot.

The module defines SQLAlchemy models and helper functions to create tables
and interact with the database. For unit tests we use an in-memory SQLite
engine but the configuration can point to any SQLAlchemy-supported backend.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List

from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    ForeignKey,
    create_engine,
    select,
)
from sqlalchemy.orm import declarative_base, relationship, Session

Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    username = Column(String, nullable=True)
    invited = Column(Boolean, default=False)
    onboarding_complete = Column(Boolean, default=False)
    table_assignment = Column(Integer, nullable=True)

    answers = relationship("Answer", back_populates="user", cascade="all, delete-orphan")


class Question(Base):
    __tablename__ = "questions"
    id = Column(Integer, primary_key=True)
    text = Column(String, nullable=False)
    type = Column(String, nullable=False)

    answers = relationship("Answer", back_populates="question", cascade="all, delete-orphan")


class Answer(Base):
    __tablename__ = "answers"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    question_id = Column(Integer, ForeignKey("questions.id"))
    text = Column(String, nullable=False)

    user = relationship("User", back_populates="answers")
    question = relationship("Question", back_populates="answers")


def create_engine_and_tables(url: str):
    engine = create_engine(url)
    Base.metadata.create_all(engine)
    return engine


def add_user(session: Session, telegram_id: int, username: str | None = None, invited: bool = False) -> User:
    user = User(telegram_id=telegram_id, username=username, invited=invited)
    session.add(user)
    session.commit()
    return user


def invite_users(session: Session, ids: Iterable[int]) -> None:
    for uid in ids:
        user = session.execute(select(User).where(User.telegram_id == uid)).scalar_one_or_none()
        if user:
            user.invited = True
        else:
            session.add(User(telegram_id=uid, invited=True))
    session.commit()


def store_answer(session: Session, user: User, question: Question, text: str) -> Answer:
    answer = Answer(user=user, question=question, text=text)
    session.add(answer)
    session.commit()
    return answer
