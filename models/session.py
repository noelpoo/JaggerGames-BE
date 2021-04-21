import firebase_admin
from flask_restful import Resource, reqparse
from flask_cors import cross_origin
from firebase_admin import credentials
from firebase_admin import firestore

from config import *
from models.answer import Answer

if not firebase_admin._apps:
    cred = credentials.Certificate(FIREBASE_KEY_PATH)
    default_app = firebase_admin.initialize_app(cred)

db = firestore.client()


class SessionResource(Resource):

    # GET ALL PAST SESSION IDS BASED ON DEVICE_ID
    @cross_origin(origin='*', headers=['Content-Type', 'Authorization'])
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('device_id', required=True, type=str)
        device_id = parser.parse_args().get('device_id')

        results = Answer.find_by_device_id(device_id)
        if results:
            session_id_list = list(set([result.session_id for result in results]))

            return_list = [
                {
                    'session_id': session,
                    'answer_ids': [
                        i.answer_id for i in Answer.find_by_session_and_device_id(session, device_id)
                    ]
                } for session in session_id_list
            ]

            if return_list:
                return {
                    'results': return_list
                }, 200
            else:
                return {
                    'message': 'no sessions found for device_id {}'.format(device_id)
                }
        else:
            return {
                'message': 'no sessions found for device_id {}'.format(device_id)
            }
