import ccxt
import pandas as pd
import numpy as np

# Configurações da API Binance
API_KEY = "WGppsqHCM893qJD9IeAx20SzEw5Ewdb1IzUBzS0r9gHZRiAP8LPbtK3l1RWqwQKZ"
API_SECRET = "QrPiz5LYJS20oRJZb3JX7W5Ts7Bd7WrZ36PlG389JaHrfxHv0Th0Jd0uTZd345cB"

# Configuração do RSI
RSI_LENGTH = 27
LOOKBACK_RIGHT = 100
LOOKBACK_LEFT = 8
RANGE_LOWER = 8
RANGE_UPPER = 60

# Conectar à Binance
exchange = ccxt.binance({
    'apiKey': API_KEY,
    'secret': API_SECRET,
})

def fetch_ohlcv(symbol, timeframe='1h', limit=500):
    """Busca dados OHLCV para o par fornecido."""
    data = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
    df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    return df

def calculate_rsi(df, length):
    """Calcula o RSI com base nos preços de fechamento."""
    delta = df['close'].diff()
    gain = np.where(delta > 0, delta, 0)
    loss = np.where(delta < 0, -delta, 0)
    avg_gain = pd.Series(gain).rolling(window=length).mean()
    avg_loss = pd.Series(loss).rolling(window=length).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def detect_divergences(df, rsi):
    """Detecta divergências bullish e bearish."""
    df['rsi'] = rsi
    bull_divergences = []
    bear_divergences = []
    
    for i in range(LOOKBACK_RIGHT, len(df)):
        # Bullish divergence
        if (
            df['low'][i] < df['low'][i - LOOKBACK_RIGHT] and
            rsi[i] > rsi[i - LOOKBACK_RIGHT] and
            RANGE_LOWER <= i - LOOKBACK_RIGHT <= RANGE_UPPER
        ):
            bull_divergences.append(df.iloc[i]['timestamp'])

        # Bearish divergence
        if (
            df['high'][i] > df['high'][i - LOOKBACK_RIGHT] and
            rsi[i] < rsi[i - LOOKBACK_RIGHT] and
            RANGE_LOWER <= i - LOOKBACK_RIGHT <= RANGE_UPPER
        ):
            bear_divergences.append(df.iloc[i]['timestamp'])
    
    return bull_divergences, bear_divergences

def scan_market():
    """Vasculha todos os pares e detecta divergências."""
    markets = exchange.load_markets()
    results = []
    for symbol in markets.keys():
        try:
            df = fetch_ohlcv(symbol)
            rsi = calculate_rsi(df, RSI_LENGTH)
            bull_div, bear_div = detect_divergences(df, rsi)
            if bull_div or bear_div:
                results.append({
                    'symbol': symbol,
                    'bullish_divergences': bull_div,
                    'bearish_divergences': bear_div,
                })
        except Exception as e:
            print(f"Erro ao processar {symbol}: {e}")
    return results

# Executar o scanner
if __name__ == "__main__":
    divergences = scan_market()
    for result in divergences:
        print(f"Par: {result['symbol']}")
        if result['bullish_divergences']:
            print(f"  Divergências Bullish: {result['bullish_divergences']}")
        if result['bearish_divergences']:
            print(f"  Divergências Bearish: {result['bearish_divergences']}")
