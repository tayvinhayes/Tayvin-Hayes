#!/usr/bin/env python3
"""Biojacked paper-trading bot: trades fake money on live Coinbase prices.

It uses the same rules as the Crypto Strategy Lab backtester. At each daily
close (midnight UTC) it checks the rule, and if the rule says to buy or sell,
it records a pretend trade at the current price and pays the fee. Nothing is
ever bought or sold for real, and no account or API key is needed: it only
reads Coinbase's public prices.

Run it:
    python3 paper_bot.py                 check once and show the status
    python3 paper_bot.py --loop          keep running, checking every hour
    python3 paper_bot.py --strategy ma   use a different rule (ma, breakout, rsi)
    python3 paper_bot.py --coin ETH-USD  use a different coin
    python3 paper_bot.py --reset         start over with fresh fake money

Each coin and rule keeps its own record in this folder:
    paper_BTC-USD_breakout.json   the account (cash, coins, start date)
    paper_BTC-USD_breakout.csv    every pretend trade
Only the Python standard library is used. Python 3.8 or newer.
"""
import argparse
import csv
import datetime as dt
import json
import os
import sys
import time
import urllib.error
import urllib.request

API = "https://api.exchange.coinbase.com"
HERE = os.path.dirname(os.path.abspath(__file__))
RULES = {
    "breakout": "Buy a close above the {enter}-day high, sell a close below the {exit}-day low",
    "ma": "Own the coin while the {fast}-day average is above the {slow}-day average",
    "rsi": "Buy when the 14-day RSI drops below {lo}, sell when it rises above {hi}",
}
DEFAULTS = {"breakout": {"enter": 20, "exit": 10}, "ma": {"fast": 50, "slow": 200}, "rsi": {"lo": 30, "hi": 55}}


# ---------- prices ----------
def get_json(path, tries=4):
    for attempt in range(tries):
        try:
            req = urllib.request.Request(API + path, headers={"User-Agent": "paper-bot/1.0"})
            with urllib.request.urlopen(req, timeout=20) as r:
                return json.load(r)
        except (urllib.error.URLError, TimeoutError, ValueError) as e:
            if attempt == tries - 1:
                if "CERTIFICATE_VERIFY_FAILED" in str(e):
                    raise RuntimeError("Python can't verify Coinbase's security certificate. On a Mac with Python from python.org, "
                                       "open Applications > Python 3.x and double-click 'Install Certificates.command', then run this again.")
                raise RuntimeError("Couldn't reach Coinbase (" + str(e) + "). Check your internet connection.")
            time.sleep(2 ** attempt)


def daily_candles(coin):
    """The last 300 finished days, oldest first: (day, open, high, low, close)."""
    rows = get_json("/products/" + coin + "/candles?granularity=86400")
    today = dt.datetime.now(dt.timezone.utc).date()
    out = []
    for ts, lo, hi, op, cl, _vol in rows:
        day = dt.datetime.fromtimestamp(ts, dt.timezone.utc).date()
        if day < today:  # today's candle is still forming
            out.append((day, float(op), float(hi), float(lo), float(cl)))
    out.sort()
    return out


def live_price(coin):
    return float(get_json("/products/" + coin + "/ticker")["price"])


# ---------- the rules (same as the backtester) ----------
def sma(vals, n):
    out, s = [None] * len(vals), 0.0
    for i, v in enumerate(vals):
        s += v
        if i >= n:
            s -= vals[i - n]
        if i >= n - 1:
            out[i] = s / n
    return out


def rsi(closes, n=14):
    out, g, l = [None] * len(closes), 0.0, 0.0
    for i in range(1, len(closes)):
        ch = closes[i] - closes[i - 1]
        up, dn = max(ch, 0.0), max(-ch, 0.0)
        if i <= n:
            g += up
            l += dn
            if i == n:
                g, l = g / n, l / n
                out[i] = 100.0 if l == 0 else 100 - 100 / (1 + g / l)
        else:
            g = (g * (n - 1) + up) / n
            l = (l * (n - 1) + dn) / n
            out[i] = 100.0 if l == 0 else 100 - 100 / (1 + g / l)
    return out


def money(v):
    return "${:,.2f}".format(v) if abs(v) < 100 else "${:,.0f}".format(v)


def decide(strategy, p, candles):
    """Whether the rule wants to own the coin after the latest close, and why, in plain words."""
    c = [x[4] for x in candles]
    h = [x[2] for x in candles]
    lo_ = [x[3] for x in candles]
    last = len(c) - 1
    if strategy == "ma":
        f, s = sma(c, p["fast"]), sma(c, p["slow"])
        if s[last] is None:
            raise SystemExit("Not enough price history for a {}-day average.".format(p["slow"]))
        own = f[last] > s[last]
        why = "{}-day average {} is {} the {}-day {}".format(p["fast"], money(f[last]), "above" if own else "below", p["slow"], money(s[last]))
        return own, why
    if strategy == "breakout":
        own = False
        for i in range(len(c)):
            if i < max(p["enter"], p["exit"]):
                continue
            hh, ll = max(h[i - p["enter"]:i]), min(lo_[i - p["exit"]:i])
            if not own and c[i] > hh:
                own = True
            elif own and c[i] < ll:
                own = False
        if own:
            why = "sells on a daily close below {}, the {}-day low".format(money(min(lo_[-p["exit"]:])), p["exit"])
        else:
            why = "buys on a daily close above {}, the {}-day high".format(money(max(h[-p["enter"]:])), p["enter"])
        return own, why
    r = rsi(c)
    own = False
    for v in r:
        if v is None:
            continue
        if not own and v < p["lo"]:
            own = True
        elif own and v > p["hi"]:
            own = False
    why = "RSI is {:.0f}; it {}".format(r[last], "sells above {}".format(p["hi"]) if own else "buys below {}".format(p["lo"]))
    return own, why


