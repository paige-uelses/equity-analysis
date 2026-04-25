import requests 
import sys

API_KEY = "api_key"
FRED_KEY = "fred_key"
BASE = "https://financialmodelingprep.com/stable"
FRED_BASE = "https://api.stlouisfed.org/fred/series/observations"

symbol = input("Enter ticker: ").upper()

#Pull data 
def get(endpoint, symbol=None, extra_params=None):
    """Pull data from FMP's stable API."""
    url = f"{BASE}/{endpoint}?apikey={API_KEY}"
    if symbol:
        url += f"&symbol={symbol}"
    if extra_params:
        url += f"&{extra_params}"
    response = requests.get(url)
    data = response.json()
    if not data or (isinstance(data, dict) and "Error Message" in data):
        print(f"No data or error for {endpoint}: {data}")
        return None
    return data[0] if isinstance(data, list) else data

def get_fred(series_id):
    """Pull the latest value of a FRED series."""
    url = f"{FRED_BASE}?series_id={series_id}&api_key={FRED_KEY}&file_type=json&sort_order=desc&limit=1"
    response = requests.get(url).json()
    try:
        return float(response['observations'][0]['value']) / 100
    except (KeyError, IndexError, ValueError):
        print(f"Failed to pull FRED series {series_id}")
        return None

profile = get("profile", symbol=symbol)
#print("PROFILE:", profile)

ratios = get("ratios-ttm", symbol=symbol)
#print("RATIOS:", ratios)
income = get("income-statement", symbol=symbol, extra_params="limit=1")
cashflow = get("cash-flow-statement", symbol=symbol, extra_params="limit=1")
balance = get("balance-sheet-statement", symbol=symbol, extra_params="limit=1")
#print("BALANCE:", balance)
 
if not all([profile, ratios, income, cashflow, balance]):
    print("Missing critical data. Exiting.")
    sys.exit()
 
risk_free = get_fred("DGS10")
if risk_free is None:
    risk_free = 0.043
 
#field extractions
price = profile.get('price')
market_cap = profile.get('marketCap')
pe_ratio = ratios.get('priceToEarningsRatioTTM')

shares = int(market_cap/price) if price and market_cap else None
tax_rate = income.get('incomeTaxExpense', 0) / income.get('incomeBeforeTax', 1) if income.get('incomeBeforeTax') else 0.21 #defaults to US corporate rate

#financials (for display)
ev_ebitda = ratios.get('enterpriseValueMultipleTTM')
profit_margin = ratios.get('netProfitMarginTTM')
operating_margin = ratios.get('operatingProfitMarginTTM')
roe = ratios.get('returnOnEquityTTM')
debt_to_equity = ratios.get('debtToEquityRatioTTM')
free_cash_flow = cashflow.get('freeCashFlow')
if free_cash_flow is None:
    print("Free cash flow data unavailable. Cannot run DCF.")
    sys.exit()

#roe
net_income = income.get('netIncome', 0)
equity = balance.get('totalStockholdersEquity', 0)
roe = net_income / equity if equity else None

#WACC inputs
beta = profile.get('beta', 1)
interest_expense = income.get('interestExpense', 0)
total_debt = balance.get('totalDebt', 0)

#Formatting - organizes formatting based on its 1000th multiple
def fmt(x):
    if x is None:
        return "N/A"
    if abs(x) >= 1e12:
        return f"${x/1e12:.2f}T"
    if abs(x) >= 1e9:
        return f"${x/1e9:.2f}B"
    if abs(x) >= 1e6:
        return f"${x/1e6:.2f}M"
    return f"${x:,.2f}"

#Formatting - percentages
def pct(x):
    if x is None:
        return "N/A"
    if abs(x) < 1:
        return f"{x * 100:.2f}%"
    else:
        return f"{x:.2f}%"

#WACC calculation
# Cost of Equity (CAPM)
equity_risk_premium = 0.05
cost_of_equity = risk_free + beta * equity_risk_premium

# Cost of Debt
if total_debt and total_debt > 0 and interest_expense:
    cost_of_debt = (abs(interest_expense) / total_debt) * (1 - tax_rate)
else:
    cost_of_debt = 0.04 * (1 - tax_rate)

# Weights
equity_value = market_cap if market_cap else 0
total_debt = total_debt if total_debt else 0
total_value = equity_value + total_debt

if total_value == 0:
    print("Cannot calculate WACC — missing capital structure data.")
    sys.exit()

weight_equity = equity_value / total_value if total_value else 1
weight_debt = total_debt / total_value if total_value else 0

# WACC
wacc = (weight_equity * cost_of_equity) + (weight_debt * cost_of_debt)

#DCF Loop
growth_rate = 0.05
discount_rate = wacc
projected_fcf = []

base_fcf = free_cash_flow
for year in range(1, 6):
    future_fcf = base_fcf * (1 + growth_rate) ** year
    pv = future_fcf / (1 + discount_rate) ** year
    projected_fcf.append(pv)

#Terminal Value
perpetual_growth = 0.025
terminal_value = future_fcf * (1 + perpetual_growth) / (discount_rate - perpetual_growth)
if discount_rate <= perpetual_growth:
    print("WACC must be greater than terminal growth rate.")
    sys.exit()
discounted_terminal = terminal_value / ((1 + discount_rate) ** 5)

#Final calculation & valuation signal 
total_pv = sum(projected_fcf) + discounted_terminal
fair_value = total_pv / shares

margin = (fair_value - price) / price
if margin > 0.15:
    signal = "Strong Buy — Undervalued"
elif margin > 0:
    signal = "Buy — Slightly Undervalued"
elif margin > -0.15:
    signal = "Hold — Fairly Valued"
else:
    signal = "Sell — Overvalued"

#print outputs 
print(f"\n=== {profile.get('companyName', symbol)} ({symbol}) ===")
print(f"Price: ${price:.2f}")
print(f"Market Cap: {fmt(market_cap)}")
print(f"P/E Ratio: {pe_ratio:.2f}" if pe_ratio else "P/E Ratio: N/A")
print(f"EV/EBITDA: {ev_ebitda:.2f}" if ev_ebitda else "EV/EBITDA: N/A")
print(f"Profit Margin: {pct(profit_margin)}")
print(f"Operating Margin: {pct(operating_margin)}")
print(f"ROE: {pct(roe)}")
print(f"Debt/Equity: {debt_to_equity:.2f}" if debt_to_equity else "Debt/Equity: N/A")
print(f"Free Cash Flow: {fmt(free_cash_flow)}\n")

print(f"--- WACC ---")
print(f"Risk-Free Rate: {pct(risk_free)}")
print(f"Beta: {beta:.2f}")
print(f"Cost of Equity: {pct(cost_of_equity)}")
print(f"Cost of Debt: {pct(cost_of_debt)}")
print(f"WACC: {pct(wacc)}\n")

print(f"--- DCF ---")
print(f"Fair Value: ${fair_value:.2f}")
print(f"Current Price: ${price:.2f}")
print(f"Margin of Safety: {margin * 100:.1f}%")
print(f"Signal: {signal}")
