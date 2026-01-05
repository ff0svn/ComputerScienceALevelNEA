import sqlite3 as sql
import threading

class databaseCleaner:
    @staticmethod
    def setup(database):
        with sql.connect(database) as connection:
            resetTime = int(connection.execute("""SELECT value 
                                                  FROM constants
                                                  WHERE name = 'emailResetTime'""").fetchone()[0])

        # Clean database every 2 reset times
        threading.Timer(2 * resetTime, databaseCleaner.cleanDB, [database])

    @staticmethod
    def cleanDB(database):
        with sql.connect(database) as connection:
            connection.execute("""DELETE FROM tempWebpage
                                  WHERE tempTimer - unixepoch() < (SELECT value 
                                                                   FROM constants
                                                                   WHERE name = 'emailResetTime')""")

            connection.execute("""DELETE FROM videoPurchase
                                  WHERE tempTimer - unixepoch() < (SELECT value 
                                                                   FROM constants
                                                                   WHERE name = 'emailResetTime')""")
