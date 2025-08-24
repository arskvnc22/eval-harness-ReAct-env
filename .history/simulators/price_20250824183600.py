from typing import Dict, Any, Tuple
from hashlib import blake2b

class PriceSimulator:
    """
    Deterministic, side-effect-free simulator for price_lookup capability.
    Returns a mock OHLC summary and a close price derived from (ticker, start, end).
    """
    def __init__(self):
        self._cache = {}  # key: (ticker,start,end) -> obs

    def _key(self, ticker: str, start: str, end: str) -> Tuple[str, str, str]:
        return (ticker.upper(), start, end)

    def _deterministic_price(self, ticker: str, start: str, end: str) -> float:
        h = blake2b(digest_size=8)
        h.update(f"{ticker}|{start}|{end}".encode())
        # bounded to reasonable price range
        return round((int.from_bytes(h.digest(), "big") % 100000) / 100 + 5.0, 2)

    def call(self, args: Dict[str, Any]) -> Dict[str, Any]:
        dr = args["date_range"]
        key = self._key(args["ticker"], dr["start"], dr["end"])
        if key in self._cache:
            return self._cache[key]
        price = self._deterministic_price(*key)
        obs = {
            "ticker": args["ticker"].upper(),
            "start": dr["start"],
            "end": dr["end"],
            "close": price,
            "ohlc": {"open": price - 0.7, "high": price + 1.2, "low": price - 1.5, "close": price}
        }
        self._cache[key] = obs
        return obs

# Singleton for convenience
PRICE_SIMULATOR = PriceSimulator()
