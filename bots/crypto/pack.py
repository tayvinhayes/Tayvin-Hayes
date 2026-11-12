import json, sys
src, out = sys.argv[1], sys.argv[2]
def sig(x, n=6):
    s = float(f'{x:.{n}g}'); return int(s) if s == int(s) else s
pack = {}
for pid, key in [('BTC-USD', 'BTC'), ('ETH-USD', 'ETH'), ('SOL-USD', 'SOL')]:
    j = json.load(open(f'{src}/{pid}.json')); t, o = j['t'], j['ohlc']
    # keep the longest unbroken daily run that ends today
    i = len(t) - 1
    while i > 0 and t[i] - t[i-1] == 86400: i -= 1
    t, o = t[i:], o[i:]
    assert all(t[k+1] - t[k] == 86400 for k in range(len(t)-1))
    pack[key] = {'t0': t[0], 'o': [sig(r[0]) for r in o], 'h': [sig(r[1]) for r in o], 'l': [sig(r[2]) for r in o], 'c': [sig(r[3]) for r in o]}
    print(key, len(t), 'days from', t[0])
open(out, 'w').write('const PRICES = ' + json.dumps(pack, separators=(',', ':')) + ';')
