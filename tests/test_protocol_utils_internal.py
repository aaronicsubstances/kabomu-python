import pytest

from types import SimpleNamespace

from kabomu.abstractions import IQuasiHttpConnection
from kabomu import protocol_utils_internal
from kabomu.errors import QuasiHttpError,\
    QUASI_HTTP_ERROR_REASON_TIMEOUT,\
    QUASI_HTTP_ERROR_REASON_PROTOCOL_VIOLATION

from tests.shared import comparison_utils

async def test_run_timeout_scheduler_1():
    expected = {}
    async def proc():
        return expected
    class TestConnection(IQuasiHttpConnection):
        def environment(self):
            return None
        def processing_options(self):
            return None
        async def schedule_timeout(self, f):
            result = await f()
            return SimpleNamespace(
                timeout=False, response=result)
    actual = await protocol_utils_internal.run_timeout_scheduler(
        TestConnection(), True, proc)
    assert actual is expected

async def test_run_timeout_scheduler_2():
    expected = {}
    async def proc():
        return expected
    class TestConnection(IQuasiHttpConnection):
        def environment(self):
            return None
        def processing_options(self):
            return None
        async def schedule_timeout(self, f):
            result = await f()
            return SimpleNamespace(
                timeout=False, response=result)
    actual = await protocol_utils_internal.run_timeout_scheduler(
        TestConnection(), False, proc)
    assert actual is True

async def test_run_timeout_scheduler_3():
    async def proc():
        raise NotImplementedError()
    actual = await protocol_utils_internal.run_timeout_scheduler(
        "tea", False, proc)
    assert actual is None

async def test_run_timeout_scheduler_4():
    async def proc():
        pass
    class TestConnection():
        async def schedule_timeout(self, f):
            pass
    actual = await protocol_utils_internal.run_timeout_scheduler(
        TestConnection(), True, proc)
    assert actual is None

async def test_run_timeout_scheduler_5():
    async def proc():
        pass
    class TestConnection:
        async def schedule_timeout(self, f):
            return SimpleNamespace(timeout=True)
    async def test_routine():
        await protocol_utils_internal.run_timeout_scheduler(
            TestConnection(), True, proc)
    actual_ex = await comparison_utils.assert_throws(
        test_routine, QuasiHttpError)
    assert str(actual_ex) == "send timeout"
    assert actual_ex.reason_code == QUASI_HTTP_ERROR_REASON_TIMEOUT

async def test_run_timeout_scheduler_6():
    async def proc():
        pass
    class TestConnection:
        async def schedule_timeout(self, f):
            return SimpleNamespace(timeout=True)
    async def test_routine():
        await protocol_utils_internal.run_timeout_scheduler(
            TestConnection(), False, proc)
    actual_ex = await comparison_utils.assert_throws(
        test_routine, QuasiHttpError)
    assert str(actual_ex) == "receive timeout"
    assert actual_ex.reason_code == QUASI_HTTP_ERROR_REASON_TIMEOUT

async def test_run_timeout_scheduler_7():
    async def proc():
        pass
    class TestConnection:
        async def schedule_timeout(self, f):
            return SimpleNamespace(timeout=True,
                                   error=ValueError("risk"))
    async def test_routine():
        await protocol_utils_internal.run_timeout_scheduler(
            TestConnection(), False, proc)
    actual_ex = await comparison_utils.assert_throws(
        test_routine, ValueError)
    assert str(actual_ex) == "risk"

@pytest.mark.parametrize("v, allow_space, expected",
    [
        ("x.n", False, True),
        ("x\n", False, False),
        ("yd\u00c7ea", True, False),
        ("x m", True, True),
        ("x m", False, False),
        ("x-yio", True, True),
        ("x-yio", False, True),
        ("x", True, True),
        ("x", False, True),
        (" !@#$%^&*()_+=-{}[]|\\:;\"'?/>.<,'", False, False),
        ("!@#$%^&*()_+=-{}[]|\\:;\"'?/>.<,'", False, True),
        (" !@#$%^&*()_+=-{}[]|\\:;\"'?/>.<,'", True, True)
    ])
