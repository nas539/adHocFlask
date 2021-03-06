from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_cors import CORS
from flask_heroku import Heroku
from flask_bcrypt import Bcrypt
import io


app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = ""

db = SQLAlchemy(app)
ma = Marshmallow(app)

heroku = Heroku(app)
CORS(app)
bcrypt = Bcrypt(app)

class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False, unique=True)
    password = db.Column(db.Date(), nullable=False)
   
    def __init__(self, username, password):
        self.username = username
        self.password = password

class UserSchema(ma.Schema):
    class Meta:
        fields = ("id", "username", "password")

user_schema = UserSchema()
users_schema = UserSchema(many=True)

class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(), nullable=False)
    company = db.Column(db.String(), nullable=False)
    start_date = db.Column(db.String(), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    author_comment = db.relationship('Users', backref='appointments', lazy='joined')
    
    def __init__(self, title, company, start_date, user_id):
        self.title = title
        self.company = company
        self.start_date = start_date
        self.user_id = user_id
        

class AppointmentSchema(ma.Schema):
    class Meta:
        fields = ("id", "title", "company", "start_date", "user_id")

appointment_schema = AppointmentSchema()
appointments_schema = AppointmentSchema(many=True)

@app.route("/user/add", methods=["POST"])
def add_user():
    if request.content_type != "application/json":
        return jsonify("Error")

    post_data = request.get_json()
    username = post_data.get("username")
    password = post_data.get("password")

    username_check = db.session.query(User.username).filter(User.username == username).first()
    if username_check is not None:
        return jsonify("Username taken")

    hashed_password = bcrypt.generate_password_hash(password).decode("utf8")

    record = User(username, hashed_password)
    db.session.add(record)
    db.session.commit()

    return jsonify("User created")

@app.route("/user/get/<id>", methods=["GET"])
def get_user_by_id(id):
    user = db.session.query(User).filter(User.id == id).first()
    return jsonify(user_schema.dump(user))

@app.route("/user/get", methods=["GET"])
def get_all_users():
    all_users = db.session.query(User).all()
    return jsonify(users_schema.dump(all_users))

@app.route("/user/login", methods=["POST"])
def verify_user():
    if request.content_type != "application/json":
        return jsonify("Error, data must be sent as json")

    post_data = request.get_json()
    username = post_data.get("username")
    password = post_data.get("password")

    stored_password = db.session.query(User.password).filter(User.username == username).first()
    
    if stored_password is None:
        return jsonify("User not Verified")

    valid_password_check = bcrypt.check_password_hash(stored_password[0], password)

    if valid_password_check == False:
        return jsonify("User not Verified")

    return jsonify("User verified")

@app.route("/appointment/add", methods=["POST"])
def add_appointment():
    if request.content_type != "application/json":
        return jsonify("Error")

    post_data = request.get_json()
    title = post_data.get("title")
    company = post_data.get("company")
    start_date = post_data.get("start_date")
    username = request.form.get("username")

    user_id = db.session.query(User.id).filter(User.username == username).first()

    new_appointment = Appointment(title, company, start_date, user_id[0])
    db.session.add(new_appointment)
    db.session.commit()

    return jsonify("Appointment added!")

@app.route("/appointment/get/data", methods=["GET"])
def get_appointment_data():
    appointment_data = db.session.query(Appointment).all()
    return jsonify(appointments_schema.dump(appointment_data))

@app.route("/appointment/get/<id>", methods=["GET"])
def get_appointment(id):
    appointment_data = db.session.query(Appointment).filter(Appointment.id == id).first()
    return jsonify(appointment_schema.dump(appointment_data))

@app.route("/appointment/get/data/<username>", methods=["GET"])
def get_appointment_data_by_username(username):
    user_id = db.session.query(User.id).filter(User.username == username).first()[0]
    appointment_data = db.session.query(Appointment).filter(Appointment.user_id == user_id).all()
    return jsonify(appointments_schema.dump(appointment_data))

@app.route("/appointment/delete/<id>", methods=["DELETE"])
def delete_appointment(id):
    appointment_data = db.session.query(Appointment).filter(Appointment.id == id).first()
    db.session.delete(appointment_data)
    db.session.commit()
    return jsonify("Appointment Deleted")


if __name__ == "__main__":
    app.run(debug=True)