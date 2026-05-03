import os
import json
import urllib.request
import math
import time
from datetime import datetime, timedelta
import pandas as pd
import tushare as ts

# 加载环境变量
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

MINIMAX_API_KEY = os.environ.get("MINIMAX_CN_API_KEY")
TUSHARE_TOKEN = os.environ.get("TUSHARE_TOKEN", "7311ce833bf688229b46e379373d4dfbf33d6118d05dd362dbbe7954")

ts.set_token(TUSHARE_TOKEN)
pro = ts.pro_api()

def ask_minimax(prompt):
    if not MINIMAX_API_KEY:
        return "未配置 MINIMAX_CN_API_KEY，跳过 AI 分析。"
        
    url = "https://api.minimax.chat/v1/text/chatcompletion_v2"
    headers = {
        "Authorization": f"Bearer {MINIMAX_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "MiniMax-M2.7", 
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2 
    }
    
    req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers)
    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            return result['choices'][0]['message']['content']
    except Exception as e:
        return f"AI分析失败: {e}"

def get_last_trade_date():
    end_date = datetime.now().strftime('%Y%m%d')
    start_date = (datetime.now() - timedelta(days=15)).strftime('%Y%m%d')
    df_cal = pro.trade_cal(exchange='SSE', is_open='1', start_date=start_date, end_date=end_date)
    return df_cal['cal_date'].iloc[-1]

def scan_a_shares(limit=3):
    last_date = get_last_trade_date()
    print(f"1. 正在获取全市场 A 股基础行情 (交易日: {last_date})...")
    
    df_stock = pro.stock_basic(exchange='', list_status='L', fields='ts_code,name')
    df_stock = df_stock[~df_stock['name'].str.contains('ST|退', na=False)]
    df_basic = pro.daily_basic(trade_date=last_date, fields='ts_code,close,pe_ttm,pb')
    df = pd.merge(df_stock, df_basic, on='ts_code')
    
    results = []
    print(f"2. 正在执行格雷厄姆内在价值全盘扫描...")
    
    for _, row in df.iterrows():
        price, pe, pb = row.get('close'), row.get('pe_ttm'), row.get('pb')
        if pd.isna(price) or pd.isna(pe) or pd.isna(pb) or price <= 0 or pe <= 0 or pb <= 0:
            continue
            
        eps, bvps = price / pe, price / pb
        graham_number = math.sqrt(22.5 * eps * bvps)
        
        if price < graham_number:
            margin = (graham_number - price) / graham_number
            results.append({
                'code': row['ts_code'], 'name': row['name'], 'price': price,
                'pe': round(pe, 2), 'pb': round(pb, 2),
                'graham': round(graham_number, 2), 'margin': round(margin * 100, 2)
            })
            
    results.sort(key=lambda x: x['margin'], reverse=True)
    return results[:limit], last_date

def generate_daily_report():
    top_stocks, trade_date = scan_a_shares(limit=3) # 挑出最便宜的3只
    
    if not top_stocks:
        print("[SILENT] 今日无满足安全边际的股票推荐。")
        return
        
    report = "=================================================\n"
    report += "🤖 【AI 投资董事会】每日深度低估扫描与排雷\n"
    report += f"📅 交易日期: {trade_date}\n"
    report += "=================================================\n"
    
    for s in top_stocks:
        print(f"\n正在召开针对 {s['name']} 的 AI 董事会会议...")
        
        summary = "无"
        try:
            info_df = pro.stock_company(ts_code=s['code'], fields='main_business')
            if not info_df.empty and not pd.isna(info_df['main_business'].iloc[0]):
                summary = str(info_df['main_business'].iloc[0])
        except:
            pass
            
        prompt = f"""
你现在主持一场针对A股公司【{s['name']}({s['code']})】的投资决策会议。
当前股价: ￥{s['price']}，理论内在价值(格雷厄姆数字): ￥{s['graham']} (安全边际: {s['margin']}%)
市盈率(PE TTM): {s['pe']}，市净率(PB): {s['pb']}
主营业务：{summary}

请以如下结构严格输出会议记录：
1. 😈 【做空蓝军排雷】：不要说好话！假设你持有10亿做空仓位，请强行挑出这只股票最致命的 3 个潜在暴雷点或价值陷阱（如：涉房涉地方债、重资产折旧、技术被淘汰等）。
2. 🧐 【F-Score 审计师】：基于皮奥特罗斯基(Piotroski)的财务健康理念和该公司的行业特征，指出要确认它“不是即将破产的垃圾股”，我们最需要重点查验它的哪 2 个底层财务指标？（如：经营现金流、毛利率等）为什么？
3. 👨‍🏫 【金融私教课】：从上述两点分析中，提取一个最核心的专业金融词汇，向非金融专业的IT工程师用生活中的比喻解释一下（80字以内）。
4. ⚖️ 【最终裁决】：(坚决回避 / 放入观察池 / 具备安全边际可买入)
"""
        analysis = ask_minimax(prompt)
        
        report += f"🔥 标的：{s['name']} ({s['code']})\n"
        report += f"   数据：现价 ￥{s['price']} | 理论估值 ￥{s['graham']} | PE {s['pe']} | PB {s['pb']}\n\n"
        report += f"{analysis}\n"
        report += "="*50 + "\n"
        
    print(report)

if __name__ == "__main__":
    generate_daily_report()
