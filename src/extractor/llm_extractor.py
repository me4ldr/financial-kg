"""
基于 LLM 的关系抽取器
使用大语言模型从文本中抽取实体和关系
"""
import json
import logging
from typing import Dict, List, Optional

logger = logging.getLogger("financial_kg")

# 默认使用通义千问 (百炼)
SYSTEM_PROMPT = """你是一个金融知识图谱信息抽取专家。请从给定的文本中抽取实体和关系。

需要抽取的实体类型：
- Company: 公司名称（简称或全称）
- Industry: 行业名称
- Product: 产品/业务名称

需要抽取的关系类型：
- belong_to_industry: 公司所属行业 (Company → Industry)
- main_product: 公司主营产品 (Company → Product)
- upstream_of: 产品上游原材料 (Product → Product)
- downstream_of: 产品下游成品 (Product → Product)
- subclass_of: 产品小类关系 (Product → Product)

请以 JSON 格式返回，格式如下：
{
  "entities": [
    {"name": "实体名", "type": "Company|Industry|Product", "attributes": {}}
  ],
  "relations": [
    {"source": "实体A", "target": "实体B", "relation": "关系类型", "attributes": {}}
  ]
}

只返回 JSON，不要其他内容。如果不确定，宁可漏掉也不要编造。
"""


class LLMExtractor:
    """基于 LLM 的实体与关系抽取"""

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None, model: str = "qwen3.6-plus"):
        self.api_key = api_key
        self.base_url = base_url or "https://dashscope.aliyuncs.com/compatible-mode/v1"
        self.model = model
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                from openai import OpenAI
                self._client = OpenAI(
                    api_key=self.api_key,
                    base_url=self.base_url,
                )
            except ImportError:
                logger.error("请安装 openai: pip install openai")
                raise
        return self._client

    def extract(self, text: str, max_tokens: int = 4096) -> Dict:
        """从文本中抽取实体和关系"""
        client = self._get_client()

        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"请从以下文本中抽取实体和关系：\n\n{text}"},
                ],
                temperature=0.1,
                max_tokens=max_tokens,
                response_format={"type": "json_object"},
            )
            result = json.loads(response.choices[0].message.content)
            return result
        except Exception as e:
            logger.error(f"LLM 抽取失败: {e}")
            return {"entities": [], "relations": []}

    def extract_batch(self, texts: List[str], max_workers: int = 4) -> List[Dict]:
        """批量抽取"""
        from concurrent.futures import ThreadPoolExecutor, as_completed

        results = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(self.extract, text): i for i, text in enumerate(texts)}
            for future in as_completed(futures):
                idx = futures[future]
                try:
                    result = future.result()
                    results.append((idx, result))
                except Exception as e:
                    logger.error(f"批量抽取失败 [idx={idx}]: {e}")
                    results.append((idx, {"entities": [], "relations": []}))

        # 按原始顺序返回
        results.sort(key=lambda x: x[0])
        return [r for _, r in results]
