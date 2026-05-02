import urllib.request
import json
import pandas as pd
import numpy as np

# 1. 获取并清洗数据 (和之前一样，这次我们拿30天的数据)
url = "https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1d&limit=30"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req) as response:
    data = json.loads(response.read().decode())

df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_asset_volume', 'number_of_trades', 'taker_buy_base', 'taker_buy_quote', 'ignore'])
for col in ['open', 'high', 'low', 'close', 'volume']:
    df[col] = df[col].astype(float)
df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
df.set_index('timestamp', inplace=True)

# 2. 计算 3日均线 (MA_3)
df['MA_3'] = df['close'].rolling(window=3).mean()

# 3. 核心步骤：生成交易信号 (Trading Signals)
# 注意：我们必须拿【昨天的均线】来作为参考线，因为我们做决策时，只能看到之前的数据
df['yesterday_MA_3'] = df['MA_3'].shift(1)

# 初始化信号列，默认为 0 (观望)
df['signal'] = 0

# 当今天的收盘价 > 昨天的3日均线，产生买入信号 (1)
df.loc[df['close'] > df['yesterday_MA_3'], 'signal'] = 1

# 当今天的收盘价 < 昨天的3日均线，产生卖出信号 (-1)
df.loc[df['close'] < df['yesterday_MA_3'], 'signal'] = -1

# 4. 观察结果：打印最近 10 天的数据
print("BTC/USDT 价格与交易信号 (1: 买入看多, -1: 卖出看空):")
print("-" * 80)
print(df[['close', 'yesterday_MA_3', 'signal']].tail(10))
