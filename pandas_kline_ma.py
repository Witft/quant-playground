import urllib.request
import json
import pandas as pd

# 1. 获取数据 (同之前一样)
url = "https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1d&limit=10" # 取10天数据以便算平均线
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})

with urllib.request.urlopen(req) as response:
    data = json.loads(response.read().decode())

# 2. 见证 Pandas 的魔法：将 JSON 列表直接转换为 DataFrame (数据表)
df = pd.DataFrame(data, columns=[
    'timestamp', 'open', 'high', 'low', 'close', 'volume', 
    'close_time', 'quote_asset_volume', 'number_of_trades', 
    'taker_buy_base', 'taker_buy_quote', 'ignore'
])

# 3. 数据清洗：量化交易中最常见的操作
# 只保留我们需要的基础列
df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]

# 将字符串类型转换为浮点数 (float)
for col in ['open', 'high', 'low', 'close', 'volume']:
    df[col] = df[col].astype(float)

# 将时间戳转换为可读日期，并将其设置为表格的索引 (Index)
df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
df.set_index('timestamp', inplace=True)

# 4. 计算技术指标：3日移动平均线 (3-Day Moving Average)
# 在纯 Python 里这需要写循环，在 Pandas 里只需要 1 行代码！
df['MA_3'] = df['close'].rolling(window=3).mean()

print("BTC/USDT 最近10天的 K线数据及 3日均线 (MA_3):")
print("-" * 60)
print(df[['close', 'MA_3']])
