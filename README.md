# MotorPH Data Cleaning & Analysis — Instructions and Design Rationale

This document explains **how to run** `MotorPH_Preprocessing` and `MotorPH_Product_Analysis`, and — more importantly — **why each step was done the way it was**, so the choices can be explained or defended (e.g. in a viva, a report, or to a reviewer) rather than just followed blindly.

---

## 1. How to run these notebooks

1. Put these four files in the **same folder**:
   - `MotorPH_Preprocessing.ipynb`
   - `MotorPH_Product_Analysis.ipynb`
   - `MotorPH_Products_List_2025.csv` (raw)
   - `MotorPH_Sales Data-3rd Quarter-Year 2025.csv` (raw)
2. Open `MotorPH_Preprocessing.ipynb` first and run all cells top to bottom. It produces two new files in the same folder:
   - `MotorPH_Products_List_2025_Cleaned.csv`
   - `MotorPH_Sales_2025_Cleaned.csv`
3. Then open `MotorPH_Product_Analysis.ipynb` and run all cells — it reads the *cleaned* Products List file produced in step 2.

The notebooks use relative filenames (`pd.read_csv("MotorPH_Products_List_2025.csv")`, not a full path like `/Users/you/Desktop/...`) on purpose — see §2.9 below for why.

---

## 2. Preprocessing — decisions and why they were made

### 2.1 Why make `.copy()` of the raw DataFrames before touching them
```python
products_clean = products.copy()
sales_clean = sales.copy()
```
The original `products` / `sales` DataFrames are kept untouched. If a cleaning step turns out to be wrong, or a stakeholder asks "what did the raw data actually look like," you can always go back to the untouched original in the same session instead of having to reload the CSV. This is standard defensive practice — never clean data in place on your only copy of "the truth."

### 2.2 Why check for missing values and duplicates *before* doing anything else
Running `.isnull().sum()` and `.duplicated().sum()` right after loading, before any transformation, establishes a **baseline**. Every later step (date parsing, price correction, etc.) can change these numbers, so you need to know the starting point to be able to say, at the end, exactly what your cleaning fixed and by how much.

### 2.3 Why fill missing `client_type` / `payment` with `"Unknown"` instead of dropping those rows
```python
sales_clean["client_type"] = sales_clean["client_type"].fillna("Unknown")
sales_clean["payment"] = sales_clean["payment"].fillna("Unknown")
```
These are categorical columns, and the missing values were a small share of rows. Dropping a row loses *every* column's data for that sale (date, product, price, quantity — all of it), just because one categorical field was blank. Replacing with an explicit `"Unknown"` label keeps the rest of that row's information (which is still valid and useful for the Product Analysis step) while being honest that the category itself wasn't recorded — it doesn't pretend to know something it doesn't. Best practice would differ if the missing rate were very high (then you'd question whether the column is reliable at all), or if the column were numeric (an "Unknown" text label can't sit in a numeric column, so you'd use a statistic like the median instead).

### 2.4 Why `pd.to_datetime(..., format="mixed", errors="coerce")` instead of a single fixed format
Real-world data entered by different people over time is rarely in one consistent date format. `format="mixed"` tells pandas to figure out each row's format individually rather than assuming they're all identical, and `errors="coerce"` turns any date pandas genuinely can't parse into `NaT` instead of crashing the whole script. This means one bad date doesn't stop the entire pipeline — it just gets flagged for the next step.

### 2.5 Why drop rows with unparseable dates rather than guess or fill them in
```python
sales_clean = sales_clean.dropna(subset=["date"]).copy()
```
There is no safe way to *invent* a transaction date — unlike a missing category, a wrong date could put a real sale in the wrong quarter, month, or reporting period, silently corrupting every date-based analysis downstream. Since only a handful of rows were affected, dropping them is a small, honest cost compared to the risk of fabricating a date that looks plausible but is wrong.

### 2.6 Why fuzzy-match unmatched product names instead of just dropping or ignoring them
```python
from difflib import get_close_matches
matches = get_close_matches(name, official_products, n=3, cutoff=0.5)
```
Several sales rows didn't match any name in the Product List — but a manual look showed most of these were typos (e.g. `"KTM 790 Dukx"` for `"KTM 790 Duke"`), not genuinely unlisted products. `get_close_matches` surfaces likely corrections automatically instead of manually eyeballing hundreds of rows, but the matches are still reviewed and applied as an explicit, human-verified dictionary (`product_name_corrections`) rather than auto-applied blindly — fuzzy matching is a *suggestion* tool here, not an auto-correct, because a wrong auto-correction could quietly merge two genuinely different products.

