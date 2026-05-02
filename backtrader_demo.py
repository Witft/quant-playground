import pandas as pd
import backtrader as bt
from datetime import datetime

print("正在从本地 CSV 文件读取历史数据...")
df = pd.read_csv('btc_365d.csv', parse_dates=['timestamp'], index_col='timestamp')

class MovingAverageStrategy(bt.Strategy):
    params = (('ma_period', 5),)

    def __init__(self):
        self.dataclose = self.datas[0].close
        self.sma = bt.indicators.SimpleMovingAverage(self.datas[0], period=self.params.ma_period)

    def next(self):
        if not self.position:
            if self.dataclose[0] > self.sma[0]:
                print(f"[{self.datas[0].datetime.date(0)}] 买入信号，收盘价: {self.dataclose[0]:.2f}")
                self.order_target_percent(target=0.99)
        else:
            if self.dataclose[0] < self.sma[0]:
                print(f"[{self.datas[0].datetime.date(0)}] 卖出信号，收盘价: {self.dataclose[0]:.2f}")
                self.close()

cerebro = bt.Cerebro()
data_feed = bt.feeds.PandasData(dataname=df)
cerebro.adddata(data_feed)
cerebro.addstrategy(MovingAverageStrategy)

start_cash = 100000.0
cerebro.broker.setcash(start_cash)
cerebro.broker.setcommission(commission=0.001)

print('='*60)
print(f'回测开始，初始资金: {start_cash:.2f}')
cerebro.run()
end_cash = cerebro.broker.getvalue()
print('='*60)
print(f'回测结束，最终总资产: {end_cash:.2f}')
print(f'总收益率: {((end_cash - start_cash) / start_cash) * 100:.2f}%')
print('='*60)
