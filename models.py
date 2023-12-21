# to return a base class that all mapped classes should inherit which are (users, books and book ratings)

from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, String, Integer, Float, ForeignKey, DateTime  # we need those data types, so we have to import them
from sqlalchemy import create_engine  # to create database and store these objects inside it, we need to create an engine
from sqlalchemy.orm import Session
Base = declarative_base()  # tha base that all tables(Books, Users, Book-Rating) inherent from

# future: to ensure using the latest version of SQLAlchemy (the used library). encoding the format of excel sheets.
# encoding: to make sure thhat all letters to be inserted are correct. (such as the issues with arabic letters)
# {
# https://stackoverflow.com/questions/34009296/using-sqlalchemy-session-from-flask-raises-sqlite-objects-created-in-a-thread-c
# (?check_same_thread=False): to make the database accessable all the time.
# واجهت مشكلة انه اذا شغلت السيرفر اقدر ارسل امر واحد فقط في البوستمان والامر الثاني يطلع لي خطأ لذلك استخدمت هذا البرامتر عشان يكون طول الوقت اكسسبل
# }
engine2 = create_engine("sqlite:///app_data.db?check_same_thread=False", future=True, encoding='utf-8')
db_session = Session(engine2)
# A Session establishes and maintains all conversations between your program and the databases.
# It represents an intermediary zone for all the Python model objects you have loaded in it.


# https://docs.sqlalchemy.org/en/14/orm/quickstart.html


class User(Base):
    __tablename__ = 'users'
    # primary key used to uniquely identify a row and a table can have only one primary key
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)

    username = Column(String, nullable=False, unique=True)
    password = Column(String, nullable=False)

    phone = Column(Integer, nullable=False)
    user_type = Column(String)
    random_code=Column(Integer)

    # to represent the User object as string 
    def __repr__(self):  # self refers to this class which is User class here
        # will return the id and the username as string of spacific user
        return f"<User(id={self.id}, username={self.username})>"

    # to show objects in dictionary
    def as_dict(self, exclude=[]):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns if c.name not in exclude}


class Book(Base):
    __tablename__ = 'books'
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    author = Column(String, nullable=False)
    pub_year = Column(Integer, nullable=False)
    publisher = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    avg_rate = Column(Float, nullable=False, default=0)
    count_rate = Column(Integer, nullable=False, default=0)
    image = Column(String, nullable=False)

    # to represent the Book object as string
    def __repr__(self):
        return f"<Book(id={self.id}, author={self.author}, title={self.title}, price={self.price}, year={self.pub_year}, avg_rate={self.avg_rate})>"

    def as_dict(self, exclude=[]):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns if c.name not in exclude}

class Author(Base):
    __tablename__ = 'authors'
    id = Column(Integer, primary_key=True)
    author_name = Column(String, nullable=False, unique=True)

    # to represent the Book object as string
    def __repr__(self):
        return f"<Author(id={self.id}, author_name={self.author_name})>"

    def as_dict(self, exclude=[]):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns if c.name not in exclude}

class Rates(Base):
    __tablename__ = 'book_rating'
    id = Column(Integer, primary_key=True)

    # Foreign key is a column or group of columns used to connect two tables or maintain relationship between them
    User_id = Column(Integer, ForeignKey('users.id'))
    Book_id = Column(Integer, ForeignKey('books.id'))
    rate = Column(Float)

    # to represent the Rate object as string
    def __repr__(self):
        return f"<Rates(User_id={self.User_id}, Book_id={self.Book_id}, rate={self.rate})>"
    def as_dict(self, exclude=[]):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns if c.name not in exclude}

#For loguot end point
class TokenBlocklist(Base):
    __tablename__ = 'token_block_list'
    id = Column(Integer, primary_key=True)
    jti = Column(String(36), nullable=False, index=True)
    created_at = Column(DateTime, nullable=False)


# in my notes$$$$$$$$
if __name__ == '__main__':
    Base.metadata.create_all(engine2)
    # meatadata is an objects that keeps together many features of the database
    # يعني مثلا كل كتاب عنده خصائص معينة مثل الاسم التايتل المؤلف وغيرها هي تحفظ هذي الاشياء مع بعض عشان تشير الى مثلا اوبجكت الكتاب
    # using this statement to creat all tables that have benn defined.

check_same_thread = False
