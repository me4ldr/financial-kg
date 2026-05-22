-- ============================================
-- Neo4j Knowledge Graph - 常用可视化查询
-- ============================================
-- 打开 Neo4j Browser: http://localhost:7474
-- 用户名: neo4j, 密码: password123
-- ============================================

-- 1. 总览：显示所有节点类型和数量
CALL db.schema.visualization()

-- 2. 完整图谱概览（采样 100 个节点）
MATCH (n)
RETURN n
LIMIT 100

-- 3. 行业层级图谱
MATCH (ind1:Industry)-[:PARENT_OF]->(ind2:Industry)
RETURN ind1, ind2
LIMIT 50

-- 4. 查看某公司的关联（公司→行业→产品）
MATCH (c:Company {name: '宁德时代'})-[r1]-(n)-[r2]-(m)
RETURN c, r1, n, r2, m
LIMIT 100

-- 5. 查看某行业的公司（电子行业）
MATCH (c:Company)-[:BELONG_TO_INDUSTRY]->(ind:Industry {name: '电子'})
RETURN c, ind
LIMIT 50

-- 6. 查看某公司的产品链
MATCH (c:Company {name: '贵州茅台'})-[:HAS_PRODUCT]->(p:Product)
RETURN c, p
LIMIT 50

-- 7. 查看某产品的所有公司
MATCH (c:Company)-[:HAS_PRODUCT]->(p:Product {name: '白酒'})
RETURN c, p
LIMIT 50

-- 8. 统计各行业公司数量
MATCH (c:Company)-[:BELONG_TO_INDUSTRY]->(ind:Industry)
RETURN ind.name AS industry, count(c) AS company_count
ORDER BY company_count DESC
LIMIT 20

-- 9. 统计各公司产品数量
MATCH (c:Company)-[:HAS_PRODUCT]->(p:Product)
RETURN c.name AS company, count(p) AS product_count
ORDER BY product_count DESC
LIMIT 20

-- 10. 找到产品最多的行业
MATCH (c:Company)-[:BELONG_TO_INDUSTRY]->(ind:Industry),
      (c)-[:HAS_PRODUCT]->(p:Product)
RETURN ind.name AS industry, count(DISTINCT p) AS product_count
ORDER BY product_count DESC
LIMIT 10
