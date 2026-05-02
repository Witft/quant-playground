import yfinance as yf
import math

def calculate_graham_number(ticker_symbol):
    print(f"正在获取 {ticker_symbol} 的财务数据...")
    ticker = yf.Ticker(ticker_symbol)
    
    try:
        # 获取基础信息
        info = ticker.info
        
        # 提取关键指标
        current_price = info.get('currentPrice', info.get('previousClose', 0))
        eps = info.get('trailingEps', 0)
        # 每股净资产 (Book Value Per Share)
        bvps = info.get('bookValue', 0)
        
        if eps <= 0 or bvps <= 0:
            return {
                "symbol": ticker_symbol,
                "error": "收益或净资产为负数，无法计算格雷厄姆数字 (不符合防御型投资标准)。"
            }
            
        # 计算格雷厄姆数字 (Graham Number = sqrt(22.5 * EPS * BVPS))
        graham_number = math.sqrt(22.5 * eps * bvps)
        
        # 计算安全边际 (Margin of Safety)
        margin_of_safety = (graham_number - current_price) / graham_number
        
        return {
            "symbol": ticker_symbol,
            "current_price": current_price,
            "eps": eps,
            "bvps": bvps,
            "graham_number": round(graham_number, 2),
            "margin_of_safety": round(margin_of_safety * 100, 2), # 转换为百分比
            "is_undervalued": current_price < graham_number
        }
        
    except Exception as e:
        return {"symbol": ticker_symbol, "error": str(e)}

def analyze_stocks(symbols):
    print("="*60)
    print("格雷厄姆价值投资 Agent - 自动化初筛")
    print("="*60)
    
    for sym in symbols:
        res = calculate_graham_number(sym)
        if "error" in res:
            print(f"[{sym}] 忽略: {res['error']}")
            print("-" * 30)
            continue
            
        print(f"代码: {res['symbol']}")
        print(f"当前股价: ${res['current_price']}")
        print(f"每股收益(EPS): ${res['eps']} | 每股净资产(BVPS): ${res['bvps']}")
        print(f"格雷厄姆合理估值: ${res['graham_number']}")
        
        if res['is_undervalued']:
            print(f"🔥 发现低估! 当前价格低于格雷厄姆数字。安全边际: {res['margin_of_safety']}%")
        else:
            print(f"❌ 估值偏高。当前价格超出了格雷厄姆的安全上限。")
        print("-" * 30)

if __name__ == "__main__":
    # 我们测试几个典型的公司：苹果(科技巨头), 可口可乐(巴菲特爱股), 以及一个可能被低估的传统企业(比如某家银行)
    test_symbols = ['AAPL', 'KO', 'C'] # C 是花旗银行
    analyze_stocks(test_symbols)
