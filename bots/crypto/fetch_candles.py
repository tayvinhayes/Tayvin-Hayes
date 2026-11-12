import json, sys, time, urllib.request, datetime as dt
out_dir = sys.argv[1]
START = {'BTC-USD': '2015-07-20', 'ETH-USD': '2016-05-18', 'SOL-USD': '2021-06-17'}
end_all = dt.datetime.now(dt.timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
for pid, s in START.items():
    rows = {}
    t = dt.datetime.fromisoformat(s).replace(tzinfo=dt.timezone.utc)
    while t < end_all:
        e = min(t + dt.timedelta(days=299), end_all)
        url = f'https://api.exchange.coinbase.com/products/{pid}/candles?granularity=86400&start={t:%Y-%m-%dT%H:%M:%SZ}&end={e:%Y-%m-%dT%H:%M:%SZ}'
        for attempt in range(4):
            try:
                req = urllib.request.Request(url, headers={'User-Agent': 'backtest-client'})
                data = json.load(urllib.request.urlopen(req, timeout=30)); break
            except Exception as ex:
                time.sleep(2 ** attempt)
        else:
            raise SystemExit(f'failed {url}')
        for ts, lo, hi, op, cl, vol in data:
            rows[ts] = (op, hi, lo, cl)
        t = e + dt.timedelta(days=1)
        time.sleep(0.25)
    ts = sorted(rows)
    # keep only complete days (drop today's partial candle)
    ts = [x for x in ts if x < int(end_all.timestamp())]
    gaps = [(ts[i], ts[i+1]) for i in range(len(ts)-1) if ts[i+1] - ts[i] != 86400]
    json.dump({'id': pid, 't': ts, 'ohlc': [rows[x] for x in ts]}, open(f'{out_dir}/{pid}.json', 'w'))
    print(pid, len(ts), 'days', dt.datetime.utcfromtimestamp(ts[0]).date(), '->', dt.datetime.utcfromtimestamp(ts[-1]).date(), 'gaps', len(gaps), gaps[:3])
