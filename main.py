import time
from deriv_api import DerivAPI
from strategy import calculate_indicators, detect_trend, calculate_trade_levels

# TARGET_MARKET configuration
# Options: "synthetic_index", "forex", "cryptocurrency"
TARGET_MARKET = "synthetic_index"

def main():
    api = DerivAPI()

    try:
        api.connect()
        if not api.authorize():
            print("Running in scan-only mode (unauthorized). Some symbols might not be available.")

        print(f"Fetching active symbols for market: {TARGET_MARKET}")
        symbols = api.get_active_symbols(TARGET_MARKET)

        if not symbols:
            print(f"No symbols found for market: {TARGET_MARKET}")
            return

        print(f"Found {len(symbols)} symbols. Starting scan...")

        while True:
            for symbol in symbols:
                print(f"Scanning {symbol}...")

                # Fetch candle data (15-minute timeframe)
                candles = api.get_candles(symbol, granularity=900, count=300)

                if not candles:
                    print(f"Could not fetch data for {symbol}. Skipping.")
                    time.sleep(1)
                    continue

                # Process data through strategy
                df = calculate_indicators(candles)
                trend = detect_trend(df)

                if trend:
                    entry, sl, tp = calculate_trade_levels(df, trend)

                    # Risk/Reward Filter
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
                        print(f"Risk/Reward Ratio: {tp_distance/sl_distance:.2f}")
                else:
                    print(f"[{symbol}] No clear trend detected.")

                # Respect rate limits
                time.sleep(1.5)

            print("Completed one full scan of all symbols. Restarting...")
            time.sleep(5)

    except KeyboardInterrupt:
        print("Bot stopped by user.")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        api.disconnect()

if __name__ == "__main__":
    main()
