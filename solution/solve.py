import pandas as pd
import numpy as np
import json
from pathlib import Path

def main():
    artifacts_dir = Path("/input_artifacts")
    # In some harbor setups or testing environments, it might be in different places.
    # But inside the Docker container, harbor puts it at /input_artifacts/
    if not artifacts_dir.exists():
        artifacts_dir = Path("/workspace/input_artifacts")
    if not artifacts_dir.exists():
        artifacts_dir = Path("./environment/input_artifacts")
    if not artifacts_dir.exists():
        artifacts_dir = Path("../environment/input_artifacts")
    if not artifacts_dir.exists():
        artifacts_dir = Path("./ecommerce_sales_analysis/environment/input_artifacts")
        
    output_dir = Path("/logs/agent")
    if not output_dir.exists():
        output_dir = Path("./logs/agent")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load and clean NA
    na = pd.read_csv(artifacts_dir / "sales_north_america.csv")
    na_dups_before = len(na)
    na = na.drop_duplicates()
    na_dups_after = len(na)
    na_dropped = na_dups_before - na_dups_after
    
    # NA has missing Total_Sales
    na['Total_Sales_Calculated'] = na['Quantity'] * na['Unit_Price'] * (1 - na['Discount_Percent'] / 100.0)
    na['Total_Sales_Calculated'] = na['Total_Sales_Calculated'].round(2)
    na['Total_Sales'] = na['Total_Sales'].fillna(na['Total_Sales_Calculated'])
    na = na.drop(columns=['Total_Sales_Calculated'])
    
    # Load and clean EU
    eu = pd.read_csv(artifacts_dir / "sales_europe.csv")
    eu_dups_before = len(eu)
    eu = eu.drop_duplicates()
    eu_dropped = eu_dups_before - len(eu)
    
    # Normalize schema
    eu = eu.rename(columns={'Date': 'Order_Date', 'Segment': 'Customer_Segment'})
    # Parse dates (format is DD/MM/YYYY)
    eu['Order_Date'] = pd.to_datetime(eu['Order_Date'], format='%d/%m/%Y').dt.strftime('%Y-%m-%d')
    # Filter invalid Quantity (Quantity <= 0)
    invalid_qty_count = (eu['Quantity'] <= 0).sum()
    eu = eu[eu['Quantity'] > 0]
    eu_dropped += invalid_qty_count
    
    # Load and clean MEA
    mea = pd.read_csv(artifacts_dir / "sales_middle_east_africa.csv")
    mea_dups_before = len(mea)
    mea = mea.drop_duplicates()
    mea_dropped = mea_dups_before - len(mea)
    
    # Normalize schema
    mea = mea.rename(columns={'Sales_Amount': 'Total_Sales', 'Discount': 'Discount_Percent'})
    # Parse dates (format is MM-DD-YYYY)
    mea['Order_Date'] = pd.to_datetime(mea['Order_Date'], format='%m-%d-%Y').dt.strftime('%Y-%m-%d')
    # Impute missing Quantity with 1
    missing_qty_count = mea['Quantity'].isnull().sum()
    mea['Quantity'] = mea['Quantity'].fillna(1.0).astype(int)
    # Recalculate Total_Sales where Quantity was missing
    calculated_sales = mea['Quantity'] * mea['Unit_Price'] * (1 - mea['Discount_Percent'] / 100.0)
    calculated_sales = calculated_sales.round(2)
    mea['Total_Sales'] = mea['Total_Sales'].fillna(calculated_sales)
    
    # Load and clean AP
    ap = pd.read_csv(artifacts_dir / "sales_asia_pacific.csv")
    ap_dups_before = len(ap)
    ap = ap.drop_duplicates()
    ap_dropped = ap_dups_before - len(ap)
    
    # Normalize schema
    ap = ap.rename(columns={'Earnings': 'Profit'})
    # Parse dates (format is YYYY-MM-DD)
    ap['Order_Date'] = pd.to_datetime(ap['Order_Date']).dt.strftime('%Y-%m-%d')
    # Filter invalid Discount_Percent (Discount_Percent < 0 or Discount_Percent > 100)
    invalid_disc_count = ((ap['Discount_Percent'] < 0) | (ap['Discount_Percent'] > 100)).sum()
    ap = ap[(ap['Discount_Percent'] >= 0) & (ap['Discount_Percent'] <= 100)]
    ap_dropped += invalid_disc_count
    
    # Load and clean SA
    sa = pd.read_csv(artifacts_dir / "sales_south_america.csv")
    sa_dups_before = len(sa)
    sa = sa.drop_duplicates()
    sa_dropped = sa_dups_before - len(sa)
    
    # Normalize schema
    sa = sa.rename(columns={'Delivery_Fee': 'Shipping_Cost', 'Transaction_ID': 'Order_ID'})
    # Parse dates (format is DD/MM/YYYY)
    sa['Order_Date'] = pd.to_datetime(sa['Order_Date'], format='%d/%m/%Y').dt.strftime('%Y-%m-%d')
    # Filter missing Customer_Name
    missing_cust_count = sa['Customer_Name'].isnull().sum()
    sa = sa.dropna(subset=['Customer_Name'])
    sa_dropped += missing_cust_count
    
    # Merge all
    all_df = pd.concat([na, eu, mea, ap, sa], ignore_index=True)
    
    # Calculate stats
    total_records_processed = len(all_df)
    total_records_dropped = int(na_dropped + eu_dropped + mea_dropped + ap_dropped + sa_dropped)
    
    global_sales = float(all_df['Total_Sales'].sum())
    global_profit = float(all_df['Profit'].sum())
    global_quantity = int(all_df['Quantity'].sum())
    global_avg_discount = float(all_df['Discount_Percent'].mean())
    
    regional_breakdown = {}
    for region, group in all_df.groupby('Region'):
        # Customer segment distribution
        segment_dist = group['Customer_Segment'].value_counts().to_dict()
        # Top category
        top_cat = group.groupby('Product_Category')['Total_Sales'].sum().idxmax()
        
        regional_breakdown[region] = {
            "total_sales": round(float(group['Total_Sales'].sum()), 2),
            "total_profit": round(float(group['Profit'].sum()), 2),
            "total_quantity": int(group['Quantity'].sum()),
            "average_discount_percent": round(float(group['Discount_Percent'].mean()), 2),
            "top_category": top_cat,
            "customer_segment_distribution": {k: int(v) for k, v in segment_dist.items()}
        }
        
    expected_output = {
        "metadata": {
            "total_records_processed": total_records_processed,
            "total_records_dropped": total_records_dropped
        },
        "global_summary": {
            "total_sales": round(global_sales, 2),
            "total_profit": round(global_profit, 2),
            "total_quantity": global_quantity,
            "average_discount_percent": round(global_avg_discount, 2)
        },
        "regional_breakdown": regional_breakdown
    }
    
    with open(output_dir / "output.json", "w") as f:
        json.dump(expected_output, f, indent=2)
        
    print("Consolidated output written successfully.")

if __name__ == '__main__':
    main()
