from service.core.retrieval import retrieve_content
from service.web_search.procss_web_search import store_and_query_snippets
import json
from openai import OpenAI
import os
import re

def extract_json_content(input_str):
    """
    提取字符串中第一个"["和最后一个"]"之间的内容（包括中括号）
    
    Args:
        input_str (str): 需要处理的输入字符串
    
    Returns:
        str or None: 提取的JSON内容，如果没有匹配则返回None
    """
    # 使用正则表达式匹配第一个"["到最后一个"]"之间的内容
    # [\s\S]* 匹配任意字符（包括换行符）
    pattern = r'(\[[\s\S]*\])'
    match = re.search(pattern, input_str)
    
    # 如果匹配成功，返回匹配的内容；否则返回None
    return match.group(1) if match else None

def middle_json_model(prompt):

    client = OpenAI(
        # 若没有配置环境变量，请用百炼API Key将下行替换为：api_key="sk-xxx",
        api_key=os.getenv("DASHSCOPE_API_KEY"), 
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )
    completion = client.chat.completions.create(
        model="qwen-plus", # 此处以qwen-plus为例，可按需更换模型名称。模型列表：https://help.aliyun.com/zh/model-studio/getting-started/models
        messages=[
            {'role': 'system', 'content': 'You are a helpful assistant.'},
            {'role': 'user', 'content': prompt}],
        response_format={"type": "json_object"}
        )
        
    return completion.choices[0].message.content

# rag搜索
def rag(query):
    indexNames ="1"
    rag_results = retrieve_content(indexNames, query)

    return rag_results

# 网页搜索
def web_search_answer(query):
    # 简化版本：直接使用搜索结果，不进行向量化处理
    try:
        from service.web_search.web_search import serper_search, process_search_results
        
        # 直接获取搜索结果
        search_results = serper_search(query)
        snippets, related_questions = process_search_results(search_results)
        
        # 直接返回搜索结果，不需要向量化和相似度计算
        return snippets
        
    except Exception as e:
        print(f"网络搜索失败: {e}")
        return f"网络搜索暂时不可用，错误信息: {str(e)}"

#规划模块plan
def agent_plan(query):
    prompt='''
    # 智能问诊助手Agent的Plan模块

你是一个专业的智能问诊助手的规划模块。你的任务是：
1. 分析用户的查询:{0}
2. 基于已有的信息，决定使用哪个工具来查询以获得更多需要的信息（医学文献库搜索或网络搜索）
3. 将用户的原始查询拆解或延伸为1-2个相关问题，以获取更全面的信息


## 可用工具
1. **医学文献库搜索**：搜索本地医学文献与诊疗指南，包含以下章节：
   - 疾病概述
   - 病因与发病机制
   - 症状与体征
   - 诊断方法与标准
   - 检查项目解读
   - 治疗方案
   - 用药指南
   - 手术指征与方式
   - 预防措施
   - 康复与随访
   - 饮食与生活方式建议
   - 并发症
   - 预后评估
   - 常见问答

2. **网络搜索**：在互联网上搜索相关信息

## 工具选择规则
- 当查询明确涉及疾病知识、症状分析、诊疗指南、检查指标解读、用药建议时，优先使用**医学文献库搜索**
- 当查询涉及以下情况时，使用**网络搜索**：
  - 最新医学研究进展或临床试验结果
  - 新药上市或药物审批动态
  - 医院、科室或专家信息
  - 医学文献库中可能没有的信息
  - 需要实时数据（如流行病疫情动态等）

## prompt延伸的规则
- 医学文献库检索的查询扩展侧重于疾病与诊疗知识的深度查询
- 网络检索的查询扩展侧重于文献库无法检索到的信息

## 输出格式
你的输出应该是一个JSON格式的列表，每个项目包含：
1. `action_name`：工具名称（"医学文献库搜索"或"网络搜索"）
2. `prompts`：问题列表，第一个是原始查询，后面是拆解或延伸的问题
[
  {{
    "action_name": "工具名称",
    "prompts": [
      "原始查询",
      "拆解/延伸问题1",
      "拆解/延伸问题2",
      "拆解/延伸问题3"
    ]
  }}
]


## 示例

### 示例1：关于疾病症状的查询
用户：高血压患者会有哪些典型症状？

输出：
[
  {{
    "action_name": "医学文献库搜索",
    "prompts": [
      "高血压患者会有哪些典型症状？",
      "高血压的诊断标准是什么？",
      "高血压不同分级的症状表现有何区别？"
    ]
  }}
]


### 示例2：关于最新研究进展的查询
用户：二甲双胍最新的研究进展怎么样？

输出：
[
  {{
    "action_name": "医学文献库搜索",
    "prompts": [
      "二甲双胍的适应症和用法用量是什么？",
      "二甲双胍有哪些常见不良反应？"
    ]
  }},
  {{
    "action_name": "网络搜索",
    "prompts": [
      "二甲双胍最新研究进展",
      "二甲双胍最新临床试验结果"
    ]
  }}
]


### 示例3：关于日常问题
用户：你好
这种情况下都不需要调用，则输出为None

只需要输出JSON的部分，前后不要输出任何信息

'''.format(query)
    result=(middle_json_model(prompt))
    print(result)
    json_list=extract_json_content(result)
    try:
        structure_output=json.loads(json_list)
    except:
        structure_output = None

    return structure_output
        
    

