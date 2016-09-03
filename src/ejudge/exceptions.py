try:
    # Reuse exception from IoSpec.
    from iospec.exceptions import BuildError
except ImportError:
    class BuildError(Exception):
        """
        Exception raised when the build process is unsuccessful.
        """


class MissingInputError(RuntimeError):
    """
    Error raised when asked for a non-existing input
    """


class EarlyTerminationError(RuntimeError):
    """
    Error raised when program finishes without consuming all inputs.
    """
