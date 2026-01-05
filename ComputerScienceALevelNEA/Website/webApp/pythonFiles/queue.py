import ctypes
from pathlib import Path

# Need to declare the node struct before adding its fields as in references iteself
class node(ctypes.Structure):
    pass
node._fields_ = [("data", ctypes.py_object),
                ("next", ctypes.POINTER(node))]

class cQueue(ctypes.Structure):
    _fields_ = [("head", ctypes.POINTER(node)),
                ("tail", ctypes.POINTER(node))]

# Load C library into context
_queueLib = ctypes.CDLL((Path(__file__).parent / "../cFiles/libqueue.so").resolve())

# Declare the C functions for python to reference

_queueLib.initQueue.argtypes = ()
_queueLib.initQueue.restype = (ctypes.POINTER(cQueue))

_queueLib.delQueue.argtypes = (ctypes.POINTER(cQueue),)
_queueLib.delQueue.restype = None

_queueLib.enqueue.argtypes = (ctypes.POINTER(cQueue), ctypes.py_object)
_queueLib.enqueue.restype = None

_queueLib.dequeue.argtypes = (ctypes.POINTER(cQueue),)
_queueLib.dequeue.restype = (ctypes.py_object)

_queueLib.isEmpty.argtypes = (ctypes.POINTER(cQueue),)
_queueLib.isEmpty.restype = (ctypes.c_int)

class queue:
    # Python wrapper around C queue class
    # Can store any python object

    global _queueLib

    def __init__(self):
        
        self.q = _queueLib.initQueue()
    
    def __del__(self):
        _queueLib.delQueue(self.q)

    def enqueue(self, data: ctypes.py_object):
        _queueLib.enqueue(self.q, data)

    def dequeue(self) -> ctypes.py_object:
        return _queueLib.dequeue(self.q)

    def isEmpty(self) -> bool:
        returnValAsInt = int(_queueLib.isEmpty(self.q))

        return returnValAsInt != 0
 

# Unit tests
if __name__ == "__main__":

    que = queue()

    print(que.isEmpty())

    que.enqueue([1,[2]])
    que.enqueue([2,3])
    que.enqueue([3,4])

    print(que.isEmpty())

    print(que.dequeue())
    print(que.dequeue())
    print(que.dequeue())

    print(que.isEmpty())

