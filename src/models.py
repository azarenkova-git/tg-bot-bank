from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Numeric, DateTime
from sqlalchemy.orm import sessionmaker, relationship, declarative_base

Base = declarative_base()


class AbstractModel(Base):
    __abstract__ = True

    id = Column(Integer, primary_key=True)

    def __repr__(self):
        return f"<{self.__class__.__name__}(id={self.id})>"


class UserModel(AbstractModel):
    __tablename__ = 'users'

    phone_number = Column(String, unique=True)
    tg_user_id = Column(Integer, unique=True)
    name = Column(String)
    transactions = relationship('TransactionModel', back_populates='user')
    balance = Column(Integer, default=0)


class TransactionModel(AbstractModel):
    __tablename__ = 'transactions'

    user_id = Column(Integer, ForeignKey('users.id'))
    amount = Column(Numeric)
    user = relationship('UserModel', back_populates='transactions')
    date = Column(DateTime)
