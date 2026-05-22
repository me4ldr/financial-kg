#!/usr/bin/env python
"""
Import financial KG data from JSON files into Neo4j
"""
import json
import time
from neo4j import GraphDatabase

NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "password123"  # default, change if needed

BATCH_SIZE = 1000

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
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

    try:
        with driver.session() as session:
            # ==========================================
            # 1. Import Companies (5199)
            # ==========================================
            print("=" * 60)
            print("Importing Companies...")
            companies = read_jsonl('/Users/xinyuan/projects/financial_kg/data/company.json')
            print(f"  Loaded {len(companies)} companies")

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
                print(f"  Processed {min(i+BATCH_SIZE, len(companies))}/{len(companies)}")

            # ==========================================
            # 2. Import Industries (157)
            # ==========================================
            print("\nImporting Industries...")
            industries = read_jsonl('/Users/xinyuan/projects/financial_kg/data/industry.json')
            print(f"  Loaded {len(industries)} industries")

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
                print(f"  Processed {min(i+BATCH_SIZE, len(industries))}/{len(industries)}")

            # ==========================================
            # 3. Import Products (52931)
            # ==========================================
            print("\nImporting Products...")
            products = read_jsonl('/Users/xinyuan/projects/financial_kg/data/product.json')
            print(f"  Loaded {len(products)} products")

            for i in range(0, len(products), BATCH_SIZE):
                batch = products[i:i+BATCH_SIZE]
                query = """
                UNWIND $batch AS row
                MERGE (p:Product {name: row.name})
                SET p.category = row.category
                """
                session.run(query, batch=batch)
                print(f"  Processed {min(i+BATCH_SIZE, len(products))}/{len(products)}")

            # ==========================================
            # 4. Import Company → Industry relations
            # ==========================================
            print("\nImporting Company → Industry relations...")
            comp_ind = read_jsonl('/Users/xinyuan/projects/financial_kg/data/company_industry.json')
            print(f"  Loaded {len(comp_ind)} relations")

            for i in range(0, len(comp_ind), BATCH_SIZE):
                batch = comp_ind[i:i+BATCH_SIZE]
                query = """
                UNWIND $batch AS row
                MATCH (c:Company {name: row.company_name})
                MATCH (ind:Industry {name: row.industry_name})
                MERGE (c)-[:BELONG_TO_INDUSTRY]->(ind)
                """
                session.run(query, batch=batch)
                print(f"  Processed {min(i+BATCH_SIZE, len(comp_ind))}/{len(comp_ind)}")

            # ==========================================
            # 5. Import Industry → Industry relations (hierarchy)
            # ==========================================
            print("\nImporting Industry → Industry relations...")
            ind_ind = read_jsonl('/Users/xinyuan/projects/financial_kg/data/industry_industry.json')
            print(f"  Loaded {len(ind_ind)} relations")

            for i in range(0, len(ind_ind), BATCH_SIZE):
                batch = ind_ind[i:i+BATCH_SIZE]
                query = """
                UNWIND $batch AS row
                MATCH (from:Industry {name: row.from_industry})
                MATCH (to:Industry {name: row.to_industry})
                MERGE (from)-[:PARENT_OF {rel: row.rel}]->(to)
                """
                session.run(query, batch=batch)
                print(f"  Processed {min(i+BATCH_SIZE, len(ind_ind))}/{len(ind_ind)}")

            # ==========================================
            # 6. Import Company → Product relations
            # ==========================================
            print("\nImporting Company → Product relations...")
            comp_prod = read_jsonl('/Users/xinyuan/projects/financial_kg/data/company_product.json')
            print(f"  Loaded {len(comp_prod)} relations")

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
                print(f"  Processed {min(i+BATCH_SIZE, len(comp_prod))}/{len(comp_prod)}")

            # ==========================================
            # 7. Verify counts
            # ==========================================
            print("\n" + "=" * 60)
            print("Verification:")
            result = session.run("""
                MATCH (c:Company) RETURN count(c) AS companies
            """)
            print(f"  Companies: {result.single()['companies']}")

            result = session.run("""
                MATCH (ind:Industry) RETURN count(ind) AS industries
            """)
            print(f"  Industries: {result.single()['industries']}")

            result = session.run("""
                MATCH (p:Product) RETURN count(p) AS products
            """)
            print(f"  Products: {result.single()['products']}")

            result = session.run("""
                MATCH ()-[r:BELONG_TO_INDUSTRY]->() RETURN count(r) AS comp_industry
            """)
            print(f"  Company→Industry: {result.single()['comp_industry']}")

            result = session.run("""
                MATCH ()-[r:PARENT_OF]->() RETURN count(r) AS industry_industry
            """)
            print(f"  Industry→Industry: {result.single()['industry_industry']}")

            result = session.run("""
                MATCH ()-[r:HAS_PRODUCT]->() RETURN count(r) AS comp_product
            """)
            print(f"  Company→Product: {result.single()['comp_product']}")

        print("\n" + "=" * 60)
        print("✅ Import complete! Data is in Neo4j.")
        print("   Open http://localhost:7474 in browser to visualize.")

    finally:
        driver.close()

if __name__ == '__main__':
    main()
