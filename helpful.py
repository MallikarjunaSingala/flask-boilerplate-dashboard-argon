from app.home import blueprint
import sqlite3 as sql

def return_db_cursor():
    conn = sql.connect('db.sqlite3')
    db = conn.cursor()
    return db