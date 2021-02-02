import os
import time
import uuid
import math
import pandas as pd
from flask import Flask, request
from flask_restful import Resource, Api, reqparse
from flask_cors import CORS, cross_origin
from flask_jwt_extended import JWTManager

from common import API_PATH, APP_SECRET_KEY


app = Flask(__name__)
app.secret_key = APP_SECRET_KEY
api = Api(app)
app.config['CORS_HEADERS'] = 'Content-Type'
cors = CORS(app, resources={r"/*": {"origins": "*"}})
jwt = JWTManager(app)

# IN-MEMORY DATABASE
# TODO - MIGRATE TO NON-SQL DB
question_db = []


# END-POINT FOR GETTING FULL LIST
# TODO - CREATE FILTER BY TYPE AND DIFFICULTY
# TODO - CREATE SORTING BY TIME/DIFFICULTY/TYPE
# TODO - CREATE FETCHING BY COUNT
class Questions(Resource):

    @cross_origin(origin='*', headers=['Content-Type', 'Authorization'])
    def get(self):
        return {
            "questions": question_db,
            "count": len(question_db)
        }, 200


# END-POINT FOR HANDLING IND/BATCH QUESTIONS
class Question(Resource):

    @cross_origin(origin='*', headers=['Content-Type', 'Authorization'])
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('uuid', type=str, required=True)
        target_uuid = parser.parse_args().get('uuid')
        if target_uuid:
            question = next(filter(lambda x: x['uuid'] == target_uuid, question_db), None)
            return {'question': question}, 200 if question is not None else 404
        else:
            return {'message': "missing query parameters"}, 400

    @cross_origin(origin='*', headers=['Content-Type', 'Authorization'])
    def post(self):
        request_data = request.get_json(force=True)
        download_url = request_data['url']

        df = pd.read_csv(download_url)
        uuid_list = []
        questions = df.iterrows()

        for index, question in questions:
            _uuid = str(uuid.uuid4())
            _question = question[0]
            difficulty = question[1]
            qn_type = question[2]
            choice_1 = str(round(question[3])) if not math.isnan(question[3]) else None
            choice_2 = str(round(question[4])) if not math.isnan(question[4]) else None
            choice_3 = str(round(question[5])) if not math.isnan(question[5]) else None
            choice_4 = str(round(question[6])) if not math.isnan(question[6]) else None
            correct = str(question[7])
            hint = question[8] if isinstance(question[8], str) else None
            obj = {
                "uuid": _uuid,
                "question": _question,
                "difficult": difficulty,
                "type": qn_type,
                "c1": choice_1,
                'c2': choice_2,
                'c3': choice_3,
                'c4': choice_4,
                'correct': correct,
                'hint': hint,
                'create_time': round(time.time())
            }
            uuid_list.append(_uuid)
            question_db.append(obj)
        response = {
            "UUIDs": uuid_list,
            "count": len(uuid_list)
        }
        return response, 201

# TODO - CREATE DELETE ENDPOINT USING UUID
# TODO - CREATE QUESTION-FEEDS API


api.add_resource(Question, '{}/question'.format(API_PATH))
api.add_resource(Questions, '{}/questions'.format(API_PATH))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)