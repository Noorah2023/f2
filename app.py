# The Server

import os
from datetime import timedelta, datetime, timezone
from random import randint
from flask import Flask, request, jsonify, make_response
from functions import get_users, get_authors, get_books, get_book_by_id, get_latest_books, ins_Book, ins_Rate, ins_user, rate_exist, user_exist, token_exist, email_exist, book_exist, book_exist_by_id, deleting_book
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required, JWTManager, decode_token, get_jwt
from middlewares import only_roles
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash, generate_password_hash
from models import db_session, TokenBlocklist
import requests

app = Flask(__name__)

#Upload PDF book file config
UPLOAD_FOLDER = 'PDF_books/'
ALLOWED_EXTENSION = {'pdf'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# JWT config
# https://flask-jwt-extended.readthedocs.io/en/stable/
app.config["JWT_SECRET_KEY"] = "0d4195ef4fce637fa458ec65e1732259"
ACCESS_EXPIRES = timedelta(hours=24 * 365) 
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = ACCESS_EXPIRES
jwt = JWTManager(app)

#Send mail config
url="https://api.mailgun.net/v3/sandbox68fd87451ea44605a2e7dabd06ddc32f.mailgun.org/messages"
#"https://api.mailgun.net/v3/sandboxb650d38b2a2d40dbbb364ce6ec44f913.mailgun.org/messages"
api="cdef3373b021909746c7b788f8c55633-b0ed5083-033dc5b2"
#"242734466f4d9585cdcf262b9fba095c-b0ed5083-87a8898b"
from_email="Ebook Store <postmaster@sandbox68fd87451ea44605a2e7dabd06ddc32f.mailgun.org>"
#"Ebook Store <postmaster@sandboxb650d38b2a2d40dbbb364ce6ec44f913.mailgun.org>"
expire_time = datetime.now() + timedelta(hours=1)       

    
# Callback function to check if a JWT exists in the redis blocklist(For logout function)
@jwt.token_in_blocklist_loader
def check_if_token_revoked(jwt_header, jwt_payload: dict) -> bool:
    jti = jwt_payload["jti"]
    token = token_exist(jti=jti)
    return token is not None

#To check that the uploaded file is a PDF file.
# ['.' in filename] to make sure that the filename has dot. 
# [filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS] take the letters after dot in the file name and check if the extension valid or not(pdf).
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSION

def user_or_visitor():
    header_jwt = request.headers.get('Authorization', 'Bearer').split('Bearer')[1].strip()
    try:
        user_identity = decode_token(header_jwt)
        return user_identity.get('sub')
    except Exception as e:
        return None

########################################### CUSTOMERS END POINTS ########################################

#-------------------------------------------------User Account
# Authentication
@app.route("/login", methods=["POST"])
def login():
    auth = request.json
    if not auth or not auth.get('username') or not auth.get('password'):
        return make_response(jsonify({"msg": 'Login required', "status": False}), 401)

    user =  user_exist(username=auth.get('username'))
    if user is not None:
        if check_password_hash(user.password, auth.get('password')):
        # account found
        # generate json web token
        # user object is an instance of User class and Userclass has as_dict() method that generate dictionary for the object
            token = create_access_token(identity=user.as_dict())
            return make_response(jsonify({'token': token, "user_type": user.user_type,"status": True}), 201)
        else:
            return make_response(jsonify({"msg": "Invalid Password", "status": False}), 401)
        # account not exist
    else:
        return make_response(jsonify({"msg": "Invalid Username", "status": False}), 401)

#Create new account
@app.route("/register", methods=["POST"])
def register():
    signup = request.get_json()  # take user data in json
    user = user_exist(username=signup['username'])
    email = email_exist(email=signup['email'])
    if user is None:
        if email is None:
            ins_user(
                name=signup['name'],
                email=signup['email'],
                username=signup['username'],
                password=signup['password'],
                phone=signup['phone'],
                # DONT ALLOW USERS TO DECIDE THEIR OWN "user_type"
                user_type="customer",
                random_code= 0
            )
            return make_response(jsonify({"msg": 'Successfully registered.', "status": True}), 201)
        else:
            # email already exists
            return make_response(jsonify({"msg": 'Email is already exist.', "status": False}), 202)
    else:
        # username already exists
        return make_response(jsonify({"msg": 'Username is already exist. Please try another username.', "status": False}), 202)

#logout
@app.route("/logout", methods=["DELETE"])
@jwt_required()
def logout():
   jti = get_jwt()["jti"]
   now = datetime.now(timezone.utc)
   db_session.add(TokenBlocklist(jti=jti, created_at=now))
   db_session.commit()
   return jsonify(msg="JWT revoked")

#Reset Password-------------------------------------------------------------------------
#Ensure that the email is exist and send a random code
@app.route("/send-random-code")
def send_random_code():
    email=request.get_json() #email
    exist=email_exist(email=email['email'])
    if exist is not None:
        code = randint(100000, 999999)
        exist.random_code = code
        db_session.commit()
        msg_resp = requests.post(
		url,
		auth=("api", api),
		data={"from": from_email,
			"to": f"{exist.name} <{email['email']}>",
			"subject": f"Hello {exist.name},",
			"text": f"Here is your temporary verification code. \n({code})\n Don't share it with any one!"})
        #print(msg_resp.content)
        time = datetime.now()
        print(time)
        return jsonify({"msg": "message sent", "status": True})
    else:
        return jsonify({"msg": "Invalid Email", "status": False})

#take and check the verification code then reset password
@app.route("/reset-password")
def reset_password():
    data = request.get_json() #email, password, random code and datetime in "%Y-%m-%d %H:%M:%S.%f" format
    user=email_exist(email=data['email']) #step1: check if the email is exist
    expire_time =datetime.strptime(data['time'], "%Y-%m-%d %H:%M:%S.%f") + timedelta(minutes=5) #step2: add an expire time for the verification code(5 minutes)
    if user.random_code == data['code']: #step3: check if the inserted code equal to sent code
        if expire_time > datetime.now(): #step4: check if the code has not been expired
            user.password = generate_password_hash(data['password']) #step5: change the password
            user.random_code = None #when the password changed, set random code in db to 0
            db_session.commit()
            return jsonify({"msg": "Password have been changed successfully", "status": True})
        else:
            user.random_code = None #when the code expired, set random code in db to 0
            db_session.commit()
            return jsonify({"msg": "Verification Code has been expired. Try again.", "status": False})
    else:
        return jsonify({"msg": "Invalid Verification Code", "status": False})   
#End of reset password code-------------------------------------------------------------------------

#show profile
@app.route("/user-profile", methods=["GET"])  # **Not sure yet**
@jwt_required()
def user_profile():
    # get the current user identity from JWT
    current_user = get_jwt_identity()
    del current_user['id'], current_user['password'], current_user['user_type']
    return jsonify( {"User Data": current_user})

#Show Books
# show all books for vistors and users in the books list page
@app.route("/books", methods=["GET"])
def get_all_books():
    filtered_by = request.get_json()
    books = get_books(year=filtered_by['year'], author=filtered_by['author'])
    output = [book.as_dict() for book in books]
    # EASY WAY [BUT IT'S BETTER TO USE LIST COMPERHENSION]
    # for book in books:
    #     output.append(book.as_dict())
    return jsonify({'Books': output})

#Show book details
@app.route("/book-details", methods=["GET"])
def book_details():
    book_id = request.get_json()
    try:
        details=get_book_by_id(id=book_id["id"]).as_dict(exclude=['id'])
        return jsonify({"Book Details": details})
    except:
        return make_response(jsonify({'msg': "Something went wrong", "status": False}), 401)

#show latest books
@app.route("/latest-books", methods=["GET"])
def latest_books():
    books=get_latest_books()
    output = [book.as_dict() for book in books]
    return jsonify({'Latest Books': output})

#show recomended books 
  

# List of authors
@app.route("/get-authors", methods=["GET"])
def get_author():
    authors = get_authors()
    output = [author.as_dict(exclude=["id"]) for author in authors] # LIST COMPERHENSION
    return jsonify({'Authors': output})



#Make Orders--------------------------------------------------------

#Send email with attachment file
@app.route("/send-mail")
def send_email():
    data = request.get_json() #email and book_id
    filename = f"PDF_books/{data['id']}.pdf"
    user=email_exist(email=data['email'])
    if user is not None:
        msg_resp = requests.post(
		url,
		auth=("api", api),
        files=[("attachment", (filename, open(filename, "rb").read()))],
		data={"from": from_email,
			"to": f"{user.name} <{data['email']}>",
			"subject": "Hello There,",
			"text": f"Here is your file. Enjoy Reading!"})
        #print(msg_resp.content)
        return jsonify({"msg": "Message sent. Please check your junk mails", "status": True})
    else:
        return jsonify({"msg": "Invalid Email", "status": False})

#End of make orders code--------------------------------------------------------

# @app.route("/can-buy", methods=["GET"])
# def can_user_buy():
#     user = user_or_vistor()
#     if(user is not None):
#        can_buy = True
#     else:
#        can_buy = False
    
#     return jsonify({'can-buy': can_buy})

# @app.route("/buy", methods=["GET"])
# @jwt_required()
# def buy_book():
#     user = get_jwt_identity()

#     return jsonify({})

#Insert rate and compute it 
@app.route("/insert-rate", methods=["POST"])
@jwt_required()
def insert_rate():
    data=request.get_json() #book_id and rate
    current_user=get_jwt_identity()
    exist = book_exist_by_id(id=data['book_id'])
    if exist is not None:
        rate=rate_exist(user_id=current_user['id'], book_id=data['book_id'] )
        if rate is None:
            ins_Rate(User_id=current_user['id'], Book_id=data['book_id'], rate=data['rate'])
            exist.count_rate = exist.count_rate+1
            db_session.commit()
            
            db_session.commit()
            return make_response(jsonify({"msg": 'Rate added successfully.', "status": True}), 201)
        else:
            return make_response(jsonify({"msg": 'You have rated this book.', "status": False}), 202)
    else:
        return make_response(jsonify({"msg": 'Invalid Book ID.', "status": False}), 401)
    
    

    #return make_response(jsonify({"msg": 'Rate added successfully.', "status": True}), 201) 
    
########################################### EMPLOYEE END POINTS ########################################
# show users
@app.route("/users", methods=["GET"])
@jwt_required()
@only_roles(['employee'])
def get_all_users():
    users = get_users()
    # exclude parameter is a list of fields that you don't need it
    output = [user.as_dict(exclude=['password']) for user in users] # LIST COMPERHENSION
    return jsonify({'Users': output})

#Add new book
@app.route("/insert-book", methods=["POST", "GET"])
@jwt_required()
@only_roles(['employee'])
def insert_new_book():
    book_data= request.form

    if book_data is not None:
        exist_book = book_exist(title=book_data['title'])
        if exist_book is None:
            new_book=ins_Book(
                title=book_data['title'],
                author=book_data['author'],
                pub_year=book_data['pub_year'],
                publisher=book_data['publisher'],
                price=book_data['price'],
                avg_rate=0,
                count_rate=0,
                image=book_data['image']
            )
            # https://flask.palletsprojects.com/en/2.2.x/patterns/fileuploads/
            #Add book pdf file to the PDF_books folder. 
            if 'file' not in request.files:
                return make_response(jsonify({"msg": "No file part in request.", "status": False}), 403)

            file = request.files['file']
            if file.filename == '':
                return make_response(jsonify({"msg": "No file uploaded. Try again.", "status": False}), 403)

            if file and allowed_file(file.filename):
# secure_filename: Used to return a secure version of the filename. This filename can then safely be stored on a regular file system and passed to os.path.join().
# (./../Book/one.pdf) this will be (Book_one.pdf)
                filename = secure_filename(file.filename) 
                filename = f"{new_book.id}.pdf" #to rename the book file to be the same as its id.
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                return make_response(jsonify({"msg": 'Book added successfully.', "status": True}), 201) 
        else: 
            return make_response(jsonify({"msg": 'Book Already Exist', "status": False}), 202)
    
    else: 
        return make_response(jsonify({"msg": 'Something went wrong. Try again', "status": False}), 401)

#Delete Book
@app.route("/delete-book")
@jwt_required()
@only_roles(['employee'])
def delete_book():
    book = request.get_json() #book id
    exist = book_exist_by_id(id=book['id'])
    if exist is not None:
        deleting = deleting_book(book_id=book['id'])
        if deleting is True:
            #Remove the pdf file related to this book id from PDF_books file
            os.remove(f"PDF_books/{book['id']}.pdf")
            return make_response(jsonify({"msg": 'Book removed successfully.', "status": True}), 201)
        else:
            return make_response(jsonify({"msg": 'Something went wrong. Try again', "status": False}), 401)
    else:
        return make_response(jsonify({"msg": 'Book not exist', "status": False}), 401)

if __name__ == '__main__':
    app.run(debug=True)

