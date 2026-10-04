#!/usr/bin/env python
# coding: utf-8


# ======================================================================
# # MotorPH Sales Data Preprocessing
# 
# Cleans the raw Product List and Sales datasets and saves the cleaned versions for use in the Product Analysis notebook.
# ======================================================================

# ======================================================================
# ## 1. Import Library
# ======================================================================

# In[ ]:


import pandas as pd


# ======================================================================
# ## 2. Load the Datasets
# ======================================================================

# In[ ]:


# Confirm the current working directory and check that the expected files are here
import os

print(os.getcwd())
print(os.listdir())


# In[ ]:


# Load the raw Product List and raw Sales datasets
products = pd.read_csv("MotorPH_Products_List_2025.csv")

sales = pd.read_csv("MotorPH_Sales Data-3rd Quarter-Year 2025.csv")


# ======================================================================
# ## 3. Inspect the Datasets
# ======================================================================

# In[ ]:


# Preview the first few rows of the Product List dataset
products.head()


# In[ ]:


# Preview the first few rows of the Sales dataset
sales.head()


# In[ ]:


# Check column names, data types, and non-null counts for the Product List
print("=== PRODUCT LIST INFORMATION ===")
products.info()


# In[ ]:


# Check column names, data types, and non-null counts for the Sales dataset
print("=== SALES DATASET INFORMATION ===")
sales.info()


# In[ ]:


# Define a reusable data-quality check instead of writing the same
# missing-value and duplicate checks out separately for each dataset --
# this way both datasets are checked with identical logic, and adding a
# third dataset later would only need one extra function call, not a
# third copy of these print statements
def check_data_quality(dataframe, name):
    print(f"=== {name.upper()} DATA QUALITY CHECK ===")
    print("Shape:", dataframe.shape)
    print("Duplicate rows:", dataframe.duplicated().sum())
    print("Missing values per column:")
    print(dataframe.isnull().sum())
    print()

check_data_quality(products, "Product List")
check_data_quality(sales, "Sales Dataset")


# In[ ]:


# Confirm every product has a unique EntrNo, and list all product IDs
print("Duplicate Product IDs:", products["EntrNo"].duplicated().sum())
print("Product IDs:")
print(products["EntrNo"].tolist())


# In[ ]:


# Review product names, and the categorical values in the Sales dataset
print("=== PRODUCT NAMES ===")
print(products["EntrName"].tolist())

print("\n=== SALES CLIENT TYPES ===")
print(sales["client_type"].value_counts(dropna=False))

print("\n=== SALES PAYMENT TYPES ===")
print(sales["payment"].value_counts(dropna=False))


# In[ ]:


# Preview how Product Type looks when extracted from EntrDetails
# (the text before the "/" separator) -- this is applied for real later,
# in the Product Analysis notebook
product_types = products["EntrDetails"].str.split("/").str[0].str.strip()

print("=== PRODUCT TYPES ===")
print(product_types.value_counts())


# ======================================================================
# ## 4. Create Working Copies
# ======================================================================

# In[ ]:


# Create working copies so the original raw data is never modified directly
products_clean = products.copy()
sales_clean = sales.copy()

print("Clean copies created successfully.")


# ======================================================================
# ## 5. Remove Duplicate Rows
# ======================================================================

# In[ ]:


# Remove exact duplicate rows from both cleaned datasets, and reset
# the index afterward so it runs cleanly from 0 with no gaps
products_clean = products_clean.drop_duplicates().reset_index(drop=True)
sales_clean = sales_clean.drop_duplicates().reset_index(drop=True)

print("Duplicate rows remaining after removal:")
print("Product List:", products_clean.duplicated().sum())
print("Sales Dataset:", sales_clean.duplicated().sum())


# ======================================================================
# ## 6. Handle Missing and Invalid Dates
# ======================================================================

# In[ ]:


# Identify which sales rows have a missing date, client_type, or payment value
missing_sales = sales_clean[
    sales_clean[["date", "client_type", "payment"]].isnull().any(axis=1)
]

