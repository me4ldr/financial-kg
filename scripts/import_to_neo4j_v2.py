#!/usr/bin/env python
"""
Import financial KG data from JSON files into Neo4j - with flush and progress
"""
import json
import sys
import time
from neo4j import GraphDatabase

NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "password123"

BATCH_SIZE = 500  # smaller batches for better progress tracking

def read_jsonl(filepath):
    """Read JSONL file and return list of dicts"""
    records = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records

def main():
    print("Connecting to Neo4j...", flush=True)
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

    try:
        with driver.session() as session:
            # Test connection
            result = session.run("RETURN 1 AS test")
            print(f"Connected! Test: {result.single()}", flush=True)

            # ==========================================
            # 1. Import Companies (5199)
            # ==========================================
            print("\n[1/6] Importing Companies...", flush=True)
            companies = read_jsonl('/Users/xinyuan/projects/financial_kg/data/company.json')
            print(f"  Loaded {len(companies)} companies", flush=True)

            for i in range(0, len(companies), BATCH_SIZE):
                batch = companies[i:i+BATCH_SIZE]
                query = """
                UNWIND $batch AS row
                MERGE (c:Company {name: row.name})
                SET c.code = row.code,
                    c.wind_code = row.wind_code,
                    c.fullname = row.fullname,
                    c.location = row.location,
                    c.time = row.time,
                    c.total_shares = row.total_shares,
                    c.mkt_cap = row.mkt_cap,
                    c.pe_ttm = row.pe_ttm,
                    c.pe_lyr = row.pe_lyr,
                    c.pb_lf = row.pb_lf,
                    c.close = row.close
                """
                session.run(query, batch=batch)
                done = min(i+BATCH_SIZE, len(companies))
                print(f"  Companies: {done}/{len(companies)}", flush=True)

            # ==========================================
            # 2. Import Industries (157)
            # ==========================================
            print("\n[2/6] Importing Industries...", flush=True)
            industries = read_jsonl('/Users/xinyuan/projects/financial_kg/data/industry.json')
            print(f"  Loaded {len(industries)} industries", flush=True)

            for i in range(0, len(industries), BATCH_SIZE):
                batch = industries[i:i+BATCH_SIZE]
                query = """
                UNWIND $batch AS row
                MERGE (ind:Industry {name: row.name})
                SET ind.code = row.code,
                    ind.level = row.level,
                    ind.level1 = row.level1
                """
                session.run(query, batch=batch)
                done = min(i+BATCH_SIZE, len(industries))
                print(f"  Industries: {done}/{len(industries)}", flush=True)

            # ==========================================
            # 3. Import Products (52931)
            # ==========================================
            print("\n[3/6] Importing Products...", flush=True)
            products = read_jsonl('/Users/xinyuan/projects/financial_kg/data/product.json')
            print(f"  Loaded {len(products)} products", flush=True)

            for i in range(0, len(products), BATCH_SIZE):
                batch = products[i:i+BATCH_SIZE]
                query = """
                UNWIND $batch AS row
                MERGE (p:Product {name: row.name})
                SET p.category = row.category
                """
                session.run(query, batch=batch)
                done = min(i+BATCH_SIZE, len(products))
                print(f"  Products: {done}/{len(products)}", flush=True)

            # ==========================================
            # 4. Import Company → Industry relations
            # ==========================================
            print("\n[4/6] Importing Company → Industry relations...", flush=True)
            comp_ind = read_jsonl('/Users/xinyuan/projects/financial_kg/data/company_industry.json')
            print(f"  Loaded {len(comp_ind)} relations", flush=True)

            for i in range(0, len(comp_ind), BATCH_SIZE):
                batch = comp_ind[i:i+BATCH_SIZE]
                query = """
                UNWIND $batch AS row
                MATCH (c:Company {name: row.company_name})
                MATCH (ind:Industry {name: row.industry_name})
                MERGE (c)-[:BELONG_TO_INDUSTRY]->(ind)
                """
                session.run(query, batch=batch)
                done = min(i+BATCH_SIZE, len(comp_ind))
                print(f"  Comp→Industry: {done}/{len(comp_ind)}", flush=True)

            # ==========================================
            # 5. Import Industry → Industry relations
            # ==========================================
            print("\n[5/6] Importing Industry → Industry relations...", flush=True)
            ind_ind = read_jsonl('/Users/xinyuan/projects/financial_kg/data/industry_industry.json')
            print(f"  Loaded {len(ind_ind)} relations", flush=True)

            for i in range(0, len(ind_ind), BATCH_SIZE):
                batch = ind_ind[i:i+BATCH_SIZE]
                query = """
                UNWIND $batch AS row
                MATCH (from:Industry {name: row.from_industry})
                MATCH (to:Industry {name: row.to_industry})
                MERGE (from)-[:PARENT_OF {rel: row.rel}]->(to)
                """
                session.run(query, batch=batch)
                done = min(i+BATCH_SIZE, len(ind_ind))
                print(f"  Industry→Industry: {done}/{len(ind_ind)}", flush=True)

            # ==========================================
            # 6. Import Company → Product relations
            # ==========================================
            print("\n[6/6] Importing Company → Product relations...", flush=True)
            comp_prod = read_jsonl('/Users/xinyuan/projects/financial_kg/data/company_product.json')
            print(f"  Loaded {len(comp_prod)} relations", flush=True)

            for i in range(0, len(comp_prod), BATCH_SIZE):
                batch = comp_prod[i:i+BATCH_SIZE]
                query = """
                UNWIND $batch AS row
                MATCH (c:Company {name: row.company_name})
                MATCH (p:Product {name: row.product_name})
                MERGE (c)-[r:HAS_PRODUCT]->(p)
                SET r.rel_type = row.rel,
                    r.product_type = row.product_type
                """
                session.run(query, batch=batch)
                done = min(i+BATCH_SIZE, len(comp_prod))
                print(f"  Comp→Product: {done}/{len(comp_prod)}", flush=True)

            # ==========================================
            # Verify counts
            # ==========================================
            print("\n" + "=" * 60, flush=True)
            print("Verification:", flush=True)

            for label in ['Company', 'Industry', 'Product']:
                result = session.run(f"MATCH (n:{label}) RETURN count(n) AS cnt")
                print(f"  {label}: {result.single()['cnt']}", flush=True)

            for rel in ['BELONG_TO_INDUSTRY', 'PARENT_OF', 'HAS_PRODUCT']:
                result = session.run(f"MATCH ()-[r:{rel}]->() RETURN count(r) AS cnt")
                print(f"  {rel}: {result.single()['cnt']}", flush=True)

        print("\n" + "=" * 60, flush=True)
        print("✅ Import complete!", flush=True)
        print("   Open http://localhost:7474 in browser to visualize.", flush=True)

    except Exception as e:
        print(f"\n❌ Error: {e}", flush=True)
        raise
    finally:
        driver.close()

if __name__ == '__main__':
    main()
