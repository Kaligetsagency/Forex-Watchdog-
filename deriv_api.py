import json
import os
import time
import websocket
from typing import List, Dict, Optional

class DerivAPI:
    def __init__(self, token: Optional[str] = None):
        self.api_url = "wss://ws.binaryws.com/websockets/v3?app_id=1089" # Default app_id
        self.token = token or os.getenv("DERIV_TOKEN")
        self.ws = None

    def connect(self):
        """Establishes a connection to the Deriv WebSocket API."""
        try:
            self.ws = websocket.create_connection(self.api_url)
            print("Connected to Deriv API")
        except Exception as e:
            print(f"Failed to connect: {e}")
            raise

    def authorize(self):
        """Authenticates the session using the API token."""
        if not self.token:
            print("No API token provided. Set DERIV_TOKEN environment variable.")
            return False

        request = {"authorize": self.token}
        self.ws.send(json.dumps(request))
        response = json.loads(self.ws.recv())

        if "error" in response:
            print(f"Authorization failed: {response['error']['message']}")
            return False

        print("Authorized successfully")
        return True

    def get_active_symbols(self, target_market: str) -> List[str]:
        """Fetches active symbols for a specific market."""
        request = {
            "active_symbols": "brief",
            "product_type": "basic"
        }
        self.ws.send(json.dumps(request))
        response = json.loads(self.ws.recv())

        if "error" in response:
            print(f"Error fetching active symbols: {response['error']['message']}")
            return []

        symbols = []
        for asset in response.get("active_symbols", []):
            if asset.get("market") == target_market:
                symbols.append(asset.get("symbol"))

        return symbols

    def get_candles(self, symbol: str, granularity: int = 900, count: int = 500) -> List[Dict]:
        """Fetches historical candle data for a symbol."""
        request = {
            "ticks_history": symbol,
            "adjust_start_time": 1,
            "count": count,
            "end": "latest",
            "granularity": granularity,
            "style": "candles"
        }
        self.ws.send(json.dumps(request))
        response = json.loads(self.ws.recv())

        if "error" in response:
            print(f"Error fetching candles for {symbol}: {response['error']['message']}")
            return []

        return response.get("candles", [])

    def disconnect(self):
        """Closes the WebSocket connection."""
        if self.ws:
            self.ws.close()
            print("Disconnected from Deriv API")
