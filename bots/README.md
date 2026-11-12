# Bots

Two tools, each published as a Claude artifact. This folder holds their source.

## Crypto Strategy Lab (`crypto/`)

Backtests three trading rules (moving-average cross, breakout, RSI dip buy) on real Coinbase daily prices for BTC, ETH and SOL, after fees, against buy and hold, and shows each rule's signal at the latest close.

The prices are baked into the page, so signals are as of the day the data was downloaded. To refresh:

```sh
cd bots/crypto
mkdir -p data
python3 fetch_candles.py data          # needs network access to api.exchange.coinbase.com
python3 pack.py data prices.js
python3 -c "t=open('template.html').read(); d=open('prices.js').read(); open('crypto-lab.html','w').write(t.replace('/*__PRICES__*/', d))"
```

Then republish `crypto-lab.html` to the same artifact.

Rules for honest results: a signal comes from a day's close and fills at the next day's open; every buy and sell pays the fee you set; slippage and taxes aren't modeled.

## Pick'em Edge Finder (`pickem/`)

You enter a pick'em line (PrizePicks style) and the sportsbook's over and under odds on the same line. It removes the book's margin to get a fair win chance, flags picks above break-even, and builds the best Power and Flex entries with quarter-Kelly stakes. Payout multipliers are editable and should match your app. It never places entries: automating entries breaks the apps' terms.
