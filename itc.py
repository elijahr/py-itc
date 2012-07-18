#!/usr/bin/env python

# I am copying this more or less verbatim from a C# library I in
# turn copied from a Java library I found on github.  I'm also
# basically doing this in the background while I watch Archer.  So,
# you know, there may be some bugs.

class IntervalTreeClock(object):
    pass

ITC = IntervalTreeClock

class IDNode(object):
    def __init__(self, val=None):
        self.left = None
        self.right = None
        self.value = val
        self.leaf = val is not None

    def __repr__(self):
        return "ID: %s"%self.enstring()

    def enstring(self):
        if self.leaf:
            return str(self.value)
        return "(%s, %s)"%(self.left.enstring(), self.right.enstring())

    def clone(self):
        rtn = IDNode(self.value)
        if self.left:
            rtn.left = self.left.clone()
        if self.right:
            rtn.right = self.right.clone()
        rtn.leaf = self.leaf
        return rtn

    def split(self):
        id1 = IDNode()
        id2 = IDNode()

        if self.leaf and self.value == 0: # s(0) -> (0, 0)
            # this isn't supposed to happen
            id1.leaf = True
            id1.value = 0

            id2.leaf = True
            id2.value = 0
        elif self.leaf and self.value == 1: # s(1) -> [(1, 0), (0, 1)]
            id1.left = IDNode(1)
            id1.right = IDNode(0)
            
            id2.left = IDNode(0)
            id2.right = IDNode(1)
        elif not self.leaf and self.left.leaf and self.left.value == 0 and \
                (not self.right.leaf or self.right.value == 1):
            # s(0, i) -> [(0, s1(i)), (0, s2(i))]
            childs = self.right.split()
            id1.left = IDNode(0)
            id1.right = childs[0]

            id2.left = IDNode(0)
            id2.right = childs[1]
        elif not self.leaf and (not self.left.leaf or self.left.value == 1) \
                and self.right.leaf and self.right.value == 0:
            # s(i, 0) -> [(s1(i), 0), (s2(i), 0)]
            childs = self.left.split()
            id1.left = childs[0]
            id1.right = IDNode(0)

            id2.left = childs[1]
            id2.right = IDNode(0)
        elif not self.leaf and (not self.left.leaf or self.left.value == 1) and \
                (not self.right.leaf or self.right.value == 1):
            # s(i1, i2) -> [(i1, 0), (0, i2)]
            id1.left = self.left.clone()
            id1.right = IDNode(0)

            id2.left = IDNode(0)
            id2.right = self.right.clone()

        return id1, id2

    def normalize(self):
        if self.left:
            self.left.normalize()
        if self.right:
            self.right.normalize()

        if not self.leaf and self.left.leaf and self.left.value == 0 and self.right.leaf and self.right.value == 0:
            # (0, 0) -> 0
            self.leaf = True
            self.value = 0
            self.left = self.right = None
        elif not self.leaf and self.left.leaf and self.left.value == 1 and self.right.leaf and self.right.value == 1:
            # (1, 1) -> 1
            self.leaf = True
            self.value = 1
            self.left = self.right = None

    def __add__(self, other): # aka join
        if self.leaf and self.value == 0:
            return other.clone()
        elif other.leaf and other.value == 0:
            return self.clone()
        rtn = IDNode()
        rtn.left = self.left + other.left
        rtn.right = self.right + other.right
        rtn.normalize()
        return rtn

