import flask
import stripe

app = flask.Flask(__name__)

# Import flask routes for each different webpage
import pythonFiles.index
import pythonFiles.search
import pythonFiles.video
import pythonFiles.accounts
import pythonFiles.databaseCleaner

# https://dev.to/nandamtejas/implementing-flask-application-using-object-oriented-programming-oops-5cb
class flaskApp():

    def __init__(self, app: flask.Flask) -> None:
        self.app: flask.Flask = app

        self.database: str = "database.db"
        # For production use, python -c 'import secrets; print(secrets.token_hex())'to generate good key
        self.app.secret_key = b'DEVKEY, DO NOT USE IN PROD'

        # Read Stripe keys from a txt file to avoid them from being commited with the code
        with open("stripeKeys.txt") as fp:

            self.stripeKeys = { 
                "secretKey": fp.readline().split(" ")[1],
                "publishableKey": fp.readline().split(" ")[1]
            } 
        stripe.api_key = self.stripeKeys["secretKey"]

        
        # Setup automated tasks
        pythonFiles.databaseCleaner.databaseCleaner.setup(self.database)

    
    def setDatabase(self, database):
        # Change database location
        # Unlikely to be used as a database change will probably require downtime
        self.database = database
    
    def updateSecretKey(self, secret_key):
        # Change secret key in case it is leaked
        self.app.secret_key = secret_key
    
    def addWebpage(self, pageObj):
        self.app.add_url_rule(pageObj.route, view_func=pageObj, methods = pageObj.methods)

if __name__ == "__main__":
    app = flaskApp(flask.Flask(__name__))

    # Compose all the webpages into the main web app.
    # Sadly this is quite ugly, as python does not support composision well
    app.addWebpage(pythonFiles.search.search(app.database, app.app.secret_key))
    app.addWebpage(pythonFiles.video.video(app.database, app.app.secret_key))
    app.addWebpage(pythonFiles.video.stripeConfig(app.database, app.app.secret_key, app.stripeKeys))
    app.addWebpage(pythonFiles.video.checkoutSession(app.database, app.app.secret_key, app.stripeKeys))
    app.addWebpage(pythonFiles.video.purchaseSuccess(app.database, app.app.secret_key))
    app.addWebpage(pythonFiles.video.purchaseFailure(app.database, app.app.secret_key))
    app.addWebpage(pythonFiles.accounts.signIn(app.database, app.app.secret_key))
    app.addWebpage(pythonFiles.accounts.register(app.database, app.app.secret_key))
    app.addWebpage(pythonFiles.accounts.signOut(app.database, app.app.secret_key))
    app.addWebpage(pythonFiles.index.index(app.database, app.app.secret_key))
    app.addWebpage(pythonFiles.accounts.resetPassword(app.database, app.app.secret_key))

    app.app.run(debug=False)