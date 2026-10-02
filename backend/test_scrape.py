import ipaddress
import socket
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from unittest import mock

from flask import Flask
from flask_login import LoginManager

from routes import scrape
from routes.scrape import scrape_bp


class _ProductPageHandler(BaseHTTPRequestHandler):
    hosts = []

    def do_GET(self):
        self.hosts.append(self.headers["Host"])
        body = b"<html><head><title>Test product</title></head></html>"
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


class ScrapeTestCase(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.config.update(SECRET_KEY="test-secret", TESTING=True, LOGIN_DISABLED=True)
        LoginManager(self.app)
        self.app.register_blueprint(scrape_bp)
        self.client = self.app.test_client()

        _ProductPageHandler.hosts = []
        self.server = HTTPServer(("127.0.0.1", 0), _ProductPageHandler)
        self.port = self.server.server_address[1]
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()

    def test_rejects_internal_address_up_front(self):
        response = self.client.post("/api/scrape", json={"url": f"http://127.0.0.1:{self.port}/"})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(_ProductPageHandler.hosts, [])

    def test_dns_rebinding_to_internal_address_never_connects(self):
        real_getaddrinfo = socket.getaddrinfo
        calls = []

        def rebinding_getaddrinfo(host, port=None, *args, **kwargs):
            if host != "rebind.test":
                return real_getaddrinfo(host, port, *args, **kwargs)
            calls.append(host)
            # public for the up-front check, internal for every lookup after it
            ip = "93.184.215.14" if len(calls) == 1 else "127.0.0.1"
            return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (ip, port or 0))]

        with mock.patch("socket.getaddrinfo", rebinding_getaddrinfo):
            response = self.client.post("/api/scrape", json={"url": f"http://rebind.test:{self.port}/"})

        self.assertEqual(response.status_code, 400)
        self.assertGreater(len(calls), 1)
        self.assertEqual(_ProductPageHandler.hosts, [])

    def test_connects_to_checked_address_with_original_host(self):
        # pretend shop.test is public and lives at 127.0.0.1, without any real DNS for it:
        # the request can only arrive if the connection goes to the checked address
        def resolve(hostname):
            return [ipaddress.ip_address("127.0.0.1")] if hostname == "shop.test" else None

        with mock.patch.object(scrape, "resolve_public_ips", resolve):
            response = self.client.post("/api/scrape", json={"url": f"http://shop.test:{self.port}/"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["title"], "Test product")
        self.assertEqual(_ProductPageHandler.hosts, [f"shop.test:{self.port}"])


if __name__ == "__main__":
    unittest.main()
