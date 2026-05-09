import time
import os
from flask import Flask, jsonify
from deriv_api import DerivAPI
from strategy import calculate_indicators, detect_trend, calculate_trade_levels

app = Flask(__name__)

# TARGET_MARKET configuration
# Options: "synthetic_index", "forex", "cryptocurrency"
TARGET_MARKET = os.getenv("TARGET_MARKET", "synthetic_index")

def perform_scan():
    """Performs a single scan of all symbols in the target market."""
    api = DerivAPI()
    results = []

    try:
        api.connect()
        if not api.authorize():
            print("Running in scan-only mode (unauthorized). Some symbols might not be available.")

        print(f"Fetching active symbols for market: {TARGET_MARKET}")
        symbols = api.get_active_symbols(TARGET_MARKET)

        if not symbols:
            print(f"No symbols found for market: {TARGET_MARKET}")
            return {"error": f"No symbols found for market: {TARGET_MARKET}"}

        print(f"Found {len(symbols)} symbols. Starting scan...")

        for symbol in symbols:
            print(f"Scanning {symbol}...")
            # Fetch candle data (15-minute timeframe)
            candles = api.get_candles(symbol, granularity=900, count=300)

            if not candles:
                print(f"Could not fetch data for {symbol}. Skipping.")
                continue

            df = calculate_indicators(candles)
            trend = detect_trend(df)

            if trend:
                entry, sl, tp = calculate_trade_levels(df, trend)
                tp_distance = abs(tp - entry)
                sl_distance = abs(sl - entry)

                if tp_distance <= sl_distance:
                    print(f"[{symbol}] No trade: TP distance is equal to or less than SL distance")
                else:
                    print(f"[{symbol}] Opportunity Found!")
                    print(f"Trend: {trend}")
                    print(f"Entry: {entry}")
                    print(f"Stop Loss: {sl}")
                    print(f"Take Profit: {tp}")

                    results.append({
                        "symbol": symbol,
                        "trend": trend,
                        "entry": entry,
                        "sl": sl,
                        "tp": tp,
                        "rr": round(tp_distance/sl_distance, 2)
                    })
            else:
                print(f"[{symbol}] No clear trend detected.")

            # Rate limiting
            time.sleep(1.0)

        return {"market": TARGET_MARKET, "opportunities": results, "count": len(results)}

    except Exception as e:
        print(f"An error occurred: {e}")
        return {"error": str(e)}
    finally:
        api.disconnect()

@app.route("/")
def index():
    return jsonify({
        "status": "online",
        "market": TARGET_MARKET,
        "usage": "Use /scan to trigger a manual scan."
    })

@app.route("/scan")
def scan():
    """Endpoint for Vercel to trigger a scan."""
    report = perform_scan()
    return jsonify(report)

def local_loop():
    """Continuous loop for local/VPS deployment."""
    print(f"Starting continuous scan for {TARGET_MARKET}...")
    while True:
        report = perform_scan()
        print(f"Scan completed: {report.get('count', 0)} opportunities found.")
        time.sleep(10)

if __name__ == "__main__":
    # If run directly, start the continuous loop
    local_loop()
