#!/usr/bin/env python
# coding: utf-8


# In[1]:


import pandas as pd


# In[2]:


# Confirm the current working directory and check that the expected files are here
import os

print(os.getcwd())
print(os.listdir())


# In[3]:


# Load the raw Product List and raw Sales datasets
products = pd.read_csv("MotorPH_Products_List_2025.csv")

sales = pd.read_csv("MotorPH_Sales Data-3rd Quarter-Year 2025.csv")


# In[4]:


# Preview the first few rows of the Product List dataset
products.head()


# In[5]:


# Preview the first few rows of the Sales dataset
sales.head()


# In[6]:


# Check column names, data types, and non-null counts for the Product List
print("=== PRODUCT LIST INFORMATION ===")
products.info()


# In[7]:


# Check column names, data types, and non-null counts for the Sales dataset
print("=== SALES DATASET INFORMATION ===")
sales.info()


# In[8]:


# Check both datasets for missing values
print("=== PRODUCT LIST MISSING VALUES ===")
print(products.isnull().sum())

print("\n=== SALES DATASET MISSING VALUES ===")
print(sales.isnull().sum())


# In[9]:


# Check both datasets for fully duplicated rows
print("=== PRODUCT LIST DUPLICATES ===")
print("Duplicate rows:", products.duplicated().sum())

print("\n=== SALES DATASET DUPLICATES ===")
print("Duplicate rows:", sales.duplicated().sum())


# In[10]:


# Confirm every product has a unique EntrNo, and list all product IDs
print("Duplicate Product IDs:", products["EntrNo"].duplicated().sum())
print("Product IDs:")
print(products["EntrNo"].tolist())


# In[11]:


# Review product names, and the categorical values in the Sales dataset
print("=== PRODUCT NAMES ===")
print(products["EntrName"].tolist())

print("\n=== SALES CLIENT TYPES ===")
print(sales["client_type"].value_counts(dropna=False))

print("\n=== SALES PAYMENT TYPES ===")
print(sales["payment"].value_counts(dropna=False))


# In[12]:


# Preview how Product Type looks when extracted from EntrDetails
# (the text before the "/" separator) -- this is applied for real later,
# in the Product Analysis notebook
product_types = products["EntrDetails"].str.split("/").str[0].str.strip()

print("=== PRODUCT TYPES ===")
print(product_types.value_counts())


# In[13]:


# Create working copies so the original raw data is never modified directly
products_clean = products.copy()
sales_clean = sales.copy()

print("Clean copies created successfully.")


# In[14]:


# Identify which sales rows have a missing date, client_type, or payment value
missing_sales = sales_clean[
    sales_clean[["date", "client_type", "payment"]].isnull().any(axis=1)
]

missing_sales


# In[15]:


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


# In[16]:


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


# In[17]:


# Drop the handful of rows with unparseable/invalid dates
sales_clean = sales_clean.dropna(subset=["date"]).copy()

print("Rows remaining:", len(sales_clean))
print("Missing dates:", sales_clean["date"].isnull().sum())


# In[18]:


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


# In[19]:


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


# In[20]:


# List sales product names that don't match any name in the Product
# List -- these are most likely typos
unmatched_products = sales_clean[
    sales_clean["product_list_price"].isna()
]["product"].value_counts()

print("=== SALES PRODUCTS NOT FOUND IN PRODUCT LIST ===")
print(unmatched_products)


# In[21]:


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


# In[22]:


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


# In[23]:


# Re-check the price lookup now that the product names have been corrected
price_lookup = products_clean.set_index("EntrName")["UnitPrice"]

sales_clean["product_list_price"] = sales_clean["product"].map(price_lookup)

print(
    "Products still not found:",
    sales_clean["product_list_price"].isnull().sum()
)


# In[24]:


# Confirm which rows still have a unit price that disagrees with the Product List
price_mismatches = sales_clean[
    sales_clean["unitprice"] != sales_clean["product_list_price"]
]

print("Rows with unit price mismatch:", len(price_mismatches))

price_mismatches[
    ["product", "unitprice", "product_list_price", "quantity", "total"]
].head(20)


# In[25]:


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


# In[26]:


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


# In[27]:


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