### 2.7 Why the Product List's `UnitPrice` is treated as the source of truth for correcting sales prices, not the other way around
The Product List is the official price catalog — one row per product, curated and presumably audited. The Sales dataset is many independent transaction records entered over time, which is exactly where inconsistencies and data-entry mistakes accumulate. When the two disagree, it's far more likely a sales entry has a typo or was recorded with a stale price than that the master catalog is wrong for every mismatched row, so the catalog wins.

### 2.8 Why `calculated_total` is recomputed a *second* time, right after the price correction
```python
sales_clean["calculated_total"] = sales_clean["unitprice"] * sales_clean["quantity"]
mismatched_totals = ...   # first check, before price correction

# ... later, after prices are corrected ...
sales_clean["total"] = sales_clean["unitprice"] * sales_clean["quantity"]
sales_clean["calculated_total"] = sales_clean["unitprice"] * sales_clean["quantity"]  # refreshed again
```
This is the fix for a real bug found during review: `calculated_total` was originally computed once, *before* the unit-price correction step, and never refreshed afterward. For any row whose price got corrected, `calculated_total` silently went stale — it no longer matched the corrected `unitprice × quantity`, even though it looked like a valid check column. Any derived/diagnostic column needs to be recomputed after every step that changes the values it depends on — this is a general rule, not just a one-off fix: if you calculate something from columns A and B, and then modify A or B, the calculated column must be redone or it becomes misleading.

### 2.9 Why relative filenames instead of a full path like `/Users/you/Desktop/DataMS1/...`
A hardcoded absolute path only works on the one computer (and the one folder) it was written on. Anyone else — a classmate, a grader, a future you on a different laptop — would need to edit the code before it runs. A relative filename works for anyone as long as the notebook and its data files sit in the same folder, which is the more portable and reproducible default.

### 2.10 Why `product_list_price` is dropped before saving the final cleaned CSV
```python
sales_clean_to_save = sales_clean.drop(columns=["product_list_price"])
```
`product_list_price` was only ever a *working/helper* column used internally to look up and cross-check prices — by the end of cleaning it always equals `unitprice`, so it carries no additional information. Shipping it in the final file would just be redundant clutter for anyone consuming the cleaned dataset afterward. General rule: keep intermediate/helper columns out of your final deliverable unless they add real information.

---

## 3. Product Analysis — decisions and why they were made

### 3.1 Why derive `Product Type` from `EntrDetails` instead of assuming a category column exists
```python
df["Product Type"] = df["EntrDetails"].str.split("/").str[0].str.strip()
```
The raw data has no dedicated "category" column — the category is embedded as the first segment of a longer descriptive text field (e.g. `"Sport / Parallel-twin, liquid-cooled"`). Splitting on `"/"` and taking the first piece extracts that category without needing to manually retype or look up a category for all 50 products.

### 3.2 Why `product_counts_all` is computed once and reused for both the count and percentage columns
```python
product_counts_all = df["Product Type"].value_counts()
product_distribution = pd.DataFrame({
    "Product Count": product_counts_all,
    "Percentage": (product_counts_all / len(df) * 100).round(2)
})
```
An earlier draft called `.value_counts()` twice — once for the count column and again inside the percentage calculation. Since the underlying data doesn't change between those two calls, computing it once and reusing the result is both faster and removes any chance of the two numbers drifting apart if the code were edited later (e.g. if a filter were added before one of the two calls but not the other).

### 3.3 Why mean, min, and max are reported together for price (not just an average)
An average alone can hide the real spread of the data — two very different product lineups (all mid-priced vs. a few very cheap and a few very expensive) can have the same average price. Reporting the minimum and maximum alongside it, and separately identifying which specific products are the cheapest/most expensive, gives a fuller and more honest picture of the price range than the average by itself.

### 3.4 Why manufacturing/acquisition year counts are sorted by index (`.sort_index()`)
```python
manufacturing_counts = df["Manufacturing Date"].value_counts().sort_index()
```
`value_counts()` on its own sorts by *frequency* (most common year first), which is not useful when the years represent a timeline — you want 2018, 2019, 2020… in order so a trend over time is actually readable, not shuffled by which year happens to have the most products.

