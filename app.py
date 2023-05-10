from flask import Flask, render_template, session, request, jsonify
from dotenv import load_dotenv
import os
from flask_migrate import Migrate
from database import *
from flask_restful import Api, Resource
from flask_cors import CORS
from functools import wraps

from controllers.change_password_view import ChangePasswordView
from controllers.login_view import  LoginView
from controllers.predict_emotion_view import EmotionView
from controllers.register_view import RegisterView
from controllers.recordings_view import RecordingsView

from werkzeug.security import check_password_hash, generate_password_hash
from models.EnglishModel import FirstModel
from service.service import Service

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://' + os.getenv("DB_USER") + \
                                        ':' + os.getenv("DB_PASSWORD") + '@' + \
                                        os.getenv("DB_HOST") + '/' + os.getenv("DB_NAME")

db = init_app(app)
api = Api(app)
CORS(app)
Migrate(app, db)
service = Service(db)
first_model = FirstModel()


def token_required(f):
    @wraps(f)
    def decorator(*args, **kwargs):

        token = None

        if 'token' in request.headers:
            token = request.headers['token']

        if not token:
            return jsonify({'Token': 'a valid token is missing'})

        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            if datetime.utcnow() > datetime.strptime(data["expiration"], "%Y-%m-%d %H:%M:%S.%f"):
                print("JWT has expired")
                return jsonify({'Token': 'token has expired'})

            current_user = db.session.query(User).filter(User.email == data['email']).first()
        except:
            return jsonify({'Message': 'token is invalid'})

        return f(*args, **kwargs)

    return decorator


# Wrapper function to apply the decorator to the resource
def token_required_resource(resource):
    if hasattr(resource, 'post'):
        resource.post = token_required(resource.post)
    elif hasattr(resource, 'get'):
        resource.get = token_required(resource.get)
    elif hasattr(resource, 'put'):
        resource.put = token_required(resource.put)
    return resource



api.add_resource(LoginView, '/login', resource_class_kwargs={
    'service': service
})

api.add_resource(ChangePasswordView, '/login/change-password', resource_class_kwargs={
    'service': service
})

api.add_resource(RegisterView, '/register', resource_class_kwargs={
    'service': service
})

api.add_resource(token_required_resource(EmotionView), '/register', resource_class_kwargs={
    'service': service,
    'first-model': first_model
})

api.add_resource(token_required_resource(RecordingsView), '/get-recordings', resource_class_kwargs = {
    'service': service
})



if __name__ == '__main__':
    app.run(debug=True)

