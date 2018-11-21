

class CommandError(Exception):pass

class SMCConnectionError(Exception):pass
class UnsupportedEntryPoint(Exception):pass
class ConfigLoadError(Exception):pass
class InvalidSessionError(Exception): pass
class SMCOperationFailure(Exception):pass

class ResolveError(Exception):
    """
    raised when the hname could not be resolved
    """
    pass
