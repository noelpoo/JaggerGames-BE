import uuid
import time
import firebase_admin
from flask_restful import Resource, reqparse
from flask_cors import cross_origin
from flask import request
from firebase_admin import credentials
from firebase_admin import firestore

from config import *

if not firebase_admin._apps:
    cred = credentials.Certificate(FIREBASE_KEY_PATH)
    default_app = firebase_admin.initialize_app(cred)

db = firestore.client()


class Answer:
    def __init__(self, answer_id, questions, answer, is_correct, score, answered_in,
                 answered_time, session_id, device_id):
        self.answer_id = answer_id
        self.questions = questions
        self.answer = answer
        self.is_correct = is_correct
        self.score = score
        self.answered_in = answered_in
        self.answered_time = answered_time
        self.session_id = session_id
        self.device_id = device_id

    @classmethod
    def find_by_answer_id(cls, answer_id):
        doc_ref = db.collection(ANSWERS_FB_DB).document(answer_id)
        doc = doc_ref.get()
        answer = doc.to_dict()
        if answer:
            return cls(answer['answer_id'],
                       answer['questions'],
                       answer['answer'],
                       answer['is_correct'],
                       answer['score'],
                       answer['answered_in'],
                       answer['answered_time'],
                       answer['session_id'],
                       answer['device_id'])

        else:
            return None

    @classmethod
    def find_by_session_and_device_id(cls, session_id, device_id):
        doc_ref = db.collection(ANSWERS_FB_DB).where('session_id', '==', session_id) \
            .where('device_id', '==', device_id).stream()
        docs = [doc.to_dict() for doc in doc_ref]
        if docs:
            return [
                cls(answer['answer_id'],
                    answer['questions'],
                    answer['answer'],
                    answer['is_correct'],
                    answer['score'],
                    answer['answered_in'],
                    answer['answered_time'],
                    answer['session_id'],
                    answer['device_id']) for answer in docs
            ]
        else:
            return None

    @classmethod
    def find_by_session_id(cls, session_id):
        doc_ref = db.collection(ANSWERS_FB_DB).where('session_id', '==', session_id).stream()
        docs = [doc.to_dict() for doc in doc_ref]
        if docs:
            return [
                cls(answer['answer_id'],
                    answer['questions'],
                    answer['answer'],
                    answer['is_correct'],
                    answer['score'],
                    answer['answered_in'],
                    answer['answered_time'],
                    answer['session_id'],
                    answer['device_id']) for answer in docs
            ]
        else:
            return None

    @classmethod
    def find_by_device_id(cls, device_id):
        doc_ref = db.collection(ANSWERS_FB_DB).where('device_id', '==', device_id).stream()
        docs = [doc.to_dict() for doc in doc_ref]
        if docs:
            return [
                cls(answer['answer_id'],
                    answer['questions'],
                    answer['answer'],
                    answer['is_correct'],
                    answer['score'],
                    answer['answered_in'],
                    answer['answered_time'],
                    answer['session_id'],
                    answer['device_id']) for answer in docs
            ]
        else:
            return None

    @classmethod
    def find_all_answers(cls):
        doc_ref = db.collection(ANSWERS_FB_DB).stream()
        docs = [doc.to_dict() for doc in doc_ref]
        if docs:
            return [
                cls(answer['answer_id'],
                    answer['questions'],
                    answer['answer'],
                    answer['is_correct'],
                    answer['score'],
                    answer['answered_in'],
                    answer['answered_time'],
                    answer['session_id'],
                    answer['device_id']) for answer in docs
            ]
        else:
            return None

    @staticmethod
    def add_answer_to_db(obj):
        try:
            answer = {
                'answer_id': obj.answer_id,
                'questions': obj.questions,
                'answer': obj.answer,
                'is_correct': obj.is_correct,
                'score': obj.score,
                'answered_in': obj.answered_in,
                'answered_time': obj.answered_time,
                'session_id': obj.session_id,
                'device_id': obj.device_id
            }
            db.collection(ANSWERS_FB_DB).document(obj.answer_id).set(answer)
            return answer
        except ReferenceError:
            return None

    @staticmethod
    def delete_by_answer_id(answer_id):
        db.collection(ANSWERS_FB_DB).document(answer_id).delete()


class AnswerResource(Resource):

    @cross_origin(origin='*', headers=['Content-Type', 'Authorization'])
    def post(self):
        data = request.get_json(force=True)
        answer = Answer(str(uuid.uuid4()), data['questions'], data['answer'], data['is_correct'], data['score'],
                        data['answered_in'], round(time.time()), data['session_id'], data['device_id'])
        result = Answer.add_answer_to_db(answer)
        if result:
            return {
                       'answer': result
                   }, 201
        else:
            return {
                       'message': 'failed to add answer to db'
                   }, 300

    @cross_origin(origin='*', headers=['Content-Type', 'Authorization'])
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('answer_id', type=str, required=True)
        answer_id = parser.parse_args().get('answer_id')
        result = Answer.find_by_answer_id(answer_id)
        if result:
            return {
                       'answer_id': result.answer_id,
                       'questions': result.questions,
                       'answer': result.answer,
                       'is_correct': result.is_correct,
                       'score': result.score,
                       'answered_in': result.answered_in,
                       'answered_time': result.answered_time,
                       'session_id': result.session_id,
                       'device_id': result.device_id
                   }, 200
        else:
            return {
                       'message': 'answer with id {} cannot be found'.format(answer_id)
                   }, 404

    @cross_origin(origin='*', headers=['Content-Type', 'Authorization'])
    def delete(self):
        parser = reqparse.RequestParser()
        parser.add_argument('answer_id', type=str, required=True)
        answer_id = parser.parse_args().get('answer_id')

        if Answer.find_by_answer_id(answer_id):
            Answer.delete_by_answer_id(answer_id)
            return {
                       'message': 'successfully deleted answer with id {}'.format(answer_id)
                   }, 200
        else:
            return {
                       'message': 'answer with id {} cannot be found'.format(answer_id)
                   }, 404


class AllAnswersResource(Resource):

    @cross_origin(origin='*', headers=['Content-Type', 'Authorization'])
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('session_id', type=str, required=False)
        parser.add_argument('device_id', type=str, required=False)
        session_id = parser.parse_args().get('session_id')
        device_id = parser.parse_args().get('device_id')

        if not session_id and not device_id:
            return_list = Answer.find_all_answers()
        elif session_id and not device_id:
            return_list = Answer.find_by_session_id(session_id)
        elif not session_id and device_id:
            return_list = Answer.find_by_device_id(device_id)
        else:
            return_list = Answer.find_by_session_and_device_id(session_id, device_id)

        if return_list:

            return {
                       'count': len(return_list),
                       'questions': [
                           {
                               'answer_id': result.answer_id,
                               'questions': result.questions,
                               'answer': result.answer,
                               'is_correct': result.is_correct,
                               'score': result.score,
                               'answered_in': result.answered_in,
                               'answered_time': result.answered_time,
                               'session_id': result.session_id,
                               'device_id': result.device_id
                           } for result in return_list
                       ]
                   }, 200
        else:
            return {
                'message': 'no answers found'
            }, 404
