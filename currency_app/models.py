from sqlalchemy import Column, Integer, String, Float, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Session, relationship
from sqlalchemy.ext.declarative import declarative_base
from passlib.context import CryptContext
import uuid

Base = declarative_base()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    deleted = Column(Boolean, default=False)

    # Отношение с таблицей счетов
    accounts = relationship("Account", order_by="Account.id", back_populates="user")
    tokens = relationship("Token", order_by="Token.id", back_populates="user")

    def verify_password(self, password):
        return pwd_context.verify(password, self.hashed_password)


    @classmethod
    def get_by_id(cls, db: Session, user_id: int):
        return db.query(cls).filter(cls.id == user_id).first()


class Token(Base):
    __tablename__ = "tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID, ForeignKey('users.id'))
    token = Column(String, unique=True, index=True)

    user = relationship("User", back_populates="tokens")


class Currency(Base):
    __tablename__ = 'currencies'

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True)
    name = Column(String, unique=True)

    # Отношения с таблицей счетов и транзакций
    accounts = relationship("Account", order_by="Account.id", back_populates="currency")
    # transactions = relationship("Transaction", order_by="Transaction.id", back_populates="currency")


class Account(Base):
    __tablename__ = 'accounts'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID, ForeignKey('users.id'))
    currency_id = Column(Integer, ForeignKey('currencies.id'))
    balance = Column(Float, default=0.0)
    deleted = Column(Boolean, default=False)

    user = relationship("User", back_populates="accounts")
    currency = relationship("Currency", back_populates="accounts")

    transactions_from = relationship("Transaction", foreign_keys="[Transaction.account_from_id]", back_populates="account_from")
    transactions_to = relationship("Transaction", foreign_keys="[Transaction.account_to_id]", back_populates="account_to")


class Transaction(Base):
    __tablename__ = 'transactions'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    type = Column(String)

    account_from_id = Column(UUID, ForeignKey('accounts.id'), nullable=True)
    account_to_id = Column(UUID, ForeignKey('accounts.id'), nullable=True)

    amount_from = Column(Float)
    amount_to = Column(Float)

    rate_from = Column(Float, nullable=True)
    rate_to = Column(Float, nullable=True)

    success = Column(Boolean, default=False)

    account_from = relationship("Account", foreign_keys=[account_from_id])
    account_to = relationship("Account", foreign_keys=[account_to_id])



