import sqlite3 as sql

with sql.connect("webapp\\database.db") as connection:

    connection.execute(""" CREATE TABLE video (
                       videoID         INT NOT NULL, 
                       title           TEXT NOT NULL, 
                       date            DATE, 
                       speakerName     TEXT, 
                       PRIMARY KEY (videoID));""")
    
    connection.execute(""" CREATE TABLE account(
                       accountName  TEXT NOT NULL,
                       password     TEXT NOT NULL,
                       email        TEXT,
                       PRIMARY KEY (accountName));""")
    
    connection.execute(""" CREATE TABLE accountVideo(
                       accountName TEXT NOT NULL,
                       videoID     INT NOT NULL,
                       PRIMARY KEY (accountName, videoID));""") 

    connection.execute(""" CREATE TABLE videoPurchase(
                       purchaseID  TEXT NOT NULL,
                       accountName TEXT NOT NULL,
                       videoID     INT NOT NULL,
                       tempTimer   DATETIME,
                       PRIMARY KEY (purchaseID));""") 
    
    connection.execute(""" CREATE TABLE speaker(
                       speakerName TEXT NOT NULL,
                       permissionGiven BIT DEFAULT 0,
                       PRIMARY KEY (speakerName));""") 
    
    connection.execute(""" CREATE TABLE tempWebpage(
                       tempKey     TEXT NOT NULL,
                       tempTimer   DATETIME,
                       accountName TEXT NOT NULL,
                       PRIMARY KEY (tempKey))""")
    
    connection.execute(""" CREATE TABLE tag(
                       tagWord     TEXT NOT NULL,
                       PRIMARY KEY (tagWord));""")
        
    connection.execute(""" CREATE TABLE videoTag(
                       videoID     INT NOT NULL,
                       tagWord     TEXT NOT NULL,
                       PRIMARY KEY (videoID, tagWord))""")

    connection.execute(""" CREATE TABLE servers(
                       serverIP    TEXT NOT NULL,
                       activePort  INT,
                       lat         REAL,
                       long        REAL,
                       PRIMARY KEY (serverIP))""")
    
    # Create table for constants, the type "BLOB" allows
    # for any typed variable to be stored in that column
    connection.execute("""CREATE TABLE constants(
                       name        TEXT NOT NULL UNIQUE,
                       value       BLOB NOT NULL,
                       PRIMARY KEY(name))""")
    
    # Insert default values for the constants into 
    # the database from a text file
    with open("constantDefaultValues.txt") as fp:
        constants = map(lambda x: [x.split(" ")[0], x.split(" ")[1]], fp.readlines())

        connection.executemany("""INSERT INTO constants(name, value)
                                              VALUES(?   , ?)""",
                                              constants)