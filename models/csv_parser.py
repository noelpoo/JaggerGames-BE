import uuid
import pandas as pd
import math
from flask_restful import Resource
from flask_cors import cross_origin
from flask import request

from utils import create_time_limit


class QuestionCSV:
    def __init__(self, c1, c2, c3, c4, correct,
                 difficult, hint, question, tags, time_limit, _type):
        self.c1 = c1
        self.c2 = c2
        self.c3 = c3
        self.c4 = c4
        self.correct = correct
        self.difficult = difficult
        self.hint = hint
        self.question = question
        self.tags = tags
        self.time_limit = time_limit
        self.type = _type


class CsvParserResource(Resource):

    @cross_origin(origin='*', headers=['Content-Type', 'Authorization'])
    def post(self):
        data = request.get_json(force=True)
        csv_url = data['url']
        try:
            df = pd.read_csv(csv_url)
            obj_list = []
            resp_list = []
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
                time_limit = question[9] if not math.isnan(question[9]) else create_time_limit(diff=difficulty,
                                                                                               qn_type=qn_type,
                                                                                               qn=_question)

                obj = QuestionCSV(choice_1, choice_2, choice_3, choice_4,
                                  correct, difficulty, hint, _question, [], time_limit, qn_type)

                obj_list.append(obj)
            for obj in obj_list:
                json_obj = {
                    'c1': obj.c1,
                    'c2': obj.c2,
                    'c3': obj.c3,
                    'c4': obj.c4,
                    'correct': obj.correct,
                    'difficult': obj.difficult,
                    'hint': obj.hint,
                    'question': obj.question,
                    'tags': obj.tags,
                    'time_limit': round(obj.time_limit),
                    'type': obj.type,
                }
                resp_list.append(json_obj)

            return {
                       'questions': resp_list
                   }, 200

        except ReferenceError:
            return {
                       'message': 'failed to parse csv'
                   }, 417
