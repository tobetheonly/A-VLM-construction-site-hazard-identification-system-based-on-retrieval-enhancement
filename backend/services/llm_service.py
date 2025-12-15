from openai import OpenAI
from config import Config


class LLMService:
    def __init__(self):
        # 隐患类型映射
        self.hazard_types = {
            "1": "未按规定穿戴反光安全服",
            "2": "高处作业未正确使用安全带",
            "3": "配电箱未及时锁闭",
            "4": "未按规定配置灭火器、消防设施等",
            "5": "现场防护栏等安全防护设施缺失、破损或设置不规范",
            "6": "设备安全防护设施、装置缺失或失效",
            "7": "起重吊装设备钢丝绳磨损、断丝严重，搭接长度不足",
            "8": "汽车吊、随车吊、泵车支腿未全部伸出、未垫枕木进行作业",
            "9": "基坑支护措施不到位",
            "10": "灭火器未按规定要求放置",
            "11": "未按规定设置接地线或接地不良",
            "12": "安全警示标志标识缺失或设置不规范",
            "13": "灭火器压力不足，灭火器、消防设施等未按规定进行检查、维护",
            "14": "不符合“三级配电两级漏电保护、一机一闸一漏一箱”要求",
            "15": "电缆外皮破损或敷设不规范"
        }

    def _create_client(self, provider: str):
        """按 provider 创建对应的 OpenAI 客户端"""
        if provider == "gpt4o":
            return OpenAI(
                base_url=Config.GPT4O_BASE_URL,
                api_key=Config.GPT4O_API_KEY
            )
        # 默认使用 Gemini（经 OpenRouter）
        return OpenAI(
            base_url=Config.GEMINI_BASE_URL,
            api_key=Config.GEMINI_API_KEY
        )

    def _pick_model(self, provider: str) -> str:
        """按 provider 选择模型名称"""
        if provider == "gpt4o":
            return Config.GPT4O_MODEL
        return Config.GEMINI_MODEL

    def generate_hazard_analysis(self, image_base64, similar_cases, few_shot_examples, provider: str = "gemini"):
        """多模态分析：图片 + 文本提示"""
        prompt = self._build_prompt(similar_cases, few_shot_examples)
        client = self._create_client(provider)
        model = self._pick_model(provider)
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_base64}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=1000
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"{provider} 分析失败: {str(e)}"

    def generate_text_analysis(self, text_prompt, provider: str = "gemini"):
        """纯文本分析备用"""
        client = self._create_client(provider)
        model = self._pick_model(provider)
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": text_prompt}],
                max_tokens=1000
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"文本分析失败: {str(e)}"

    def _build_prompt(self, similar_cases, few_shot_examples):
        """构建提示词"""
        prompt = """
你是一个专业的隐患识别专家。请分析上传的图片，识别其中的安全隐患，并提供整改建议，15种隐患类型如下所示。
"1": "未按规定穿戴反光安全服",
"2": "高处作业未正确使用安全带",
"3": "配电箱未及时锁闭",
"4": "未按规定配置灭火器、消防设施等",
"5": "现场防护栏等安全防护设施缺失、破损或设置不规范",
"6": "设备安全防护设施、装置缺失或失效",
"7": "起重吊装设备钢丝绳磨损、断丝严重，搭接长度不足",
"8": "汽车吊、随车吊、泵车支腿未全部伸出、未垫枕木进行作业",
"9": "基坑支护措施不到位",
"10": "灭火器未按规定要求放置",
"11": "未按规定设置接地线或接地不良",
"12": "安全警示标志标识缺失或设置不规范",
"13": "灭火器压力不足，灭火器、消防设施等未按规定进行检查、维护",
"14": "不符合“三级配电两级漏电保护、一机一闸一漏一箱”要求",
"15": "电缆外皮破损或敷设不规范"
"""
        prompt += "\n部分类别的相关例子如下:\n"
        for i, example in enumerate(few_shot_examples, 1):
            example_type = example.get('type', '未知')
            example_type_desc = self.hazard_types.get(example_type, example_type)
            prompt += f"\n示例{i}:\n"
            prompt += f"类型: {example_type} ({example_type_desc})\n"
            prompt += f"描述: {example.get('description', '无描述')}\n"
            prompt += f"建议: {example.get('suggestion', '无建议')}\n"

        prompt += "\n 以下几个示例的图片与上传的图片非常类似，其隐患类别和描述如下，请据此确定隐患类型并提出建议：\n"
        for i, case in enumerate(similar_cases, 1):
            case_type = case.get('type', '未知')
            case_type_desc = self.hazard_types.get(case_type, case_type)
            prompt += f"\n相似案例{i}:\n"
            prompt += f"类型: {case_type} ({case_type_desc})\n"
            prompt += f"描述: {case.get('description', '无描述')}\n"

        prompt += """
请按照以下格式输出分析结果（JSON 或可被 JSON 解析）：
{
"type": "隐患类型",
"description": "详细描述",
"suggestion": "整改建议",
"confidence": 0.95
}
"""
        return prompt