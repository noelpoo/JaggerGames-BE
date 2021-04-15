import sqlite3
import os
from common import DATA_BASE

if os.path.exists(DATA_BASE):
    os.remove(DATA_BASE)
    print('re-initialised DB file')

connection = sqlite3.connect(DATA_BASE)
cursor = connection.cursor()


create_table_tags = "CREATE TABLE IF NOT EXISTS tags (uuid text, tag text, localisation text)"
cursor.execute(create_table_tags)


# INJECT TEST VALUES
tags = [
    ("1234-abcd-efg", "pri_one_math", "Primary one Mathematics"),
    ("1234-abcd-asd", "pri_one_sci", "Primary one Science")
]

insert_query = "INSERT INTO tags VALUES (?, ?, ?)"
cursor.executemany(insert_query, tags)


query = "SELECT * FROM tags"
for row in cursor.execute(query):
    print(row)

connection.commit()
connection.close()




