===============================
pyadbc
===============================

.. image:: https://badge.fury.io/py/pyadbc.png
    :target: http://badge.fury.io/py/pyadbc
    
.. image:: https://travis-ci.org/tarmstrong/pyadbc.png?branch=master
        :target: https://travis-ci.org/tarmstrong/pyadbc

.. image:: https://pypip.in/d/pyadbc/badge.png
        :target: https://crate.io/packages/pyadbc?version=latest


PyADBC: Design by Contract in Python


PyADBC provides pure python support for `Design by
Contract <https://en.wikipedia.org/wiki/Design_by_contract>`__.
Invariants, pre- and post-conditions are added using decorators.

* Free software: BSD license

Usage
-----

Invariants
~~~~~~~~~~

To define an invariant on a class (a condition that always holds after
the object is instantiated), use the ``@invariant`` decorator. The
``self`` passed into the passed lambda is the same ``self`` that would
be passed to a method.

::

    @invariant(lambda self: self.capacity >= 0)
    class List(object):
        # ...

Preconditions
~~~~~~~~~~~~~

Preconditions can be specified with ``@requires``. These are properties
that must evaluate to ``True`` *before* the method is run.

::

    @requires(lambda self: self.size() < self.capacity)
    def append(self, bla):
        self._size += 1
        self.things.append(bla)

Postconditions
~~~~~~~~~~~~~~

Postconditions can be specified with ``@ensures``:

::

    @ensures(lambda self: self.size() == len(self.things))
    def append(self, bla):
        self._size += 1
        self.things.append(bla)

These are properties that must evaluate to ``True`` *after* the method
has run.

``@old`` for before/after comparisons
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In order to compare properties of the object before and after an
operation, PyADBC provides the ``@old`` decorator. You can use it to
"cache" values for use in the postcondition.

For example, the following method's postcondition guarantees that the
``x`` instance attribute is increased by one. Dictionaries returned in
the functions passed to ``@old`` will be merged and passed as a second
argument to the postcondition functions.

::

    @ensures(lambda self, old: old['x'] + 1 == self.x,
            lambda self, old: old['size'] < 0)
    @old(lambda self: {'x': self.x, 'size': self._size})
    def doThing(self):
        self.x -= 1

Exceptions
~~~~~~~~~~

If any conditions defined by the above decorators evaluate to ``False``,
one of the following exceptions will be raised based on what kind of
condition it is:

-  ``PreconditionFailedException``, which implies that the client of the
   class failed to satisfy the class's contract.
-  ``PostconditionFailedException``, which implies that the object
   itself failed to satisfy its class's contract.
-  ``InvariantFailedException``, which implies that the object has
   entered an illegal state.

``@dbcinherit`` for inheriting classes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

An important feature of DBC is that it can validate the `Liskov
Substitution
Principle <https://en.wikipedia.org/wiki/Liskov_substitution_principle>`__.
That is, if a child class ``CoolList`` inherits from the base class
``List``, its operations should satsify ``List``'s contracts. This gives
some assurance that the principle holds for the child class.

To do this with PyADBC, you need to explicitly decorate the child class,
e.g.:

::

    @dbcinherit
    class CoolList(List):
       # ...

If ``CoolList`` overrides the ``append()`` method, the contract of
``List``'s ``append()`` method will be applied to ``CoolList``'s
``append()``.

This also currently works with multiple inheritance.

Other solutions
---------------

-  `PyDBC <http://www.nongnu.org/pydbc/>`__, which uses a metaclass.
-  `pycontract <http://www.wayforward.net/pycontract/>`__, which uses
   docstrings. See the Python Enhancement Proposal (PEP) that references
   this implementation
   `here <http://www.python.org/dev/peps/pep-0316/>`__.

Contributing
------------

See ``TODO.md`` for missing features. Suggestions and bug reports are
always welcome.

Acknowledgements
----------------

Thanks to

-  Prof. Constantinos Constantinides, for his feedback regarding Liskov
   and for teaching me about DBC in the first place