#任务状态state
def adjust_format(original_data):
    """
    调整数据格式，使每个action_name只搭配一个prompt
    
    参数:
    original_data (list): 原始数据，每个action_name对应多个prompts
    
    返回:
    list: 调整后的数据，每个action_name只对应一个prompt
    """
    adjusted_data = []
    
    for item in original_data:
        action_name = item['action_name']
        prompts = item['prompts']
        
        # 为每个prompt创建一个新的字典
        for prompt in prompts:
            adjusted_item = {
                'action_name': action_name,
                'prompt': prompt
            }
            adjusted_data.append(adjusted_item)
    
    return adjusted_data


def reflection(user_query,memory_global):
    prompt='''
    你是一个专业的智能问诊助手的规划模块。你的任务是：
1. 分析用户的查询:{0}
2. 基于已有的信息，是否还需要延伸再进行查询

##目前已有的信息:
{1}


## 可用工具
1. **医学文献库搜索**：搜索本地医学文献与诊疗指南，包含以下章节：
   - 疾病概述
   - 病因与发病机制
   - 症状与体征
   - 诊断方法与标准
   - 检查项目解读
   - 治疗方案
   - 用药指南
   - 手术指征与方式
   - 预防措施
   - 康复与随访
   - 饮食与生活方式建议
   - 并发症
   - 预后评估
   - 常见问答

2. **网络搜索**：在互联网上搜索相关信息

## 工具选择规则
- 当查询明确涉及疾病知识、症状分析、诊疗指南、检查指标解读、用药建议时，优先使用**医学文献库搜索**
- 当查询涉及以下情况时，使用**网络搜索**：
  - 最新医学研究进展或临床试验结果
  - 新药上市或药物审批动态
  - 医院、科室或专家信息
  - 医学文献库中可能没有的信息
  - 需要实时数据（如流行病疫情动态等）

## prompt延伸的规则
- 医学文献库检索的查询扩展侧重于疾病与诊疗知识的深度查询
- 网络检索的查询扩展侧重于文献库无法检索到的信息

###重要！
至多再扩展不超过3个查询，如果需要扩展则按照下面的输出格式输出，如果不需要则返回None




## 输出格式
你的输出应该是一个JSON格式的列表，每个项目包含：
1. `action_name`：工具名称（"医学文献库搜索"或"网络搜索"）
2. `prompts`：一个扩展的问题，如果是网络检索，prompt不包含具体疾病名，如果是文献库检索，prompt只包含询问疾病相关内容，检索内容一定是一个简单问题，不包含对比
[
  {{
    "action_name": "工具名称",
    "prompts":'查询内容'
  }}
  ...
]

    '''.format(user_query,memory_global)
    result=(middle_json_model(prompt))
    # print(result)
    json_list=extract_json_content(result)
    try:
        structure_output=json.loads(json_list)
    except:
        structure_output = None

    return structure_output
        
    

