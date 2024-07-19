import io
import time
from typing import Callable, Dict
from destinations import MetricsDestination
from collectors import MetricsCollector


class WSGIMetricsMiddleware:
    def __init__(self, app: Callable, metrics_collector: MetricsCollector):
        self.app = app
        self.metrics_collector = metrics_collector

    def __call__(self, environ: Dict, start_response: Callable):
        start_time = time.time()

        # Collect request headers size
        headers_size = sum(len(key) + len(value) for key, value in environ.items() if key.startswith('HTTP_'))
        self.metrics_collector.record("request_headers_size", headers_size)

        # Collect request body size
        content_length = environ.get('CONTENT_LENGTH')
        if content_length:
            self.metrics_collector.record("request_body_size", int(content_length))
        else:
            # If CONTENT_LENGTH is not set, we need to read the body to determine its size
            body = environ['wsgi.input'].read()
            body_size = len(body)
            self.metrics_collector.record("request_body_size", body_size)
            # Create a new file-like object with the body content for the WSGI app to read
            environ['wsgi.input'] = io.BytesIO(body)

        def custom_start_response(status, headers, exc_info=None):
            self.metrics_collector.record("response_status", status.split()[0])
            return start_response(status, headers, exc_info)

        response_iter = self.app(environ, custom_start_response)
        response_size = 0

        def response_wrapper():
            nonlocal response_size
            for chunk in response_iter:
                response_size += len(chunk)
                yield chunk
            self.metrics_collector.record("response_size", response_size)

        wrapped_response = response_wrapper()

        end_time = time.time()
        self.metrics_collector.record("request_duration", end_time - start_time)
        self.metrics_collector.record("request_method", environ["REQUEST_METHOD"])
        self.metrics_collector.record("request_path", environ["PATH_INFO"])

        return wrapped_response


class ASGIMetricsMiddleware:
    def __init__(self, app: Callable, metrics_collector: MetricsCollector):
        self.app = app
        self.metrics_collector = metrics_collector

    async def __call__(self, scope: Dict, receive: Callable, send: Callable):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        start_time = time.time()

        # Collect request headers size
        headers_size = sum(len(name) + len(value) for name, value in scope.get('headers', []))
        self.metrics_collector.record("request_headers_size", headers_size)

        # Prepare to collect request body size
        body_size = 0
        response_size = 0

        async def wrapped_receive():
            nonlocal body_size
            message = await receive()
            if message['type'] == 'http.request':
                body_size += len(message.get('body', b''))
            return message

        async def wrapped_send(message):
            nonlocal response_size
            if message["type"] == "http.response.start":
                self.metrics_collector.record("response_status", message["status"])
            elif message["type"] == "http.response.body":
                response_size += len(message.get("body", b""))
                if message.get("more_body", False) is False:
                    # This is the last body message, so we can now record the total body size
                    self.metrics_collector.record("request_body_size", body_size)
                    self.metrics_collector.record("response_size", response_size)
            await send(message)

        await self.app(scope, wrapped_receive, wrapped_send)

        end_time = time.time()
        self.metrics_collector.record("request_duration", end_time - start_time)
        self.metrics_collector.record("request_method", scope["method"])
        self.metrics_collector.record("request_path", scope["path"])