import flask

from .webPage import webPage

class index(webPage):
    def __init__(self, database, secret_key) -> None:
        super().__init__(database, secret_key)

        self.route = "/"
        self.methods = ["GET", "POST"]
        self.__name__ = "index"

    def webPageMethod(self):
        if flask.request.method == "GET":
            return flask.render_template("index.html")
        elif flask.request.method == "POST":
            # User entered value into search function
            # Redirect with data to the search page
            return flask.redirect("search?query=" + flask.request.form["input"] + (("&sort=" + flask.request.form["sortStyle"]) if ("sortStyle" in flask.request.form) else "") + (("&tag=" + flask.request.form["tag"]) if (flask.request.form["tag"] != "") else ""))
