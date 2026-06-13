# Research Workflow — Diversified Trend on CME Micros

> **STATUS: PARKED (2026-06-13).** On hold pending a multi-symbol / portfolio
> backtester (see `docs/ROADMAP.md` → Backlog). This strategy's edge is
> cross-sectional diversification across a basket of CME micros; a single-symbol
> trend backtest is **not** an acceptable substitute — it discards that
> diversification, the strategy's reason for existing. Do not resume research
> until the portfolio backtester exists. Strategy #1 is now the intraday
> conditional strategy (`research/intraday_conditional_strategy_notes.md`).

Living document tracking the research workflow for the diversified-trend strategy.
Update as decisions are made.

---

## Strategy Summary

**Type:** Time-series momentum (trend following) on a diversified basket of CME micro futures.

**Holding period:** Multi-day to multi-week. Hold through overnights. Hold through weekends with conservative vol-target sizing.

**Capital:** $25,000–$50,000. Account equity must stay above $25k (PDT floor) at all times.

**Known headwind:** Current US policy regime (2025–2028) may be hostile to trend strategies due to mean-reverting policy-announcement volatility, particularly on weekends. Accepted as a regime risk rather than a strategy design driver.

---

## Step 0 — Lock the Framing

### Strategy Thesis

Time-series momentum captures slow-moving drift across asset classes driven by underreaction to fundamentals, behavioral anchoring, and risk transfer from hedgers to speculators. The effect has persisted out-of-sample for decades across instruments and is not arbed away because the drawdowns are too deep for most institutional capital to hold through. The strategy is expected to continue working in the long run, but the current US policy regime may create a hostile environment that could last through 2029. Sizing must be conservative enough to survive a worse-than-historical drawdown, and evaluation must use a window long enough to span at least one regime change.

**Who is on the other side of the trade:**
- Hedgers transferring risk (commercial producers, asset managers reducing exposure mechanically)
- Discretionary traders fading trends that "look extended"

### Explicit Constraints

- Hold through overnights: **yes**
- Hold through weekends: **yes**, with conservative sizing
- Trump-specific concern: acknowledged as a known headwind for 2025–2028, **not** a strategy design driver
- Universe: diversified basket across equity / commodity / (possibly rates / FX)
- Capital: $25–50k, must stay above $25k PDT floor at all times
- Per-trade risk: 0.5–1% of equity as starting assumption, refined during sizing work

### Success and Kill Criteria

Committed in writing **before** research begins. Numbers below are starting points — refine if needed, but commit before looking at data.

| Phase | Criterion | Action if met | Action if not met |
|---|---|---|---|
| OOS | Sharpe ≥ 0.4 (net of realistic costs) | Proceed to paper | Kill or document why OOS is uninformative |
| OOS | Max drawdown ≤ 25% | Proceed to paper | Kill or revisit sizing |
| Paper | Sharpe over 3+ months not catastrophically worse than OOS | Proceed to small live | Extend paper, investigate, or kill |
| Live | Drawdown to within 10% of PDT floor | **Kill immediately** | — |
| Live | 18 months of live underperformance vs. backtest by >2 standard errors | Kill | — |

---

## Step 1 — Universe and Data

### Decision: Futures (CME Micros) over ETFs

Locked decision. Reasons:
- Trend works better on a diversified multi-asset basket than concentrated equity; futures give cleaner access to non-equity assets
- Section 1256 tax treatment (60/40 blend) materially improves after-tax returns
- No PDT considerations
- 23-hour sessions help on weekend policy events: Sunday evening reopen lets positions partially adjust before Monday equity open
- Cleaner shorts (no borrow, no locate)
- Cheaper round-trip costs at this size

### Initial Basket

| Instrument | Asset Class | Notional (approx) | Notes |
|---|---|---|---|
| MES | US large-cap equity | ~$27k | Core equity exposure |
| MNQ | US tech equity | ~$43k | Tech tilt; reconsider given correlation with MES |
| M2K | US small-cap equity | ~$11k | Size factor diversification |
| MGC | Gold | ~$24k | Inflation hedge, partial policy-uncertainty beneficiary |
| MCL | Crude oil | ~$7k | Commodity diversification |

**Excluded from v1:**
- MYM (Dow) — largely redundant with MES
- Micro FX / rates — adds real diversification but defer to v2; validate framework first

### Data

- Source: IBKR daily futures bars (~20 years available)
- Continuous contract series required; methodology matters
- Cache everything to `market_data_bars` table before research starts — no live IBKR pulls during iteration

### Sample Period

| Window | Dates | Purpose |
|---|---|---|
| Full research data | 2005–present | Covers 2008, 2010–19 low-vol, 2020 COVID, 2022 inflation, 2024–25 policy regime |
| In-sample (IS) | 2005 through end-2022 (~18 years) | Signal development, parameter sensitivity, cost stress |
| Out-of-sample (OOS) | 2023–present | **Untouched until final candidate.** One shot. |

