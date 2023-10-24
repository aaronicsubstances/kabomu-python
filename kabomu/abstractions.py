import abc


class IQuasiHttpAltTransport(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    async def request_serializer(self, connection, request):
        raise NotImplementedError()

    @abc.abstractmethod
    async def response_serializer(self, connection, response):
        raise NotImplementedError()

    @abc.abstractmethod
    async def request_deserializer(self, connection):
        raise NotImplementedError()

    @abc.abstractmethod
    async def response_deserializer(self, connection):
        raise NotImplementedError()


class IQuasiHttpClientTransport(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    async def allocate_connection(self, remote_endpoint, send_options):
        raise NotImplementedError()
    
    @abc.abstractmethod
    async def establish_connection(self, connection):
        raise NotImplementedError()
    
    @abc.abstractmethod
    async def release_connection(self, connection, response):
        raise NotImplementedError()
    
    @abc.abstractmethod
    def get_readable_stream(self, connection):
        raise NotImplementedError()
    
    @abc.abstractmethod
    def get_writable_stream(self, connection):
        raise NotImplementedError()


class IQuasiHttpConnection(metaclass=abc.ABCMeta):

    @property
    @abc.abstractmethod
    def processing_options(self):
        raise NotImplementedError()

    @property
    @abc.abstractmethod
    def environment(self):
        raise NotImplementedError()

    @abc.abstractmethod
    async def schedule_timeout(self, proc):
        raise NotImplementedError()

class QuasiHttpProcessingOptions():
    def __init__(self,
                 extra_connectivity_params=None,
                 timeout_millis=None,
                 max_headers_size=None,
                 max_response_body_size=None):
        self.extra_connectivity_params = extra_connectivity_params
        self.timeout_millis = timeout_millis
        self.max_headers_size = max_headers_size
        self.max_response_body_size = max_response_body_size


class DefaultQuasiHttpRequest():
    def __init__(self,
                 target=None,
                 headers=None,
                 content_length=None,
                 body=None,
                 http_method=None,
                 http_version=None,
                 environment=None):
        self.target = target
        self.headers = headers
        self.content_length = content_length
        self.body = body
        self.http_method = http_method
        self.http_version = http_version
        self.environment = environment

    async def release(self):
        body = self.body
        if body:
            await body.aclose()


class DefaultQuasiHttpResponse():
    def __init__(self,
                 status_code=None,
                 headers=None,
                 content_length=None,
                 body=None,
                 http_status_message=None,
                 http_version=None,
                 environment=None):
        self.status_code = status_code
        self.headers = headers
        self.content_length = content_length
        self.body = body
        self.http_status_message = http_status_message
        self.http_version = http_version
        self.environment = environment

    async def release(self):
        body = self.body
        if body:
            await body.aclose()


class IQuasiHttpServerTransport(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    async def release_connection(self, connection):
        raise NotImplementedError()
    
    @abc.abstractmethod
    def get_readable_stream(self, connection):
        raise NotImplementedError()
    
    @abc.abstractmethod
    def get_writable_stream(self, connection):
        raise NotImplementedError()


class IQuasiHttpApplication(metaclass=abc.ABCMeta):

    @abc.abstractmethod
    async def process_request(self, request):
        raise NotImplementedError()

class DefaultTimeoutResult:
    def __init__(self,
                 response=None,
                 timeout=True,
                 error=None):
        self.response = response
        self.timeout = timeout
        self.error = error
