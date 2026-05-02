import urllib.request
import json
import datetime

# 调用币安公开API获取BTC/USDT的日K线数据，取最近5天
url = "https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1d&limit=5"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})

try:
    with urllib.request.urlopen(req) as response:
        # 读取并解析JSON数据
        data = json.loads(response.read().decode())
        
    print(f"{'日期 (Date)':<15} | {'开盘 (Open)':<10} | {'最高 (High)':<10} | {'最低 (Low)':<10} | {'收盘 (Close)':<10} | {'成交量 (Volume)':<10}")
    print("-" * 80)
    
    # 遍历每一天的K线数据
    for kline in data:
        # 币安API返回的时间戳是毫秒级的，除以1000转换为秒
        date_str = datetime.datetime.fromtimestamp(kline[0]/1000).strftime('%Y-%m-%d')
        open_p = float(kline[1])
        high_p = float(kline[2])
        low_p = float(kline[3])
        close_p = float(kline[4])
        volume = float(kline[5])
        
        # 打印这一天的数据
        print(f"{date_str:<15} | {open_p:<10.2f} | {high_p:<10.2f} | {low_p:<10.2f} | {close_p:<10.2f} | {volume:<10.2f}")
except Exception as e:
    print(f"获取数据出错: {e}")
