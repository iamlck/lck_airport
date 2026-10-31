import datetime
from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey, create_engine
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class SessionModel(Base):
    __tablename__ = "sessions"

    id = Column(String(64), primary_key=True, index=True)
    user_id = Column(String(64), nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    summary = Column(Text, nullable=True)

    messages = relationship("MessageModel", back_populates="session", cascade="all, delete-orphan", order_by="MessageModel.created_at")


class MessageModel(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(64), ForeignKey("sessions.id"), nullable=False, index=True)
    role = Column(String(16), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    strategy = Column(String(16), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    session = relationship("SessionModel", back_populates="messages")

