from pyadbc import *

@invariant(lambda self: self.capacity >= 0)
class List(object):
    def __init__(self, capacity):
        self.capacity = capacity
        self.things = []
        self._size = 0
        self.x = 10

    @ensures(lambda self, old: old['x'] + 1 == self.x,
            lambda self, old: old['size'] < 0)
    @old(lambda self: {'x': self.x, 'size': self._size})
    def doThing(self):
        self.x -= 1

    @requires(lambda self: self.size() < self.capacity)
    @ensures(lambda self: self.size() == len(self.things))
    def append(self, bla):
        self._size += 1
        self.things.append(bla)

    @requires(lambda self: self.size() != self.capacity)
    @ensures(lambda self: self.size() == len(self.things))
    def append_buggy(self, bla):
        self.things.append(bla)

    @ensures()
    def size(self):
        return self._size

@dbcinherit
class CoolList(List):
    def append(self, bla):
        self.things.append(bla)

def test_normal():
    """This should execute normally."""
    t = List(10)
    for i in range(10):
        t.append(i)
    assert True

def test_prefail():
    """Precondition should fail
    because we haven't ensured that the capacity >= size +1."""
    t = List(2)
    t.append(1)
    t.append(1)
    try:
        t.append(1)
        assert False
    except PreconditionFailedException as e:
        assert True

def test_postfail():
    """Postcondition should fail
    because the append implementation is buggy."""
    t = List(2)
    try:
        t.append_buggy(1)
        assert False
    except PostconditionFailedException as e:
        assert True

def test_invfail():
    """The invariant doesn't hold after the
    constructor is called."""
    try:
        t = List(-1)
        assert False
    except InvariantFailedException as e:
        assert True

def test_invfail2():
    """The invariant is broken before calling
    append(1), and thus the invariant should fail
    when calling that method."""
    t = List(10)
    t.capacity = -20
    try:
        t.append(1)
        assert False
    except InvariantFailedException as e:
        assert True

def test_old():
    t = List(10)
    try:
        t.doThing()
        assert False
    except PostconditionFailedException as e:
        assert True

def test_liskov():
    t = CoolList(2)
    try:
        t.append_buggy(1)
        assert False
    except PostconditionFailedException as e:
        assert True
    # Thanks to Prof. Constantinos Constantinides for
    # pointing out this problem with the original implementation.
    #
    # This append should fail because it doesn't
    # meet the postcondition of the parent class.
    # (Liskov substitution principle)
    t = CoolList(2)
    try:
        t.append(1)
        assert False
    except PostconditionFailedException as e:
        assert True

if __name__ == '__main__':
    test_liskov()