def test_contains_only_printable_ascii_chars(v, allow_space, expected):
    actual = protocol_utils_internal.contains_only_printable_ascii_chars(
        v, allow_space)
    assert actual == expected

@pytest.mark.parametrize("v, expected",
    [
        ("x\n", False),
        ("yd\u00c7ea", False),
        ("x m", False),
        ("xmX123abcD", True),
        ("xm", True),
        ("x-yio", True),
        ("x:yio", False),
        ("123", True),
        ("x", True)
    ])
def test_contains_only_header_name_chars(v, expected):
    actual = protocol_utils_internal.contains_only_header_name_chars(v)
    assert actual == expected

def test_validate_http_header_section_1():
    csv_data = [
        ["GET", "/", "HTTP/1.0", "24"]
    ]
    protocol_utils_internal.validate_http_header_section(
        False, csv_data)

def test_validate_http_header_section_2():
    csv_data = [
        ["HTTP/1.0", "204", "No Content", "-10"],
        ["Content-Type", "application/json; charset=UTF8"],
        ["Transfer-Encoding", "chunked"],
        ["Date", "Tue, 15 Nov 1994 08:12:31 GMT"],
        ["Authorization", "Basic QWxhZGRpbjpvcGVuIHNlc2FtZQ=="],
        ["User-Agent", "Mozilla/5.0 (X11; Linux x86_64; rv:12.0) Gecko/20100101 Firefox/12.0"]
    ]
    protocol_utils_internal.validate_http_header_section(
        True, csv_data)

@pytest.mark.parametrize("is_response, csv_data, expected_error_message",
    [
        (
            True,
            [
                ["HTTP/1 0", "200", "OK", "-10"]
            ],
            "quasi http status line field contains spaces"
        ),
        (
            False,
            [
                ["HTTP/1 0", "20 4", "OK", "-10"]
            ],
            "quasi http request line field contains spaces"
        ),
        (
            True,
            [
                ["HTTP/1.0", "200", "OK", "-1 0"]
            ],
            "quasi http status line field contains spaces"
        ),
        (
            True,
            [
                ["HTTP/1.0", "200", "OK", "-51"],
                ["Content:Type", "application/json; charset=UTF8"]
            ],
            "quasi http header name contains characters other than hyphen"
        ),
        (
            False,
            [
                ["HTTP/1.0", "200", "OK", "51"],
                ["Content-Type", "application/json; charset=UTF8\n"]
            ],
            "quasi http header value contains newlines"
        )
    ])
def test_validate_http_header_section_for_errors(
        is_response, csv_data, expected_error_message):
    with pytest.raises(QuasiHttpError) as actual_ex:
        protocol_utils_internal.validate_http_header_section(
            is_response, csv_data)
    assert actual_ex.value.reason_code == QUASI_HTTP_ERROR_REASON_PROTOCOL_VIOLATION
    assert expected_error_message in str(actual_ex.value)

@pytest.mark.parametrize("is_response, req_or_status_line, remaining_headers, expected",
    [
        (
            False,
            [
                "GET",
                "/home/index?q=results",
                "HTTP/1.1",
                -1
            ],
            {
                "Content-Type": [ "text/plain" ]
            },
            '"GET","/home/index?q=results","HTTP/1.1","-1"\n' +
                '"Content-Type","text/plain"\n'
        ),
        (
            True,
            ["HTTP/1.1", 200, "OK", 12],
            {
                "Content-Type": ["text/plain", "text/csv"],
                "Accept": ["text/html"],
                "Accept-Charset": ["utf-8"]
            },
            '"HTTP/1.1","200","OK","12"\n' +
                '"Content-Type","text/plain","text/csv"\n' +
                '"Accept","text/html"\n' +
                '"Accept-Charset","utf-8"\n'
        ),
        (
            False,
            [None, None, None, 0],
            None,
            '"","","","0"\n'
        )
    ])
