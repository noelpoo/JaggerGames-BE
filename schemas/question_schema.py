GET_ALL_QUESTIONS_SCHEMA = \
    {
        "count": {"type": "number"},
        "type": "array",
        "questions": [
            {
                "type": "object",
                "properties": {
                    "c1": {"type": "string"},
                    "c2": {"type": "string"},
                    "c3": {"type": "string"},
                    "c4": {"type": "string"},
                    "correct": {"type": "string"},
                    "create_time": {"type": "number"},
                    "difficult": {"type": "number"},
                    "hint": {"type": "string"},
                    "question": {"type": "string"},
                    "tags": {
                        "type": "array",
                        "tags":
                            [
                                {"type": "string"}
                            ]
                    },
                    "time_limit": {"type": "number"},
                    "type": {"type": "number"},
                    "uuid": {"type": "string"}
                }
            }
        ]
    }
