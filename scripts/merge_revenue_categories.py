#!/usr/bin/env python3
"""
merge_revenue_categories.py

Merges "Business Category" (主营构成大类) data into the Financial KG.
Strategy: Minimalist - Only the latest revenue amount per company-category link.
No ratios, no historical data.
"""

import json
import logging
from pathlib import Path

# Paths
KG_PATH = Path("/Users/xinyuan/projects/financial_kg/output/financial_kg.json")
CACHE_PATH = Path("/Users/xinyuan/projects/medical-announcement-scraper/output/revenue_cache.json")
OUTPUT_PATH = Path("/Users/xinyuan/projects/financial_kg/output/financial_kg_enriched.json")

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("merge_revenue")


def main():
    logger.info("Loading Knowledge Graph...")
    with open(KG_PATH, "r", encoding="utf-8") as f:
        kg = json.load(f)

    # Index nodes by ID for fast lookup
    node_map = {node["id"]: node for node in kg["nodes"]}
    
    # Load Revenue Cache
    logger.info("Loading Revenue Cache...")
    with open(CACHE_PATH, "r", encoding="utf-8") as f:
        cache = json.load(f)

    nodes_added = 0
    edges_added = 0

    # Existing edges
    existing_edges = kg["edges"]

    # We need to create new edges: [Company] --(main_business_revenue)--> [Product Category]
    # Product Category node type: 'product_category' to distinguish from specific 'product' nodes
    
    # Track new nodes to add
    new_nodes_ids = set()
    
    # Process each company in cache
    for ts_code, data in cache.items():
        company_name = data.get("name")
        company_data = data.get("data")
        
        if not company_data:
            continue

        # 1. Find the latest period
        periods = sorted(company_data.keys())
        if not periods:
            continue
        latest_period = periods[-1]
        
        items = company_data[latest_period]
        
        # Find the company node ID in KG
        # The KG usually uses "Company Name" or "Code" as ID. Let's assume ID is Name or we need to match.
        # Looking at previous logs: KG nodes have "id", "node_type": "company", "code": "600276.SH"
        # Let's find the node where code matches ts_code or id matches name
        
        company_node_id = None
        
        # Search for matching company node
        # Strategy: Match by ts_code if available in node attributes, else by name
        for node in kg["nodes"]:
            if node.get("node_type") == "company":
                if node.get("code") == ts_code:
                    company_node_id = node["id"]
                    break
                elif node.get("name") == company_name:
                    company_node_id = node["id"]
                    break
        
        if not company_node_id:
            # If company not in KG, we skip or create it? 
            # Let's skip for now to avoid cluttering KG with companies that might be duplicates or unmapped
            continue

        # 2. Create edges for each item in latest period
        for item in items:
            bz_item = item.get("bz_item")
            sales = item.get("bz_sales_yi")
            
            if not bz_item or sales is None:
                continue

            # Create Product Category Node if not exists
            if bz_item not in node_map:
                node_map[bz_item] = {
                    "id": bz_item,
                    "node_type": "product_category",
                    "name": bz_item,
                    "category": "主营构成大类"
                }
                new_nodes_ids.add(bz_item)
                nodes_added += 1

            # Add Edge: [Company] --(main_business_revenue)--> [Category]
            # Check if edge already exists (unlikely for this specific relation type)
            # For simplicity, we just add it. If strict dedup is needed, we can check.
            
            new_edge = {
                "source": company_node_id,
                "target": bz_item,
                "relation": "main_business_revenue",
                "period": latest_period,
                "revenue_yi": sales
            }
            existing_edges.append(new_edge)
            edges_added += 1

    # Update KG
    kg["nodes"].extend([node_map[nid] for nid in new_nodes_ids])
    kg["edges"] = existing_edges

    logger.info(f"Nodes added: {nodes_added} (type: product_category)")
    logger.info(f"Edges added: {edges_added} (relation: main_business_revenue)")
    logger.info(f"Total nodes now: {len(kg['nodes'])}")
    logger.info(f"Total edges now: {len(kg['edges'])}")

    # Save
    logger.info(f"Saving enriched KG to {OUTPUT_PATH}")
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(kg, f, ensure_ascii=False, indent=2)
    
    logger.info("Done! 🎉")


if __name__ == "__main__":
    main()
