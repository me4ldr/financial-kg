"""
实体关系抽取器基类
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any


class BaseEntityExtractor(ABC):
    """实体抽取器基类"""

    @abstractmethod
    def extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """从文本中抽取实体"""
        ...


class BaseRelationExtractor(ABC):
    """关系抽取器基类"""

    @abstractmethod
    def extract_relations(
        self, entities: List[Dict[str, Any]], context: str
    ) -> List[Dict[str, Any]]:
        """从文本和实体中抽取关系"""
        ...
