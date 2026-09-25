#!/usr/bin/env python
# coding: utf-8


# In[1]:


# Import library
import pandas as pd

# Load the cleaned Product List dataset produced by the preprocessing step
df = pd.read_csv("MotorPH_Products_List_2025_Cleaned.csv")

print("Dataset loaded successfully!")


# In[2]:


# Preview the first few rows
df.head()


# In[3]:


# Confirm the dataset is complete: check shape, missing values,
# duplicate rows, and duplicate product IDs
print("Dataset shape:", df.shape)
print("\nMissing values:")
print(df.isnull().sum())

print("\nDuplicate rows:", df.duplicated().sum())
print("Duplicate Product IDs:", df["EntrNo"].duplicated().sum())

df.info()


# In[4]:


# Count the total number of products in the inventory
total_products = len(df)

print("Total Number of Products:", total_products)


# In[5]:


# Derive a Product Type column by taking the text before the "/"
# separator in EntrDetails (e.g. "Sport / Parallel-twin..." -> "Sport")
df["Product Type"] = (
    df["EntrDetails"]
    .str.split("/")
    .str[0]
    .str.strip()
)

df[["EntrName", "EntrDetails", "Product Type"]].head()


# In[6]:


# Count how many products fall into each Product Type
product_counts = df["Product Type"].value_counts()

print("=== COUNTS BY PRODUCT TYPE ===")
print(product_counts)


# In[7]:


# Calculate the average, minimum, and maximum unit price across all products
average_price = df["UnitPrice"].mean()
minimum_price = df["UnitPrice"].min()
maximum_price = df["UnitPrice"].max()

print("=== UNIT PRICE STATISTICS ===")
print(f"Average Unit Price: ₱{average_price:,.2f}")
print(f"Minimum Unit Price: ₱{minimum_price:,.2f}")
print(f"Maximum Unit Price: ₱{maximum_price:,.2f}")


# In[8]:


# Identify the cheapest and most expensive products
cheapest_product = df.loc[df["UnitPrice"].idxmin()]
most_expensive_product = df.loc[df["UnitPrice"].idxmax()]

print("=== PRICE EXTREMES ===")

print(
    "Cheapest Product:",
    cheapest_product["EntrName"],
    "-",
    f"₱{cheapest_product['UnitPrice']:,.2f}"
)

print(
    "Most Expensive Product:",
    most_expensive_product["EntrName"],
    "-",
    f"₱{most_expensive_product['UnitPrice']:,.2f}"
)


# In[9]:


# Calculate the total value of the inventory (sum of all unit prices)
total_inventory_cost = df["UnitPrice"].sum()

print(
    "Total Inventory Cost:",
    f"₱{total_inventory_cost:,.2f}"
)


# In[10]:


# Build a summary table showing both the count and percentage share
# of each Product Type
product_counts_all = df["Product Type"].value_counts()

product_distribution = pd.DataFrame({
    "Product Count": product_counts_all,
    "Percentage": (product_counts_all / len(df) * 100).round(2)
})

product_distribution


# In[11]:


# Count products by manufacturing year, sorted chronologically
manufacturing_counts = df["Manufacturing Date"].value_counts().sort_index()

print("=== PRODUCTS BY MANUFACTURING YEAR ===")
print(manufacturing_counts)


# In[12]:


# Count products by acquisition year, sorted chronologically
acquisition_counts = df["Acquisiton"].value_counts().sort_index()

print("=== PRODUCTS BY ACQUISITION YEAR ===")
print(acquisition_counts)

