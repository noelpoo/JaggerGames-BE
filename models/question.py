import uuid
import time
import firebase_admin
from flask_restful import Resource, reqparse
from flask_cors import cross_origin
from flask import request
from firebase_admin import credentials
from firebase_admin import firestore

from config import *
from utils import split_multiple_params_into_list, check_list_contains_list

if not firebase_admin._apps:
    cred = credentials.Certificate(FIREBASE_KEY_PATH)
    default_app = firebase_admin.initialize_app(cred)

db = firestore.client()


class Question:
    def __init__(self, c1, c2, c3, c4, correct, create_time,
                 difficult, hint, question, tags, time_limit, type, uuid):
        self.c1 = c1
        self.c2 = c2
        self.c3 = c3
        self.c4 = c4
        self.correct = correct
        self.create_time = create_time
        self.difficult = difficult
        self.hint = hint
        self.question = question
        self.tags = tags
        self.time_limit = time_limit
        self.type = type
        self.uuid = uuid

    @classmethod
    def find_by_uuid(cls, uuid):
        doc_ref = db.collection(QUESTIONS_FB_DB).document(uuid)
        doc = doc_ref.get()
        question = doc.to_dict()
        if question:
            return cls(question['c1'],
                       question['c2'],
                       question['c3'],
                       question['c4'],
                       question['correct'],
                       question['create_time'],
                       question['difficult'],
                       question['hint'],
                       question['question'],
                       question['tags'],
                       question['time_limit'],
                       question['type'],
                       question['uuid'])
        else:
            return None

    @classmethod
    def find_all_questions(cls):
        questions_list = []
        doc_ref = db.collection(QUESTIONS_FB_DB).stream()
        for docs in doc_ref:
            question = docs.to_dict()
            if question:
                question_obj = cls(question['c1'],
                                   question['c2'],
                                   question['c3'],
                                   question['c4'],
                                   question['correct'],
                                   question['create_time'],
                                   question['difficult'],
                                   question['hint'],
                                   question['question'],
                                   question['tags'],
                                   question['time_limit'],
                                   question['type'],
                                   question['uuid'])
                questions_list.append(question_obj)
        if questions_list:
            return questions_list
        else:
            return None

    @staticmethod
    def add_question_to_db(obj):
        try:
            question = {
                'c1': obj.c1 if obj.c1 else None,
                'c2': obj.c2 if obj.c2 else None,
                'c3': obj.c3 if obj.c3 else None,
                'c4': obj.c4 if obj.c4 else None,
                'correct': obj.correct,
                'create_time': obj.create_time,
                'difficult': obj.difficult,
                'hint': obj.hint,
                'question': obj.question,
                'tags': obj.tags,
                'time_limit': obj.time_limit,
                'type': obj.type,
                'uuid': obj.uuid
            }
            db.collection(QUESTIONS_FB_DB).document(obj.uuid).set(question)
            return question
        except AttributeError:
            return None

    @staticmethod
    def delete_question_from_db(_uuid):
        db.collection(QUESTIONS_FB_DB).document(_uuid).delete()


class QuestionResource(Resource):

    @cross_origin(origin='*', headers=['Content-Type', 'Authorization'])
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('uuid', type=str, required=True)
        _uuid = parser.parse_args().get('uuid')
        result = Question.find_by_uuid(_uuid)
        if result:
            return {
                       'c1': result.c1,
                       'c2': result.c2,
                       'c3': result.c3,
                       'c4': result.c4,
                       'correct': result.correct,
                       'create_time': result.create_time,
                       'difficult': result.difficult,
                       'hint': result.hint,
                       'question': result.question,
                       'tags': result.tags,
                       'time_limit': result.time_limit,
                       'type': result.type,
                       'uuid': result.uuid
                   }, 200
        else:
            return {
                       'message': 'question with uuid {} cannot be found'.format(_uuid)
                   }, 403

    # TODO - ADD TAGS VALIDATION
    @cross_origin(origin='*', headers=['Content-Type', 'Authorization'])
    def post(self):
        data = request.get_json(force=True)
        question = Question(
            data['c1'],
            data['c2'],
            data['c3'],
            data['c4'],
            data['correct'],
            int(time.time()),
            data['difficult'],
            data['hint'],
            data['question'],
            data['tags'],
            data['time_limit'],
            data['type'],
            str(uuid.uuid4())
        )

        result = Question.add_question_to_db(question)
        if result:
            return {
                       'question': result
                   }, 201
        else:
            return {
                       'message': 'malformed body'
                   }, 300

    @cross_origin(origin='*', headers=['Content-Type', 'Authorization'])
    def delete(self):
        parser = reqparse.RequestParser()
        parser.add_argument('uuid', type=str, required=True)
        _uuid = parser.parse_args().get('uuid')

        if Question.find_by_uuid(_uuid):
            Question.delete_question_from_db(_uuid)
            return {
                       'message': 'successfully deleted {}'.format(_uuid)
                   }, 200
        else:
            return {
                       'message': 'question with uuid {} not found'.format(_uuid)
                   }, 300


class AllQuestionsResource(Resource):

    @cross_origin(origin='*', headers=['Content-Type', 'Authorization'])
    def get(self):

        parser = reqparse.RequestParser()
        parser.add_argument('type', type=int, required=False)
        parser.add_argument('difficult', type=int, required=False)
        parser.add_argument('tags', type=str, required=False)

        _type = parser.parse_args().get('type')
        _difficult = parser.parse_args().get('difficult')
        _tags = split_multiple_params_into_list(parser.parse_args().get('tags'))
        qn_obj_list = Question.find_all_questions()

        if qn_obj_list:

            if _type or _type == 0:
                list_type = [result for result in qn_obj_list if result.type == _type]
            else:
                list_type = qn_obj_list

            if _difficult or _difficult == 0:
                list_diff = [result for result in list_type if result.difficult == _difficult]
            else:
                list_diff = list_type

            if _tags:
                list_tag = [result for result in list_diff if check_list_contains_list(result.tags, _tags)]
            else:
                list_tag = list_diff

            return {
                       'count': len(list_tag),
                       'questions': [
                           {
                               'c1': result.c1,
                               'c2': result.c2,
                               'c3': result.c3,
                               'c4': result.c4,
                               'correct': result.correct,
                               'create_time': result.create_time,
                               'difficult': result.difficult,
                               'hint': result.hint,
                               'question': result.question,
                               'tags': result.tags,
                               'time_limit': result.time_limit,
                               'type': result.type,
                               'uuid': result.uuid
                           } for result in list_tag
                       ]
                   }, 200
        else:
            return {
                       'message': 'no questions found in database'
                   }, 404