# ---------- the paper account ----------
def files(coin, strategy):
    base = os.path.join(HERE, "paper_{}_{}".format(coin, strategy))
    return base + ".json", base + ".csv"


def load(path, cash, fee):
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return {"cash": cash, "units": 0.0, "fee": fee, "start_cash": cash, "start_price": None, "started": None, "acted_on": None, "trades": 0}


def save(path, acct):
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(acct, f, indent=2)
    os.replace(tmp, path)


def log_trade(path, row):
    new = not os.path.exists(path)
    with open(path, "a", newline="") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["time_utc", "action", "price", "coins", "dollars", "fee", "account_value"])
        w.writerow(row)


def check(coin, strategy, p, acct, json_path, csv_path):
    candles = daily_candles(coin)
    price = live_price(coin)
    now = dt.datetime.now(dt.timezone.utc)
    last_close_day = candles[-1][0].isoformat()
    if acct["start_price"] is None:
        acct["start_price"], acct["started"] = price, now.isoformat(timespec="seconds")
    want, why = decide(strategy, p, candles)
    own = acct["units"] > 0
    action = None
    if acct["acted_on"] != last_close_day and want != own:  # one decision per daily close
        fee = acct["fee"] / 100
        if want:
            spend = acct["cash"]
            acct["units"] = spend * (1 - fee) / price
            acct["cash"] = 0.0
            action = ("BUY", spend * fee, spend)
        else:
            gross = acct["units"] * price
            acct["cash"] = gross * (1 - fee)
            acct["units"] = 0.0
            action = ("SELL", gross * fee, gross)
        acct["trades"] += 1
    acct["acted_on"] = last_close_day
    value = acct["cash"] + acct["units"] * price
    if action:
        log_trade(csv_path, [now.isoformat(timespec="seconds"), action[0], round(price, 2), round(acct["units"], 8), round(action[2], 2), round(action[1], 2), round(value, 2)])
    save(json_path, acct)
    hold = acct["start_cash"] * (1 - acct["fee"] / 100) * price / acct["start_price"]
    ticker = coin.split("-")[0]
    print("")
    print("{}  {} {}".format(now.strftime("%Y-%m-%d %H:%M UTC"), ticker, money(price)))
    if action:
        print("  >>> PAPER {} at {} (fee {})".format(action[0], money(price), money(action[1])))
    print("  Rule:     {} ({})".format(strategy, RULES[strategy].format(**p)))
    print("  Signal:   {} - {}".format("OWN IT" if want else "IN CASH", why))
    print("  Holding:  {}".format("{:.6f} {}".format(acct["units"], ticker) if acct["units"] > 0 else "cash"))
    print("  Value:    {}  (started with {} on {})".format(money(value), money(acct["start_cash"]), acct["started"][:10]))
    print("  Holding {} instead would be worth {}. Pretend trades so far: {}".format(ticker, money(hold), acct["trades"]))


def main():
    ap = argparse.ArgumentParser(description="Paper-trade a crypto rule on live Coinbase prices. Fake money only.")
    ap.add_argument("--coin", default="BTC-USD", help="Coinbase pair, like BTC-USD, ETH-USD or SOL-USD (default BTC-USD)")
    ap.add_argument("--strategy", default="breakout", choices=sorted(RULES), help="which rule to follow (default breakout)")
    ap.add_argument("--cash", type=float, default=1000, help="fake starting dollars (default 1000)")
    ap.add_argument("--fee", type=float, default=0.6, help="fee per trade in percent (default 0.6)")
    ap.add_argument("--loop", action="store_true", help="keep running and check every hour")
    ap.add_argument("--every", type=float, default=60, help="minutes between checks with --loop (default 60)")
    ap.add_argument("--reset", action="store_true", help="start over with fresh fake money")
    for k in ("enter", "exit", "fast", "slow", "lo", "hi"):
        ap.add_argument("--" + k, type=int, help=argparse.SUPPRESS)
    a = ap.parse_args()
    coin = a.coin.upper()
    p = dict(DEFAULTS[a.strategy])
    for k in p:
        if getattr(a, k) is not None:
            p[k] = getattr(a, k)
    json_path, csv_path = files(coin, a.strategy)
    if a.reset:
        for f in (json_path, csv_path):
            if os.path.exists(f):
                os.remove(f)
        print("Started over: fresh fake money for {} {}.".format(coin, a.strategy))
    acct = load(json_path, a.cash, a.fee)
    print("Paper trading {} with the {} rule. Fake money only; nothing is bought or sold for real.".format(coin, a.strategy))
    while True:
        try:
            check(coin, a.strategy, p, acct, json_path, csv_path)
        except RuntimeError as e:
            print("\n" + str(e))
            if not a.loop:
                sys.exit(1)
        if not a.loop:
            break
        print("  Next check in {:g} minutes. Press Ctrl+C to stop.".format(a.every))
        try:
            time.sleep(max(1.0, a.every * 60))
        except KeyboardInterrupt:
            break
    if a.loop:
        print("\nStopped. Your paper account is saved; run the same command to pick up where you left off.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nStopped. Your paper account is saved; run the same command to pick up where you left off.")
