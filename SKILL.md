# ClawSavings — Israeli Discounts & Price Comparison

## When to Use This Skill

Activate when the user asks about:
- **Saving money** on purchases in Israel
- **Best card/club** to use at a specific store
- **Cheapest place** to buy a product
- **Discounts, vouchers, deals** for Israeli stores
- **Price comparison** across supermarkets
- Questions in Hebrew like: "איפה הכי זול", "באיזה כרטיס כדאי", "איפה יש הנחה"

## Knowledge Base

Read the KB from: `~/.openclaw/workspace/skills/clawsavings/discounts.json`

### Schema Overview

```
discounts.json
├── sources        — all discount sources (htzone, poalim_wonder, etc.)
├── categories     — organized by type (supermarkets, pharma, fashion, etc.)
│   └── [category]
│       ├── he           — Hebrew name
│       ├── stores       — list of stores in this category
│       └── sources      — which discount sources apply
│           └── [source_id]
│               ├── type         — pos_discount / voucher / cashback / price_comparison
│               ├── max_pct      — max percentage off (structural layer)
│               ├── deals        — specific voucher prices (deal layer)
│               └── cached_at    — when deals were last refreshed
├── quick_lookup
│   ├── store_to_category     — map store name → category
│   └── best_sources_by_category — ranked sources per category
└── meta
    └── cache_ttl_days        — 30 days
```

## Decision Logic

### Question: "Which card/club should I use at store X?"

1. Look up store in `quick_lookup.store_to_category`
2. Get category's `sources` 
3. For each source, check:
   - `type` — is it POS discount (automatic) or voucher (need to buy)?
   - `max_pct` — what's the maximum savings?
   - `deals` — any specific current deals?
4. Rank by effective savings percentage
5. Return top options with practical notes

**Example response:**
```
לויקטורי יש כמה אופציות:
1. **פועלים וונדר** — שובר ₪300 ב-₪259 + 50 נקודות (~13.7% הנחה)
2. **כרטיס הייטקזון** — עד 20% אוטומטית במעמד החיוב
3. **שוברים הייטקזון** — צריך לבדוק מחיר עדכני באתר
```

### Question: "Where's cheapest for product X?"

For **supermarket products**:
1. Note that gov XML data is the authoritative source
2. Point to the scraper: `https://github.com/OpenIsraeliSupermarkets/israeli-supermarket-scarpers`
3. Provide general knowledge ranking:
   - **Cheapest overall:** רמי לוי, אושר עד
   - **Good value:** ויקטורי, יינות ביתן  
   - **Premium pricing:** שופרסל דיל, AM:PM
   - **Depends on item:** הכי חשוב להשוות מחירים ספציפיים

**Example response:**
```
באופן כללי, רמי לוי ואושר עד הכי זולים לסל קניות רגיל.
לבדיקה מדויקת של מוצר ספציפי — אפשר להשתמש בסורק מחירי הממשלה: 
https://github.com/OpenIsraeliSupermarkets/israeli-supermarket-scarpers

אם יש לך כרטיס הייטקזון או פועלים וונדר, שווה לשלב עם שוברים.
```

### Question: General "how to save money on X"

1. Identify category
2. List all applicable sources from `best_sources_by_category`
3. Explain each option briefly
4. Recommend the best combination

## Cache Refresh Logic

When `cached_at` is `null` or older than 30 days:

1. **Do NOT block the response** — answer with structural data (max_pct)
2. Note that specific deal prices may be stale
3. If user needs exact voucher prices:
   - Use browser tool to check the source URL
   - Parse current deals
   - Update `deals` array and `cached_at` in discounts.json
   - Save the updated JSON

### Refresh URLs by Source

| Source | URL to Check |
|--------|--------------|
| htzone_club | `https://www.htzone.co.il/sale/{category_id}` |
| poalim_wonder | `https://www.bankhapoalim.co.il/he/Poalim-Wonder` |

**Note:** Both require login. If browser can't access, note that login is required and suggest user check manually.

## Output Format

- **Language:** Hebrew preferred (users in WhatsApp group speak Hebrew)
- **Tone:** Helpful, practical, no fluff
- **Format:** Concise bullet points, ranked by savings
- **Include:** Specific numbers when available (₪300 → ₪259)
- **Don't include:** Long explanations, marketing fluff

### Template

```
[Store/Category question]:

הכי כדאי:
1. **[Source]** — [specific deal or max %]
2. **[Source]** — [specific deal or max %]

💡 [One practical tip if relevant]
```

## Examples

### User: "באיזה כרטיס כדאי לסופר-פארם?"

```
לסופר-פארם:

1. **כרטיס הייטקזון** — עד 20% אוטומטית בקופה
2. **שוברים הייטקזון** — צריך לבדוק מחיר עדכני

💡 אם יש לך כרטיס הייטקזון, פשוט תשלם איתו — ההנחה אוטומטית
```

### User: "איפה הכי זול לקנות חלב?"

```
באופן כללי:
- **רמי לוי / אושר עד** — הכי זולים
- **ויקטורי / יינות ביתן** — מחירים סבירים
- **שופרסל / AM:PM** — יקרים יותר

לבדיקה מדויקת של מוצר ספציפי יש סורק מחירים ממשלתי (קוד פתוח).

💡 אם קונים בכמויות, שווה לשלב עם שובר מפועלים וונדר
```

### User: "יש הנחות לוולט?"

```
לוולט:

**פועלים וונדר** — שובר ₪100 ב-₪80 + 25 נקודות (20% הנחה!)

💡 זה הדיל הכי טוב שיש כרגע למשלוחים
```

## Maintenance

### Quarterly Review
- Check if htzone/poalim benefits changed
- Update `max_pct` values in structural layer
- Update `last_reviewed` in JSON root

### On-Demand Refresh
- When user asks for specific voucher price and cache is stale
- Browser automation to scrape current deals
- Update `deals` array + `cached_at`

## Limitations

1. **Login-required sources:** Can't auto-refresh htzone/poalim without credentials
2. **Gov XML integration:** Not yet implemented — point to scraper repo
3. **Real-time prices:** Voucher prices change; always note when data is stale
