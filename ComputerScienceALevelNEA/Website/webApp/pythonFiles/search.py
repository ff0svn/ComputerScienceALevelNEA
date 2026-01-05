import flask
import sqlite3 as sql

from .webPage import webPage
from .queue import queue
from .sort import sort

class search(webPage):
    def __init__(self, database, secret_key) -> None:
        super().__init__(database, secret_key)

        self.route = "/search"
        self.methods = ["GET", "POST"]
        self.__name__ = "search"

    def webPageMethod(self):
        
        query = None
        sortType = None
        tag = ""

        # Error handling to avoid crashes
        if "query" in flask.request.args:
            #https://flask.palletsprojects.com/en/stable/quickstart/#the-request-object
            query = flask.request.args["query"]
        else:
            query = ""

        if "tag" in flask.request.args:
            tag = flask.request.args["tag"]

        if "sort" in flask.request.args:
            sortType = flask.request.args["sort"]
        else:
            sortType = "name"
            
        if flask.request.method == "GET":
            results = self.generateSearchResults(query, tag, sortType)
            
            return flask.render_template("search.html", results = results)
            
        elif flask.request.method == "POST":
            
            return flask.redirect("search?query=" + flask.request.form["input"] + (("&sort=" + flask.request.form["sortStyle"]) if ("sortStyle" in flask.request.form) else "") + (("&tag=" + flask.request.form["tag"]) if (flask.request.form["tag"] != "") else ""))
            
        
    def generateSearchResults(self, name: str, tag: str, sortStyle: str):

        with sql.connect(self.database, uri = True) as connection:

            # When query is empty, replace with an SQL arbitrary length wildcard
            if name == "": name = "%"
            
            if sortStyle == "tag":

                if tag not in list(map(lambda x: x[0], connection.execute("SELECT tagWord FROM tag").fetchall())):
                    return []

                results = connection.execute("""SELECT title, date, videoID, speakerName
                                                FROM video""").fetchall()

                depth: int = int(connection.execute("""SELECT value 
                                                FROM constants
                                                WHERE name = 'searchDepth'""").fetchone()[0])

                similarityDictionary = search.findSimilarityDictionary(connection, tag, depth)
                
                newResults = []
                for currResult in results:
                    currTags = []
                    currTotal = 0

                    currTags = connection.execute("""SELECT videoTag.tagWord
                                                     FROM video
                                                     INNER JOIN videoTag
                                                     ON video.videoID = videoTag.videoID
                                                     WHERE video.videoID = ?""", (currResult[2] ,)).fetchall()

                    for tag in currTags:
                        currTotal += similarityDictionary[tag[0]]
                        
                    newResults.append((*currResult, currTotal / len(currTags)))
                
                results = newResults
                # Sort the results by their similarity scores
                results = sort.sort(results, key = lambda x : x[-1])

                for l in results:
                    print(l)
                                
            # Instead of multiple if statements, I could've modified one SQL command
            # depending on the value of sortStyle, but that would increase the risk of 
            # SQL-injection and as such I have elected to use the less "elegant" option
            elif sortStyle == "name":
                results = connection.execute("""SELECT title, date, videoID, speakerName
                                                FROM video
                                                WHERE title LIKE ?
                                                ORDER BY title""", (name, )).fetchall()
            
            elif sortStyle == "speaker":
                results = connection.execute("""SELECT title, date, videoID, speakerName
                                                FROM video
                                                WHERE title LIKE ?
                                                ORDER BY speakerName""", (name, )).fetchall()
            
            elif sortStyle == "date":
                results = connection.execute("""SELECT title, date, videoID, speakerName
                                                FROM video
                                                WHERE title LIKE ?
                                                ORDER BY date""", (name, )).fetchall()

        return results


    @staticmethod
    def findSimilarityDictionary(connection: sql.Connection, initialTag: str, depth: int):
        listOfPaths = search.findPaths(connection, initialTag, depth)
    
        # Merge paths with the same endpoint to get 
        # a dictionary giving the tags closeness values 
        similarityDictionary = {}

        for path in listOfPaths:
            
            similarityDictionary[path[1][-1]] = similarityDictionary.get(path[1][-1], 1) + path[0]
        
        return similarityDictionary


    @staticmethod
    def findPaths(connection: sql.Connection, initialTag: str, depth: int):

        listOfPaths: list = []

        pathQueue = queue()
        pathQueue.enqueue([1, [initialTag]])

        while (not pathQueue.isEmpty()) and depth > 0:
            

            currPath = pathQueue.dequeue()

            # Find all adjacent nodes (and weights) with SQL and 
            # add the path going through it to the pathQueue

            SQLreturn = connection.execute("""  SELECT COUNT(*) AS [count], node
                                                FROM (SELECT videoTag.tagWord AS node
                                                        FROM video
                                                        INNER JOIN videoTag
                                                        ON video.videoID = videoTag.videoID
                                                        WHERE video.videoID IN 
                                                            (SELECT videoTag.videoID FROM videoTag WHERE videoTag.tagWord = ?))
                                                GROUP BY node """, currPath[1][-1]).fetchall()

            totalConnections = list(filter(lambda x : x[1] == currPath[1][-1], SQLreturn))[0][0]

            for count, tag in SQLreturn:

                # Avoid revisiting nodes, to save on compute 
                # and lower preference for highly cyclic areas

                if tag not in currPath[1]:
                    # Add the path along this node to the queue, along with its weight
                    pathQueue.enqueue([currPath[0]*count / totalConnections, currPath[1] + [tag]])

            listOfPaths.append(currPath)
            depth = depth - 1
        
        return listOfPaths
