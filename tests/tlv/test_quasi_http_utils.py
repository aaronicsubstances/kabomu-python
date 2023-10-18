import pytest
from types import SimpleNamespace

from kabomu import quasi_http_utils

def test_constant_values():
    assert quasi_http_utils.METHOD_CONNECT == "CONNECT"
    assert quasi_http_utils.METHOD_DELETE == "DELETE"
    assert quasi_http_utils.METHOD_GET == "GET"
    assert quasi_http_utils.METHOD_HEAD == "HEAD"
    assert quasi_http_utils.METHOD_OPTIONS == "OPTIONS"
    assert quasi_http_utils.METHOD_PATCH == "PATCH"
    assert quasi_http_utils.METHOD_POST == "POST"
    assert quasi_http_utils.METHOD_PUT == "PUT"
    assert quasi_http_utils.METHOD_TRACE == "TRACE"

    assert quasi_http_utils.STATUS_CODE_OK == 200
    assert quasi_http_utils.STATUS_CODE_SERVER_ERROR == 500
    assert quasi_http_utils.STATUS_CODE_CLIENT_ERROR_BAD_REQUEST == 400
    assert quasi_http_utils.STATUS_CODE_CLIENT_ERROR_UNAUTHORIZED == 401
    assert quasi_http_utils.STATUS_CODE_CLIENT_ERROR_FORBIDDEN == 403
    assert quasi_http_utils.STATUS_CODE_CLIENT_ERROR_NOT_FOUND == 404
    assert quasi_http_utils.STATUS_CODE_CLIENT_ERROR_METHOD_NOT_ALLOWED == 405
    assert quasi_http_utils.STATUS_CODE_CLIENT_ERROR_PAYLOAD_TOO_LARGE == 413
    assert quasi_http_utils.STATUS_CODE_CLIENT_ERROR_URI_TOO_LONG == 414
    assert quasi_http_utils.STATUS_CODE_CLIENT_ERROR_UNSUPPORTED_MEDIA_TYPE == 415
    assert quasi_http_utils.STATUS_CODE_CLIENT_ERROR_UNPROCESSABLE_ENTITY == 422
    assert quasi_http_utils.STATUS_CODE_CLIENT_ERROR_TOO_MANY_REQUESTS == 429

def test_merge_processing_options_1():
    preferred = None
    fallback = None
    actual = quasi_http_utils.merge_processing_options(
        preferred, fallback)
    assert not actual

def test_merge_processing_options_2():
    preferred = {}
    fallback = None
    actual = quasi_http_utils.merge_processing_options(
        preferred, fallback)
    assert actual is preferred

def test_merge_processing_options_3():
    preferred = None
    fallback = {}
    actual = quasi_http_utils.merge_processing_options(
        preferred, fallback)
    assert actual is fallback

def test_merge_processing_options_4():
    preferred = {}
    fallback = {}
    actual = quasi_http_utils.merge_processing_options(
        preferred, fallback)
    expected = SimpleNamespace()
    expected.extra_connectivity_params = {}
    expected.max_headers_size = 0
    expected.max_response_body_size = 0
    expected.timeout_millis = 0
    assert actual == expected

def test_merge_processing_options_5():
    class PreferredCls:
        def __init__(self):
            self.extra_connectivity_params = {
                "scheme": "tht"
            }
            self.max_headers_size = 10
            self.max_response_body_size = -1
            self.timeout_millis = 0
    class FallbackCls:
        def __init__(self):
            self.extra_connectivity_params = {
                "scheme": "htt",
                "two": 2
            }
            self.max_headers_size = 30
            self.max_response_body_size = 40
            self.timeout_millis = -1
    actual = quasi_http_utils.merge_processing_options(
        PreferredCls(), FallbackCls())
    expected = SimpleNamespace()
    expected.extra_connectivity_params = {
        "scheme": "tht",
        "two": 2
    }
    expected.max_headers_size = 10
    expected.max_response_body_size = -1
    expected.timeout_millis = -1
    assert actual == expected

@pytest.mark.parametrize("preferred, fallback1, default_value, expected",  
    [
        (1, None, 20, 1),
        (5, 3, 11, 5),
        (-15, 3, -1, -15),
        (None, 3, -1, 3),
        (None, None, 2, 2),
        (None, None, -8, -8),
        (None, None, 0, 0),
        # remainder is to test parseInt32
        ("89", "67", 10, 89),
        (None, "67", 0, 67),
        (None, None, -7, -7)
    ])
def test_determine_effective_non_zero_integer_option(
        preferred, fallback1, default_value, expected):
    actual = quasi_http_utils._determine_effective_non_zero_integer_option(
        preferred, fallback1, default_value)
    assert actual == expected

@pytest.mark.parametrize("preferred, fallback1, default_value",  
    [
        ([1], "67", 10),
        (None, {"k":3}, 10),
        (None, "6.7", 0)
    ])
def test_determine_effective_non_zero_integer_option_for_errors(
        preferred, fallback1, default_value):
    with pytest.raises(Exception):
        quasi_http_utils._determine_effective_non_zero_integer_option(
            preferred, fallback1, default_value)

@pytest.mark.parametrize("preferred, fallback1, default_value, expected",  
    [
        (None, 1, 30, 1),
        (5, 3, 11, 5),
        (None, 3, -1, 3),
        (None, None, 2, 2),
        (None, None, -8, -8),
        (None, None, 0, 0),
        # remainder is to test parseInt32
        ("89", "67", 10, 89),
        (-90, "67", 0, 67),
        (None, None, "-7", -7)
    ])
def test_determine_effective_positive_integer_option(
        preferred, fallback1, default_value, expected):
    actual = quasi_http_utils._determine_effective_positive_integer_option(
        preferred, fallback1, default_value)
    assert actual == expected

@pytest.mark.parametrize("preferred, fallback1, default_value",  
    [
        ([1], "67", 10),
        (-8, { "k": 3 }, 10),
        (None, "6.7", 0),
        (None, None, 912_144_545_452),
        (None, None, None)
    ])
def test_determine_effective_positive_integer_option_for_errors(
        preferred, fallback1, default_value):
    with pytest.raises(Exception):
        quasi_http_utils._determine_effective_positive_integer_option(
            preferred, fallback1, default_value)

@pytest.mark.parametrize("preferred, fallback, expected",  
    [
        (
            None,
            None,
            {}
        ),
        (
            {},
            {},
            {}
        ),
        (
            {"a": 2, "b": 3},
            None,
            {"a": 2, "b": 3}
        ),
        (
            None,
            {"a": 2, "b": 3},
            {"a": 2, "b": 3}
        ),
        (
            {"a": 2, "b": 3},
            {"c": 4, "d": 3},
            {"a": 2, "b": 3, "c": 4, "d": 3}
        ),
        (
            {"a": 2, "b": 3},
            {"a": 4, "d": 3},
            {"a": 2, "b": 3, "d": 3}
        ),
        (
            {"a": 2},
            {"a": 4, "d": 3},
            {"a": 2, "d": 3}
        )
    ])
def test_determine_effective_options(preferred, fallback, expected):
    actual = quasi_http_utils._determine_effective_options(
        preferred, fallback)
    assert actual == expected
