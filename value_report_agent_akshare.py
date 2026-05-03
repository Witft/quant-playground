import os
import json
import urllib.request
import math
import akshare as ak

# 加载 .env
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

MINIMAX_API_KEY = os.environ.get("MINIMAX_CN_API_KEY")
if not MINIMAX_API_KEY:
    raise ValueError("请在环境变量中设置 MINIMAX_CN_API_KEY")

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

def get_stock_context_akshare(symbol):
    """
    使用开源免费的 AkShare 获取 A 股数据 (基于雪球接口获取最新估值指标，基于巨潮资讯获取简介)
    symbol 格式: SH600519 (上海), SZ002594 (深圳)
    """
    print(f"\n正在通过 AkShare(免费开源) 抓取 {symbol} 的数据...")
    
    try:
        # 获取基础财务估值指标 (基于雪球接口)
        df_xq = ak.stock_individual_spot_xq(symbol=symbol)
        
        # 将行转为字典便于读取
        data_dict = dict(zip(df_xq['item'], df_xq['value']))
        
        current_price = float(data_dict.get('现价', 0))
        pe = float(data_dict.get('市盈率(TTM)', 0))
        pb = float(data_dict.get('市净率', 0))
        eps = float(data_dict.get('每股收益', 0))
        bvps = float(data_dict.get('每股净资产', 0))
        stock_name = data_dict.get('名称', symbol)
        
        # 计算格雷厄姆数字
        graham_number = 0
        if eps > 0 and bvps > 0:
            graham_number = round(math.sqrt(22.5 * eps * bvps), 2)
            
        # 获取公司业务简介 (基于巨潮资讯，只需要传入6位数字代码)
        pure_code = symbol[2:]
        summary = "未找到公司简介。"
        try:
            df_profile = ak.stock_profile_cninfo(symbol=pure_code)
            if not df_profile.empty:
                summary = df_profile['主营业务'].iloc[0] + " " + df_profile['机构简介'].iloc[0]
        except Exception:
            pass

        return {
            "symbol": f"{stock_name} ({symbol})",
            "price": current_price,
            "pe": pe,
            "pb": pb,
            "eps": eps,
            "bvps": bvps,
            "debt_to_equity": "N/A (基础指标未包含)",
            "graham_number": graham_number,
            "summary": summary
        }
    except Exception as e:
        return {"symbol": symbol, "error": f"获取数据失败: {e}"}

def generate_investment_report(stock_data):
    if "error" in stock_data:
        return stock_data["error"]
        
    prompt = f"""
你是一位深谙本杰明·格雷厄姆(Benjamin Graham)价值投资理念的资深华尔街分析师，现在需要分析中国 A 股市场。
请根据以下公司数据和业务简介，给出一份简短、尖锐的分析报告。

【公司数据】
股票名称与代码: {stock_data['symbol']}
当前股价: ￥{stock_data['price']}
市盈率(PE TTM): {stock_data['pe']}
市净率(PB): {stock_data['pb']}
每股收益(EPS): ￥{stock_data['eps']}
每股净资产(BVPS): ￥{stock_data['bvps']}
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
    # AkShare 雪球接口格式: 沪市带 SH，深市带 SZ
    stock = get_stock_context_akshare('SH600519')
    report = generate_investment_report(stock)
    
    print("="*60)
    print(f"📊 {stock['symbol']} 价值投资 AI 研报 (数据源: AkShare)")
    print("="*60)
    print(report)
    print("="*60)
