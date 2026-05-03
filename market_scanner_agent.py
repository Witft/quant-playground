import os
import json
import urllib.request
import math
import time
import pandas as pd

# 强制禁用代理 (保险措施)
os.environ['HTTP_PROXY'] = ''
os.environ['HTTPS_PROXY'] = ''
os.environ['http_proxy'] = ''
os.environ['https_proxy'] = ''

# 猴子补丁：为所有 requests 请求加上伪装 Headers 并禁用代理
import patch_requests

import akshare as ak


try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

MINIMAX_API_KEY = os.environ.get("MINIMAX_CN_API_KEY")

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

def scan_a_shares(limit=3):
    print("1. 正在连线东方财富，获取全市场 A 股实时行情...")
    df = ak.stock_zh_a_spot_em()
    
    # 过滤掉 ST 股和退市股
    df = df[~df['名称'].str.contains('ST|退', na=False)]
    
    results = []
    print(f"2. 成功获取 {len(df)} 只股票数据。正在执行格雷厄姆内在价值全盘扫描...")
    
    for _, row in df.iterrows():
        price = row.get('最新价')
        pe = row.get('市盈率-动态')
        pb = row.get('市净率')
        
        # 数据清洗与校验
        try:
            price, pe, pb = float(price), float(pe), float(pb)
        except:
            continue
            
        # 排除亏损、停牌或异常数据（市盈率/市净率必须大于0，才符合防御性投资）
        if pd.isna(price) or pd.isna(pe) or pd.isna(pb) or price <= 0 or pe <= 0 or pb <= 0:
            continue
            
        eps = price / pe
        bvps = price / pb
        
        graham_number = math.sqrt(22.5 * eps * bvps)
        
        # 筛选条件：当前股价必须低于格雷厄姆数字
        if price < graham_number:
            margin = (graham_number - price) / graham_number
            results.append({
                'code': row['代码'],
                'name': row['名称'],
                'price': price,
                'pe': pe,
                'pb': pb,
                'graham': round(graham_number, 2),
                'margin': round(margin * 100, 2) # 安全边际百分比
            })
            
    # 按照安全边际降序排序 (越低估的排越前面)
    results.sort(key=lambda x: x['margin'], reverse=True)
    top_stocks = results[:limit]
    
    print(f"3. 扫描完成！共发现 {len(results)} 只低于理论价值的股票。")
    print(f"   准备将 Top {limit} 送入 MiniMax 进行排雷分析...")
    return top_stocks

def generate_daily_report(top_stocks):
    report = "=================================================\n"
    report += "🤖 【A股全市场扫描】每日深度低估 TOP 榜单\n"
    report += "=================================================\n"
    
    for s in top_stocks:
        print(f"\n正在让 LLM 深度分析 {s['name']}...")
        
        # 尝试获取公司简介
        summary = "无"
        try:
            df_profile = ak.stock_profile_cninfo(symbol=s['code'])
            if not df_profile.empty:
                summary = str(df_profile['主营业务'].iloc[0])
        except:
            pass
            
        prompt = f"""
你是一个犀利的价值投资分析师。系统在A股5000只股票中，扫描到了严重低于格雷厄姆数字的公司：
股票：{s['name']}({s['code']})
当前股价：{s['price']}，理论内在价值：{s['graham']}
市盈率(PE): {s['pe']}，市净率(PB): {s['pb']}
主营业务：{summary}

极度低估往往意味着市场存在极度悲观的预期（即“价值陷阱”）。
请用非常简短的 2-3 句话（控制在60字以内），一针见血地指出这家公司为什么会被市场如此低估？（例如：是否属于夕阳产业、重资产、强周期性、政策打压等）。直接给结论。
"""
        analysis = ask_minimax(prompt)
        
        report += f"🔥 {s['name']} ({s['code']})\n"
        report += f"   现价: ￥{s['price']} | 格雷厄姆估值: ￥{s['graham']} (安全边际: {s['margin']}%)\n"
        report += f"   指标: PE = {s['pe']}, PB = {s['pb']}\n"
        report += f"   ⚠️ AI 排雷简评: {analysis}\n"
        report += "-"*50 + "\n"
        
    return report

if __name__ == "__main__":
    # 为了测试速度和节省 Token，我们默认只拿全市场最被低估的前 3 只股票进行 AI 分析
    top_undervalued = scan_a_shares(limit=3)
    final_md = generate_daily_report(top_undervalued)
    
    print("\n\n" + final_md)
