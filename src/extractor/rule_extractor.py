"""
基于规则的关系抽取器
实现上下游关系、产品小类关系等的启发式抽取
"""
import re
import logging
from typing import Dict, List

logger = logging.getLogger("financial_kg")


class RuleExtractor:
    """基于规则的实体关系抽取"""

    # 上游关系模式
    UPSTREAM_PATTERNS = [
        r"(.+?)是(.+?)的原料",
        r"(.+?)是(.+?)的原材料",
        r"(.+?)是(.+?)的主要原料",
        r"(.+?)是(.+?)的主要原材料",
        r"(.+?)是(.+?)的重要原材料",
        r"(.+?)是(.+?)的主要构件",
        r"(.+?)是(.+?)的重要原材料",
        r"(.+?)作为(.+?)的上游原料",
        r"(.+?)用于生产(.+?)",
        r"(.+?)是(.+?)的原材料之一",
    ]

    # 下游关系模式
    DOWNSTREAM_PATTERNS = [
        r"(.+?)的下游产品是(.+?)",
        r"(.+?)的下游成品是(.+?)",
        r"(.+?)的下游行业是(.+?)",
        r"(.+?)主要用于(.+?)",
        r"(.+?)广泛应用于(.+?)",
    ]

    # 小类关系模式
    SUBCLASS_PATTERNS = [
        r"(.+?)是一种(.+?)",
        r"(.+?)属于(.+?)",
        r"(.+?)是(.+?)的一种",
    ]

    def extract_upstream_relations(self, text: str) -> List[Dict]:
        """从文本中抽取上游原材料关系"""
        relations = []
        for pattern in self.UPSTREAM_PATTERNS:
            matches = re.findall(pattern, text)
            for match in matches:
                relations.append({
                    "from_entity": match[0].strip(),
                    "to_entity": match[1].strip(),
                    "rel": "upstream_of",
                    "source": "rule",
                    "pattern": pattern,
                })
        return relations

    def extract_downstream_relations(self, text: str) -> List[Dict]:
        """从文本中抽取下游产品关系"""
        relations = []
        for pattern in self.DOWNSTREAM_PATTERNS:
            matches = re.findall(pattern, text)
            for match in matches:
                relations.append({
                    "from_entity": match[0].strip(),
                    "to_entity": match[1].strip(),
                    "rel": "downstream_of",
                    "source": "rule",
                    "pattern": pattern,
                })
        return relations

    def extract_subclass_relations(self, text: str) -> List[Dict]:
        """从文本中抽取产品小类关系"""
        relations = []
        for pattern in self.SUBCLASS_PATTERNS:
            matches = re.findall(pattern, text)
            for match in matches:
                relations.append({
                    "from_entity": match[0].strip(),
                    "to_entity": match[1].strip(),
                    "rel": "subclass_of",
                    "source": "rule",
                    "pattern": pattern,
                })
        return relations

    def extract_all(self, text: str) -> List[Dict]:
        """抽取所有关系"""
        relations = []
        relations.extend(self.extract_upstream_relations(text))
        relations.extend(self.extract_downstream_relations(text))
        relations.extend(self.extract_subclass_relations(text))
        return relations
