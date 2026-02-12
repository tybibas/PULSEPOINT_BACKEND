import http.server
import socketserver
import os

PORT = int(os.environ.get("PORT", 8080))

class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b"""
        <html>
        <head>
            <title>QuantiFire IDE V3 Backend</title>
            <style>
                body { font-family: sans-serif; text-align: center; padding: 50px; background: #1a1a1a; color: #fff; }
                h1 { color: #4ade80; }
                .status { background: #333; padding: 20px; border-radius: 8px; display: inline-block; margin-top: 20px; }
            </style>
        </head>
        <body>
            <h1>QuantiFire Backend Active</h1>
            <p>This deployment hosts the Python execution environment.</p>
            <div class="status">
                Status: <strong>Running</strong><br>
                Environment: Railway<br>
                Worker Job: Modal
            </div>
        </body>
        </html>
        """)

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print(f"Serving at port {PORT}")
    httpd.serve_forever()
