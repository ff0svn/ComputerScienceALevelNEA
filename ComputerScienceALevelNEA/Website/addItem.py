import sqlite3 as sql
import requests

def IPtoLatLon(IP: str):
    response = requests.get("http://ip-api.com/json/{}?fields=status,lat,lon,query".format(IP))

    if response.ok:
        jsonLoc = response.json()

        print(jsonLoc)
        location = (jsonLoc["lat"], jsonLoc["lon"])
        return location

with sql.connect("webApp\\database.db") as connection:
    while False:
        
        #connection.execute("""INSERT INTO video 
        #                          (videoID, title, date, speakerName)
        #                    VALUES(?,       ?,     ?,    ?      )
        #                    """,  (input(""), input(""), input(""), input("")))

        # connection.execute("""INSERT INTO accountVideo
        #                            (accountName, videoID)
        #                      VALUES(?,           ?);
        #                   """,     (input(""),   input("")))
        
        #connection.execute("""INSERT INTO tag
        #                            (tagWord)
        #                      VALUES(?)""", input(""))

        #  connection.execute("""INSERT INTO videoTag
        #                               (videoID, tagWord)
        #                         VALUES(?, ?)""", (input(""), input("")))

        #connection.execute("""INSERT INTO speaker
        #                                (speakerName, permissionGiven)
        #                            VALUES(?, ?)""", (input(""), input("")))

        # ip = input("")
        # loc = IPtoLatLon(ip)

        # connection.execute("""INSERT INTO servers
        #                         (serverIP, activePort, lat, long)
        #                     VALUES(?, ?, ?, ?)""", (ip, input(""), loc[0], loc[1]))
        pass