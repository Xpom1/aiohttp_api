from sqlalchemy import (
    MetaData, Table, Column, Integer, String, ForeignKey, create_engine
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Poll(Base):
    __tablename__ = 'polls'
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    questions = relationship("Question", back_populates="poll")


class Question(Base):
    __tablename__ = 'questions'
    id = Column(Integer, primary_key=True)
    text = Column(String, nullable=False)
    poll_id = Column(Integer, ForeignKey('polls.id'))
    poll = relationship("Poll", back_populates="questions")
    options = relationship("Option", back_populates="question")


class Option(Base):
    __tablename__ = 'options'
    id = Column(Integer, primary_key=True)
    text = Column(String, nullable=False)
    question_id = Column(Integer, ForeignKey('questions.id'))
    question = relationship("Question", back_populates="options")
    votes = relationship("Vote", back_populates="option")


class Vote(Base):
    __tablename__ = 'votes'
    id = Column(Integer, primary_key=True)
    option_id = Column(Integer, ForeignKey('options.id'))
    option = relationship("Option", back_populates="votes")
