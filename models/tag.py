import uuid
import firebase_admin
from flask_restful import Resource, reqparse
from flask_cors import cross_origin
from flask import request
from firebase_admin import credentials
from firebase_admin import firestore

from config import *
from utils import check_if_tag_exists

if not firebase_admin._apps:
    cred = credentials.Certificate(FIREBASE_KEY_PATH)
    default_app = firebase_admin.initialize_app(cred)

db = firestore.client()


class Tag:
    def __init__(self, _uuid, tag, localisation):
        self.uuid = _uuid
        self.tag = tag
        self.localisation = localisation

    @classmethod
    def find_by_tag(cls, tag):
        doc_ref = db.collection(TAGS_FB_DB).where('tag', '==', tag).stream()
        docs = [doc.to_dict() for doc in doc_ref]
        if docs:
            return [
                cls(
                    doc['uuid'],
                    doc['tag'],
                    doc['localisation']
                ) for doc in docs
            ]
        else:
            return None

    @classmethod
    def find_by_uuid(cls, _uuid):
        doc_ref = db.collection(TAGS_FB_DB).where('uuid', '==', _uuid).stream()
        docs = [doc.to_dict() for doc in doc_ref]
        if docs:
            return [
                cls(
                    doc['uuid'],
                    doc['tag'],
                    doc['localisation']
                ) for doc in docs
            ]
        else:
            return None

    @classmethod
    def find_by_localisation(cls, localisation):
        doc_ref = db.collection(TAGS_FB_DB).where('localisation', '==', localisation).stream()
        docs = [doc.to_dict() for doc in doc_ref]
        if docs:
            return [
                cls(
                    doc['uuid'],
                    doc['tag'],
                    doc['localisation']
                ) for doc in docs
            ]
        else:
            return None

    @classmethod
    def find_all_tags(cls):
        doc_ref = db.collection(TAGS_FB_DB).stream()
        docs = [doc.to_dict() for doc in doc_ref]
        if docs:
            return [
                cls(
                    doc['uuid'],
                    doc['tag'],
                    doc['localisation']
                ) for doc in docs
            ]
        else:
            return None

    @classmethod
    def validate_request_tags_exists(cls, request_tags):
        return [i for i in request_tags if i not in [tag.tag for tag in cls.find_all_tags()]]

    @staticmethod
    def add_tag_to_db(obj):
        try:
            tag = {
                'uuid': obj.uuid,
                'tag': obj.tag,
                'localisation': obj.localisation
            }
            db.collection(TAGS_FB_DB).document(obj.uuid).set(tag)
            return tag
        except AttributeError:
            return None

    @staticmethod
    def delete_tag_from_db_using_uuid(_uuid):
        db.collection(TAGS_FB_DB).document(_uuid).delete()


class TagsResource(Resource):

    @cross_origin(origin='*', headers=['Content-Type', 'Authorization'])
    def post(self):
        data = request.get_json(force=True)
        if not check_if_tag_exists(Tag.find_all_tags(), data):
            try:
                tag = Tag(str(uuid.uuid4()), data['tag'], data['localisation'])
                result = Tag.add_tag_to_db(tag)
                if result:
                    return {
                               'tag': result
                           }, 201
                else:
                    return {
                               'message': "something went wrong"
                           }, 400
            except AttributeError:
                return {
                           'message': 'something went wrong'
                       }, 400
        else:
            return {
                       'message': 'tag already exists'
                   }, 400

    @cross_origin(origin='*', headers=['Content-Type', 'Authorization'])
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('uuid', type=str, required=False)
        parser.add_argument('tag', type=str, required=False)
        parser.add_argument('localisation', type=str, required=False)

        _uuid = parser.parse_args().get('uuid')
        tag = parser.parse_args().get('tag')
        localisation = parser.parse_args().get('localisation')

        if _uuid:
            result = Tag.find_by_uuid(_uuid)
            if result:
                result = result[0]
                return {
                           'tag': result.tag,
                           'uuid': result.uuid,
                           'localisation': result.localisation
                       }, 200
            else:
                return {
                           'message': 'tag with uuid {} not found'.format(_uuid)
                       }, 404

        elif tag:
            result = Tag.find_by_tag(tag)
            if result:
                result = result[0]
                return {
                           'tag': result.tag,
                           'uuid': result.uuid,
                           'localisation': result.localisation
                       }, 200
            else:
                return {
                           'message': 'tag with tag {} not found'.format(tag)
                       }, 404

        elif localisation:
            result = Tag.find_by_localisation(localisation)
            if result:
                result = result[0]
                return {
                           'tag': result.tag,
                           'uuid': result.uuid,
                           'localisation': result.localisation
                       }, 200
            else:
                return {
                           'message': 'tag with localisation {} not found'.format(localisation)
                       }, 404

        else:
            results = Tag.find_all_tags()
            if results:
                return {
                           'tags': [
                               {
                                   'tag': result.tag,
                                   'uuid': result.uuid,
                                   'localisation': result.localisation
                               } for result in results
                           ]
                       }, 200
            else:
                return {
                           'message': 'no tags were found'
                       }, 404

    @cross_origin(origin='*', headers=['Content-Type', 'Authorization'])
    def delete(self):
        parser = reqparse.RequestParser()
        parser.add_argument('uuid', type=str, required=False)
        parser.add_argument('tag', type=str, required=False)
        parser.add_argument('localisation', type=str, required=False)

        _uuid = parser.parse_args().get('uuid')
        tag = parser.parse_args().get('tag')
        localisation = parser.parse_args().get('localisation')

        if _uuid:
            if Tag.find_by_uuid(_uuid):
                Tag.delete_tag_from_db_using_uuid(_uuid)
                return {
                           'message': 'successfully deleted tag with uuid {}'.format(_uuid)
                       }, 200
            else:
                return {
                           'message': 'tag with uuid {} does not exist'.format(_uuid)
                       }, 404
        elif tag:
            result = Tag.find_by_tag(tag)
            if result:
                tgt_uuid = result[0].uuid
                Tag.delete_tag_from_db_using_uuid(tgt_uuid)
                return {
                           'message': 'successfully deleted tag'
                       }, 200
            else:
                return {
                           'message': 'tag with tag {} does not exist'.format(tag)
                       }, 404

        elif localisation:
            result = Tag.find_by_localisation(localisation)
            if result:
                tgt_uuid = result[0].uuid
                Tag.delete_tag_from_db_using_uuid(tgt_uuid)
                return {
                           'message': 'successfully deleted tag'
                       }, 200
            else:
                return {
                           'message': 'tag with tag {} does not exist'.format(localisation)
                       }, 404