### 3.5 Why `groupby("Product Type")` is used instead of relying on the single overall average price
```python
price_by_type = df.groupby("Product Type")["UnitPrice"].agg(
    ["mean", "min", "max", "count"]
).sort_values("mean", ascending=False)
```
The overall average price (§3.3) tells you one number for the whole inventory, but it hides how much that number varies *between* categories — a single average can't tell you whether Scooters and Heritage bikes are priced similarly or wildly differently. Grouping by `Product Type` before aggregating breaks the single average into one average (plus min, max, and count) per category, which is what actually let us discover that Heritage motorcycles average ₱842,000 while Commuter bikes average only ₱57,950 — a gap the single overall average completely hides. Sorting the result by mean price, rather than leaving it in whatever order the categories first appear, also makes the highest- and lowest-priced categories immediately readable without having to scan the whole table.

---

## 4. What was verified, and how

Every statistic in the accompanying report was independently recomputed directly from the cleaned CSV files with pandas — not just copied from a notebook's saved output — specifically so that a stale or manually-edited output cell couldn't slip an incorrect number into the final report. The `calculated_total` staleness bug (§2.8) was caught this way: comparing the report's numbers against a fresh, independent recalculation surfaced a mismatch that a plain re-read of the notebook would have missed, because the notebook's *old* saved output looked internally consistent even though it no longer matched the underlying corrected data.

---

## 5. Common issues and troubleshooting

- **`FileNotFoundError` when reading a CSV.** The notebooks use relative filenames (§2.9), so this almost always means the notebook and the CSV are not in the same folder, or the filename doesn't match exactly (check for hidden trailing spaces or a different file extension, e.g. `.csv` vs `.CSV`). Fix: place the `.ipynb` and the `.csv` files together in one folder, and confirm the filename in the code matches the actual file exactly.
- **`KeyError` on a column name (e.g. `"UnitPrice"`, `"EntrDetails"`).** This means the DataFrame doesn't have a column by that exact name — usually because `MotorPH_Product_Analysis.ipynb` was run against the *raw* Products List instead of the *cleaned* one. Fix: run `MotorPH_Preprocessing.ipynb` completely first, confirm `MotorPH_Products_List_2025_Cleaned.csv` was created, and make sure the analysis notebook reads that cleaned file, not the raw one.
- **Numbers in a fresh run don't match the numbers in the report.** This is expected if you run only *part* of a notebook, or run cells out of order — later cells (e.g. `groupby` price comparisons) depend on columns created by earlier cells (e.g. the derived `Product Type` column in §3.1). Fix: use Restart & Run All (or Runtime → Run all in Colab) rather than re-running individual cells out of sequence.
- **A `NaN`/`NaT` shows up somewhere unexpected after re-running.** This is usually not a bug — it's the intended result of `errors="coerce"` (§2.4) or `.fillna("Unknown")` (§2.3) doing exactly what they're designed to do. Before treating it as an error, check whether that row was already flagged as having a missing or unparseable value in the earlier diagnostic step (§2.2).
- **The corrected product-name dictionary doesn't cover a name you're seeing.** This means the raw data has a typo variant that wasn't present when `product_name_corrections` (§2.6) was built. Fix: run the `get_close_matches` suggestion step again on the current data and extend the dictionary — don't assume the existing dictionary is exhaustive for a different or updated dataset.

---

## 6. Real-world relevance

Beyond satisfying the assignment's cleaning and analysis requirements, the specific choices documented here map onto decisions a real inventory or sales team would actually have to make. Treating the Product List as the price source of truth (§2.7) mirrors how a business reconciles a transactional system against a master catalog when the two disagree. Recording unmatched categories as `"Unknown"` instead of silently dropping rows (§2.3) mirrors how a real reporting pipeline should degrade gracefully instead of quietly losing data. And the category-level price comparison (§3.5) is the kind of finding that has direct business value: discovering that Scooters are MotorPH's highest-*volume* category but not its highest-*priced* one is exactly the sort of insight that would inform pricing strategy, inventory investment, or marketing focus in an actual dealership setting — not just an artifact of the assignment.

---

## Contributors: [Documentation](https://docs.google.com/document/d/1VFg7gmGbCpslOg42giInZZzJ0qiP5IykUMUImtbMHe4/edit?usp=sharing)
- Keren Jemimah Tabor-Abueg
- Christian Jess Torrefiel
- Xyril Anne Fabellon
- Reymar Navarro
