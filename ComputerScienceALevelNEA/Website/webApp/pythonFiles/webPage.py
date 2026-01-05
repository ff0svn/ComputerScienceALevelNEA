import abc
import flask

class webPage(abc.ABC):

    def __init__(self, database, secret_key) -> None:
        super().__init__()

        self.database = database
        self.secret_key = secret_key

        self.route = ""
        self.methods = []
    
    def __call__(self):
        return self.webPageMethod()
    
    def setDatabase(self, database):
        self.database = database
    
    def setSecretKey(self, secret_key):
        self.secret_key = secret_key
    
    @abc.abstractmethod
    def webPageMethod(self) -> str | flask.Response | None:
        pass