**Rule:** Looking at OOS counts as using it. If results inform any subsequent tweak, OOS is contaminated and fresh data is required.

---

## Step 2 — Signal Construction (in `research/` notebooks)

Work in notebooks until there is a candidate worth backtesting. Do not touch the main codebase yet.

### Baseline Signal

Start here. Do not over-engineer.

- **Per-instrument signal:** sign of trailing N-month return, N in 6–12 month range
- **Position direction:** +1 (long) if positive, −1 (short) if negative, 0 only if explicitly flat
- **Position sizing:** inverse-volatility weighted across the basket so each instrument contributes equal risk
- **Rebalance:** weekly (Friday close → execute Monday open)

### Visual Inspection (before any backtest)

- Plot signal vs. forward return for each instrument
- Plot signal persistence (how often does the sign flip?)
- Look at signal behavior during regimes of interest: 2008, 2020, 2022, 2024–25
- Confirm signal behaves as thesis predicts; if not, understand why before backtesting

### Do NOT (on first pass)

- Add regime conditioning or filters
- Add stop-losses (trend strategies generally don't; tends to be overfit)
- Combine multiple signals
- Tune parameters

---

## Step 3 — In-Sample Backtest

Use existing `run_backtest` harness with a `BacktestConfig`. The bar-family backtester is fit for this.

### Sizing Approach

- Target portfolio volatility: **10–12% annualized** (conservative starting point given Trump-weekend concern)
- Per-instrument vol scaling: each instrument's position contributes equal risk to portfolio
- Position size derived from rolling realized vol estimate (e.g., 60-day) — **point-in-time, no lookahead**
- Cap per-instrument exposure at a fraction of portfolio (e.g., 40%) so a single instrument can't dominate

### What to Look At First

- **Equity curve shape** — smooth-ish drift with deep drawdowns is normal; long flat periods are normal
- **Drawdown distribution** — what is the max? How long was the longest one? Psychologically tolerable?
- **Trade frequency** — should be low (weekly rebalance, but most weeks no flip)
- **Per-instrument contribution** — if one instrument dominates returns, that is a red flag
- **Regime behavior** — 2008, 2020, 2022, 2024–25

### Cost Assumptions (aggressive, not optimistic)

| Item | Assumption |
|---|---|
| Commission | $0.85 per contract per side (IBKR tiered micros) |
| Slippage | 1 tick per side (conservative for micros at this size) |
| Financing | None (futures mark-to-market daily) |
| Exchange/regulatory fees | ~$0.30–$0.40 per contract |

---

## Step 4 — Parameter Sensitivity (NOT Optimization)

Critical step. Most overfit strategies die here if done honestly.

### Sweeps

Sweep over a range of values and look at the **distribution** of Sharpes, not the max.

| Parameter | Sweep range |
|---|---|
| Lookback (months) | 3, 6, 9, 12, 15, 18 |
| Rebalance frequency | Weekly, biweekly, monthly |
| Vol estimation window | 30d, 60d, 90d |
| Vol target level | 8%, 10%, 12%, 15% |

### What to Look For

- **Broad plateau** where Sharpe is relatively stable across a wide parameter range → real edge
- **Single peak** with degradation on either side → likely overfit; kill

Pick parameters from the **middle of plateaus**, not from optimization peaks. Document the choice and reasoning.

### Tooling Note

`ROADMAP.md` backlog item "research parameter sweeps on the custom engine" is currently load-bearing here. For v1, a notebook-level sweep suffices. Build the codebase tooling once there is a strategy worth re-sweeping.

---

## Step 5 — Cost Stress Test

Take the best candidate from Step 4 and **double** commission and slippage assumptions. Does it still work?

| Outcome | Interpretation |
|---|---|
| Survives 2x costs with degraded but acceptable Sharpe (e.g., 0.7 → 0.5) | Probably real |
| Goes from 0.7 → 0.1 at 2x costs | Probably overfit to favorable cost assumptions; kill |

Real fills include events not modeled: limit-up/limit-down halts, fast markets, dislocated Sunday opens, occasional outsized slippage. Stress testing accounts for this.

---

## Step 6 — Out-of-Sample Validation (ONE SHOT)

Run the locked candidate on 2023–present data. **One shot. No tweaking after seeing results.**

### Acceptable

- OOS Sharpe somewhat lower than IS (normal — trend has had a hard time recently, OOS includes 2024–25 policy regime)
- OOS drawdowns somewhat larger than IS
- Equity curve shape consistent with IS — slow drift, occasional drawdowns, no catastrophic single events

### Not Acceptable

- OOS Sharpe < 0 or near zero
- A drawdown in OOS materially larger than anything seen IS
- Equity curve shape qualitatively different from IS

### Pre-Committed OOS Interpretation Rule

Decide **before looking at OOS** how to interpret underperformance. Suggested framing:

| IS Sharpe | OOS Sharpe | Interpretation | Action |
|---|---|---|---|
| 0.7 | 0.3 | Plausibly real strategy degraded by regime | Proceed with caution |
| 0.7 | 0.0 | Ambiguous — could be regime, could be broken | Pause; consider extending OOS window before deciding |
| 0.7 | −0.2 | Strategy is not what was thought | **Kill** |

If OOS fails: **do not tweak and re-test.** Either kill the strategy or document why OOS is uninformative and acquire fresh data before any further testing.

---

## Step 7 — Paper Trading

**Minimum 3 months, ideally 6.**

### What Paper Tests

- Does live infrastructure produce fills consistent with backtest assumptions?
- Does real-time signal computation match what the backtest produced?
- Are there execution edge cases (rolls, exchange holidays, partial fills, contract changes) the backtest missed?
- Can the strategy be held psychologically through a paper drawdown? There will be one in 3–6 months.

### End-of-Paper Comparison

Compare paper fills to backtest assumptions. If paper slippage is 2x what was modeled, the Step 5 cost stress test was the right exercise.

### What Paper Does NOT Validate

- Real fills in fast markets
- Real slippage during specific weekend gap events
- Psychology under real-money drawdown

---

## Step 8 — Pre-Live Checklist

Before any live capital, close the `RISK.md` gaps:

- [ ] System-wide per-order size limit enforced in `orders/order_handler.py`
- [ ] Kill switch implemented and tested
- [ ] Daily loss limit implemented (per `ROADMAP.md` backlog)
- [ ] Stale data / disconnect guard before submitting orders
- [ ] Position size limit enforced at order layer (not just strategy layer)
- [ ] Buying power / margin headroom check
- [ ] PDT floor monitoring (alert if equity approaches $25k threshold)
- [ ] Alerting on order rejections, connection drops, unexpected position state
- [ ] Reconnect logic for IBKR socket drops (error codes 1100/1102)
- [ ] Documented runbook for "something is wrong, what do I do?"
- [ ] Account number changed to live account, port changed to 7496, **verified twice**

---

## Step 9 — Live, Small

Smallest sizing that exercises the full system. For micros: possibly 1 contract per instrument regardless of vol scaling, just to see end-to-end behavior with real money.

### Scale Up Only After

- A live drawdown has been seen and held through without panicking
- Live fills match paper fills statistically
- System has run unattended through at least one weekend without incident
- No surprises in commissions, margin calls, or any other operational concern

---

## Timeline Expectation

Realistic timeline from "start research" to "live with meaningful size":

| Phase | Duration |
|---|---|
| Steps 1–4 (research through parameter sensitivity) | 4–6 weeks |
| Steps 5–6 (cost stress + OOS) | 1–2 weeks |
| Step 7 (paper) | 3–6 months minimum |
| Step 8 (pre-live checklist) | 2–4 weeks of focused work |
| Step 9 (live small → scaled) | 3–6 months |
| **Total** | **9–15 months** |

Compressing this is the most common path to losing money.

---

## Open Decisions

Items where docs are silent and a commitment is needed before starting. Track and resolve.

| # | Decision | Recommendation | Status |
|---|---|---|---|
| 1 | Continuous futures roll methodology — needs documentation in `DATA_MODEL.md` | Ratio-adjusted for signals; unadjusted for PnL | Open |
| 2 | Include micro FX/rates in initial basket? | No — start equity + metals + crude; add later | Open |
| 3 | Pre-committed OOS interpretation rule | Drafted above (Step 6 table); commit before research | Open |
| 4 | Parameter sweep tooling — notebook or codebase build? | Notebook for v1; codebase once a strategy is worth re-sweeping | Open |
| 5 | Specific kill criteria for live (Sharpe, DD thresholds, time windows) | Starting points in Step 0 table; commit before research | Open |

---

## Progress Log

Append entries as research progresses. Date, what was done, what was learned.

| Date | Step | Notes |
|---|---|---|
| YYYY-MM-DD | — | — |

---

## Handoff note for Claude Code:
This conversation produced a research plan for PaperStreet's first strategy: time-series momentum on a diversified CME micros basket (MES, MNQ, M2K, MGC, MCL — possibly micro FX/rates as v2). Hold through overnights and weekends with conservative vol-target sizing (~10-12% annualized portfolio vol). No code changes proposed yet — research will happen in research/ notebooks. Several open infra/doc questions surfaced that aren't currently in design docs: (1) continuous futures roll methodology needs a decision and documentation in DATA_MODEL.md (suggested: ratio-adjusted for signals, unadjusted for PnL); (2) RISK.md gaps must be closed before any live trading — specifically per-order size limit, kill switch, daily loss limit, stale-data guard, reconnect logic; (3) the ROADMAP.md backlog item for parameter sweep tooling on the custom engine is a likely near-term need; (4) specific OOS interpretation criteria and live kill criteria need to be committed in writing. None of these need code yet, but flagging for prioritization when research surfaces concrete need.