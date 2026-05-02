import urllib.request
import json
import pandas as pd
import numpy as np

# 1. 获取并清洗数据 (这次拿半年180天数据来测)
url = "https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1d&limit=180"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req) as response:
    data = json.loads(response.read().decode())

df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_asset_volume', 'number_of_trades', 'taker_buy_base', 'taker_buy_quote', 'ignore'])
for col in ['open', 'high', 'low', 'close', 'volume']:
    df[col] = df[col].astype(float)
df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
df.set_index('timestamp', inplace=True)

# 2. 计算指标和信号
df['MA_5'] = df['close'].rolling(window=5).mean()  # 这次用5日均线
df['yesterday_MA_5'] = df['MA_5'].shift(1)

# 生成信号：只做多 (做多=1, 观望=0)
df['signal'] = 0
df.loc[df['close'] > df['yesterday_MA_5'], 'signal'] = 1
df.loc[df['close'] < df['yesterday_MA_5'], 'signal'] = 0

# 3. 核心：计算收益率 (Returns)
# 基础市场收益率：如果我一直拿着比特币不动 (Buy and Hold)
# pct_change() 计算今天的收盘价相对昨天涨跌了百分之几
df['market_return'] = df['close'].pct_change()

# 策略收益率：昨天的信号决定今天的仓位
# 如果昨天的 signal=1（持仓），我今天就吃到了 market_return
# 如果昨天的 signal=0（空仓），我今天收益就是 0
df['strategy_return'] = df['signal'].shift(1) * df['market_return']

# 4. 统计累计收益率 (Cumulative Returns)
# 把每天的收益率用累乘的方法加起来 (1 + 收益率 的连乘)
df['cum_market_return'] = (1 + df['market_return']).cumprod()
df['cum_strategy_return'] = (1 + df['strategy_return']).cumprod()

# 打印最终结果
final_market = (df['cum_market_return'].iloc[-1] - 1) * 100
final_strategy = (df['cum_strategy_return'].iloc[-1] - 1) * 100

print("="*60)
print("简单 5日均线 策略回测结果 (最近180天)")
print("="*60)
print(f"如果你一直持有BTC不动 (市场收益): {final_market:.2f}%")
print(f"如果你使用5日均线策略 (策略收益): {final_strategy:.2f}%")
print("-"*60)
print("请注意：这个回测非常简陋，它没有扣除手续费(Fee)，也没有考虑滑点(Slippage)！")
