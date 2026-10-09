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
  details?: StrategyDetails;
}

// Content of a strategy's own page. Describes the logic at concept level
// only: no indicator lengths, thresholds or other parameters.
export interface StrategyDetails {
  tagline: string;
  facts: { label: string; value: string }[];
  idea: string[];
  // How positions are opened: either conditions that must all hold at once
  // ('checks'), or a repeating process ('steps', shown numbered).
  entry: {
    title: string;
    intro: string;
    kind: 'checks' | 'steps';
    items: { title: string; text: string }[];
    verdict: string;
    note?: string;
  };
  exit: {
    title: string;
    items: { title: string; text: string }[];
    note?: string;
  };
  risk: string[];
  goodIn: string[];
  badIn: string[];
}

const all: Strategy[] = [
  {
    id: 'mr-atr',
    name: 'ATR Mean Reversion',
    timeframe: 'Daily',
    market: 'Crypto spot, broad universe',
    liveSince: '2026-02-24',
    summary:
      'Buys sharp sell-offs that are large relative to the coin’s own volatility (ATR) and sells into the rebound, usually at the close of the same day. Up to five positions at a time.',
    glyph: 'atr',
    details: {
      tagline:
        'Waits below the market for sell-offs that overshoot, buys the panic, and is usually out again by the close of the same day.',
      facts: [
        { label: 'Markets', value: 'A broad set of liquid coins, spot' },
        { label: 'Chart', value: 'Daily candles' },
        { label: 'Direction', value: 'Long only' },
        { label: 'Leverage', value: 'None' },
        { label: 'Positions', value: 'Up to five, equal size' },
        { label: 'Typical holding', value: 'Less than a day' },
        { label: 'Live since', value: '24 February 2026' },
      ],
      idea: [
        'Crypto overreacts. On a day of heavy selling, liquidations and triggered stops push prices further than the news behind the move would justify, and part of that overshoot is often undone within hours. The strategy tries to be the buyer at the moment the sellers run out.',
        'It does not chase. Instead of buying at the market, it places an order well below the day’s low, and that order only fills if the selling carries on into an extreme. The distance is measured in the coin’s own volatility, so a quiet coin and a wild one are treated the same way. Each trade is small and short; the edge comes from repeating the same pattern across many coins.',
      ],
      entry: {
        title: 'When it buys',
        intro: 'An order is placed when two conditions meet at the daily close, and a trade only opens if the market then comes to that order:',
        kind: 'checks',
        verdict: 'Price reaches the order: the trade opens.',
        items: [
          {
            title: 'A weak day',
            text: 'The coin closes at or below the previous day’s low. Sellers are in control.',
          },
          {
            title: 'A restless market',
            text: 'Recent daily swings are larger than the coin’s longer-term average. Calm drifts lower are ignored.',
          },
          {
            title: 'An order below the low',
            text: 'A limit order is placed below the day’s low, at a distance scaled to recent volatility. It is valid for one day; if price does not get there, it is cancelled.',
          },
        ],
        note: 'There is deliberately no trend filter. The strategy buys sharp dips in rising and falling markets alike; in testing, adding a trend filter made the results worse.',
      },
      exit: {
        title: 'When it sells',
        items: [
          {
            title: 'First close in profit',
            text: 'If the day closes above the entry price, the position is sold at the close. Most trades end this way, on the same day they were bought.',
          },
          {
            title: 'No rebound',
            text: 'If the close stays weak compared with the coin’s short-term average, the position is sold as well. The bounce did not come, and the strategy does not wait for it.',
          },
          {
            title: 'Emergency stop',
            text: 'A wide stop is placed together with the order, so it is active from the moment of the fill. It is only meant for crashes that do not bounce at all.',
          },
        ],
        note: 'A position is only held overnight when the close lands between the two exit rules, which is rare.',
      },
      risk: [
        'No leverage. Coins are bought on the spot market, so a trade can never lose more than the capital in it.',
        'Capital is split into five equal slots, so a single coin is never more than a fifth of the strategy.',
        'Short holding times keep exposure low: most of the time the strategy holds nothing and waits.',
        'It buys into falling prices on purpose. When a sell-off turns into a crash, several positions can lose at once, and the emergency stop sits far below the entry.',
      ],
      goodIn: [
        'Volatile markets with sharp but short sell-offs, where panics are bought back quickly.',
        'Busy phases with many coins swinging at once, which produce more setups.',
      ],
      badIn: [
        'Crashes that keep going for days, where there is no rebound to sell into.',
        'Calm markets: few setups, and orders below the low are rarely reached.',
        'Market-wide sell-offs, when all five slots fill on the same day and the positions move together.',
      ],
    },
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
    details: {
      tagline:
        'Rides sustained trends in Bitcoin and Ether, but only once several independent signals agree that the trend is real.',
      facts: [
        { label: 'Markets', value: 'Bitcoin and Ether, spot' },
        { label: 'Chart', value: '4-hour candles' },
        { label: 'Direction', value: 'Long only' },
        { label: 'Leverage', value: 'None' },
        { label: 'Positions', value: 'One per asset' },
        { label: 'Trades per year', value: 'About 1 to 5' },
        { label: 'Live since', value: '1 August 2025' },
      ],
      idea: [
        'Crypto markets trend. When Bitcoin or Ether start a sustained move, it often runs for weeks or months, longer than most people expect. A trend-following strategy does not try to predict these moves. It waits until a trend is clearly under way, joins it, and stays in until the trend loses its drive.',
        'The hard part is telling a real trend from noise. On a 4-hour chart, price keeps producing short bursts that look like the start of something and then fade. This strategy deals with that by asking for several different views of the trend to agree before it buys, and by checking the state of the whole market, not just the coin it trades.',
      ],
      entry: {
        title: 'When it buys',
        intro: 'A trade opens only when all six checks pass at the same time:',
        kind: 'checks',
        verdict: 'All six agree: the trade opens.',
        items: [
        { title: 'Momentum', text: 'Short-term price momentum sits above its long-term balance point.' },
        { title: 'Cloud', text: 'The Ichimoku cloud under the current price points upward.' },
        { title: 'Long-term average', text: 'Price trades above a long-term moving average.' },
        { title: 'Ichimoku picture', text: 'A score that combines seven classic Ichimoku signals is positive overall.' },
        { title: 'Trend direction', text: 'A smoothed fast trend line runs above a slower one.' },
        {
          title: 'Bitcoin regime',
          text: 'Bitcoin itself is in an uptrend on the daily chart: it has broken out to a multi-week high above its long-term average, and no breakdown has ended that phase since.',
        },
        ],
        note: 'After a trade closes, the strategy waits a day before it can enter again, so it does not jump straight back into a trend that has just turned.',
      },
      exit: {
        title: 'When it sells',
        items: [
        {
          title: 'Momentum fades',
          text: 'The position closes when short-term momentum falls back below its long-term balance point. The trend has lost its drive, even if price has not fallen much yet.',
        },
        {
          title: 'Protective stop',
          text: 'At entry, a stop is set below the entry price, at a distance based on recent volatility. It limits the loss when a breakout fails straight away.',
        },
        ],
        note: 'The Bitcoin regime only decides whether new trades may open. Once a trade is running, the exit rules alone decide when it ends.',
      },
      risk: [
        'No leverage. Positions are bought on the spot market, so a trade can never lose more than the capital in it, and the protective stop is there to cut a failed trade early.',
        'Capital is split evenly between Bitcoin and Ether, with at most one position in each.',
        'Long only. In falling markets the strategy is simply out and holds cash.',
      ],
      goodIn: [
        'Long, persistent uptrends, such as bull markets in Bitcoin and Ether.',
        'Phases where Bitcoin leads the market higher and the rest follows.',
      ],
      badIn: [
        'Sideways, choppy markets, where trends start and fail repeatedly. The checks filter out many false starts, but not all of them.',
        'Sharp reversals. The strategy buys after a trend is visible and sells after it weakens, so it never catches the exact bottom or top and gives back part of each move.',
        'Bear markets. It stays out, which protects capital but earns nothing.',
      ],
    },
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
    details: {
      tagline:
        'Every week, it buys the strongest of the largest coins and shorts the weakest, betting that recent winners keep beating recent losers.',
      facts: [
        { label: 'Markets', value: 'The five largest coins, perpetual futures' },
        { label: 'Rebalancing', value: 'Weekly' },
        { label: 'Direction', value: 'Long and short' },
        { label: 'Leverage', value: '1.5x, isolated margin' },
        { label: 'Positions', value: 'Two or three at a time' },
        { label: 'Live since', value: '31 January 2026' },
      ],
      idea: [
        'Momentum is one of the most persistent effects in financial markets: assets that have done well recently tend to keep doing well for a while, and laggards tend to keep lagging. In crypto, where money rotates quickly between a handful of large coins, the effect is especially visible.',
        'Cross-sectional means the strategy does not ask whether a coin will go up. It asks which coins are doing best compared with the others. Holding the leaders and shorting the laggard turns that ranking into a position that can make money whether the market rises or falls, as long as the leaders keep beating the laggards.',
      ],
      entry: {
        title: 'How it trades',
        intro: 'Once a week, the strategy runs through the same cycle:',
        kind: 'steps',
        verdict: 'A week later, the cycle starts again.',
        items: [
          {
            title: 'Pick the field',
            text: 'Take the five largest coins by market value, without stablecoins. The list is reviewed twice a year, so the strategy always trades the market’s heavyweights.',
          },
          { title: 'Rank', text: 'Rank the five by how they performed over the past few weeks.' },
          { title: 'Read the market', text: 'Check whether Bitcoin trades above or below its medium-term trend.' },
          {
            title: 'Take positions',
            text: 'In an uptrend, go long the two strongest coins and short the weakest. Otherwise, go long only the strongest and short the weakest, so the book is balanced.',
          },
          { title: 'Hold', text: 'Keep the positions for one week, at equal size, then close them.' },
        ],
      },
      exit: {
        title: 'When it sells',
        items: [
          {
            title: 'After one week',
            text: 'Every position closes after a fixed week, whatever happened in between. There is no profit target; the next ranking decides what to hold.',
          },
          {
            title: 'No stop-loss',
            text: 'Risk is controlled by holding longs and shorts together, by the weekly reset and by modest leverage of 1.5x, not by stops. Each position uses isolated margin, so one trade can never draw on the rest of the account.',
          },
        ],
      },
      risk: [
        'Long and short at the same time. In a broad sell-off the short offsets part of the losses on the longs, and in a downtrend the book is balanced one against one.',
        'Leverage of 1.5x on perpetual futures, with isolated margin for each position.',
        'Equal size for every position, reset weekly, so no single coin dominates.',
        'Only the largest, most liquid coins, which keeps trading costs and slippage low.',
      ],
      goodIn: [
        'Markets with clear leaders, when money flows into a few coins for weeks at a time.',
        'Strong moves in either direction, as long as the coins move by different amounts.',
      ],
      badIn: [
        'Sudden reversals, when last week’s laggard jumps to the top. Short squeezes hit the short side hardest.',
        'Markets where all large coins move in lockstep, so the ranking carries little information.',
        'Quiet, sideways phases, where trading costs and funding eat the small differences.',
      ],
    },
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
    details: {
      tagline:
        'Buys short, sharp dips inside an uptrend, adds as the dip stretches, and sells everything at once when the bounce comes.',
      facts: [
        { label: 'Markets', value: 'Liquid coins, spot' },
        { label: 'Chart', value: 'Daily candles' },
        { label: 'Direction', value: 'Long only' },
        { label: 'Leverage', value: 'None' },
        { label: 'Positions', value: 'Up to four coins, three tranches each' },
        { label: 'Live since', value: '25 July 2026' },
      ],
      idea: [
        'In a healthy uptrend, sell-offs rarely last long. A few red days in a row push a coin far below where it traded a week earlier, short-term traders give up, and buyers who missed the trend step back in. The very short-term RSI measures exactly this kind of stretch: it drops to extreme lows after only a handful of falling days.',
        'The strategy does not buy the first sign of weakness. Most small dips end before they become interesting, so the first oversold days are only counted. Only if the selling continues does it start to buy, in equal tranches, so the deeper the dip goes, the lower the average price. When the bounce comes, the whole position is sold in one go.',
      ],
      entry: {
        title: 'How it trades',
        intro: 'Each dip runs through the same sequence, decided at the daily close:',
        kind: 'steps',
        verdict: 'The next dip starts a new count.',
        items: [
          {
            title: 'Healthy trend',
            text: 'A new sequence may only begin while the coin trades above its medium-term average.',
          },
          {
            title: 'Oversold',
            text: 'The short-term RSI falls deep into oversold territory. The count starts.',
          },
          {
            title: 'Let it run',
            text: 'The first oversold days are only counted, not bought. Dips that end quickly are skipped.',
          },
          {
            title: 'Scale in',
            text: 'From then on, every further oversold day adds one equal tranche, up to three in total.',
          },
          {
            title: 'Sell the bounce',
            text: 'Once the short-term RSI is back above neutral, the whole position is sold at the close. If that happens before the first tranche, the sequence ends without a trade.',
          },
        ],
        note: 'The trend check only decides whether a sequence may start. Once the count runs, further tranches are added even if price slips below the average.',
      },
      exit: {
        title: 'When it sells',
        items: [
          {
            title: 'Recovery',
            text: 'All tranches are sold together at the first daily close with the short-term RSI above neutral. There is no profit target beyond that; the strategy takes the bounce and steps aside.',
          },
          {
            title: 'No stop-loss',
            text: 'There is no stop. Risk is limited by the trend check at the start, by splitting each position into tranches, and by trading spot without leverage.',
          },
        ],
      },
      risk: [
        'No leverage. Coins are bought on the spot market, so a position can never lose more than the capital in it.',
        'Each coin has a fixed slot, and each slot is filled in equal tranches, so a single dip never commits the whole slot at the first price.',
        'At most four coins at a time, which limits how much is invested during a market-wide sell-off.',
        'No stop-loss. A dip that turns into a lasting decline is held until it bounces, which can take a while.',
      ],
      goodIn: [
        'Uptrends with short, sharp pullbacks that are bought back within days.',
        'Markets where sell-offs overshoot and snap back.',
      ],
      badIn: [
        'A trend that breaks: the dip keeps going after all tranches are in, and the position sits at a loss until a bounce comes.',
        'Long bear markets, where few sequences may start at all.',
        'Slow, grinding declines without the sharp drops the RSI reacts to.',
      ],
    },
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

// Always listed in the order the strategies went live.
export const strategies: Strategy[] = [...all].sort((a, b) => a.liveSince.localeCompare(b.liveSince));
