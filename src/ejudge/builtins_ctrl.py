"""
Import builtin functions for easy recovery when a script or a preparation
routine messes with Python's __builtins__.
"""
import builtins

# Save this for later
__original__ = vars(builtins)
_print = print
_input = input


def update(dic=None, **kwds):
    """
    Update the builtins module with the given values
    """

    dic = dict(dic or {})
    dic.update(kwds)
    for k, v in dic.items():
        setattr(builtins, k, v)


def restore():
    """
    Restores builtins to original state
    """

    for k, v in vars(builtins).items():
        if k not in __original__:
            delattr(builtins, k)
    for k, v in __original__.items():
        setattr(builtins, k, v)
    builtins.print = _print
    builtins.input = _input
