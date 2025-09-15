class RK800Error(Exception):
    """Base exception for all RK800 errors"""
    pass


class NetworkError(RK800Error):
    """Base class for network-related errors"""
    pass


class TLSError(NetworkError):
    """Base class for TLS-related errors"""
    pass


class PacketHandlingError(NetworkError):
    """Raised when packet handling fails"""
    pass


class ClientDisconnectedError(NetworkError):
    """Raised when client disconnects unexpectedly"""
    pass


class ServerError(RK800Error):
    """Base class for server-related errors"""
    pass


class ConfigurationError(RK800Error):
    """Raised when configuration is invalid"""
    pass


class ResourceError(RK800Error):
    """Raised when resource management fails"""
    pass
