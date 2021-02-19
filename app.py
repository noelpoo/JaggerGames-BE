import os
import time
import uuid
import math
import firebase_admin
import pandas as pd
from firebase_admin import credentials
from firebase_admin import firestore
from flask import Flask, request
from flask_restful import Resource, Api, reqparse
from flask_cors import CORS, cross_origin
from flask_jwt_extended import JWTManager

from common import *

# FIREBASE DB
cred = credentials.Certificate(FIREBASE_KEY_PATH)
firebase_admin.initialize_app(cred)
db = firestore.client()

app = Flask(__name__)
app.secret_key = APP_SECRET_KEY
api = Api(app)
app.config['CORS_HEADERS'] = 'Content-Type'
cors = CORS(app, resources={r"/*": {"origins": "*"}})
jwt = JWTManager(app)

# IN-MEMORY DATABASE
# TODO - MIGRATE TO NON-SQL DB
question_db = []
answer_db = []


# TODO - CREATE FILTER BY TYPE AND DIFFICULTY
# TODO - CREATE SORTING BY TIME/DIFFICULTY/TYPE
# TODO - CREATE FETCHING BY COUNT
# TODO - "correct" field to accept string or array (for MMCQ)
# TODO - more enum for MMCQ question type


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
            if question:
                return {'question': question}, 200
            else:
                return {'message': 'question_uuid does not exist'}, 404
        else:
            return {'message': "missing query parameters"}, 400

    @cross_origin(origin='*', headers=['Content-Type', 'Authorization'])
    def delete(self):
        global question_db
        parser = reqparse.RequestParser()
        parser.add_argument('uuid', type=str, required=True)
        _uuid = parser.parse_args().get('uuid')
        if _uuid:
            question_db = list(filter(lambda x: x['uuid'] != _uuid, question_db))
            return {'questions': question_db, "count": len(question_db)}, 200
        else:
            return {'message': "missing parameters"}, 400

    @cross_origin(origin='*', headers=['Content-Type', 'Authorization'])
    def post(self):
        request_data = request.get_json(force=True)
        download_url = request_data['url']
        try:
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
                time_limit = question[9] if not math.isnan(question[9]) else create_time_limit(diff=difficulty, qn_type=qn_type, qn=_question)
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
                    'create_time': round(time.time()),
                    'time_limit': round(time_limit)
                }
                uuid_list.append(_uuid)
                question_db.append(obj)
                db.collection('questions').document(_uuid).set(obj)
            response = {
                "UUIDs": uuid_list,
                "count": len(uuid_list)
            }
            return response, 201
        except TypeError:
            return {"message": "failed to parse CSV, please make sure CSV format is correct"}, 400


class Answer(Resource):

    @cross_origin(origin='*', headers=['Content-Type', 'Authorization'])
    def post(self):
        data = request.get_json(force=True)
        answer_id = str(uuid.uuid4())
        obj = {
            'answer_id': answer_id,
            'questions': data['question'],
            'answer': data['answer'],
            'is_correct': data['is_correct'],
            'score': data['score'],
            'answered_in': data['answered_in'],
            'answered_time': round(time.time()),
            'session_id': data['player']['session_id'],
            'device_id': data['player']['device_id']
        }
        answer_db.append(obj)
        print(obj)
        return obj, 201 if obj else 403

    @cross_origin(origin='*', headers=['Content-Type', 'Authorization'])
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('answer_id', type=str, required=True)
        answer_id = parser.parse_args().get('answer_id')
        if answer_id:
            answer = next(filter(lambda x: x['answer_id'] == answer_id, answer_db), None)
            if answer:
                return {'answer': answer}, 200
            else:
                return {'message': 'answer_id not found'}, 404
        else:
            return {'message': 'missing query param'}, 400

    @cross_origin(origin='*', headers=['Content-Type', 'Authorization'])
    def delete(self):
        parser = reqparse.RequestParser()
        parser.add_argument('answer_id', type=str, required=True)
        answer_id = parser.parse_args().get('answer_id')
        has_delete = False
        if answer_id:
            for answer in answer_db:
                if answer['answer_id'] == answer_id:
                    answer_db.remove(answer)
                    has_delete = True
        if has_delete:
            return {'message': 'succesfully deleted {}'.format(answer_id)}, 200
        else:
            return {'message': 'failed to find answer {}'.format(answer_id)}, 404


# END-POINT FOR GETTING FULL LIST
class Answers(Resource):

    @cross_origin(origin='*', headers=['Content-Type', 'Authorization'])
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('device_id', type=str, required=False)
        parser.add_argument('session_id', type=str, required=False)
        device_id = parser.parse_args().get('device_id')
        session_id = parser.parse_args().get('session_id')
        batch = []
        if device_id and session_id:
            for answer in answer_db:
                if answer['device_id'] == device_id and answer['session_id'] == session_id:
                    batch.append(answer)
        elif device_id and not session_id:
            for answer in answer_db:
                if answer['device_id'] == device_id:
                    batch.append(answer)
        elif not device_id and session_id:
            for answer in answer_db:
                if answer['session_id'] == session_id:
                    batch.append(answer)
        elif not device_id and not session_id:
            for answer in answer_db:
                batch.append(answer)

        if batch:
            return {
                       "count": len(batch),
                       "answers": batch
                   }, 200
        else:
            return {
                       'message': 'no answer with matching device_id or session_id'
                   }, 404


# TODO - CREATE QUESTION-FEEDS API

def create_time_limit(diff, qn_type, qn):
    base = MIN_TIME_LIMIT
    diff_pt = DIFF_WEIGHT * diff * base
    type_pt = TYPE_WEIGHT * qn_type * base
    qn_pt = 0
    if len(qn) > 10:
        qn_pt = (len(qn) - 10) * LEN_WEIGHT
    return round(base + diff_pt + type_pt + qn_pt)


# CREATING ENDPOINTS
api.add_resource(Question, '{}/question'.format(API_PATH))
api.add_resource(Questions, '{}/questions'.format(API_PATH))
api.add_resource(Answer, '{}/answer'.format(API_PATH))
api.add_resource(Answers, '{}/answers'.format(API_PATH))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=DEBUG)

