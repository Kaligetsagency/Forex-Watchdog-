import time
import os
from flask import Flask, jsonify, render_template, request
from deriv_api import DerivAPI
from strategy import calculate_indicators, detect_trend, calculate_trade_levels

# TARGET_MARKET configuration
# The user can set this variable to "synthetic_index", "forex", or "cryptocurrency"
TARGET_MARKET = os.getenv("TARGET_MARKET", "synthetic_index")

app = Flask(__name__)
app = app # Alias for Vercel
application = app # Alias for Vercel
handler = app # Alias for Vercel

def perform_scan(target_market):
    """Performs a single scan of all symbols in the target market."""
    api = DerivAPI()
    results = []

    try:
        api.connect()
        if not api.authorize():
            print("Running in scan-only mode (unauthorized). Some symbols might not be available.")

        print(f"Fetching active symbols for market: {target_market}")
        symbols = api.get_active_symbols(target_market)

        if not symbols:
            print(f"No symbols found for market: {target_market}")
            return {"error": f"No symbols found for market: {target_market}"}

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

                # Check for zero distance to avoid division by zero
                if sl_distance == 0:
                    print(f"[{symbol}] Skipping: Stop Loss distance is zero.")
                    continue

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
                        "entry": round(entry, 5),
                        "sl": round(sl, 5),
                        "tp": round(tp, 5),
                        "rr": round(tp_distance/sl_distance, 2)
                    })
            else:
                print(f"[{symbol}] No clear trend detected.")

            # Rate limiting - shorter delay for web response responsiveness
            time.sleep(0.5)

        return {"market": target_market, "opportunities": results, "count": len(results)}

    except Exception as e:
        print(f"An error occurred: {e}")
        return {"error": str(e)}
    finally:
        api.disconnect()

@app.route("/")
def index():
    """Renders the dashboard UI."""
    return render_template("index.html")

@app.route("/scan")
def scan():
    """Endpoint for the dashboard to trigger a scan."""
    market = request.args.get("market", TARGET_MARKET)
    report = perform_scan(market)
    return jsonify(report)

if __name__ == "__main__":
    # For local development
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
