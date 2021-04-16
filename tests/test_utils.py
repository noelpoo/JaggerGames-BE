import pytest

from utils import check_list_contains_list, check_if_tag_exists
from models.question import Question

test_question = Question(
    'c1',
    'c2',
    'c3',
    'c4',
    'correct',
    12312309,
    0,
    'hint',
    'question',
    ['tag_one', 'tag_two', 'tag_three'],
    10,
    0,
    'uuid'
)

query_tags = ['tag_one']


def test_check_list_contains_list():
    result = check_list_contains_list(test_question.tags, query_tags)
    print(result)


if __name__ == '__main__':
    test_check_list_contains_list()

