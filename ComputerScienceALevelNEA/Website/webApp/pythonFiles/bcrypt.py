import secrets
import ctypes
from pathlib import Path
# https://pgi-jcns.fz-juelich.de/portal/pages/using-c-from-python.html

class charArr(ctypes.Structure):
    _fields_ = [("data", ctypes.c_char_p),
                ("size", ctypes.c_int)]

# Load the C library into context and offer type declerations of the function
_bcryptLib = ctypes.CDLL((Path(__file__).parent / "../cFiles/libbcrypt.so").resolve())
_bcryptLib.bcrypt.argtypes = (ctypes.c_int, ctypes.c_char_p, ctypes.POINTER(charArr))
_bcryptLib.bcrypt.restype = (ctypes.c_char_p)

class bcrypt:

    # Cost can vary from 4 - 31. The password can be a maximum of 72 bytes
    # I have salt as "bytes" instead of str, because of the inconsitencies
    # of how C and python treats "string". The way I'm using char* in C
    # is more similar to python's bytes than it's str 
    # Returns data in the form:
    #         $2a$[cost]$[22 character salt][31 character hash]
    @staticmethod
    def __bcrypt(cost: int, salt: bytes, password: str) -> str:
        global _bcryptLib
        passwordAsStruct = charArr(ctypes.c_char_p(password.encode('utf-8')), len(password))

        returnValue = _bcryptLib.bcrypt(ctypes.c_int(cost), ctypes.c_char_p(salt), ctypes.pointer(passwordAsStruct))
        return str(returnValue)[2:-1]

    @staticmethod
    def generateHash(password: str, cost: int) -> str:
        salt: bytes = secrets.token_bytes(16)

        return bcrypt.__bcrypt(cost, salt, password)

    @staticmethod
    def __B64ToBytes(input: str) -> bytes:
        base64String = "./ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
        base64Convertion = dict([(base64String[i], i) for i in range(64)])

        byteInt = 0
        for i, char in enumerate(input):
            byteInt += base64Convertion[char] << (6*i)

        return byteInt.to_bytes(int(len(input)*(3/4)) + 1, "little")

    @staticmethod
    def hashCompare(password: str, hash: str) -> bool:
        try:
            cost: int = int(hash[4:6])

            # Extract the value of the salt from that of the hash, and convert from B64
            salt: bytes = bcrypt.__B64ToBytes(hash[7:29])

        except ValueError:
            # If the cost is not in the right place this must be an invalid hash
            # Therefore we must return False
            return False
        
        except KeyError:
            # If bcrypt.__B64ToBytes raises a key error, there must be an invalid salt
            # As this is the case, the hash cannot be correct, and we must return False
            return False
               
        enteredHash = bcrypt.__bcrypt(cost, salt, password)

        return hash == enteredHash

    @staticmethod
    def checkValidPassword(password: str) -> str:
        if (password == ""):
            return "Password is required"
        if (len(password) < 8):
            return "Password must be at least 8 character long"
        
        return None

# Unit test for the bcrypt module
if __name__ == "__main__":
    hash10 = bcrypt.generateHash("testPassword1", 10)

    print("Should pass: " + ("Passed" if bcrypt.hashCompare("testPassword1", hash10) else "Failed"))
    print("Should fail: " + ("Passed" if bcrypt.hashCompare("wrongPassword", hash10) else "Failed"))

    hash12 = bcrypt.generateHash("newTestPassword", 12)

    print("Should pass: " + ("Passed" if bcrypt.hashCompare("newTestPassword", hash12) else "Failed"))
    print("Should fail: " + ("Passed" if bcrypt.hashCompare("wrongPassword", hash12) else "Failed"))