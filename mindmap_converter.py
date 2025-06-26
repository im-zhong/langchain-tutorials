from typing import Dict, Any, List
import logging
import re
import json

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MindMapConverter:
    """思维导图格式转换器"""

    @staticmethod
    def simple_to_frontend(simple_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        将简单的思维导图格式转换为前端需要的格式

        Args:
            simple_data: 简单格式的思维导图数据

        Returns:
            Dict: 前端格式的思维导图数据
        """
        logger.info(f"开始转换简单格式到前端格式: 类型={type(simple_data)}")

        # 安全检查
        if not isinstance(simple_data, dict):
            logger.error(f"输入数据不是字典类型: {type(simple_data)}")
            if isinstance(simple_data, str):
                logger.info(f"尝试将字符串解析为JSON")
                try:
                    simple_data = json.loads(simple_data)
                except json.JSONDecodeError as e:
                    logger.error(f"JSON解析失败: {str(e)}")
                    return {"error": "输入数据格式错误"}
            else:
                return {"error": "输入数据格式错误"}

        def convert_node(node_data: Dict[str, Any]) -> Dict[str, Any]:
            """递归转换节点"""
            # 获取标题，确保是字符串类型
            title = node_data.get("title", "未命名节点")
            if not isinstance(title, str):
                logger.warning(f"节点标题不是字符串类型: {type(title)}")
                title = str(title)

            frontend_node = {
                "data": {
                    "text": f"<p>{title}</p>",
                    "expand": True,
                    "richText": True,
                    "isActive": False,
                },
                "children": [],
            }

            # 根节点需要额外的属性
            if "children" in node_data and isinstance(node_data["children"], list):
                if (
                    len(node_data["children"]) == 0
                    and "generalization" not in frontend_node["data"]
                ):
                    # 这可能是根节点
                    frontend_node["data"].update(
                        {"generalization": [], "imgMap": {}, "gradientStyle": False}
                    )

                # 转换子节点
                for child in node_data["children"]:
                    frontend_node["children"].append(convert_node(child))

            return frontend_node

        try:
            # 转换根节点
            root_node = convert_node(simple_data)

            # 确保根节点有完整的属性
            if "generalization" not in root_node["data"]:
                root_node["data"].update(
                    {"generalization": [], "imgMap": {}, "gradientStyle": False}
                )

            # 添加版本信息
            result = {**root_node, "smmVersion": "0.14.0-fix.1"}

            logger.info(f"转换完成: 键={list(result.keys())}")
            return result
        except Exception as e:
            logger.error(f"转换过程中发生错误: {str(e)}")
            import traceback

            logger.error(f"详细错误: {traceback.format_exc()}")
            return {"error": f"转换失败: {str(e)}"}

    @staticmethod
    def frontend_to_simple(frontend_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        将前端格式转换为简单格式（用于存储和LLM处理）

        Args:
            frontend_data: 前端格式的思维导图数据

        Returns:
            Dict: 简单格式的思维导图数据
        """

        def convert_node(node_data: Dict[str, Any]) -> Dict[str, Any]:
            """递归转换节点"""
            import re

            # 提取文本内容
            text = node_data.get("data", {}).get("text", "")
            title = re.sub(r"<[^>]*>", "", text)  # 移除HTML标签

            simple_node = {"title": title, "children": []}

            # 转换子节点
            if "children" in node_data and isinstance(node_data["children"], list):
                for child in node_data["children"]:
                    simple_node["children"].append(convert_node(child))

            return simple_node

        return convert_node(frontend_data)

    @staticmethod
    def validate_simple_format(data: Dict[str, Any]) -> bool:
        """
        验证简单格式数据的有效性

        Args:
            data: 要验证的数据

        Returns:
            bool: 是否有效
        """
        if not isinstance(data, dict):
            return False

        if "title" not in data:
            return False

        if "children" not in data:
            return False

        if not isinstance(data["children"], list):
            return False

        # 递归验证子节点
        for child in data["children"]:
            if not MindMapConverter.validate_simple_format(child):
                return False

        return True

    @staticmethod
    def extract_text_content(mindmap_data: Dict[str, Any]) -> str:
        """
        从思维导图数据中提取所有文本内容

        Args:
            mindmap_data: 思维导图数据（简单格式或前端格式）

        Returns:
            str: 提取的文本内容
        """

        def extract_from_simple(node: Dict[str, Any], level: int = 0) -> str:
            """从简单格式提取文本"""
            text = f"{'  ' * level}{node.get('title', '')}\n"

            for child in node.get("children", []):
                text += extract_from_simple(child, level + 1)

            return text

        def extract_from_frontend(node: Dict[str, Any], level: int = 0) -> str:
            """从前端格式提取文本"""
            import re

            raw_text = node.get("data", {}).get("text", "")
            title = re.sub(r"<[^>]*>", "", raw_text)  # 移除HTML标签
            text = f"{'  ' * level}{title}\n"

            for child in node.get("children", []):
                text += extract_from_frontend(child, level + 1)

            return text

        # 判断是简单格式还是前端格式
        if "title" in mindmap_data:
            return extract_from_simple(mindmap_data)
        elif "data" in mindmap_data:
            return extract_from_frontend(mindmap_data)
        else:
            return ""


if __name__ == "__main__":
    with open("mindmap.json", "r") as f:
        mindmap_data = json.load(f)
    frontend_data = MindMapConverter.simple_to_frontend(mindmap_data)
    with open("mindmap_frontend.json", "w") as f:
        json.dump(frontend_data, f, indent=4)