missing_sales


# In[ ]:


# Fill missing categorical values with "Unknown" and convert the date
# column to a proper datetime type
sales_clean = sales.copy()

sales_clean["client_type"] = sales_clean["client_type"].fillna("Unknown")
sales_clean["payment"] = sales_clean["payment"].fillna("Unknown")

sales_clean["date"] = pd.to_datetime(
    sales_clean["date"],
    format="mixed",
    errors="coerce"
)

print("Date type:", sales_clean["date"].dtype)
print("Missing dates:", sales_clean["date"].isnull().sum())


# In[ ]:


# Identify which date values could not be parsed, so we know what will be dropped
test_dates = pd.to_datetime(
    sales["date"],
    format="mixed",
    errors="coerce"
)

failed_dates = sales[
    sales["date"].notna() & test_dates.isna()
]

print("Dates that failed conversion:")
print(failed_dates[["date"]])


# In[ ]:


# Drop the handful of rows with unparseable/invalid dates
sales_clean = sales_clean.dropna(subset=["date"]).copy()

print("Rows remaining:", len(sales_clean))
print("Missing dates:", sales_clean["date"].isnull().sum())


# ======================================================================
# ## 7. Validate and Correct Sales Totals and Prices
# ======================================================================

# In[ ]:


# Recompute total from unitprice x quantity and flag rows where the
# recorded total disagrees with that calculation
sales_clean["calculated_total"] = (
    sales_clean["unitprice"] * sales_clean["quantity"]
)

mismatched_totals = sales_clean[
    sales_clean["total"] != sales_clean["calculated_total"]
]

print("Rows with incorrect totals:", len(mismatched_totals))
mismatched_totals.head()


# In[ ]:


# Look up each sale's official unit price from the Product List and
# flag rows where the sale's unit price disagrees with it
price_lookup = products_clean.set_index("EntrName")["UnitPrice"]

sales_clean["product_list_price"] = sales_clean["product"].map(price_lookup)

price_mismatches = sales_clean[
    sales_clean["unitprice"] != sales_clean["product_list_price"]
]

print("Rows with unit price mismatch:", len(price_mismatches))

price_mismatches[
    ["product", "unitprice", "product_list_price", "quantity", "total"]
].head(20)


# In[ ]:


# List sales product names that don't match any name in the Product
# List -- these are most likely typos
unmatched_products = sales_clean[
    sales_clean["product_list_price"].isna()
]["product"].value_counts()

print("=== SALES PRODUCTS NOT FOUND IN PRODUCT LIST ===")
print(unmatched_products)


# In[ ]:


# Use fuzzy string matching to suggest the correct product name for
# each unmatched entry
from difflib import get_close_matches

official_products = products_clean["EntrName"].tolist()

print("=== POSSIBLE PRODUCT NAME CORRECTIONS ===")

for name in unmatched_products.index:
    matches = get_close_matches(
        name,
        official_products,
        n=3,
        cutoff=0.5
    )
    print(name, "->", matches)


# In[ ]:


# Apply the manually verified corrections for the typo'd product names
product_name_corrections = {
    "Yamaha Serow 25x": "Yamaha Serow 250",
    "KTM 790 Dukx": "KTM 790 Duke",
    "Suzuki Raider R150 Fx": "Suzuki Raider R150 Fi",
    "Kawasaki KLX 23x": "Kawasaki KLX 230",
    "Bajaj CT12x": "Bajaj CT125",
    "Yamaha Sniper 15x": "Yamaha Sniper 155",
    "Bristol Bobber 65x": "Bristol Bobber 650",
    "Yamaha MT-1x": "Yamaha MT-15",
    "Benelli 502x": "Benelli 502C",
    "TVS Apache RTR 200 4x": "TVS Apache RTR 200 4V",
    "Motorstar Xplorer 250x": "Motorstar Xplorer 250R",
    "CFMoto 300Sx": "CFMoto 300SR",
    "Honda ADV 16x": "Honda ADV 160"
}

