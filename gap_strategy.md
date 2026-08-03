# Gap Strategy

## Why Single-Agent Should Struggle

- Number of artifacts: 5 CSV files (one per region) + 1 original dataset reference.
- Estimated input size: ~2000 records across 5 regions.
- Coverage pressure: The agent must process and clean all 5 regional CSV shards. Failing to process any single file correctly causes the global aggregates and regional summaries to be completely incorrect.
- Reconciliation pressure: Different files have completely different schema anomalies (e.g., one renamed 'Delivery_Fee' -> 'Shipping_Cost', another renamed 'Date' -> 'Order_Date') and date formats (YYYY-MM-DD vs DD/MM/YYYY vs MM-DD-YYYY). The single agent must map and convert columns differently for each file, then combine them.
- Expected failure mode: A single agent will often use a single generic cleaning script that fails on the specific anomalies of individual regions (e.g., failing to filter negative quantities in Europe, failing to impute missing quantities in Middle East & Africa, or failing to filter invalid discounts in Asia Pacific). It might also lose attention over long token lengths and generate a partially completed JSON, failing the verifier checks.

## Why Multi-Agent Should Succeed

- Natural subproblems: The problem decomposes naturally into 5 independent cleaning and mapping subproblems (one for each regional file) and 1 final aggregation/consolidation subproblem.
- Sub-agent ownership plan: Five parallel sub-agents are spawned, each assigned to inspect and clean a single regional file. Each sub-agent only needs to focus on the mapping and formatting rules of its own region.
- Reducer strategy: The synthesizer agent reads the intermediate cleaned outputs from all 5 sub-agents, aggregates the global and regional numbers, computes the customer segment distribution and top categories, checks schema consistency, and writes the final JSON output.
- Why final synthesis is verifiable: The final output JSON has precise numeric summaries, distributions, and top product categories. The verifier can check all of these values deterministically.

## Expected Score Pattern

- Oracle expected score: 1.0
- Single-agent expected score: 0.50
- Multi-agent expected score: 1.00
- Target gap: 50 percentage points

## Oracle Validation

- Oracle run completed: yes
- Oracle reward: 1.0
- Notes: The oracle solution cleans the shards using a python script, achieving a perfect 1.0 score.
