import flask
import sqlite3 as sql
import re
import smtplib
from email import message
import secrets

from .bcrypt import bcrypt
from .webPage import webPage


class signIn(webPage):
    def __init__(self, database, secret_key) -> None:
        super().__init__(database, secret_key)

        self.route = "/signIn"
        self.methods = ["GET", "POST"]
        self.__name__ = "signIn"

    def webPageMethod(self):
        # For a GET request just return the HTML of the page
        if flask.request.method == "GET":
            return flask.render_template("signIn.html")
        
        elif flask.request.method == "POST":
            # Store the entered values for username and password
            username = flask.request.form["username"]
            password = flask.request.form["password"]

            # If user did not enter a username, inform them and return to sign in page
            if (username == ""):
                flask.flash("Username is required", "error")
                return flask.redirect(flask.url_for("signIn"))

            # Check they have entered a secure and valid password
            passwordErrorMessage = bcrypt.checkValidPassword(password)
            if (passwordErrorMessage != None):
                # If invalid password, inform user and return to sign in page
                flask.flash(passwordErrorMessage, "error")
                return flask.redirect(flask.url_for("signIn"))

            with sql.connect("database.db", uri= True) as connection:
                # Get stored password hash from database
                account = connection.execute("""SELECT password
                                                FROM account
                                                WHERE accountName = ?;""",
                                                (username,))

                account = account.fetchall()
                if len(account) == 1:
                    # Check whether the password's hash matches the hash in the database
                    if (bcrypt.hashCompare(password, account[0][0])):
                        # SOURCE https://flask.palletsprojects.com/en/stable/quickstart/#sessions
                        flask.session["username"] = username
                        return flask.redirect(flask.url_for("index"))
                    else:
                        flask.flash("Incorrect password", "error")
                        return flask.redirect(flask.url_for("signIn"))            
                else:
                    flask.flash("Username not found in database", "error")
                    return flask.redirect(flask.url_for("signIn"))
                    

class register(webPage):
    def __init__(self, database, secret_key) -> None:
        super().__init__(database, secret_key)

        self.route = "/register"
        self.methods = ["GET", "POST"]
        self.__name__ = "register"

    def webPageMethod(self):
        # For a GET request just return the HTML of the page
        if flask.request.method == "GET":
            return flask.render_template("register.html")
        
        elif flask.request.method == "POST":
            # Store the entered values for username, password and email
            username = flask.request.form["username"]
            password = flask.request.form["password"]
            email = flask.request.form["email"]
            

            # Ensure the username and password are both valid
            if (username == ""):
                flask.flash("Username is required", "error")
                return flask.redirect(flask.url_for("register"))
            
            passwordErrorMessage = bcrypt.checkValidPassword(password)
            if (passwordErrorMessage != None):
                flask.flash(passwordErrorMessage, "error")
                return flask.redirect(flask.url_for("register"))
            
            # Check whether an email is valid with regex
            if (((re.fullmatch("[^@]*@([^@])*\\.([^@^.]*)", email)) is None)):
                flask.flash("Email needs to be in form ____@____.___", "error")
                return flask.redirect(flask.url_for("register"))
            
            
            with sql.connect(self.database, uri= True) as connection:
                # Get the current number of bcrypt iterations from database
                bcryptCost = int(connection.execute("""SELECT value 
                                                FROM constants
                                                WHERE name = 'bcryptCurrCost'""").fetchone()[0])
                
                usernameCheck = connection.execute("""SELECT * 
                                                      FROM account
                                                      WHERE accountName = ?;""",
                                                      (username,))
                
                # Check if username is already in use
                if len(usernameCheck.fetchall()) != 0:
                    flask.flash("Username already in uses", "error")
                    return flask.redirect(flask.url_for("register"))
                
                # If not, insert the new information into the database
                connection.execute("""INSERT INTO account(accountName, password, email)
                                                  VALUES (?, ?, ?)"""
                                                        ,(username, bcrypt.generateHash(password, bcryptCost), email))
                
                # Sign user in to improve user experience                
                flask.session["username"] = username
                return flask.redirect(flask.url_for("index"))