sales_clean["product"] = sales_clean["product"].replace(product_name_corrections)

print("Product names corrected.")


# In[ ]:


# Re-check the price lookup now that the product names have been corrected
price_lookup = products_clean.set_index("EntrName")["UnitPrice"]

sales_clean["product_list_price"] = sales_clean["product"].map(price_lookup)

print(
    "Products still not found:",
    sales_clean["product_list_price"].isnull().sum()
)


# In[ ]:


# Confirm which rows still have a unit price that disagrees with the Product List
price_mismatches = sales_clean[
    sales_clean["unitprice"] != sales_clean["product_list_price"]
]

print("Rows with unit price mismatch:", len(price_mismatches))

price_mismatches[
    ["product", "unitprice", "product_list_price", "quantity", "total"]
].head(20)


# In[ ]:


# Correct mismatched unit prices using the official Product List price
sales_clean.loc[
    sales_clean["unitprice"] != sales_clean["product_list_price"],
    "unitprice"
] = sales_clean["product_list_price"]

# Recalculate total based on corrected unit price
sales_clean["total"] = (
    sales_clean["unitprice"] * sales_clean["quantity"]
)

# Refresh calculated_total too -- previously this was left stale from before
# the price correction above, so for any row whose unitprice just changed,
# calculated_total no longer matched total/unitprice/quantity in the saved file.
sales_clean["calculated_total"] = (
    sales_clean["unitprice"] * sales_clean["quantity"]
)

print("Unit prices corrected using Product List.")
print(
    "Remaining unit price mismatches:",
    (sales_clean["unitprice"] != sales_clean["product_list_price"]).sum()
)

print(
    "Remaining incorrect totals:",
    (sales_clean["total"] !=
     sales_clean["unitprice"] * sales_clean["quantity"]).sum()
)

print(
    "Remaining stale calculated_total rows:",
    (sales_clean["calculated_total"] !=
     sales_clean["unitprice"] * sales_clean["quantity"]).sum()
)


# ======================================================================
# ## 8. Final Validation
# ======================================================================

# In[ ]:


# Run a final set of checks to confirm both datasets are fully cleaned
print("=== FINAL CLEANING VALIDATION ===")

print("\nProduct List:")
print("Rows:", len(products_clean))
print("Missing values:", products_clean.isnull().sum().sum())
print("Duplicate rows:", products_clean.duplicated().sum())
print("Duplicate Product IDs:", products_clean["EntrNo"].duplicated().sum())

print("\nSales Dataset:")
print("Rows:", len(sales_clean))
print("Missing values:", sales_clean.isnull().sum().sum())
print("Duplicate rows:", sales_clean.duplicated().sum())

print(
    "Products not matched:",
    sales_clean["product_list_price"].isnull().sum()
)

print(
    "Price mismatches:",
    (sales_clean["unitprice"] != sales_clean["product_list_price"]).sum()
)

print(
    "Incorrect totals:",
    (sales_clean["total"] !=
     sales_clean["unitprice"] * sales_clean["quantity"]).sum()
)


# ======================================================================
# ## 9. Save Cleaned Datasets
# ======================================================================

# In[ ]:


# Save the cleaned Product List and Sales datasets for use in the
# Product Analysis notebook
products_clean.to_csv(
    "MotorPH_Products_List_2025_Cleaned.csv",
    index=False
)

# product_list_price was only a lookup helper used to find/verify price
# mismatches -- it always equals unitprice once cleaning is done, so it
# does not need to ship in the final file.
sales_clean_to_save = sales_clean.drop(columns=["product_list_price"])

sales_clean_to_save.to_csv(
    "MotorPH_Sales_2025_Cleaned.csv",
    index=False
)

print("Cleaned files saved successfully!")
print("Product List: MotorPH_Products_List_2025_Cleaned.csv")
print("Sales Dataset: MotorPH_Sales_2025_Cleaned.csv")

