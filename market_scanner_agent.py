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
TUSHARE_TOKEN = os.environ.get("TUSHARE_TOKEN")

if not TUSHARE_TOKEN:
    print("⚠️ 警告: 未在环境变量中找到 TUSHARE_TOKEN，请确保已在 .env 文件中配置！")
    # 临时退回公共测试Token防崩溃
    TUSHARE_TOKEN = "7311ce833bf688229b46e379373d4dfbf33d6118d05dd362dbbe7954"

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
        "temperature": 0.1 
    }
    
    req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers)
    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            return result['choices'][0]['message']['content']
    except Exception as e:
        return f"AI分析失败: {e}"

def get_last_trade_date():
    """获取最近的一个交易日"""
    end_date = datetime.now().strftime('%Y%m%d')
    start_date = (datetime.now() - timedelta(days=15)).strftime('%Y%m%d')
    df_cal = pro.trade_cal(exchange='SSE', is_open='1', start_date=start_date, end_date=end_date)
    return df_cal['cal_date'].iloc[-1]

def scan_a_shares(limit=3):
    last_date = get_last_trade_date()
    print(f"1. 正在通过 Tushare 获取全市场 A 股基础信息与行情数据 (交易日: {last_date})...")
    
    # 获取所有正常上市的股票列表 (名称、代码)
    df_stock = pro.stock_basic(exchange='', list_status='L', fields='ts_code,name')
    # 过滤掉 ST 和退市股
    df_stock = df_stock[~df_stock['name'].str.contains('ST|退', na=False)]
    
    # 获取当天的所有指标 (PE, PB, 收盘价等)
    df_basic = pro.daily_basic(trade_date=last_date, fields='ts_code,close,pe_ttm,pb')
    
    # 将名称与指标合并
    df = pd.merge(df_stock, df_basic, on='ts_code')
    
    results = []
    print(f"2. 成功获取 {len(df)} 只股票数据。正在执行格雷厄姆内在价值全盘扫描...")
    
    for _, row in df.iterrows():
        price = row.get('close')
        pe = row.get('pe_ttm') # 优先使用滚动市盈率，更准确
        pb = row.get('pb')
        
        # 排除空数据、亏损企业
        if pd.isna(price) or pd.isna(pe) or pd.isna(pb) or price <= 0 or pe <= 0 or pb <= 0:
            continue
            
        # 反推指标
        eps = price / pe
        bvps = price / pb
        
        graham_number = math.sqrt(22.5 * eps * bvps)
        
        # 筛选条件：当前股价低于格雷厄姆数字
        if price < graham_number:
            margin = (graham_number - price) / graham_number
            results.append({
                'code': row['ts_code'],
                'name': row['name'],
                'price': price,
                'pe': round(pe, 2),
                'pb': round(pb, 2),
                'graham': round(graham_number, 2),
                'margin': round(margin * 100, 2)
            })
            
    # 按照安全边际降序排序
    results.sort(key=lambda x: x['margin'], reverse=True)
    top_stocks = results[:limit]
    
    print(f"3. 扫描完成！共发现 {len(results)} 只低于理论价值的股票。")
    print(f"   准备将 Top {limit} 送入 MiniMax 进行排雷分析...")
    return top_stocks

def generate_daily_report(top_stocks):
    report = "=================================================\n"
    report += "🤖 【Tushare全市场扫描】每日深度低估 TOP 榜单\n"
    report += "=================================================\n"
    
    for s in top_stocks:
        print(f"\n正在让 LLM 深度分析 {s['name']}...")
        
        # 获取公司主营业务简介
        summary = "无"
        try:
            info_df = pro.stock_company(ts_code=s['code'], fields='main_business')
            if not info_df.empty and not pd.isna(info_df['main_business'].iloc[0]):
                summary = str(info_df['main_business'].iloc[0])
        except Exception as e:
            print(f"获取 {s['name']} 简介失败: {e}")
            
        prompt = f"""
你是一个犀利的价值投资分析师。系统在A股5000只股票中，扫描到了严重低于格雷厄姆数字的公司：
股票：{s['name']}({s['code']})
当前股价：{s['price']}，理论内在价值：{s['graham']}
市盈率(PE TTM): {s['pe']}，市净率(PB): {s['pb']}
主营业务：{summary}

极度低估往往意味着市场存在极度悲观的预期（即“价值陷阱”）。
请用非常简短的 2-3 句话（控制在60字以内），一针见血地指出这家公司为什么会被市场如此低估？（例如：是否属于夕阳产业、重资产、强周期性、政策打压等）。直接给结论。
"""
        analysis = ask_minimax(prompt)
        
        report += f"🔥 {s['name']} ({s['code']})\n"
        report += f"   现价: ￥{s['price']} | 格雷厄姆估值: ￥{s['graham']} (安全边际: {s['margin']}%)\n"
        report += f"   指标: PE TTM = {s['pe']}, PB = {s['pb']}\n"
        report += f"   ⚠️ AI 排雷简评: {analysis}\n"
        report += "-"*50 + "\n"
        
    return report

if __name__ == "__main__":
    top_undervalued = scan_a_shares(limit=3)
    final_md = generate_daily_report(top_undervalued)
    print("\n\n" + final_md)
