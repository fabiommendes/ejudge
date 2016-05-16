"""
Import builtin functions for easy recovery when a script or a preparation
routine messes with Python's __builtins__.
"""
import builtins

# Save this for later
__original__ = vars(builtins)
_print = print
_input = input


def update(D=None, **kwds):
    """Update the buitins module with the given values"""

    D = dict(D or {})
    D.update(kwds)
    for k, v in D.items():
        setattr(builtins, k, v)


def restore():
    """Restores builtins to original state"""

    for k, v in vars(builtins).items():
        if k not in __original__:
            delattr(builtins, k)
    for k, v in __original__.items():
        setattr(builtins, k, v)
    builtins.print = _print
    builtins.input = _input
