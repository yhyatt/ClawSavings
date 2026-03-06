# ClawSavings 💰

Israeli discounts and price comparison skill for [OpenClaw](https://openclaw.dev).

Answers two questions:
1. **"Where's cheapest for product X?"** — via Israeli supermarket price data
2. **"Which card/club should I use at store Y?"** — via structured discount knowledge base

## Features

- 📊 **Discount KB** — which card/club gives the best deal at each store
- 🏪 **12+ categories** — supermarkets, pharma, fashion, electronics, entertainment, and more
- 🇮🇱 **Hebrew-first** — designed for Israeli users (WhatsApp groups, Telegram)
- 🔄 **Cache-aware** — serves fast from cache, refreshes stale data on-demand

## Discount Sources

| Source | Type | Login Required |
|--------|------|----------------|
| **HiTech Zone Card** | POS discount (up to 20%) | ✅ |
| **HiTech Zone Club** | Vouchers | ✅ |
| **HiTech Zone PRO²** | Cashback (up to 15%) | ✅ |
| **Poalim Wonder** | Vouchers + points | ✅ |
| **Gov Price Transparency** | Full price comparison | ❌ |

## Architecture

### Two-Layer Knowledge Base

```
discounts.json
├── Structural Layer (near-static)
│   └── Which card/club covers which category
│   └── Approximate % off
│   └── Update: manually, quarterly
│
└── Deal Layer (dynamic)
    └── Specific voucher prices (e.g., Victory ₪300 → ₪259)
    └── cached_at timestamp
    └── Refresh: on-demand when stale (30-day TTL)
```

**Why two layers?**
- Structural data rarely changes — no need to scrape constantly
- Deal prices change often — cache with TTL, refresh when needed
- Fast responses from cache, accurate data when it matters

### On-Demand Enrichment

When a user asks about specific voucher prices:
1. Check `cached_at` timestamp
2. If null or >30 days old → mark as potentially stale
3. If exact price needed → browser lookup → update cache → respond
4. Subsequent requests served from cache

## Categories

| Category | Hebrew | Example Stores |
|----------|--------|----------------|
| supermarkets | רשתות מזון | שופרסל, רמי לוי, ויקטורי |
| restaurants | מסעדות | ארומה, קפה קפה, לנדוור |
| delivery | משלוחים | וולט, תן ביס |
| pharma | פארם | סופר-פארם, ניופארם |
| fashion | אופנה | קסטרו, פוקס, זארה |
| electronics | אלקטרוניקה | KSP, באג, איווורי |
| entertainment | בילויים | יס פלאנט, סינמה סיטי |
| travel | תיירות | איסתא, בוקינג |
| home_renovation | ריהוט | איקאה, אייס |
| gym_sports | כושר | הולמס פלייס |
| fuel | דלק | פז, סונול |
| kids_baby | ילדים | שילב, טויס אר אס |

## Usage

### Installation

Copy to your OpenClaw skills directory:

```bash
cp -r ClawSavings ~/.openclaw/workspace/skills/clawsavings
```

### Example Queries

**Hebrew (primary):**
- "באיזה כרטיס כדאי לסופר-פארם?"
- "איפה הכי זול לקנות חלב?"
- "יש הנחות לוולט?"
- "מה ההנחות בהייטקזון?"

**English:**
- "What's the best card for Super-Pharm?"
- "Where's cheapest for groceries?"
- "Any Wolt discounts?"

## Manual KB Updates

### Update Structural Data (quarterly)

Edit `discounts.json` and update:
- `max_pct` values when card benefits change
- `stores` arrays when new chains open
- `sources` when new discount programs launch

### Update Deal Prices

```bash
# Run refresh script (requires browser automation)
python scripts/refresh_deals.py --source poalim_wonder

# Or manually edit discounts.json:
# 1. Find the source in the category
# 2. Update deals array with current prices
# 3. Set cached_at to today's date
```

## Future Plans

### Gov XML Price Integration

Full product-level price comparison via mandatory government transparency data:
- Scraper: https://github.com/OpenIsraeliSupermarkets/israeli-supermarket-scarpers
- Covers: Shufersal, Rami Levy, Victory, Yeinot Bitan, Mega, Carrefour, etc.
- **No auth needed** — fully open data

Implementation:
1. Set up daily XML scrape job
2. Index products by barcode
3. Query: "where's cheapest for [product]" → return ranked store prices

### Browser Automation for Deal Refresh

Automated refresh for login-required sources:
- Store htzone/poalim credentials securely
- Periodic scrape of voucher pages
- Update deal layer automatically

## File Structure

```
clawsavings/
├── SKILL.md          # Agent instructions
├── discounts.json    # Knowledge base
├── README.md         # This file
└── scripts/
    └── refresh_deals.py  # Deal refresh automation (stub)
```

## Contributing

1. Fork the repo
2. Update KB with new deals/sources
3. Test with sample queries
4. PR with description of changes

## License

MIT
