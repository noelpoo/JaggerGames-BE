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

from utils import *
from config import *

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


# TODO - CREATE FETCHING BY COUNT
# TODO - "correct" field to accept string or array (for MMCQ)
# TODO - more enum for MMCQ question type
# TODO - create job to refresh tag_list in-memory

class Tags(Resource):
    @cross_origin(origin='*', headers=['Content-Type', 'Authorization'])
    def post(self):
        tag_id = str(uuid.uuid4())
        data = request.get_json(force=True)

        docs = db.collection(TAGS_FB_DB).stream()
        _tags = [doc.to_dict() for doc in docs]

        if not check_if_tag_exists(_tags, data):
            obj = {
                "uuid": tag_id,
                "tag": data['tag'],
                "localisation": data['localisation']
            }
            db.collection(TAGS_FB_DB).document(tag_id).set(obj)
            return obj, 201 if obj else 403
        else:
            return {
                "message": "duplicate tag or tag-localisation"
            }, 403

    @cross_origin(origin='*', headers=['Content-Type', 'Authorization'])
    def delete(self):
        data = request.get_json(force=True)
        to_delete = data['uuids']
        for uuid in to_delete:
            db.collection(TAGS_FB_DB).document(uuid).delete()
        return {
            "deleted": to_delete
        }, 200
        # db.collection(QUESTIONS_FB_DB).document(_uuid).delete()

    @cross_origin(origin='*', headers=['Content-Type', 'Authorization'])
    def get(self):
        docs = db.collection(TAGS_FB_DB).stream()
        _tags = [doc.to_dict() for doc in docs]
        return {
            'tags': _tags
        }, 200


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
    # check =  any(item in List1 for item in List2)



    #
    # @cross_origin(origin='*', headers=['Content-Type', 'Authorization'])
    # def get(self):
    #     parser = reqparse.RequestParser()
    #     parser.add_argument('difficult', type=str, required=False)
    #     parser.add_argument('type', type=str, required=False)
    #     difficult = parser.parse_args().get('difficult')
    #     difficult = int(difficult) if difficult or difficult == 0 else None
    #     _type = parser.parse_args().get('type')
    #     _type = int(_type) if _type or _type == 0 else None
    #
    #     if difficult is not None and _type is not None:
    #         docs = db.collection(QUESTIONS_FB_DB).where('difficult', '==', difficult).where('type', '==', _type).stream()
    #         qn_list = [doc.to_dict() for doc in docs]
    #         if qn_list:
    #             return {
    #                 'questions': qn_list,
    #                 'count': len(qn_list)
    #             }, 200
    #         else:
    #             return {
    #                 'message': 'no questions of difficulty {} and type {} found'.format(difficult, _type),
    #                 'code': 404
    #             }, 404
    #
    #     elif difficult is not None and _type is None:
    #         docs = db.collection(QUESTIONS_FB_DB).where('difficult', '==', difficult).stream()
    #         qn_list = [doc.to_dict() for doc in docs]
    #         if qn_list:
    #             return {
    #                        'questions': qn_list,
    #                        'count': len(qn_list)
    #                    }, 200
    #         else:
    #             return {
    #                        'message': 'no questions of difficulty {} found'.format(difficult),
    #                        'code': 404
    #                    }, 404
    #
    #     elif difficult is None and _type is not None:
    #         docs = db.collection(QUESTIONS_FB_DB).where('type', '==', _type).stream()
    #         qn_list = [doc.to_dict() for doc in docs]
    #         if qn_list:
    #             return {
    #                        'questions': qn_list,
    #                        'count': len(qn_list)
    #                    }, 200
    #         else:
    #             return {
    #                        'message': 'no questions of type {} found'.format(_type),
    #                        'code': 404
    #                    }, 404
    #
    #     elif _type is None and difficult is None:
    #         docs = db.collection(QUESTIONS_FB_DB).stream()
    #         resp_list = [doc.to_dict() for doc in docs]
    #         if resp_list:
    #             return {
    #                 "questions": resp_list,
    #                 "count": len(resp_list)
    #             }, 200
    #         else:
    #             return {
    #                 'message': 'no entries found',
    #                 'code': 404
    #             }, 404


# TODO - add TAGS validation for tags field in post request, validate that tags exist in db
class QuestionNonCSV(Resource):
    @cross_origin(origin='*', headers=['Content-Type', 'Authorization'])
    def post(self):
        _uuid = str(uuid.uuid4())

        data = request.get_json(force=True)
        choice_one = data['c1'] if data['c1'] else None
        choice_two = data['c2'] if data['c2'] else None
        choice_three = data['c3'] if data['c3'] else None
        choice_four = data['c4'] if data['c4'] else None
        obj = {
            "c1": choice_one,
            "c2": choice_two,
            "c3": choice_three,
            "c4": choice_four,
            "correct": data['correct'],
            'create_time': round(time.time()),
            "difficult": data['difficult'],
            "hint": data['hint'],
            "question": data['question'],
            "time_limit": data['time_limit'],
            "type": data['type'],
            "uuid": _uuid,
            "tags": data['tags']
        }
        db.collection(QUESTIONS_FB_DB).document(_uuid).set(obj)

        return {
            'message': "sucessfully uploaded",
            'code': 200,
            'uuid': _uuid,
            'uploaded': obj
        }, 201


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
                    'time_limit': round(time_limit),
                    'tags': []
                }
                uuid_list.append(_uuid)
                db.collection(QUESTIONS_FB_DB).document(_uuid).set(obj)
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
api.add_resource(Question, '{}/question'.format(API_PATH))
api.add_resource(Questions, '{}/questions'.format(API_PATH))
api.add_resource(Answer, '{}/answer'.format(API_PATH))
api.add_resource(Answers, '{}/answers'.format(API_PATH))
api.add_resource(Tags, '{}/tags'.format(API_PATH))
api.add_resource(QuestionNonCSV, '{}/question_non_csv'.format(API_PATH))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=DEBUG)

