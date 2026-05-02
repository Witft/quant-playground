import urllib.request
import json
import csv
import datetime

url = "https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1d&limit=365"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req) as response:
    data = json.loads(response.read().decode())

with open('btc_365d.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    for row in data:
        dt = datetime.datetime.fromtimestamp(row[0]/1000).strftime('%Y-%m-%d')
        writer.writerow([dt, row[1], row[2], row[3], row[4], row[5]])
print("数据已成功保存至本地 btc_365d.csv")
