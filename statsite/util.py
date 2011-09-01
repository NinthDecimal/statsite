"""
Contains utility functions.
"""

import collections
import copy

def quacks_like_dict(object):
    """Check if object is dict-like"""
    return isinstance(object, collections.Mapping)

def deep_merge(a, b):
    """Merge two deep dicts non-destructively

    Uses a stack to avoid maximum recursion depth exceptions

    >>> a = {'a': 1, 'b': {1: 1, 2: 2}, 'd': 6}
    >>> b = {'c': 3, 'b': {2: 7}, 'd': {'z': [1, 2, 3]}}
    >>> c = merge(a, b)
    >>> from pprint import pprint; pprint(c)
    {'a': 1, 'b': {1: 1, 2: 7}, 'c': 3, 'd': {'z': [1, 2, 3]}}
    """
    assert quacks_like_dict(a), quacks_like_dict(b)
    dst = copy.deepcopy(a)

    stack = [(dst, b)]
    while stack:
        current_dst, current_src = stack.pop()
        for key in current_src:
            if key not in current_dst:
                current_dst[key] = current_src[key]
            else:
                if quacks_like_dict(current_src[key]) and quacks_like_dict(current_dst[key]) :
                    stack.append((current_dst[key], current_src[key]))
                else:
                    current_dst[key] = current_src[key]
    return dst

def resolve_class_string(full_string):
    """
    Given a string such as "foo.bar.Baz" this will properly
    import the "Baz" class from the "foo.bar" module.
    """
    module_string, _, cls_string = full_string.rpartition(".")
    if module_string == "":
        raise ValueError, "Must specify a module for class: %s" % full_string
    elif cls_string == "":
        raise ValueError, "Must specify a class for module: %s" % full_string

    module = __import__(module_string, globals(), locals(), [cls_string], -1)
    if not hasattr(module, cls_string):
        raise ImportError, "Class not found in module: %s" % full_string

    return getattr(module, cls_string)
