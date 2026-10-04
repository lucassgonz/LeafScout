import { marketPriceFor, MARKET_PRICES, priceChangePercent } from '../marketPrices';

describe('marketPrices data', () => {
  it('has a price entry for all three crops', () => {
    expect(marketPriceFor('coffee')).toBeDefined();
    expect(marketPriceFor('cassava')).toBeDefined();
    expect(marketPriceFor('bean')).toBeDefined();
  });

  it('every entry has a positive latest price and at least one trend point', () => {
    for (const cropId of Object.keys(MARKET_PRICES) as Array<keyof typeof MARKET_PRICES>) {
      const price = MARKET_PRICES[cropId];
      expect(price.latest_avg_usd_per_kg).toBeGreaterThan(0);
      expect(price.trend.length).toBeGreaterThan(0);
    }
  });

  it('every entry cites a source', () => {
    for (const cropId of Object.keys(MARKET_PRICES) as Array<keyof typeof MARKET_PRICES>) {
      expect(MARKET_PRICES[cropId].source).toMatch(/WFP/);
    }
  });
});

describe('priceChangePercent', () => {
  it('computes percent change from the first to the latest trend point', () => {
    const price = {
      commodity: 'Test',
      reference_country: 'Testland',
      unit: 'kg',
      latest_date: '2026-06-01',
      latest_avg_usd_per_kg: 1.1,
      latest_n_markets: 5,
      trend: [
        { date: '2026-01-01', avg_usd_per_kg: 1.0, n_markets: 5 },
        { date: '2026-06-01', avg_usd_per_kg: 1.1, n_markets: 5 },
      ],
      source: 'WFP Food Prices via HDX',
      note: '',
    };
    expect(priceChangePercent(price)).toBeCloseTo(10, 5);
  });

  it('returns a negative number when price dropped', () => {
    const price = {
      commodity: 'Test',
      reference_country: 'Testland',
      unit: 'kg',
      latest_date: '2026-06-01',
      latest_avg_usd_per_kg: 0.8,
      latest_n_markets: 5,
      trend: [
        { date: '2026-01-01', avg_usd_per_kg: 1.0, n_markets: 5 },
        { date: '2026-06-01', avg_usd_per_kg: 0.8, n_markets: 5 },
      ],
      source: 'WFP Food Prices via HDX',
      note: '',
    };
    expect(priceChangePercent(price)).toBeCloseTo(-20, 5);
  });
});
