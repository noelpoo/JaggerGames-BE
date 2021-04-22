import os
from flask import Flask
from flask_restful import Api
from flask_cors import CORS
from flask_jwt_extended import JWTManager

from config import *

# IMPORTING API RESOURCES FROM MODELS
from models.tag import TagsResource
from models.question import QuestionResource, AllQuestionsResource
from models.csv_parser import CsvParserResource
from models.answer import AnswerResource, AllAnswersResource
from models.session import SessionResource


app = Flask(__name__)
app.secret_key = APP_SECRET_KEY
api = Api(app)
app.config['CORS_HEADERS'] = 'Content-Type'
cors = CORS(app, resources={r"/*": {"origins": "*"}})
jwt = JWTManager(app)


# TODO - CREATE FETCHING BY COUNT
# TODO - "correct" field to accept string or array (for MMCQ)
# TODO - more enum for MMCQ question type


# ENDPOINTS FOR QUESTIONS
api.add_resource(QuestionResource, '{}/question'.format(API_PATH))
api.add_resource(AllQuestionsResource, '{}/questions'.format(API_PATH))
# ENDPOINT FOR CSV PARSER API
api.add_resource(CsvParserResource, '{}/csv_parser'.format(API_PATH))
# ENDPOINT FOR ANSWERS
api.add_resource(AnswerResource, '{}/answer'.format(API_PATH))
api.add_resource(AllAnswersResource, '{}/answers'.format(API_PATH))
# ENDPOINT FOR TAGS
api.add_resource(TagsResource, '{}/tags'.format(API_PATH))
# ENDPOINT FOR SESSIONS API
api.add_resource(SessionResource, '{}/session'.format(API_PATH))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=DEBUG)
