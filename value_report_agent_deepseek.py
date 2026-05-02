import yfinance as yf
import json
import urllib.request
import math

# 使用硅基流动的免费 DeepSeek-V3 接口
DEEPSEEK_API_KEY = "sk-yibvmdnnhxavhoxrrmoahfivhngszgwwiijvtvymzngshncz"

def ask_deepseek(prompt):
    url = "https://api.siliconflow.cn/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "deepseek-ai/DeepSeek-V3",
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

def get_stock_context(symbol):
    print(f"\n正在抓取 {symbol} 的数据...")
    ticker = yf.Ticker(symbol)
    info = ticker.info
    
    current_price = info.get('currentPrice', info.get('previousClose', 0))
    eps = info.get('trailingEps', 0)
    bvps = info.get('bookValue', 0)
    pe = info.get('trailingPE', 'N/A')
    pb = info.get('priceToBook', 'N/A')
    debt_to_equity = info.get('debtToEquity', 'N/A')
    summary = info.get('longBusinessSummary', '未找到公司简介。')
    
    graham_number = 0
    if eps > 0 and bvps > 0:
        graham_number = round(math.sqrt(22.5 * eps * bvps), 2)
        
    return {
        "symbol": symbol,
        "price": current_price,
        "pe": pe,
        "pb": pb,
        "eps": eps,
        "bvps": bvps,
        "debt_to_equity": debt_to_equity,
        "graham_number": graham_number,
        "summary": summary
    }

def generate_investment_report(stock_data):
    prompt = f"""
你是一位深谙本杰明·格雷厄姆(Benjamin Graham)价值投资理念的资深华尔街分析师。
请根据以下公司数据和业务简介，给出一份简短、尖锐的分析报告。

【公司数据】
股票代码: {stock_data['symbol']}
当前股价: ${stock_data['price']}
市盈率(PE): {stock_data['pe']}
市净率(PB): {stock_data['pb']}
债务股本比(Debt to Equity): {stock_data['debt_to_equity']} (正常健康企业应小于100)
格雷厄姆数字(理论内在价值): ${stock_data['graham_number']}

【公司业务简介】
{stock_data['summary']}

请按照以下结构输出报告：
1. **商业模式一句话总结**：这家公司到底是靠什么赚钱的？
2. **护城河判断**：它的业务是否容易被竞争对手复制？
3. **财务与估值诊断**：结合格雷厄姆数字、PE和债务情况，判断当前估值是高估、合理还是低估？负债是否健康？
4. **价值投资者行动建议**：(坚决回避 / 放入观察池 / 具备安全边际可买入)
"""
    print(f"正在让 DeepSeek-V3 模型分析 {stock_data['symbol']}...")
    report = ask_deepseek(prompt)
    return report

if __name__ == "__main__":
    stock = get_stock_context('C')
    report = generate_investment_report(stock)
    
    print("="*60)
    print(f"📊 {stock['symbol']} 价值投资 AI 研报")
    print("="*60)
    print(report)
    print("="*60)