def deduplicate_memory_global(memory):
    """
    对最终的memory进行全局去重，根据所有结果中的content_with_weight字段去重
    
    Args:
        memory: 记忆列表，每个元素包含"提问"和"结果"字段
        
    Returns:
        deduplicated_memory: 去重后的记忆列表
    """
    if not isinstance(memory, list):
        return memory
    
    # 用于跟踪已见过的content_with_weight
    seen_content = set()
    deduplicated_memory = []
    
    for memory_item in memory:
        if not isinstance(memory_item, dict) or '结果' not in memory_item:
            # 如果不是预期的结构，直接添加
            deduplicated_memory.append(memory_item)
            continue
            
        result = memory_item['结果']
        
        # 如果结果是列表，需要检查每个元素的content_with_weight
        if isinstance(result, list):
            deduplicated_result = []
            for item in result:
                if isinstance(item, dict) and 'content_with_weight' in item:
                    content = item['content_with_weight'].strip()  # 去除首尾空格
                    content_hash = hash(content)  # 使用hash来比较，避免长字符串比较问题
                    
                    if content_hash not in seen_content:
                        seen_content.add(content_hash)
                        deduplicated_result.append(item)
                    else:
                        # 如果已见过，打印调试信息
                        print(f"发现重复内容，已过滤: id={item.get('id', 'unknown')}, 内容前50字符: {content[:50]}")
                else:
                    # 如果没有content_with_weight字段，直接添加
                    deduplicated_result.append(item)
            
            # 创建新的memory_item，使用去重后的结果
            new_memory_item = {
                "提问": memory_item['提问'],
                "结果": deduplicated_result
            }
            deduplicated_memory.append(new_memory_item)
        else:
            # 如果结果不是列表，直接添加
            deduplicated_memory.append(memory_item)
    
    return deduplicated_memory

#执行模块tools,依次执行actions内的动作，根据action_name判断执行函数web_search_answer()，还是rag()
def process_actions(actions):
    """
    处理动作列表函数
    
    Args:
        actions: 动作列表，每个动作包含action_name和prompt
        
    Returns:
        memory: 包含每次调用结果的记忆列表
    """
    # 初始化记忆列表
    memory = []
    
    # 依次处理每个动作
    for action in actions:
        action_name = action['action_name']
        prompt = action['prompt']
        
        print(f'正在执行{action_name}: "{prompt}"')
        
        try:
            # 根据动作类型调用相应的函数
            if action_name == '医学文献库搜索':
                result = rag(prompt)
            elif action_name == '网络搜索':
                result = web_search_answer(prompt)
            else:
                result = f"未知的动作类型: {action_name}"
            
            # 将结果添加到记忆中
            memory_item = {
                "提问": prompt,
                "结果": result
            }
            memory.append(memory_item)
            
            # 输出结果
            print(f"提问：{prompt}")
            print(f"结果：{result}")
            print("-------------------")
            
        except Exception as e:
            # 如果执行失败，打印详细错误信息，继续下一轮循环
            print(f"--------{action_name}检索失败，错误详情: {str(e)}-----------")
            import traceback
            print(f"完整错误堆栈: {traceback.format_exc()}")
            continue
    
    print("所有执行动作已完成，结果已添加到memory中。")
    
    # 对最终的memory进行全局去重
    # 统计去重前的总结果数量
    total_before = sum(len(item['结果']) if isinstance(item['结果'], list) else 1 for item in memory)
    
    deduplicated_memory = deduplicate_memory_global(memory)
    
    # 统计去重后的总结果数量
    total_after = sum(len(item['结果']) if isinstance(item['结果'], list) else 1 for item in deduplicated_memory)
    
    print(f"去重前memory数量: {len(memory)}, 去重后memory数量: {len(deduplicated_memory)}")
    print(f"去重前总结果数量: {total_before}, 去重后总结果数量: {total_after}, 过滤了 {total_before - total_after} 个重复项")
    
    return deduplicated_memory


