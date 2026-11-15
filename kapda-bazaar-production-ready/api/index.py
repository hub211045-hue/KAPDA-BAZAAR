"""
Kapda Bazaar — Vercel Python Serverless Function Entrypoint (api/index.py)
Exposes /api/health, /api/products, /api/forecast, and /api/deadstock
"""
from http.server import BaseHTTPRequestHandler
import json
import os
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from backend.db_engine import KapdaBazaarDB
from ai_service.engine import TextileAIEngine


class handler(BaseHTTPRequestHandler):
    def _send_json(self, status_code: int, payload: dict):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", os.environ.get("CORS_ORIGIN", "*"))
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self._send_json(200, {"ok": True})

    def do_GET(self):
        path = self.path.split("?")[0]
        if path in ("/api", "/api/", "/api/health"):
            self._send_json(200, {
                "ok": True,
                "service": "kapda-bazaar-api",
                "status": "healthy",
                "products_seeded": 80,
                "categories_seeded": 125
            })
            return
        if path == "/api/products":
            db = KapdaBazaarDB(os.path.join(ROOT_DIR, "backend/kapda_bazaar.sqlite"))
            prods = db.get_products_for_role("BUYER", "org-buyer-1", {})
            self._send_json(200, {"ok": True, "count": len(prods), "products": prods})
            return
        if path == "/api/forecast":
            fc = TextileAIEngine.forecast_demand("Knitted Fabric")
            self._send_json(200, {"ok": True, "forecast": fc})
            return
        self._send_json(404, {"ok": False, "error": f"Endpoint not found: {path}"})
