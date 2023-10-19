from types import SimpleNamespace

from kabomu.misc_utils_internal import parse_int_32

# Request environment variable for local server endpoint.
ENV_KEY_LOCAL_PEER_ENDPOINT = "kabomu.local_peer_endpoint"

# Request environment variable for remote client endpoint.
ENV_KEY_REMOTE_PEER_ENDPOINT = "kabomu.remote_peer_endpoint"

# Request environment variable for the transport instance from
# which a request was received.
ENV_KEY_TRANSPORT_INSTANCE = "kabomu.transport"

# Request environment variable for the connection from which a
# request was received.
ENV_KEY_CONNECTION = "kabomu.connection"

METHOD_CONNECT = "CONNECT"
METHOD_DELETE = "DELETE"
METHOD_GET = "GET"
METHOD_HEAD = "HEAD"
METHOD_OPTIONS = "OPTIONS"
METHOD_PATCH = "PATCH"
METHOD_POST = "POST"
METHOD_PUT = "PUT"
METHOD_TRACE = "TRACE"

# 200 OK
STATUS_CODE_OK = 200

# 400 Bad Request
STATUS_CODE_CLIENT_ERROR_BAD_REQUEST = 400

# 401 Unauthorized
STATUS_CODE_CLIENT_ERROR_UNAUTHORIZED = 401

# 403 Forbidden
STATUS_CODE_CLIENT_ERROR_FORBIDDEN = 403

# 404 Not Found
STATUS_CODE_CLIENT_ERROR_NOT_FOUND = 404

# 405 Method Not Allowed
STATUS_CODE_CLIENT_ERROR_METHOD_NOT_ALLOWED = 405

# 413 Payload Too Large
STATUS_CODE_CLIENT_ERROR_PAYLOAD_TOO_LARGE = 413

# 414 URI Too Long
STATUS_CODE_CLIENT_ERROR_URI_TOO_LONG = 414

# 415 Unsupported Media Type
STATUS_CODE_CLIENT_ERROR_UNSUPPORTED_MEDIA_TYPE = 415

# 422 Unprocessable Entity
STATUS_CODE_CLIENT_ERROR_UNPROCESSABLE_ENTITY = 422

# 429 Too Many Requests
STATUS_CODE_CLIENT_ERROR_TOO_MANY_REQUESTS = 429

# 500 Internal Server Error
STATUS_CODE_SERVER_ERROR = 500

# The default value of maximum size of headers in a request or response.
DEFAULT_MAX_HEADERS_SIZE = 8_192

def _get_optional_attr(instance, *args):
    for n in args:
        if instance == None or not hasattr(instance, n):
            return None
        instance = getattr(instance, n)
    return instance

def _bind_method(proc, instance):
    return proc.__get__(instance, instance.__class__)

def merge_processing_options(preferred, fallback):
    if preferred is None or fallback is None:
        return preferred if preferred is not None else fallback
    merged_options = SimpleNamespace()
    merged_options.timeout_millis =\
        _determine_effective_non_zero_integer_option(
            _get_optional_attr(preferred, "timeout_millis"),
            _get_optional_attr(fallback, "timeout_millis"),
        0)
    merged_options.extra_connectivity_params =\
        _determine_effective_options(
            _get_optional_attr(preferred, "extra_connectivity_params"),
            _get_optional_attr(fallback, "extra_connectivity_params"))
    merged_options.max_headers_size =\
        _determine_effective_positive_integer_option(
            _get_optional_attr(preferred, "max_headers_size"),
            _get_optional_attr(fallback, "max_headers_size"),
        0)
    merged_options.max_response_body_size =\
        _determine_effective_non_zero_integer_option(
            _get_optional_attr(preferred, "max_response_body_size"),
            _get_optional_attr(fallback, "max_response_body_size"),
        0)
    return merged_options

def _determine_effective_non_zero_integer_option(
        preferred, fallback1, default_value):
    if preferred:
        return parse_int_32(preferred)
    if fallback1:
        return parse_int_32(fallback1)
    return parse_int_32(default_value)

def _determine_effective_positive_integer_option(
        preferred, fallback1, default_value):
    if preferred:
        effective_value = parse_int_32(preferred)
        if effective_value > 0:
            return effective_value
    if fallback1:
        effective_value = parse_int_32(fallback1)
        if effective_value > 0:
            return effective_value
    return parse_int_32(default_value)

def _determine_effective_options(
        preferred, fallback):
    dest = {}
    # since we want preferred options to overwrite fallback options,
    # set fallback options first.
    if fallback:
        dest.update(**fallback)
    if preferred:
        dest.update(**preferred)
    return dest
