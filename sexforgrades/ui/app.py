"""Web UI server for SexForGrades."""
from http.server import HTTPServer, SimpleHTTPRequestHandler
import os


class SLEHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=os.path.join(os.path.dirname(__file__), '../../static'), **kwargs)

    def log_message(self, *args):
        pass


def serve(port=8080):
    server = HTTPServer(('127.0.0.1', port), SLEHandler)
    print(f"SexForGrades UI at http://127.0.0.1:{port}")
    server.serve_forever()
