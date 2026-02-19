from sqlalchemy import (
    Column,
    Index,
    Integer,
    Text,
    String,
    Boolean,
    ForeignKey,
    DateTime,
)

from .meta import Base
from passlib.context import CryptContext#for password hashing, if needed in the future
from sqlalchemy.orm import relationship #for defining relationships between tables, if needed in the future
from datetime import datetime #for handling timestamps, if needed in the future

class MyModel(Base):
    __tablename__ = 'models'
    id = Column(Integer, primary_key=True)
    name = Column(Text)
    value = Column(Integer)


Index('my_index', MyModel.name, unique=True, mysql_length=255)



class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(100), unique=True)
    email = Column(String(200), unique=True, nullable=False)
    password = Column(String(300))

    products = relationship("Product", back_populates="owner")


class Product(Base):
    __tablename__ = 'products'
    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False)
    description = Column(Text, nullable=False)
    price = Column(Integer, nullable=False)
    image = Column(Text)

    
    is_deleted = Column(Boolean, default=False)
    user_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="products")

class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True)
    token = Column(String, nullable=False, unique=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    expires_at = Column(DateTime, nullable=False)
    is_revoked = Column(Boolean, default=False)

    user = relationship("User")    