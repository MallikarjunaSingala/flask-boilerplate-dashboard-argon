import sqlite3
from flask import Flask, _app_ctx_stack
def connect_db():
    return sqlite3.connect(app.config['DATABASE'])

def init_db():
    '''
        Initialize the DB when the app is first run
    '''
    with closing(connect_db()) as db:
        with app.open_resource('schema.sql', mode='r') as schema:
            db.cursor().executescript(schema.read())
        db.commit()