# 初始化OpenAI客户端
def final_answer(user_query):
    client = OpenAI(
        # 如果没有配置环境变量，请用百炼API Key替换：api_key="sk-xxx"
        api_key = os.getenv("DASHSCOPE_API_KEY"),
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
    )
    
    reasoning_content = ""  # 定义完整思考过程
    answer_content = ""     # 定义完整回复
    is_answering = False   # 判断是否结束思考过程并开始回复

    action_tool=agent_plan(user_query)
    print("action_tool")
    print(action_tool)

    if action_tool:
        adjusted_tools = adjust_format(action_tool)
        actions=adjusted_tools
    else:
        actions=[]

    for action in actions:
        action_name = action['action_name']
        prompt = action['prompt']
        message = {
            "role": "agent",
            "content": f'正在执行{action_name}: "{prompt}"'
        }

        json_message = json.dumps(message)
        yield f"event: message\ndata: {json_message}\n\n"

    memory_new=process_actions(actions)

    memory_global=[]
    # memory_global.extend(memory_new[1:])
    memory_global.extend(list(memory_new)[1:])

    # 反思模块
    action_reflect=reflection(user_query,memory_global)
    if action_reflect:
        print("回顾内容，进行反思...")
        memory_new=process_actions(actions)
        memory_global.extend(memory_new)
        
    final_prompt=f'''
        你是一个专业的智能问诊助手，负责根据用户的问题和提供的医学参考文献生成回答。请严格按照以下要求生成回答：
        1. 基于提供的医学参考文献进行回答，如果原文没有参考内容，根据你自己的医学知识进行回答
        2. 你需要用专业、严谨且通俗易懂的医学语言进行输出，体现出专业医疗助手的素养
        3. 回答应当结构清晰，必要时使用列表、分点说明症状、诊断依据、治疗建议等
        4. 涉及具体用药、剂量或治疗方案时，必须明确提示"请遵医嘱"
        5. 在回答结尾，必须附上声明："⚠️ 本回答仅供参考，不能替代专业医生的面诊。如有不适，请及时就医。"

        医学参考文献：
        {memory_global}

        用户问题：{user_query}

    '''

    print(final_prompt)    
    print('-'*130)
    
    # 创建聊天完成请求
    completion = client.chat.completions.create(
        model="deepseek-r1",  # 此处以 deepseek-r1 为例，可按需更换模型名称
        messages=[
            {"role": "user", "content": final_prompt}
        ],
        stream=True,
        # 解除以下注释会在最后一个chunk返回Token使用量
        # stream_options={
        #     "include_usage": True
        # }
    )
    
    print("\n" + "=" * 20 + "思考过程" + "=" * 20 + "\n")
    
    for chunk in completion:
        if chunk.choices[0].finish_reason == "stop":

            # 结束时发送 [DONE] 事件
            yield "event: end\ndata: [DONE]\n\n"
            break
        else:
            # 实时输出消息
            delta = chunk.choices[0].delta
            if delta.content:
                message = {
                    "role": "assistant",
                    "content": delta.content,
                    "thinking": False,
                }
                json_message = json.dumps(message)
                yield f"event: message\ndata: {json_message}\n\n"
            else :
                message = {
                    "role": "assistant",
                    "content": delta.reasoning_content,
                    "thinking": True,
                }
                json_message = json.dumps(message)
                yield f"event: message\ndata: {json_message}\n\n"