def test_encode_quasi_http_headers(
        is_response, req_or_status_line, remaining_headers,
        expected):
    actual = protocol_utils_internal.encode_quasi_http_headers(
        is_response, req_or_status_line, remaining_headers)
    assert actual.decode() == expected

@pytest.mark.parametrize("is_response, req_or_status_line, remaining_headers, expected",
    [
        (
            False,
            ["GET", "/home/index?q=results", "HTTP/1.1", "-1"],
            {
                "": ["text/plain"]
            },
            "quasi http header name cannot be empty"
        ),
        (
            True,
            ["HTTP/1.1", 400, "Bad Request", 12],
            {
                "Content-Type": ["", "text/csv"]
            },
            "quasi http header value cannot be empty"
        ),
        (
            False,
            ["GET or POST", None, None, 0],
            None,
            "quasi http request line field contains spaces"
        ),
        (
            False,
            ["GET", None, None, "0 ior 1"],
            None,
            "quasi http request line field contains spaces"
        ),
        (
            True,
            ["HTTP 1.1", "200", "OK", "0"],
            None,
            "quasi http status line field contains spaces"
        )
    ])
def test_encode_quasi_http_headers_for_errors(
        is_response, req_or_status_line, remaining_headers,
        expected):
    with pytest.raises(QuasiHttpError) as actual_ex:
        protocol_utils_internal.encode_quasi_http_headers(
            is_response, req_or_status_line, remaining_headers)
    assert actual_ex.value.reason_code == QUASI_HTTP_ERROR_REASON_PROTOCOL_VIOLATION
    assert expected in str(actual_ex.value)

@pytest.mark.parametrize("is_response, s, expected_headers, expected_req_or_status_line",
    [
        (
            False,
            "GET,/home/index?q=results,HTTP/1.1,-1\n" +
                "Content-Type,text/plain\n",
            {
                "content-type": ["text/plain"]
            },
            ["GET", "/home/index?q=results", "HTTP/1.1", "-1"]
        ),
        (
            True,
            "HTTP/1.1,200,OK,12\n" +
                "Content-Type,text/plain,text/csv\n" +
                "content-type,application/json\n" +
                "\r\n" +
                "ignored\n" +
                "Accept,text/html\n" +
                "Accept-Charset,utf-8\n",
            {
                "content-type": [
                    "text/plain", "text/csv", "application/json"],
                "accept": ["text/html"],
                "accept-charset": ["utf-8"]
            },
            ["HTTP/1.1", "200", "OK", "12"]
        ),
        (
            False,
            "\"\",\"\",\"\",0\n",
            {},
            ["", "", "", "0"]
        )
    ])
def test_decode_quasi_http_headers(is_response, s, expected_headers,
                                   expected_req_or_status_line):
    headers_receiver = {}
    actual_req_or_status_line = protocol_utils_internal.decode_quasi_http_headers(
        is_response, s.encode(), headers_receiver)
    assert actual_req_or_status_line == expected_req_or_status_line
    assert headers_receiver == expected_headers

@pytest.mark.parametrize("is_response, s, expected_error_message",
    [
        (
            False,
            "\"k\n,lopp",
            "invalid quasi http headers"
        ),
        (
            False,
            "",
            "invalid quasi http headers"
        ),
        (
            True,
            "HTTP/1.1,200",
            "invalid quasi http status line"
        ),
        (
            False,
            "GET,HTTP/1.1,",
            "invalid quasi http request line"
        )
    ])
def test_decode_quasi_http_headers_for_errors(is_response, s,
                                              expected_error_message):
    with pytest.raises(QuasiHttpError) as actual_ex:
        protocol_utils_internal.decode_quasi_http_headers(
            is_response, s.encode(), {})
    assert actual_ex.value.reason_code == QUASI_HTTP_ERROR_REASON_PROTOCOL_VIOLATION
    assert expected_error_message in str(actual_ex.value)
