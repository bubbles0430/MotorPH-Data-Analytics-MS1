# MotorPH Product Inventory Data Analysis – Milestone 1

## Project Overview

This repository contains the Python scripts used to clean and analyze the MotorPH Product List and Sales datasets for the 3rd Quarter of 2025. The workflow was conducted using Python and the pandas library in Jupyter Notebook.

## Data Preprocessing

`MotorPH_Preprocessing.ipynb` / `MotorPH_Preprocessing.py` load the raw Product List and Sales datasets, check for missing values and duplicates, correct mismatched product names and unit prices in the sales data against the official Product List, and export the cleaned datasets used by the analysis below.

## Analysis Objectives

The analysis examines:

- Total number of products
- Distribution of products by product type
- Average, minimum, and maximum unit prices
- Lowest- and highest-priced products
- Total inventory cost
- Distribution by manufacturing year
- Distribution by acquisition year

## Key Results

- Total Products: 50
- Product Types: 17
- Average Unit Price: ₱257,872.00
- Minimum Unit Price: ₱48,000.00
- Maximum Unit Price: ₱995,000.00
- Total Inventory Cost: ₱12,893,600.00
- Lowest-Priced Product: Rusi Flash 125 – ₱48,000.00
- Highest-Priced Product: BMW R nineT – ₱995,000.00
- Products manufactured in 2022–2023: 74%
- Products acquired in 2023–2024: 76%

## Technology Used

- Python
- pandas
- Jupyter Notebook
- Anaconda

## Python Scripts

`MotorPH_Preprocessing.py` – cleans the raw datasets and produces the cleaned CSV files.

`MotorPH_Product_Analysis.py` – contains the Python/pandas workflow used to generate the descriptive statistics and findings presented in the Milestone 1 report.
