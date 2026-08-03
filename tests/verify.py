import json
import sys
from pathlib import Path

def evaluate():
    score = 0.0
    checks = []
    
    def add_check(name, passed, weight):
        nonlocal score
        checks.append((name, passed, weight))
        if passed:
            score += weight

    agent_output_path = Path("/logs/agent/output.json")
    if not agent_output_path.exists():
        agent_output_path = Path("./logs/agent/output.json")
    if not agent_output_path.exists():
        agent_output_path = Path("../logs/agent/output.json")

    expected_output_path = Path("/tests/expected_output.json")
    if not expected_output_path.exists():
        expected_output_path = Path("/task/tests/expected_output.json")
    if not expected_output_path.exists():
        expected_output_path = Path("./tests/expected_output.json")
    if not expected_output_path.exists():
        expected_output_path = Path("../tests/expected_output.json")
    if not expected_output_path.exists():
        expected_output_path = Path("./ecommerce_sales_analysis/tests/expected_output.json")
        
    # Check 1: Existence and JSON structure
    if not agent_output_path.exists():
        print(f"Error: Agent output not found at {agent_output_path}")
        add_check("output_exists", False, 0.1)
        return 0.0, checks
        
    try:
        with open(agent_output_path, "r") as f:
            agent_data = json.load(f)
        add_check("valid_json", True, 0.1)
    except Exception as e:
        print(f"Error parsing agent JSON: {e}")
        add_check("valid_json", False, 0.1)
        return 0.0, checks
        
    # Load expected data
    try:
        with open(expected_output_path, "r") as f:
            expected_data = json.load(f)
    except Exception as e:
        print(f"Error loading expected output: {e}")
        return 0.0, [("expected_json_load", False, 0.0)]

    # Check 2: Metadata
    try:
        agent_meta = agent_data.get("metadata", {})
        exp_meta = expected_data.get("metadata", {})
        meta_passed = (
            int(agent_meta.get("total_records_processed", -1)) == int(exp_meta.get("total_records_processed", -2)) and
            int(agent_meta.get("total_records_dropped", -1)) == int(exp_meta.get("total_records_dropped", -2))
        )
        add_check("metadata_match", meta_passed, 0.1)
    except Exception as e:
        print(f"Error checking metadata: {e}")
        add_check("metadata_match", False, 0.1)

    # Helper for float matching
    def is_close(a, b, tol=1e-2):
        try:
            return abs(float(a) - float(b)) <= tol
        except (ValueError, TypeError):
            return False

    # Check 3: Global Summary
    try:
        agent_glob = agent_data.get("global_summary", {})
        exp_glob = expected_data.get("global_summary", {})
        
        sales_ok = is_close(agent_glob.get("total_sales"), exp_glob.get("total_sales"))
        profit_ok = is_close(agent_glob.get("total_profit"), exp_glob.get("total_profit"))
        qty_ok = int(agent_glob.get("total_quantity", -1)) == int(exp_glob.get("total_quantity", -2))
        disc_ok = is_close(agent_glob.get("average_discount_percent"), exp_glob.get("average_discount_percent"))
        
        glob_passed = sales_ok and profit_ok and qty_ok and disc_ok
        add_check("global_summary_match", glob_passed, 0.2)
        if not glob_passed:
            print("Global Summary mismatch:")
            print(f"  Sales: {agent_glob.get('total_sales')} vs {exp_glob.get('total_sales')} ({sales_ok})")
            print(f"  Profit: {agent_glob.get('total_profit')} vs {exp_glob.get('total_profit')} ({profit_ok})")
            print(f"  Qty: {agent_glob.get('total_quantity')} vs {exp_glob.get('total_quantity')} ({qty_ok})")
            print(f"  Discount: {agent_glob.get('average_discount_percent')} vs {exp_glob.get('average_discount_percent')} ({disc_ok})")
    except Exception as e:
        print(f"Error checking global summary: {e}")
        add_check("global_summary_match", False, 0.2)

    # Check 4: Regional Breakdown (5 regions, 0.12 each)
    agent_reg = agent_data.get("regional_breakdown", {})
    exp_reg = expected_data.get("regional_breakdown", {})
    
    for region, exp_stats in exp_reg.items():
        try:
            agent_stats = agent_reg.get(region)
            if not agent_stats:
                print(f"Region {region} missing from agent breakdown")
                add_check(f"region_{region}_match", False, 0.12)
                continue
                
            r_sales_ok = is_close(agent_stats.get("total_sales"), exp_stats.get("total_sales"))
            r_profit_ok = is_close(agent_stats.get("total_profit"), exp_stats.get("total_profit"))
            r_qty_ok = int(agent_stats.get("total_quantity", -1)) == int(exp_stats.get("total_quantity", -2))
            r_disc_ok = is_close(agent_stats.get("average_discount_percent"), exp_stats.get("average_discount_percent"))
            r_top_ok = str(agent_stats.get("top_category")).strip().lower() == str(exp_stats.get("top_category")).strip().lower()
            
            # Segments check
            agent_seg = agent_stats.get("customer_segment_distribution", {})
            exp_seg = exp_stats.get("customer_segment_distribution", {})
            r_seg_ok = all(
                int(agent_seg.get(seg, -1)) == int(exp_seg.get(seg, -2))
                for seg in ["Consumer", "Corporate", "Home Office"]
            )
            
            reg_passed = r_sales_ok and r_profit_ok and r_qty_ok and r_disc_ok and r_top_ok and r_seg_ok
            add_check(f"region_{region}_match", reg_passed, 0.12)
            if not reg_passed:
                print(f"Region {region} mismatch:")
                print(f"  Sales: {agent_stats.get('total_sales')} vs {exp_stats.get('total_sales')} ({r_sales_ok})")
                print(f"  Profit: {agent_stats.get('total_profit')} vs {exp_stats.get('total_profit')} ({r_profit_ok})")
                print(f"  Qty: {agent_stats.get('total_quantity')} vs {exp_stats.get('total_quantity')} ({r_qty_ok})")
                print(f"  Discount: {agent_stats.get('average_discount_percent')} vs {exp_stats.get('average_discount_percent')} ({r_disc_ok})")
                print(f"  Top Cat: {agent_stats.get('top_category')} vs {exp_stats.get('top_category')} ({r_top_ok})")
                print(f"  Segments: {agent_seg} vs {exp_seg} ({r_seg_ok})")
        except Exception as e:
            print(f"Error checking region {region}: {e}")
            add_check(f"region_{region}_match", False, 0.12)
            
    return score, checks

if __name__ == "__main__":
    score, checks = evaluate()
    score = round(score, 4)
    if score > 1.0:
        score = 1.0
        
    try:
        Path("/logs/verifier").mkdir(parents=True, exist_ok=True)
        Path("/logs/verifier/reward.txt").write_text(str(score))
    except Exception:
        Path("./logs/verifier").mkdir(parents=True, exist_ok=True)
        Path("./logs/verifier/reward.txt").write_text(str(score))
    
    print("\n--- Evaluation Results ---")
    for name, passed, weight in checks:
        print(f"{name}: {'PASS' if passed else 'FAIL'} (weight: {weight})")
    print(f"Final Score: {score}")
