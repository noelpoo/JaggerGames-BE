from common import *


def check_if_tag_exists(list_of_tag_obj, new_tag):
    exists = False

    list_of_tags = [{
        'tag': obj.tag,
        'uuid': obj.uuid,
        'localisation': obj.localisation
    } for obj in list_of_tag_obj]

    for tag in list_of_tags:
        if tag['tag'] == new_tag['tag'] or tag['localisation'] == new_tag['localisation']:
            exists = True
            break

    return exists


def create_time_limit(diff, qn_type, qn):
    base = MIN_TIME_LIMIT
    diff_pt = DIFF_WEIGHT * diff * base
    type_pt = TYPE_WEIGHT * qn_type * base
    qn_pt = 0
    if len(qn) > 10:
        qn_pt = (len(qn) - 10) * LEN_WEIGHT
    return round(base + diff_pt + type_pt + qn_pt)