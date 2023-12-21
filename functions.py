from models import db_session, Book, User, Rates, TokenBlocklist, Author
from sqlalchemy.exc import IntegrityError
import pandas as pd
from sqlalchemy import func
from  werkzeug.security import generate_password_hash

#inserting functions of users, books and ratings
#https://www.geeksforgeeks.org/python-try-except/
#https://docs.sqlalchemy.org/en/14/orm/quickstart.html
def ins_user(name, email, username, password, phone, user_type, random_code):
    #https://www.geeksforgeeks.org/python-try-except/
    db_session.rollback() #ignore changes
    try:
        user = User(name=name, email=email, username=username, password=generate_password_hash(password), phone=phone, user_type=user_type, random_code=None)
        db_session.add(user)
        db_session.commit() #save changes which is (add user)
        return True
    except IntegrityError as e:
        print(f'could not add {username}')
        pass
    return False

    
def ins_Book(title, author, pub_year, publisher, price, avg_rate, count_rate, image):
    db_session.rollback()
    try:
        book = Book(title=title, author=author, pub_year=pub_year, publisher=publisher, price=price, avg_rate=avg_rate, count_rate= count_rate, image=image )
        db_session.add(book)
        db_session.commit()
        db_session.flush()
        return book
    except IntegrityError as e:
        print(f'could not add book {title}')
        pass
    return False

    
def ins_Rate(User_id, Book_id, rate):
    db_session.rollback()
    try:
        rating = Rates(User_id=User_id, Book_id=Book_id, rate=rate )
        db_session.add(rating)        
        db_session.commit()
        return True
    except IntegrityError as e:
        print(f'could not add rate {id}')
        pass
    return False

def ins_author(id, author_name):
    db_session.rollback()
    try:
        author = Author(id=id, author_name=author_name )
        db_session.add(author)        
        db_session.commit()
        return True
    except IntegrityError as e:
        print(f'could not add author {id}')
        pass
    return False

#get all values of inserted data
#https://docs.sqlalchemy.org/en/14/orm/query.html#sqlalchemy.orm.Query.first
def get_users():
    return db_session.query(User).all()

def get_ratings():
    return db_session.query(Rates).all()

def get_books(year=None, author=None):
    query=db_session.query(Book)

    if(year != None):
        query=query.filter(Book.pub_year == year)
    if(author != None):
        query=query.filter(func.lower(Book.author) == author.lower())    
    return query.all()

def get_authors():
    return db_session.query(Author).all()

#get spacific data
def get_user_by_id(id):
    return db_session.query(User).get(id)

def get_book_by_id(id):
    return db_session.query(Book).get(id)    

def get_spacific_user_rates(user_id):
    return (db_session.query(Rates.Book_id, Rates.rate).filter(Rates.User_id == user_id).all())

def did_user_rate(user_id):
    return len(db_session.query(Rates).filter(Rates.User_id == user_id).all()) > 0

#authentication

def user_exist(username):
    return db_session.query(User).filter(func.lower(User.username) == username.lower()).first()
def email_exist(email):
    return db_session.query(User).filter(func.lower(User.email) == email.lower()).first()
def book_exist(title):
    return db_session.query(Book).filter(func.lower(Book.title) == title.lower()).first()
def book_exist_by_id(id):
    return db_session.query(Book).filter(Book.id == id).first()
def rate_exist(user_id, book_id):
    return db_session.query(Rates).filter(Rates.User_id==user_id, Rates.Book_id==book_id).first()
#For loguot end point
def token_exist(jti):
    return db_session.query(TokenBlocklist.id).filter_by(jti=jti).scalar()


#Delete book
def deleting_book(book_id):
    book=db_session.query(Book).filter(Book.id == book_id).first()
    db_session.delete(book)
    db_session.commit()
    return True

#convert rows of (get_users | get_books | get_ratings) into dictionary and then convert this dictionry into dataframe????????????
# https://stackoverflow.com/questions/49432167/how-to-convert-rows-into-a-list-of-dictionaries-in-pyspark
# https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.from_records.html
def get_users_df():
    return pd.DataFrame.from_records(row.as_dict() for row in get_users()) 
def get_books_df(year, author):
    return pd.DataFrame.from_records(row.as_dict() for row in get_books(year, author))
def get_ratings_df():
    return pd.DataFrame.from_records(row.as_dict() for row in get_ratings())

def get_latest_books():
    return sorted(get_books(), key=lambda x: -x.pub_year)[:10]


# print(get_books())
# print('----------------------------')
# print(get_books_df())

