import urllib.request
import json
import pandas as pd
import backtrader as bt
from datetime import datetime

# ==========================================
# 1. 数据准备环节 (和之前类似，处理给 Backtrader 吃)
# ==========================================
print("正在从币安获取数据，请稍候...")
url = "https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1d&limit=365"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req) as response:
    data = json.loads(response.read().decode())

df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_asset_volume', 'number_of_trades', 'taker_buy_base', 'taker_buy_quote', 'ignore'])
for col in ['open', 'high', 'low', 'close', 'volume']:
    df[col] = df[col].astype(float)
df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
df.set_index('timestamp', inplace=True)

# ==========================================
# 2. 定义交易策略 (面向对象风格)
# ==========================================
class MovingAverageStrategy(bt.Strategy):
    # 定义可配置的参数
    params = (
        ('ma_period', 5),
    )

    def __init__(self):
        # 记录收盘价
        self.dataclose = self.datas[0].close
        # 在这里声明指标：计算移动平均线
        # Backtrader 会自动帮你处理时间序列，不需要你手动算
        self.sma = bt.indicators.SimpleMovingAverage(
            self.datas[0], period=self.params.ma_period)

    def next(self):
        # next() 方法每天都会被框架调用一次
        
        # 检查是否已经有持仓
        if not self.position:
            # 如果没有持仓，且今天的收盘价突破了均线 -> 买入
            if self.dataclose[0] > self.sma[0]:
                print(f"[{self.datas[0].datetime.date(0)}] 触发买入信号，收盘价: {self.dataclose[0]}")
                # 买入所有可用资金能买的数量 (简化操作)
                self.order_target_percent(target=0.99)
        else:
            # 如果已经持有仓位，且今天收盘价跌破了均线 -> 卖出平仓
            if self.dataclose[0] < self.sma[0]:
                print(f"[{self.datas[0].datetime.date(0)}] 触发卖出信号，收盘价: {self.dataclose[0]}")
                self.close()

# ==========================================
# 3. 配置并运行回测引擎 (Cerebro)
# ==========================================
cerebro = bt.Cerebro()

# 将 Pandas DataFrame 转换为 Backtrader 可用的数据源
data_feed = bt.feeds.PandasData(dataname=df)
cerebro.adddata(data_feed)

# 添加我们刚才写的策略
cerebro.addstrategy(MovingAverageStrategy)

# 设置初始资金：100,000 USDT
start_cash = 100000.0
cerebro.broker.setcash(start_cash)

# 设置千分之一的手续费 (极其关键！)
cerebro.broker.setcommission(commission=0.001)

print('='*60)
print(f'回测开始，初始资金: {start_cash:.2f}')

# 执行回测
cerebro.run()

end_cash = cerebro.broker.getvalue()
print('='*60)
print(f'回测结束，最终总资产: {end_cash:.2f}')
print(f'总收益率: {((end_cash - start_cash) / start_cash) * 100:.2f}%')
print('='*60)
