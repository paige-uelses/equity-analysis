# equity-analysis
**Stock Analyzer**
- Python tool that pulls live financial data from the Financial Modeling Prep and FRED APIs, calculates WACC using CAPM, and runs a DCF valuation to estimate intrinsic value.

**What it does**
- Pulls key financial metrics (P/E, EV/EBITDA, margins, ROE, FCF, debt/equity)
- Calculates WACC from live inputs — 10-Year Treasury yield from FRED, company beta, and capital structure
- Runs a 5-year DCF model with terminal value to estimate fair value per share
a margin-of-safety signal (strong buy / buy / hold / sell)

**APIs used**
- Financial Modeling Prep — company fundamentals, ratios, financial statements
- FRED (Federal Reserve) — 10-Year Treasury yield for risk-free rate

**Next updates**
- Monte Carlo simulation to quantify valuation uncertainty across a range of outcomes
- Peer comparisons (P/E and EV/EBITDA vs industry)

**Future Enhancements**
- Sentiment analysis on earnings calls and news
- Historical trend tracking for revenue and margins
- Scorecard-style output (valuation: cheap/fair/expensive, profitability: strong/weak, etc.)
  
**Disclaimer**
- This is a personal project for learning and not financial advice. DCF models are highly sensitive to assumptions and don't capture many real-world factors.
