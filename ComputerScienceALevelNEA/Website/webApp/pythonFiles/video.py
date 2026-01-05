import flask
import sqlite3 as sql
import requests
import stripe

from .webPage import webPage
from .sort import sort

# https://testdriven.io/blog/flask-stripe-tutorial/

class video(webPage):
    def __init__(self, database, secret_key) -> None:
        super().__init__(database, secret_key)

        self.route = "/video"
        self.methods = ["GET"]
        self.__name__ = "video"

    def webPageMethod(self):
        videoID = flask.request.args["videoID"]

        if flask.request.method == "GET":
            with sql.connect(self.database, uri= True) as connection:
                canAccess = False
                if "username" in flask.session:
                    canAccess = True
                    results = connection.execute("""SELECT video.videoID, video.title, speaker.permissionGiven
                                                FROM video INNER JOIN accountVideo
                                                ON video.videoID = accountVideo.videoID
                                                INNER JOIN speaker
                                                ON video.speakerName = speaker.speakerName
                                                WHERE video.videoID = ?
                                                AND accountVideo.accountName = ?""",
                                                (videoID, flask.session["username"]))

                    video = results.fetchone()

                elif not("username" in flask.session):
                    # If they are not signed in, redirect to homepage and inform them

                    flask.flash("Need to be signed in to access videos", "error")
                    return flask.redirect(flask.url_for("index"))

                if video is None:
                    canAccess = False
                    results = connection.execute("""SELECT video.videoID, video.title, speaker.permissionGiven
                                                FROM video INNER JOIN speaker
                                                ON video.speakerName = speaker.speakerName
                                                WHERE video.videoID = ?""",
                                                (videoID))

                    video = results.fetchone()
      

                if results.arraysize != 1:
                    flask.abort(500)

                # Check if the speaker gave permission for their video to be distributed, otherwise return No Content HTTP code
                if video[2] == 0:
                    flask.abort(204) # Find source for this
                elif video[2] == 1:
                    if canAccess == True:
                        closestServerIP = self.findClosestStreamingServer(flask.request.remote_addr)

                        return flask.render_template("videoOwned.html", video = video, serverIP = closestServerIP)
                    else:
                        return flask.render_template("videoUnowned.html", video = video)
                    
    
    def findClosestStreamingServer(self, clientIP):
        response = requests.get("http://ip-api.com/json/{}?fields=status,lat,lon,query".format(clientIP))

        with sql.connect(self.database, uri = True) as connection:
            # Each server's latitude and longnitude is pre-claculated when added to the database
            # Significatly speeds up computation time
            results = connection.execute("""SELECT serverIP, lat, long FROM servers""")

            servers =  results.fetchall()

        if response.ok:
            jsonLoc = response.json()

            # If there is an error in finding location
            # Fallback assuming lat/lon at (0,0)
            if(jsonLoc["status"] == "fail"):
                jsonLoc["lat"] = 0
                jsonLoc["lon"] = 0

            location = (jsonLoc["lat"], jsonLoc["lon"])

            # Sort servers based on distance from client and return first element
            sortedServers = sort.sort(servers, lambda x: video.euclideanDist((x[1], x[2]), location))
            return sortedServers[0]

    @staticmethod
    def euclideanDist(loc1, loc2):
        # Assumes that the earth is a flat plane
        # As used in an approximation doesn't matter too much

        dx = loc1[0] - loc2[0]
        dy = loc1[1] - loc2[1]

        # Classic bit of pythag
        return (dx ** 2 + dy ** 2)**0.5


class stripeConfig(webPage):
    def __init__(self, database, secret_key, stripeKeys) -> None:
        super().__init__(database, secret_key)

        self.route = "/config"
        self.methods = ["GET"]
        self.__name__ = "config"

        self.stripeKeys = stripeKeys
    
    def webPageMethod(self):
        stripeConfig = {"publicKey": self.stripeKeys["publishableKey"]}
        return flask.jsonify(stripeConfig)

class checkoutSession(webPage):
    def __init__(self, database, secret_key, stripeKeys) -> None:
        super().__init__(database, secret_key)

        self.route = "/checkoutSession"
        self.methods = ["GET"]
        self.__name__ = "checkoutSession"

        self.stripeKeys = stripeKeys
    
    def webPageMethod(self):

        with sql.connect(self.database, uri = True) as connection:
            results = connection.execute("""SELECT value 
                                            FROM constants
                                            WHERE name = 'siteURL'""")
            
            siteURL = results.fetchone()[0].strip()

            print(siteURL)

        stripe.api_key = self.stripeKeys["secretKey"]

        videoID = flask.request.args["videoID"]

        try: 
            # Generate checkout session for the order

            checkoutSession = stripe.checkout.Session.create(
                success_url = siteURL + "/purchaseSuccess?sessionID={CHECKOUT_SESSION_ID}",
                cancel_url = siteURL + "/purchaseFailure?videoID=" + videoID,
                payment_method_types = ["card"],
                mode = "payment",
                line_items = [
                    {
                        "price_data": {
                            "currency": "gbp",
                            "product_data": {
                                "name": "Video Purchase",
                            },
                            "unit_amount": 30
                        },
                        "quantity": 1,
                    }
                ]
            )

            # Create new purchase record to keep track of the purchases
            with sql.connect(self.database, uri = True) as connection:
                connection.execute("""INSERT INTO videoPurchase(purchaseID, accountName, videoID, tempTimer)
                                                         VALUES(?         , ?          , ?      , unixepoch())""",
                                                               (checkoutSession["id"], flask.session["username"], videoID))

            return flask.jsonify({"sessionId": checkoutSession["id"]})
        
        except Exception as e:
            print(e)
            return flask.jsonify(error = str(e)), 403

class purchaseSuccess(webPage):
    def __init__(self, database, secret_key) -> None:
        super().__init__(database, secret_key)

        self.route = "/purchaseSuccess"
        self.methods = ["GET"]
        self.__name__ = "purchaseSuccess"
    
    def webPageMethod(self):
        sessionID = flask.request.args["sessionID"]

        with sql.connect(self.database, uri = True) as connection:
            results = connection.execute("""SELECT accountName, videoID
                                            FROM videoPurchase
                                            WHERE purchaseID = ? 
                                            AND tempTimer - unixepoch() < (SELECT value 
                                                                           FROM constants 
                                                                           WHERE name = 'emailResetTime')""",
                                            (sessionID,))
            
            result = results.fetchone()
            accountName, videoID = result[0], result[1]

            connection.execute("""INSERT INTO accountVideo(accountName, videoID)
                                                    VALUES(?          , ?      )""",
                                                          (accountName, videoID))
        
        flask.flash("Purchase Successful")
        return flask.redirect("video?videoID=" + str(videoID))

class purchaseFailure(webPage):
    def __init__(self, database, secret_key) -> None:
        super().__init__(database, secret_key)

        self.route = "/purchaseFailure"
        self.methods = ["GET"]
        self.__name__ = "purchaseFailure"
    
    def webPageMethod(self):
        videoID = flask.request.args["videoID"]
       
        flask.flash("Purchase Failed", "error")
        return flask.redirect("video?videoID=" + str(videoID))
    