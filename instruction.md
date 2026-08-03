# E-commerce Regional Sales Data Cleaning & Aggregation

## Background
We have received sales data from 5 different regional divisions: North America, Europe, Middle East & Africa, Asia Pacific, and South America. However, the data files are messy, contain inconsistencies, schema variations, formatting differences, duplicate rows, and missing records. 

Your task is to ingest all regional sales data files from `/input_artifacts/`, clean the data according to the rules below, standardize the column schemas and date formats, and produce a unified consolidated report.

## Input Files
The source data consists of five files located under the `/input_artifacts/` directory:
- `sales_north_america.csv`
- `sales_europe.csv`
- `sales_middle_east_africa.csv`
- `sales_asia_pacific.csv`
- `sales_south_america.csv`

## Column Schema Mapping
The final standardized schema of the cleaned dataset must use the following column names:
- `Order_ID` (string)
- `Order_Date` (string, format: YYYY-MM-DD)
- `Customer_Name` (string)
- `Customer_Segment` (string)
- `Country` (string)
- `Region` (string)
- `Product_Category` (string)
- `Product_Name` (string)
- `Quantity` (integer)
- `Unit_Price` (float)
- `Discount_Percent` (integer, e.g. 15 for 15%)
- `Total_Sales` (float)
- `Shipping_Cost` (float)
- `Profit` (float)
- `Payment_Method` (string)

Each regional file may have different headers that you must map to the standardized schema:
- **North America**: Already uses the standard schema.
- **Europe**:
  - `Date` maps to `Order_Date`
  - `Segment` maps to `Customer_Segment`
- **Middle East & Africa**:
  - `Sales_Amount` maps to `Total_Sales`
  - `Discount` maps to `Discount_Percent`
- **Asia Pacific**:
  - `Earnings` maps to `Profit`
- **South America**:
  - `Delivery_Fee` maps to `Shipping_Cost`
  - `Transaction_ID` maps to `Order_ID`

All other columns not mentioned in a file's custom mapping have standard names.

## Data Cleaning & Parsing Rules
To ensure the aggregated results are 100% accurate, you must strictly apply the following cleaning procedures in this exact order for each file before combining:

1. **Deduplication**: Remove exact duplicate rows in each file.
2. **Remove Missing Customer Names**: Discard any records where `Customer_Name` is empty, missing, or null.
3. **Filter Out Returns**: Discard any records where `Quantity` is less than or equal to 0.
4. **Filter Out Invalid Discounts**: Discard any records where `Discount_Percent` (or equivalent renamed column) is less than 0 or greater than 100.
5. **Handle Missing Quantities**: 
   - If `Quantity` is missing or null, fill it with `1`.
   - If `Quantity` was missing, or if `Total_Sales` is missing or null, you must calculate `Total_Sales` as:
     `Total_Sales = Quantity * Unit_Price * (1 - Discount_Percent / 100.0)`
     Round this calculated value to 2 decimal places.
6. **Date Format Standardization**:
   - Dates in the files are formatted in various ways:
     - North America: `YYYY-MM-DD`
     - Europe: `DD/MM/YYYY` (e.g., 25/12/2023)
     - Middle East & Africa: `MM-DD-YYYY` (e.g., 12-25-2023)
     - Asia Pacific: `YYYY-MM-DD`
     - South America: `DD/MM/YYYY` (e.g., 25/12/2023)
   - You must convert all dates to `YYYY-MM-DD` format.

## Required Output
You must output a single consolidated JSON report saved exactly at `/logs/agent/output.json`.

The JSON structure must match the following format exactly:
```json
{
  "metadata": {
    "total_records_processed": <integer: count of total cleaned rows across all regions combined>,
    "total_records_dropped": <integer: count of all rows dropped due to duplicates or invalid/filtered values>
  },
  "global_summary": {
    "total_sales": <float: sum of Total_Sales, rounded to 2 decimal places>,
    "total_profit": <float: sum of Profit, rounded to 2 decimal places>,
    "total_quantity": <integer: sum of Quantity>,
    "average_discount_percent": <float: average of Discount_Percent across all processed records, rounded to 2 decimal places>
  },
  "regional_breakdown": {
    "<RegionName1>": {
      "total_sales": <float: sum of Total_Sales for this region, rounded to 2 decimal places>,
      "total_profit": <float: sum of Profit for this region, rounded to 2 decimal places>,
      "total_quantity": <integer: sum of Quantity for this region>,
      "average_discount_percent": <float: average of Discount_Percent for this region, rounded to 2 decimal places>,
      "top_category": "<string: the Product_Category with the highest sum of Total_Sales in this region>",
      "customer_segment_distribution": {
        "Consumer": <integer: count of records in this region for this segment>,
        "Corporate": <integer: count of records in this region for this segment>,
        "Home Office": <integer: count of records in this region for this segment>
      }
    },
    ...
  }
}
```
