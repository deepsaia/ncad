"""Websocket test for browser live-reload: /ws/livereload sends a boot-id hello on connect.

The live-reload model is reconnect-and-compare: the handler sends one JSON hello frame carrying the
live boot id when a client connects, and the client reloads when a reconnect yields a different id.
The ws route exists only in dev; in production the handler is not mounted (404 on connect).
"""

import json
import tempfile

import pytest
from tornado.httpclient import HTTPClientError
from tornado.testing import AsyncHTTPTestCase, gen_test
from tornado.web import Application
from tornado.websocket import websocket_connect

from ncad.service.api_router import ApiRouter
from ncad.service.ncad_service import make_deps


class _LiveReloadDevTest(AsyncHTTPTestCase):
    """Dev app: the ws route is mounted and sends the hello frame."""

    def get_app(self) -> Application:
        self.deps = make_deps(models_dir=self.get_temp_dir(), examples_dir=None,
                              dev=True, boot_id="boot-dev")
        return Application(ApiRouter().rules(self.deps))

    def get_temp_dir(self) -> str:
        if not hasattr(self, "_tmp"):
            self._tmp = tempfile.mkdtemp()
        return self._tmp

    @gen_test
    async def test_hello_frame_carries_boot_id(self):
        url = f"ws://127.0.0.1:{self.get_http_port()}/ws/livereload"
        conn = await websocket_connect(url)
        message = await conn.read_message()
        conn.close()
        payload = json.loads(message)
        assert payload["type"] == "hello"
        assert payload["boot_id"] == "boot-dev"


class _LiveReloadProdTest(AsyncHTTPTestCase):
    """Production app: the ws route is NOT mounted, so a connect attempt fails."""

    def get_app(self) -> Application:
        deps = make_deps(models_dir=self.get_temp_dir(), examples_dir=None,
                         dev=False, boot_id="boot-prod")
        return Application(ApiRouter().rules(deps))

    def get_temp_dir(self) -> str:
        if not hasattr(self, "_tmp"):
            self._tmp = tempfile.mkdtemp()
        return self._tmp

    @gen_test
    async def test_ws_route_absent_in_production(self):
        url = f"ws://127.0.0.1:{self.get_http_port()}/ws/livereload"
        with pytest.raises(HTTPClientError) as exc:
            await websocket_connect(url)
        assert exc.value.code == 404
