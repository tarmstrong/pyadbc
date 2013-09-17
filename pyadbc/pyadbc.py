#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""pyadbc.py : Design By Contract in Python

This module brings design by contract to python classes. It is heavily inspired
by the AspectJ-based ABDC library developed by the Ansymo group at the
University of Antwerp.

See http://ansymo.ua.ac.be/artefacts/adbc
"""

class PreconditionFailedException(Exception): pass
class PostconditionFailedException(Exception): pass
class InvariantFailedException(Exception): pass

def invariant(*iconditions):
    """Decorator to specify an invariant on a class.

    If the passed functions do not hold before or after
    a  method call, a InvariantFailedException will be thrown.

    e.g.
        @invariant(lambda self: self.size >= 0,
                   lambda self: self.capacity >= 0,
                   lambda self: self.capacity >= self.size)
        class Stack(object):
            def __init__(self, capacity):
                self.size = 0
                self.capacity = capacity
                self.elements = []
    """
    import inspect
    def classwrapper(klass):
        conditions = []
        for condition in iconditions:
            conditions.append(_Condition(condition, inv = True))
        methods = inspect.getmembers(klass, predicate=inspect.ismethod)
        for method in methods:
            _invariant_wrap(klass, method, conditions)
        return klass
    return classwrapper

def dbcinherit(klass):
    import inspect
    child_class_methods = dict(inspect.getmembers(klass))
    for b in klass.__bases__:
        dbcmethods = [(mname, m.cw) for (mname, m) in inspect.getmembers(b) if hasattr(m, 'cw')]
        dbcmethods_dict = dict(dbcmethods)
        for method_name, parent_method in dbcmethods_dict.items():
            child_method = child_class_methods[method_name]

            # Check whether or not the method has been overridden.
            if not hasattr(child_method, 'cw'):
                import copy
                cw = copy.deepcopy(parent_method)
                cw.method = child_method
                def call_wrapper(self, *args, **kwargs):
                    return cw(self, *args, **kwargs)
                call_wrapper.cw = cw
                setattr(klass, method_name, call_wrapper)
    return klass

def requires(*preconditions):
    """Decorator to specify a precondition on a method.

    If the function does not return True before a function is called,
    a PreconditionFailedException will be thrown. This states that
    the caller is at fault, because they did not satisfy the contract.

    e.g.
        class Stack(object):
            # ...

            # Can't push onto the stack if the stack is already full.
            @requires(lambda self: self.size < self.capacity)
            def push(self, el):
                # ...
    """
    conditions = []
    for precond in preconditions:
        conditions.append(_Condition(precond))
    def method_wrapper(method):
        if hasattr(method, 'cw'):
            method.cw.preconds.extend(conditions)
            cw = method.cw
        else:
            cw = _PyADBCMethodCallWrapper(method, pre_conditions=conditions)
        def call_wrapper(self, *args, **kwargs):
            return cw(self, *args, **kwargs)
        call_wrapper.cw = cw
        return call_wrapper
    return method_wrapper

def ensures(*postconditions):
    """Decorator to specify a postcondition on a method.

    If the conditions do not hold after the method is called,
    a PostconditionFailedException will be thrown. This means
    that the class has failed to meet its own contract.

    e.g.
        class Stack(object):
            # ...

            # Pushing onto the stack should not result in the stack
            # being over capacity.
            @ensures(lambda self: self.size <= self.capacity)
            def push(self, el):
                # ...
    """
    conditions = []
    for postcond in postconditions:
        conditions.append(_Condition(postcond))
    def method_wrapper(method):
        if hasattr(method, 'cw'):
            method.cw.postconds.extend(conditions)
            cw = method.cw
        else:
            cw = _PyADBCMethodCallWrapper(method, post_conditions=conditions)
        def call_wrapper(self, *args, **kwargs):
            return cw(self, *args, **kwargs)
        call_wrapper.cw = cw
        return call_wrapper
    return method_wrapper

def old(oldfun):
    """Decorator to capture values for use in the @ensures decorator conditions.

    A @ensures decorator may wish to compare the state of the object before
    the method was invoked to the state of the object after the method was
    invoked. @old provides a means of capturing this "previous" state.

    e.g.
        class Stack(object):
            # ...

            # pushing onto the stack should increase the size by one.
            @ensures(lambda self, old: self.size == old['size'] + 1)
            @old(lambda self: {'size': self.size})
            def push(self, el):
                # ...
    """
    def method_wrapper(method):
        if hasattr(method, 'cw'):
            method.cw.olds.append(oldfun)
            cw = method.cw
        else:
            cw = _PyADBCMethodCallWrapper(method, olds=[oldfun])
        def call_wrapper(self, *args, **kwargs):
            return cw(self, *args, **kwargs)
        call_wrapper.cw = cw
        return call_wrapper
    return method_wrapper

class _Condition(object):
    def __init__(self, condition, inv = False):
        self.condition = condition
        self._invariant = inv
    def __call__(self, calleeself, old = {}):
        condition = self.condition
        import inspect
        argspec = inspect.getargspec(condition)
        if len(argspec.args) == 2:
            return condition(calleeself, old)
        else:
            return condition(calleeself)

class _PyADBCMethodCallWrapper(object):
    """Wrapper for methods that have been decorated by pyadbc.

    This object's __call__ method is what runs when the "contracted" method is
    invoked.
    """
    def __init__(self, method, pre_conditions=[], post_conditions = [], olds = []):
        self.method = method
        self.preconds = list(pre_conditions)
        self.postconds = list(post_conditions)
        self.olds = olds
        self.oldvals = {}

    def __call__(self, calleeself, *args, **kwargs):
        method = self.method
        oldvals = {}
        # Save the @old values for use in postconditions.
        for oldfun in self.olds:
            vals = oldfun(calleeself)
            oldvals = dict(oldvals.items() + vals.items())
        self.oldvals = oldvals
        # Check the preconditions.
        for cond in self.preconds:
            if cond(calleeself) != True:
                if cond._invariant:
                    raise InvariantFailedException()
                else:
                    raise PreconditionFailedException()
        result = method(calleeself, *args, **kwargs)
        # Check the postconditions.
        for cond in self.postconds:
            if cond(calleeself, oldvals) != True:
                if cond._invariant:
                    raise InvariantFailedException()
                else:
                    raise PostconditionFailedException()
        return result

def _invariant_wrap(klass, method, conditions):
    method_name = method[0]
    mfunc = method[1].__func__
    if hasattr(mfunc, 'cw'):
        if method_name != '__init__':
            # Preconditions checked before the constructor is run will probably
            # fail.
            mfunc.cw.preconds = list(conditions) + mfunc.cw.preconds
        mfunc.cw.postconds = list(conditions) + mfunc.cw.postconds
    else:
        if method_name == '__init__':
            cw = _PyADBCMethodCallWrapper(mfunc, post_conditions=conditions)
            def call_wrapper(self, *args, **kwargs):
                return cw(self, *args, **kwargs)
            call_wrapper.cw = cw
            setattr(klass, method_name, call_wrapper)
        else:
            cw = _PyADBCMethodCallWrapper(mfunc, post_conditions=conditions, pre_conditions=conditions)
            def call_wrapper(self, *args, **kwargs):
                return cw(self, *args, **kwargs)
            call_wrapper.cw = cw
            setattr(klass, method_name, call_wrapper)
