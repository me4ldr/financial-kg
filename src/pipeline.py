"""
金融知识图谱 - 数据流水线
"""
import logging
from pathlib import Path
from typing import Optional

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s")
logger = logging.getLogger("financial_kg")


def run_pipeline(config_path: Optional[str] = None):
    """运行知识图谱构建流水线"""
    logger.info("🚀 启动金融知识图谱流水线...")

    # TODO: 实现流水线逻辑
    # 1. 数据加载
    # 2. 实体抽取
    # 3. 关系抽取
    # 4. 图构建
    # 5. 存储与导出

    logger.info("✅ 流水线完成（待实现）")


if __name__ == "__main__":
    run_pipeline()
