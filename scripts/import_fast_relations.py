#!/usr/bin/env python
"""
Fast import: Company → Product relations using CREATE (nodes already exist)
"""
import json
import sys
import time
from neo4j import GraphDatabase

NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "password123"

BATCH_SIZE = 5000  # much larger batches since we just CREATE

def read_jsonl(filepath):
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
            # Import Company → Product relations
            print("\nImporting Company → Product relations (fast mode)...", flush=True)
            comp_prod = read_jsonl('/Users/xinyuan/projects/financial_kg/data/company_product.json')
            print(f"  Loaded {len(comp_prod)} relations", flush=True)

            for i in range(0, len(comp_prod), BATCH_SIZE):
                batch = comp_prod[i:i+BATCH_SIZE]
                query = """
                UNWIND $batch AS row
                MATCH (c:Company {name: row.company_name})
                MATCH (p:Product {name: row.product_name})
                CREATE (c)-[r:HAS_PRODUCT]->(p)
                """
                session.run(query, batch=batch)
                done = min(i+BATCH_SIZE, len(comp_prod))
                elapsed = time.time() - start_time
                print(f"  Comp→Product: {done}/{len(comp_prod)} ({elapsed:.1f}s elapsed)", flush=True)

            print("\n✅ All relations imported!", flush=True)

            # Verify
            result = session.run("MATCH ()-[r:HAS_PRODUCT]->() RETURN count(r) AS cnt")
            print(f"  Total HAS_PRODUCT relations: {result.single()['cnt']}", flush=True)

        print("\n" + "=" * 60, flush=True)
        print("✅ Import complete! Open http://localhost:7474 to visualize.", flush=True)

    except Exception as e:
        print(f"\n❌ Error: {e}", flush=True)
        raise
    finally:
        driver.close()

if __name__ == '__main__':
    start_time = time.time()
    main()
