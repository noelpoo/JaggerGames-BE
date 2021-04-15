import os
import time
import uuid
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from flask import Flask, request
from flask_restful import Resource, Api, reqparse
from flask_cors import CORS, cross_origin
from flask_jwt_extended import JWTManager

from config import *
from models.tag import TagsResource
from models.question import QuestionResource, AllQuestionsResource
from models.csv_parser import CsvParserResource

# FIREBASE DB
if not firebase_admin._apps:
    cred = credentials.Certificate(FIREBASE_KEY_PATH)
    default_app = firebase_admin.initialize_app(cred)

db = firestore.client()

app = Flask(__name__)
app.secret_key = APP_SECRET_KEY
api = Api(app)
app.config['CORS_HEADERS'] = 'Content-Type'
cors = CORS(app, resources={r"/*": {"origins": "*"}})
jwt = JWTManager(app)


# TODO - CREATE FETCHING BY COUNT
# TODO - "correct" field to accept string or array (for MMCQ)
# TODO - more enum for MMCQ question type
# TODO - create job to refresh tag_list in-memory


class Questions(Resource):
    # TODO - TOP DOWN FILTERING, DIFFICULTY > TYPE > TAGS
    @cross_origin(origin='*', headers=['Content-Type', 'Authorization'])
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('difficult', type=str, required=False)
        parser.add_argument('type', type=str, required=False)
        parser.add_argument('tags', type=list, required=False)

        difficult = parser.parse_args().get('difficult')
        difficult = int(difficult) if difficult or difficult == 0 else None
        _type = parser.parse_args().get('type')
        _type = int(_type) if _type or _type == 0 else None
        tags = parser.parse_args().get('tags')
        tags = tags if tags or tags != [] else None

        # filtered_list = []
        docs = db.collection(QUESTIONS_FB_DB).stream()
        unfiltered_list = [doc.to_dict() for doc in docs]
        print("unfiltered list: {}".format(unfiltered_list))

        if difficult:
            new_list = [doc for doc in unfiltered_list if doc['difficult'] == difficult]
        else:
            new_list = unfiltered_list

        if _type:
            new_list = [doc for doc in new_list if doc['type'] == _type]
        else:
            new_list = new_list

        if tags:
            new_list = [doc for doc in new_list if (doc['tags'] == tags)]
        else:
            new_list = new_list

        return {
            'count': len(new_list),
            'questions': new_list
        }


# END-POINT FOR HANDLING IND/BATCH QUESTIONS
class Question(Resource):

    @cross_origin(origin='*', headers=['Content-Type', 'Authorization'])
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('uuid', type=str, required=True)
        target_uuid = parser.parse_args().get('uuid')
        if target_uuid:
            doc_ref = db.collection(QUESTIONS_FB_DB).document(target_uuid)
            doc = doc_ref.get()
            if doc.exists:
                question = doc.to_dict()
                return {'question': question}, 200
            else:
                return {'message': 'question_uuid does not exist'}, 404
        else:
            return {'message': "missing query parameters"}, 400

    @cross_origin(origin='*', headers=['Content-Type', 'Authorization'])
    def delete(self):
        parser = reqparse.RequestParser()
        parser.add_argument('uuid', type=str, required=True)
        _uuid = parser.parse_args().get('uuid')
        if _uuid:
            doc_ref = db.collection(QUESTIONS_FB_DB).document(_uuid)
            doc = doc_ref.get()
            if doc.exists:
                print('doc exists')
                db.collection(QUESTIONS_FB_DB).document(_uuid).delete()
                return {'message': "successfully deleted question {}".format(_uuid)}, 200
            else:
                return {'message': 'unable to find question {}'.format(_uuid)}, 404
        else:
            return {'message': "missing parameters"}, 400


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
        db.collection(ANSWERS_FB_DB).document(answer_id).set(obj)
        return obj, 201 if obj else 403

    @cross_origin(origin='*', headers=['Content-Type', 'Authorization'])
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('answer_id', type=str, required=True)
        answer_id = parser.parse_args().get('answer_id')
        if answer_id:
            doc_ref = db.collection(ANSWERS_FB_DB).document(answer_id)
            doc = doc_ref.get()
            if doc.exists:
                answer = doc.to_dict()
                return {
                    'answer': answer
                }, 200
            else:
                return {
                    "message": "item does not exists",
                    "code": 404
                }, 404
        else:
            return {
                "message": "malformed request parameter",
                "code": 400
            }, 400

    @cross_origin(origin='*', headers=['Content-Type', 'Authorization'])
    def delete(self):
        parser = reqparse.RequestParser()
        parser.add_argument('answer_id', type=str, required=True)
        answer_id = parser.parse_args().get('answer_id')
        has_delete = False
        if answer_id:
            doc_ref = db.collection(ANSWERS_FB_DB).document(answer_id)
            doc = doc_ref.get()
            if doc.exists:
                db.collection(ANSWERS_FB_DB).document(answer_id).delete()
                has_delete = True
            if has_delete:
                return {'message': 'succesfully deleted {}'.format(answer_id)}, 200
            else:
                return {'message': 'failed to find answer {}'.format(answer_id)}, 404
        else:
            return {
                'message': 'malformed query param',
                'code': 400
            }, 400


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
            docs = db.collection(ANSWERS_FB_DB).where('session_id', '==', session_id).where('device_id', '==', device_id).stream()
            for doc in docs:
                doc_resp = doc.to_dict()
                batch.append(doc_resp)
        elif device_id and not session_id:
            docs = db.collection(ANSWERS_FB_DB).where('device_id', '==', device_id).stream()
            for doc in docs:
                doc_resp = doc.to_dict()
                batch.append(doc_resp)
        elif not device_id and session_id:
            docs = db.collection(ANSWERS_FB_DB).where('session_id', '==', session_id).stream()
            for doc in docs:
                doc_resp = doc.to_dict()
                batch.append(doc_resp)
        elif not device_id and not session_id:
            docs = db.collection(ANSWERS_FB_DB).stream()
            for doc in docs:
                doc_resp = doc.to_dict()
                batch.append(doc_resp)

        if batch:
            return {
                       "count": len(batch),
                       "answers": batch
                   }, 200
        else:
            return {
                       'message': 'no answer with matching device_id or session_id',
                       'code': 404
                   }, 404


# TODO - CREATE QUESTION-FEEDS API

# CREATING ENDPOINTS
# api.add_resource(Question, '{}/question'.format(API_PATH))
api.add_resource(QuestionResource, '{}/question'.format(API_PATH))
api.add_resource(AllQuestionsResource, '{}/questions'.format(API_PATH))
api.add_resource(CsvParserResource, '{}/csv_parser'.format(API_PATH))
api.add_resource(Answer, '{}/answer'.format(API_PATH))
api.add_resource(Answers, '{}/answers'.format(API_PATH))
api.add_resource(TagsResource, '{}/tags'.format(API_PATH))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=DEBUG)

