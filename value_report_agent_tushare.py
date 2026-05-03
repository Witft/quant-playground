import os
import json
import urllib.request
import math
import tushare as ts
from datetime import datetime, timedelta

# 加载 .env
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# 1. 配置 API Keys
MINIMAX_API_KEY = os.environ.get("MINIMAX_CN_API_KEY")
if not MINIMAX_API_KEY:
    raise ValueError("请在环境变量中设置 MINIMAX_CN_API_KEY")

# Tushare Token (如果没有在 .env 配置，则使用一个免费的公共测试 Token)
TUSHARE_TOKEN = os.environ.get("TUSHARE_TOKEN", "7311ce833bf688229b46e379373d4dfbf33d6118d05dd362dbbe7954")
ts.set_token(TUSHARE_TOKEN)
pro = ts.pro_api()

def ask_minimax(prompt):
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
        return f"调用 LLM 失败: {e}"

# 2. 通过 Tushare 抓取 A 股数据与文本
def get_stock_context_tushare(symbol):
    print(f"\n正在通过 Tushare 抓取 {symbol} 的数据...")
    
    # 获取最近的一个有数据的交易日（往前推最多10天，避开周末和节假日）
    df = None
    for i in range(10):
        date_str = (datetime.now() - timedelta(days=i)).strftime('%Y%m%d')
        temp_df = pro.daily_basic(ts_code=symbol, trade_date=date_str)
        if not temp_df.empty:
            df = temp_df
            break
            
    if df is None or df.empty:
        return {"symbol": symbol, "error": "未获取到交易数据，请检查代码(如 600519.SH)或 Token 权限。"}

    close = df['close'].iloc[0]
    pe = df['pe'].iloc[0]
    pb = df['pb'].iloc[0]
    
    # Tushare 的 daily_basic 直接提供 PE 和 PB，我们反推 EPS(每股收益) 和 BVPS(每股净资产)
    eps = close / pe if pe and pe > 0 else 0
    bvps = close / pb if pb and pb > 0 else 0
    
    # 获取公司主营业务简介
    summary = "未找到公司简介。"
    try:
        info_df = pro.stock_company(ts_code=symbol, fields='ts_code,main_business')
        if not info_df.empty:
            summary = info_df['main_business'].iloc[0]
    except Exception:
        pass
    
    # 计算格雷厄姆数字
    graham_number = 0
    if eps > 0 and bvps > 0:
        graham_number = round(math.sqrt(22.5 * eps * bvps), 2)
        
    return {
        "symbol": symbol,
        "price": close,
        "pe": pe,
        "pb": pb,
        "eps": round(eps, 2),
        "bvps": round(bvps, 2),
        "debt_to_equity": "N/A (Tushare 基础版未提供)",
        "graham_number": graham_number,
        "summary": summary
    }

# 3. 核心：构建 Agent Prompt
def generate_investment_report(stock_data):
    if "error" in stock_data:
        return stock_data["error"]
        
    prompt = f"""
你是一位深谙本杰明·格雷厄姆(Benjamin Graham)价值投资理念的资深华尔街分析师，现在需要分析中国 A 股市场。
请根据以下公司数据和业务简介，给出一份简短、尖锐的分析报告。

【公司数据】
股票代码: {stock_data['symbol']}
当前股价: ￥{stock_data['price']}
市盈率(PE): {stock_data['pe']}
市净率(PB): {stock_data['pb']}
格雷厄姆数字(理论内在价值): ￥{stock_data['graham_number']}

【公司业务简介】
{stock_data['summary']}

请按照以下结构输出报告：
1. **商业模式一句话总结**：这家公司到底是靠什么赚钱的？
2. **护城河判断**：它的业务是否容易被竞争对手复制？
3. **财务与估值诊断**：结合格雷厄姆数字、PE判断当前估值是高估、合理还是低估？
4. **价值投资者行动建议**：(坚决回避 / 放入观察池 / 具备安全边际可买入)
"""
    print(f"正在让 MiniMax-M2.7 模型分析 {stock_data['symbol']}...")
    report = ask_minimax(prompt)
    return report

if __name__ == "__main__":
    # Tushare 的代码后缀与雅虎不同：上海是 .SH，深圳是 .SZ
    # 我们以 贵州茅台 (600519.SH) 为例
    stock = get_stock_context_tushare('600519.SH')
    report = generate_investment_report(stock)
    
    print("="*60)
    print(f"📊 {stock['symbol']} 价值投资 AI 研报 (数据源: Tushare)")
    print("="*60)
    print(report)
    print("="*60)
