"""
金融知识图谱 - 数据加载模块
支持从 Tushare API、本地 JSON 文件加载数据
"""
import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger("financial_kg")


class DataLoader:
    """数据加载器"""

    def __init__(self, data_dir: Optional[str] = None):
        self.data_dir = Path(data_dir or os.path.join(os.path.dirname(__file__), "..", "data"))
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def load_json(self, filename: str) -> list:
        """加载 JSON 数据（每行一个 JSON 对象）"""
        path = self.data_dir / filename
        if not path.exists():
            logger.warning(f"文件不存在: {path}")
            return []
        items = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        obj = json.loads(line)
                        if obj:
                            items.append(obj)
                    except json.JSONDecodeError:
                        continue
        return items

    def save_json(self, filename: str, data: list):
        """保存数据为 JSON（每行一个对象）"""
        path = self.data_dir / filename
        with open(path, "w", encoding="utf-8") as f:
            for item in data:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")
        logger.info(f"保存 {len(data)} 条数据 → {path}")

    def load_companies(self) -> List[Dict]:
        """加载公司实体"""
        return self.load_json("company.json")

    def load_industries(self) -> List[Dict]:
        """加载行业实体"""
        return self.load_json("industry.json")

    def load_products(self) -> List[Dict]:
        """加载产品实体"""
        return self.load_json("product.json")

    def load_company_industry(self) -> List[Dict]:
        """加载公司-行业关系"""
        return self.load_json("company_industry.json")

    def load_industry_industry(self) -> List[Dict]:
        """加载行业-行业关系"""
        return self.load_json("industry_industry.json")

    def load_company_product(self) -> List[Dict]:
        """加载公司-产品关系"""
        return self.load_json("company_product.json")

    def load_product_product(self) -> List[Dict]:
        """加载产品-产品关系"""
        return self.load_json("product_product.json")

    def summary(self) -> Dict:
        """数据统计摘要"""
        return {
            "companies": len(self.load_companies()),
            "industries": len(self.load_industries()),
            "products": len(self.load_products()),
            "company_industry": len(self.load_company_industry()),
            "industry_industry": len(self.load_industry_industry()),
            "company_product": len(self.load_company_product()),
            "product_product": len(self.load_product_product()),
        }
