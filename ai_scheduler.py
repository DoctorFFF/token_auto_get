"""
AI 智能签到调度分析引擎
基于 MiniMax API 实现签到策略智能分析
"""

import os
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional


class AIScheduler:
    """AI 调度分析器"""
    
    def __init__(self, api_key: str, model: str = "MiniMax-M1"):
        self.api_key = api_key
        self.model = model
        self.api_url = "https://api.minimax.chat/v1/chat/completions"
    
    def _call_ai_analysis(self, context: str) -> Dict:
        """调用 MiniMax AI 进行分析"""
        
        system_prompt = """你是一个专业的签到风控分析专家。请根据提供的站点和账号数据，分析并生成最优签到策略。

你的任务：
1. 分析每个账号的签到成功率和历史记录
2. 识别可能存在风控风险的账号
3. 生成安全的签到策略

输出要求（必须是合法 JSON）：
{
  "recommended_accounts": [
    {
      "username": "账号名",
      "priority": "high|medium|low",
      "reason": "推荐签到的原因"
    }
  ],
  "skip_accounts": [
    {
      "username": "账号名",
      "reason": "不推荐签到的原因"
    }
  ],
  "interval_seconds": {
    "recommended": 3.5,
    "min": 2.0,
    "max": 5.0,
    "reasoning": "为什么推荐这个间隔时间"
  },
  "risk_level": "low|medium|high",
  "best_checkin_time": "推荐签到时间段（如：10:00-12:00）",
  "reasoning": "整体分析结论和建议",
  "warnings": ["风险提示列表"]
}

注意事项：
- 成功率低于 50% 的账号建议跳过
- 今日已签到的账号不需要重复签到
- 连续失败的账号需要谨慎对待
- 间隔时间应设置在 2-8 秒之间，根据风险等级调整
- 必须输出合法 JSON，不要包含 Markdown 格式或其他文本
"""
        
        user_message = f"""请分析以下站点数据并生成签到策略：

{context}

请直接输出 JSON 格式的分析结果，不要包含任何其他文字。"""
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            "temperature": 0.3,
            "max_tokens": 2000
        }
        
        try:
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            ai_response = result["choices"][0]["message"]["content"]
            
            # 解析 JSON
            strategy = self._parse_ai_response(ai_response)
            
            return {
                "success": True,
                "strategy": strategy,
                "raw_response": ai_response
            }
            
        except requests.exceptions.Timeout:
            return {
                "success": False,
                "error": "AI 请求超时，请稍后重试"
            }
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": f"AI 请求失败: {str(e)}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"解析 AI 响应失败: {str(e)}"
            }
    
    def _parse_ai_response(self, response_text: str) -> Dict:
        """解析 AI 返回的 JSON 响应"""
        # 尝试直接解析
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            pass
        
        # 尝试提取 JSON 块（如果包含 Markdown 代码块）
        import re
        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', response_text)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass
        
        # 尝试找到第一个 { 和最后一个 }
        start = response_text.find('{')
        end = response_text.rfind('}')
        if start != -1 and end != -1:
            try:
                return json.loads(response_text[start:end+1])
            except json.JSONDecodeError:
                pass
        
        raise ValueError(f"无法解析 AI 响应:\n{response_text}")


class StrategyStorage:
    """AI 策略存储"""
    
    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        self.storage_file = os.path.join(data_dir, "ai_strategies.json")
        os.makedirs(data_dir, exist_ok=True)
    
    def save_strategy(self, plugin_name: str, strategy: Dict):
        """保存 AI 策略"""
        data = self._load()
        
        if plugin_name not in data:
            data[plugin_name] = []
        
        strategy_record = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "strategy": strategy
        }
        
        data[plugin_name].append(strategy_record)
        
        # 保留最近 20 条记录
        data[plugin_name] = data[plugin_name][-20:]
        
        self._save(data)
    
    def get_latest_strategy(self, plugin_name: str) -> Optional[Dict]:
        """获取最新的 AI 策略"""
        data = self._load()
        
        if plugin_name in data and data[plugin_name]:
            return data[plugin_name][-1]
        
        return None
    
    def _load(self) -> Dict:
        """加载策略数据"""
        if not os.path.exists(self.storage_file):
            return {}
        
        try:
            with open(self.storage_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    
    def _save(self, data: Dict):
        """保存策略数据"""
        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)


# 便捷函数
def create_scheduler(api_key: str) -> AIScheduler:
    """创建 AI 调度器"""
    return AIScheduler(api_key)


def create_storage(data_dir: str) -> StrategyStorage:
    """创建策略存储器"""
    return StrategyStorage(data_dir)
