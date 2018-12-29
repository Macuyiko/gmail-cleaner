import sqlite3
import os

class EmailDB(object):
    def __init__(self, database=None, connect=True):
        if database is None:
            database = os.path.dirname(os.path.realpath(__file__)) + '/emails.db'
        self.database = database
        if connect:
            self.connect()
            self.ensure_tables()

    def connect(self):
        self.conn = sqlite3.connect(self.database)
        old_isolation = self.conn.isolation_level
        self.conn.isolation_level = None
        self.conn.cursor().execute('''PRAGMA journal_mode=WAL;''')
        self.conn.row_factory = sqlite3.Row
        self.conn.isolation_level = old_isolation
        
    def query(self, sql, args=(), one=False, noreturn=False):
        if type(args) == list and noreturn:
            cur = self.conn.cursor()
            cur.executemany(sql, args)
        else:
            cur = self.conn.execute(sql, args)
        if noreturn:
            cur.close()
            self.conn.commit()
            return None
        rv = cur.fetchall()
        cur.close()
        return (rv[0] if rv else None) if one else rv

    def ensure_tables(self):
        create_statement = '''CREATE TABLE IF NOT EXISTS "email" (
            "id" TEXT NOT NULL PRIMARY KEY, 
            "trashed" INTEGER NOT NULL, 
            "header_from" TEXT,
            "header_subject" TEXT)'''
        self.query(create_statement, noreturn=True)

    def clear_emails(self):
        self.query('DELETE FROM "email"', noreturn=True)

    def insert_email(self, id):
        self.query('INSERT INTO "email" ("id", "trashed") VALUES (?, 0)', (id,), noreturn=True)

    def insert_emails(self, ids):
        self.query('INSERT INTO "email" ("id", "trashed") VALUES (?, 0)', ids, noreturn=True)

    def update_email(self, id, header_from, header_subject):
        print((header_from, header_subject, id))
        self.query('UPDATE "email" SET "header_from" = ?, "header_subject" = ? WHERE "id" = ?', 
                    (header_from, header_subject, id), noreturn=True)
    
    def trash_email(self, id):
        self.query('UPDATE "email" SET "trashed" = 1 WHERE "id" = ?', (id,), noreturn=True)
    
    def trash_emails(self, ids):
        self.query('UPDATE "email" SET "trashed" = 1 WHERE "id" = ?', ids, noreturn=True)
    
    def select_emails(self):
        return self.query('SELECT * FROM "email" WHERE "trashed" = 0')

    def select_grouped_emails(self):
        return self.query('''SELECT header_from, count(*) AS "amount" FROM "email"
                            WHERE "trashed" = 0 
                            GROUP BY "header_from" 
                            ORDER BY "amount" DESC''')

    def select_byfrom_emails(self, header_from):
        return self.query('''SELECT * FROM "email" WHERE "trashed" = 0 AND "header_from" = ?''', (header_from,))

    def select_updateable_emails(self):
        return self.query('SELECT * FROM "email" WHERE "trashed" = 0 AND "header_from" IS NULL')

    def has_emails(self):
        return self.query('SELECT * FROM "email"', one=True) is not None