class EventNode(object):
    def __init__(self, val=0):
        self.value = val
        self.leaf = True

    def get_leaf(self):
        return self._leaf

    def set_leaf(self, val):
        if val:
            self.left = None
            self.right = None
        else:
            self.left = EventNode()
            self.right = EventNode()
        self._leaf = val

    leaf = property(get_leaf, set_leaf)

    def __repr__(self):
        return "EN: %s"%self.enstring()

    def enstring(self):
        if self.leaf:
            return str(self.value)
        return "(%s, %s, %s)"%(self.value, self.left.enstring(), self.right.enstring())

    def clone(self):
        rtn = EventNode()
        rtn.leaf = self.leaf
        if not self.leaf:
            rtn.left = self.left
            rtn.right = self.right
        rtn.value = self.value
        return rtn

    def __add__(self, n):
        '''
        Known as "Lift" (static method) in the Java ITC implementation
        '''
        rtn = self.clone()
        rtn.value += n
        return rtn

    def __iadd__(self, n):
        '''
        Known as "Lift" in the Java ITC implementation
        '''
        self.value += n
        return self

    def __isub__(self, n):
        '''
        aka "Sink"
        '''
        self.value -= n
        return self

    def __sub__(self, n):
        rtn = self.clone()
        rtn.value -= n
        return rtn

    def __mul__(self, other):
        '''
        Join.  Probably this should be __mul__ for both ID and Event nodes, for consistency.
        '''
        rtn = self.clone()
        if not self.leaf and not other.leaf:
            if self.value > other.value:
                return other * self
            else:
                d = other.value - self.value
                other.left += d
                other.right += d
                rtn.left = self.left * other.left
                rtn.right = self.right * other.right
                return rtn
        elif self.leaf and not other.leaf:
            rtn.leaf = False
            return rtn * other
        elif not self.leaf and other.leaf:
            oth = other.clone()
            oth.leaf = False
            return self * oth
        rtn.value = max(self.value, other.value)
        return rtn

    def normalize(self):
        if self.left:
            self.left.normalize()
        if self.right:
            self.right.normalize()
        if not self.leaf and self.left.leaf and self.right.leaf and self.left.value == self.right.value:
            self.value = left.value
            self.leaf = True
        elif not self.leaf:
            mm = min(self.left.value, self.right.value)
            self += mm
            self.left -= mm
            self.right -= mm

    def __le__(self, other):
        if not self.leaf and not other.leaf:
            if self.value > other.value:
                return False
            xl1 = self.left + self.value
            xl2 = other.left + other.value
            if not xl1 <= xl2:
                return False
            xr1 = self.right + self.value
            xr2 = other.right + other.value
            if not xr1 <= xr2:
                return False
            return True
        elif not self.leaf and other.leaf:
            if self.value > other.value:
                return False
            xl1 = self.left + self.value
            if not xl1 <= other:
                return False
            xr1 = self.right + self.value
            if not xr1 <= other:
                return False
            return True
        elif self.leaf and other.leaf:
            return self.value <= other.value
        elif self.leaf and not other.leaf:
            if self.value < other.value:
                return True
            ev = self.clone()
            ev.leaf = False
            return ev < other
        return False

    def height(self):
        '''
        Is destructive
        '''
        if not self.leaf:
            self.left.height()
            self.right.height()
            self.value += max(self.left.value, self.right.value)
            self.leaf = True

    def __eq__(self, other):
        if not other: # probably don't need this check but ok
            return False
        if self.leaf and other.leaf and self.value == other.value:
            return True
        if self.value == other.value and self.left == other.left and self.right == other.right:
            return True
        return False

class Stamp(object):
    def __init__(self, idn=None, evn=None):
        if idn:
            self.idn = idn
        else:
            self.idn = IDNode(1)
        if evn:
            self.evn = evn
        else:
            self.evn = EventNode()

    def fork(self):
        lid, rid = self.idn.split()
        l = Stamp(lid, self.evn.clone())
        r = Stamp(rid, self.evn.clone())
        return l, r

    def __add__(self, other):
        idn = self.idn + other.idn
        evn = self.evn * other.evn
        return Stamp(idn, evn)

    def __le__(self, other):
        return self.evn <= other.evn

    def peek(self):
        idn = IDNode(0)
        evn = self.evn.clone()
        return Stamp(idn, evn)

    def event(self):
        old = self.evn.clone()
        self.fill()
        if old == self.evn:
            self.grow()

    def grow(self):
        '''
        This gets kind of weird.
        '''
        if self.idn.leaf and self.idn.value == 1 and self.evn.leaf:
            self.evn += 1
            return 0
        elif self.evn.leaf:
            self.evn.leaf = False
	        # here 1000 is "some large constant" that needs to be
            # larger than the tree height of e
            return self.grow() + 1000
        elif not self.idn.leaf and self.idn.right.leaf and self.idn.right.value == 0:
            return Stamp(self.idn.left, self.evn.left).grow() + 1
        elif not self.idn.leaf:
            e1 = self.evn.left.clone()
            e2 = self.evn.right.clone()
            costl = Stamp(self.idn.left, self.evn.left).grow()
            costr = Stamp(self.idn.right, self.evn.right).grow()
            if costl < costr:
                self.evn.right = e2
                return costl + 1
            else:
                self.evn.left = e1
                return costr + 1
        return -1

    def fill(self):
        if self.idn.leaf and self.idn.value == 0:
            pass
        elif self.idn.leaf and self.idn.value == 1:
            self.evn.height()
        elif self.evn.leaf:
            pass
        elif not self.idn.leaf and self.idn.left.leaf and self.idn.left.value == 1:
            Stamp(self.idn.right, self.evn.right).fill()
            self.evn.left.height()
            self.evn.left.value = max(self.evn.left.value, self.evn.right.value)
            self.evn.normalize()
        elif not self.idn.leaf and self.idn.right.leaf and self.idn.right.value == 1:
            Stamp(self.idn.left, self.evn.left).fill()
            self.evn.right.height()
            self.evn.right.value = max(self.evn.right.value, self.evn.left.value)
            self.evn.normalize()
        elif not self.idn.leaf:
            Stamp(self.idn.left, self.evn.left).fill()
            Stamp(self.idn.right, self.evn.right).fill()
            self.evn.normalize()