class signOut(webPage):
    def __init__(self, database, secret_key) -> None:
        super().__init__(database, secret_key)

        self.route = "/signOut"
        self.methods = ["GET", "POST"]
        self.__name__ = "signOut"

    def webPageMethod(self):

        if flask.request.method == "GET":
            if "username" in flask.session:
                return flask.render_template("signOut.html")
            
            else:
                # https://en.wikipedia.org/wiki/List_of_HTTP_status_codes#2xx_success
                # User should not be able to access this page if they are not signed in
                flask.abort("403")

        elif flask.request.method == "POST":
            # Sign out button has been pressed, so sign out user
            flask.session.pop("username")
            return flask.redirect(flask.url_for("index"))
    
class resetPassword(webPage):
    def __init__(self, database, secret_key) -> None:
        super().__init__(database, secret_key)

        self.route = "/resetPassword"
        self.methods = ["GET", "POST"]
        self.__name__ = "resetPassword"

    def webPageMethod(self):

        enteredKey = None
        # Error handling to avoid crashes
        if "tempKey" in flask.request.args:
            enteredKey = flask.request.args["tempKey"]

        if flask.request.method == "GET":
            
            if enteredKey == None:
                return flask.render_template("resetPassword.html")
            else:
                # User has been sent here from email link, as such offer them to change their password
                with sql.connect(self.database, uri=True) as connection:
                    # Search for the account linked with tempKey
                    accounts = connection.execute("""SELECT accountName FROM tempWebpage
                                                     WHERE tempKey = ?
                                                     AND tempTimer - unixepoch() < (SELECT value 
                                                                                    FROM constants
                                                                                    WHERE name = 'emailResetTime')""",
                                                        (enteredKey,))
                    
                    account = accounts.fetchall()   

                # Check if there exists a valid reset link
                if len(account) == 0:
                    # Inform the user and return them to the original reset password page
                    flask.flash("Invalid link - The time may have run out", "error")
                    return flask.redirect(flask.url_for("resetPassword"))
                elif len(account) == 1:
                    return flask.render_template("changeResetPassword.html")
                
                # The program should never reach here
                flask.flash("Serious Error - Attempt to reset again, then if not working contact support", "error")
                return flask.redirect(flask.url_for("index"))
        
        elif flask.request.method == "POST":
            if enteredKey == None:
                # Have user enter username as is the primary for account table
                username = flask.request.form["username"]

                if username == "":
                    flask.flash("Username is required", "error")
                    return flask.redirect(flask.url_for("resetPassword"))

                # Setup temporary webpage for idk like an hour or smth
                # Send an email to the person with the temporary link
                # Need to be quite long like >200 chars, but fewer than 2000 ish
                # as some browser may not support links that large
                with sql.connect(self.database, uri= True) as connection:
                    # SCREENSHOT  Delete
                    # Get URLsize from constant table
                    URLSize = int(connection.execute("""SELECT value 
                                                    FROM constants
                                                    WHERE name = 'URLSize'""").fetchone()[0])
                    
                    # Create array of valid chars, then use that to securely (using secrets library) generate a key
                    chars: list[str] = [chr(i) for i in range(ord("A"), ord("Z"))] + [chr(i) for i in range(ord("1"), ord("9"))]
                    key: str = ""

                    for _ in range(URLSize):
                        key += secrets.choice(chars)
    

                    connection.execute("""INSERT INTO tempWebpage(tempKey, tempTimer, accountName)
                                                      VALUES     (?      , unixepoch()    , ?)"""
                                                                ,(key               , username))

                    # END DELETE
                    # Uncomment
                    #connection.execute("""INSERT INTO tempWebpage(tempKey, tempTimer, accountName)
                    #                                  VALUES     (hex(randomblob(SELECT value FROM constants WHERE name = 'URLSize')),
                    #                                              unixepoch()    , ?)""", username)

                    email = connection.execute("""SELECT email FROM account
                                                  WHERE accountName = ?"""
                                                                    ,(username,))

                    email = email.fetchall()

                    # Check that email is present
                    if len(email) == 1:
                        # Send email with the link to reset the password
                        self.sendRecoveryEmail(key, username, email[0][0])
                        flask.flash("Email sent")
                        return flask.redirect(flask.url_for("resetPassword"))

                    else:
                        flask.flash("Username not found in database", "error")
                        return flask.redirect(flask.url_for("resetPassword"))
            else:
                 # Store the both the entered values for the password
                password = flask.request.form["password"]
                repeatPassword = flask.request.form["confirm password"]

                # Check the passwords match
                if password == repeatPassword:
                    passwordErrorMessage = bcrypt.checkValidPassword(password)
                    if (passwordErrorMessage != None):
                        flask.flash(passwordErrorMessage, "error")
                        return flask.redirect(flask.request.url)

                    with sql.connect(self.database, uri= True) as connection:
                        bcryptCost = int(connection.execute("""SELECT value 
                                                        FROM constants
                                                        WHERE name = 'bcryptCurrCost'""").fetchone()[0])
            
                        # Update the accounts password to equal the one entered
                        # SCREENSHOT uncomment
                        #connection.execute("""UPDATE account
                        #                      INNER JOIN tempWebpage
                        #                      ON account.accountName = tempWebpage.accountName
                        #                      SET account.password = ?
                        #                      WHERE tempWebpage.tempKey = ?""",
                        #                      (bcrypt.generateHash(password, bcryptCost), enteredKey))
                        # 

                        # SCREENSHOTS delete
                        key = connection.execute("""SELECT accountName FROM tempWebpage
                                              WHERE tempKey = ?""", (enteredKey,))

                        connection.execute("""UPDATE account
                                              SET password = ?
                                              WHERE accountName = ?""",
                                              (bcrypt.generateHash(password, bcryptCost), (key.fetchall())[0][0]))
                        # SCREENSHOT end
                        
                        # Now the password is changed, we can delete the temp webpage
                        connection.execute("""DELETE FROM tempWebpage
                                              WHERE tempKey = ?""", (enteredKey,))
                        
                        flask.flash("Password successfully changed")
                        return flask.redirect(flask.url_for("index"))
                else:
                    flask.flash("Passwords entered do not match", "error")
                    return flask.redirect(flask.request.url)
    
    def sendRecoveryEmail(self, key, username, email) -> None:
        
        with sql.connect(self.database, uri= True) as connection:
            emailAddress = connection.execute("""SELECT value 
                                                 FROM constants
                                                 WHERE name = 'emailAddress'""").fetchone()[0]

            emailPassword = connection.execute("""SELECT value 
                                                  FROM constants
                                                  WHERE name = 'emailPassword'""").fetchone()[0]

            siteURL = connection.execute("""SELECT value 
                                            FROM constants
                                            WHERE name = 'siteURL'""").fetchone()[0]

            emailResetTime = int(connection.execute("""SELECT value 
                                                       FROM constants
                                                       WHERE name = 'emailResetTime'""").fetchone()[0])

        emailTemplate = flask.render_template("emailTemplate.html")

        linkWithEnding = siteURL + flask.url_for("resetPassword") + "?tempKey=" + key

        emailTemplate = emailTemplate.format(
                            username = username, 
                            linkWithEnding = linkWithEnding,
                            time = str(emailResetTime // 60),
                            link = siteURL + flask.url_for("resetPassword"))

        msg = message.EmailMessage()
        msg.set_content(emailTemplate, subtype = "html")

        msg["Subject"] = "Please reset your password - LPS"
        msg["From"] = emailAddress
        msg["To"] = email

        with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
            smtp.ehlo()
            # Secure with tls encryption
            smtp.starttls()
            smtp.ehlo()

            # Login into the email account
            smtp.login(emailAddress, emailPassword)

            smtp.sendmail(msg["From"], msg["To"], msg.as_string())
