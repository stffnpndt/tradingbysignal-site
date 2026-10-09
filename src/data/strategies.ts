// The live strategies, in the order they went live.
// `glyph` selects the small diagram drawn next to each strategy.

export type Glyph = 'atr' | 'ichimoku' | 'momentum' | 'rsi' | 'ladder';

export interface Strategy {
  id: string;
  name: string;
  timeframe: string;
  market: string;
  liveSince: string; // ISO date
  summary: string;
  glyph: Glyph;
}

export const strategies: Strategy[] = [
  {
    id: 'mr-atr',
    name: 'ATR Mean Reversion',
    timeframe: 'Daily',
    market: 'Crypto spot, broad universe',
    liveSince: '2025-02-24',
    summary:
      'Buys sharp sell-offs that are large relative to the coin’s own volatility (ATR) and sells into the rebound, usually within a few days. Up to five positions at a time.',
    glyph: 'atr',
  },
  {
    id: 'tf-ichimoku',
    name: 'Ichimoku Trend Following',
    timeframe: '4-hour',
    market: 'Bitcoin and Ether, spot',
    liveSince: '2025-08-01',
    summary:
      'Rides established trends using the Ichimoku cloud. A daily Bitcoin breakout filter keeps it out of the market when the broader trend is weak.',
    glyph: 'ichimoku',
  },
  {
    id: 'csm',
    name: 'Cross-Sectional Momentum',
    timeframe: 'Weekly',
    market: 'Crypto perpetual futures, long and short',
    liveSince: '2026-01-31',
    summary:
      'Ranks a filtered set of coins by recent performance every week. Goes long the strongest and short the weakest, so it can earn in rising and falling markets.',
    glyph: 'momentum',
  },
  {
    id: 'mr-rsi',
    name: 'RSI Mean Reversion',
    timeframe: 'Daily',
    market: 'Crypto spot',
    liveSince: '2026-07-25',
    summary:
      'Waits for a deeply oversold short-term RSI and scales in over up to three tranches as the dip extends, then exits once price recovers.',
    glyph: 'rsi',
  },
  {
    id: 'rsi-red-legs',
    name: 'RSI Red Legs',
    timeframe: 'Daily',
    market: '20 large crypto assets and the Nasdaq-100 (QQQ)',
    liveSince: '2026-09-18',
    summary:
      'Builds a position in up to five equal legs while a sell-off continues, guided by RSI, and closes the whole ladder on the rebound.',
    glyph: 'ladder',
  },
];
