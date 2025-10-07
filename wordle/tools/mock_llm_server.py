"""Simple mock LLM HTTP server for contributors.

Usage:
    python tools/mock_llm_server.py

Listens on http://localhost:8080/predict and accepts POST JSON {"messages": [...]}
Responds with JSON {"guess": "arise"} or a heuristic 5-letter word from the messages.
"""
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import random

SAMPLE_GUESSES = ["arise", "adieu", "crate", "slate", "shine", "crane"]

class Handler(BaseHTTPRequestHandler):
    def _set_headers(self, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'application/json')
        self.end_headers()

    def do_POST(self):
        print(f"Received POST {self.path} from {self.client_address}")
        if self.path != '/predict':
            self._set_headers(404)
            self.wfile.write(json.dumps({"error": "Not found"}).encode())
            return

        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode('utf-8')
        try:
            payload = json.loads(body) if body else {}
        except Exception:
            payload = {}

        # naive heuristic: pick a sample guess, or if messages provided, try to pick a word mentioned
        guess = None
        messages = payload.get('messages') if isinstance(payload, dict) else None
        if messages and isinstance(messages, list):
            # search for a 5-letter token in the content, but skip the literal
            # token 'guess' (and a few common filler words) which can appear
            # in assistant prompts. Prefer alphabetic tokens only.
            stopwords = {"guess", "my", "first", "is", "okay", "lets", "let's", "begin"}
            for m in messages:
                if isinstance(m, dict) and 'content' in m and isinstance(m['content'], str):
                    for raw_token in m['content'].split():
                        token = ''.join(ch for ch in raw_token if ch.isalpha())
                        if len(token) == 5 and token.isalpha() and token.lower() not in stopwords:
                            guess = token.lower()
                            break
                    if guess:
                        break

        if not guess:
            guess = random.choice(SAMPLE_GUESSES)

        self._set_headers(200)
        self.wfile.write(json.dumps({"guess": guess}).encode())


if __name__ == '__main__':
    server_address = ('', 8080)
    # allow address reuse to avoid TIME_WAIT port binding issues
    class ReuseHTTPServer(HTTPServer):
        allow_reuse_address = True

    httpd = ReuseHTTPServer(server_address, Handler)
    print('Mock LLM server running at http://localhost:8080/predict')
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print('\nShutting down (KeyboardInterrupt)')
    except Exception as e:
        print('Server error:', e)
    finally:
        try:
            httpd.server_close()
        except Exception:
            pass
