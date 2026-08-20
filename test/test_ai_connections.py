import _project_path  # noqa: F401

import json
import os
import sys

from dotenv import load_dotenv
from openai import OpenAI


# 从当前项目的 .env 中读取配置
load_dotenv()


def get_required_config(name):
    """读取必填配置，但不会把密钥打印出来。"""
    value = os.getenv(name, "").strip()

    if not value:
        raise RuntimeError(f"{name} 没有配置")

    if "这里换成" in value:
        raise RuntimeError(f"{name} 仍然是演示文字，没有替换成真实配置")

    return value


def show_error(test_name, error):
    """显示容易理解的错误提示。"""
    message = str(error)

    print()
    print("=" * 60)
    print(f"{test_name}失败")
    print(f"错误类型：{type(error).__name__}")
    print(f"错误信息：{message}")
    print()

    if "401" in message:
        print("可能原因：API密钥错误、失效，或者复制时多了空格。")
    elif "402" in message:
        print("可能原因：DeepSeek API账户余额不足。")
    elif "404" in message:
        print("可能原因：模型名称错误，或者当前账户不能使用该模型。")
    elif "429" in message:
        print("可能原因：调用太频繁或账户额度暂时用完。")
    elif "timeout" in message.lower():
        print("可能原因：网络连接超时，请稍后重试。")
    else:
        print("请把这段错误信息发给我，但不要发送.env文件或真实密钥。")

    print("=" * 60)


def create_llm_client():
    """创建聊天模型客户端。"""
    return OpenAI(
        api_key=get_required_config("LLM_API_KEY"),
        base_url=get_required_config("LLM_BASE_URL"),
    )


def test_normal_chat():
    """测试DeepSeek是否可以正常回答。"""
    print("[1/3] 正在测试DeepSeek普通聊天……")

    client = create_llm_client()
    model = get_required_config("LLM_MODEL")

    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": "你是医院物业安管系统的接口测试助手。",
            },
            {
                "role": "user",
                "content": "请只回答：聊天模型连接成功",
            },
        ],
        stream=False,
    )

    answer = response.choices[0].message.content or ""

    if not answer.strip():
        raise RuntimeError("接口返回成功，但回答内容为空")

    print(f"模型名称：{model}")
    print(f"模型回答：{answer.strip()}")
    print("普通聊天测试通过。")
    print()


def test_tool_call():
    """测试模型是否支持Agent所需的工具调用。"""
    print("[2/3] 正在测试Agent工具调用……")

    client = create_llm_client()
    model = get_required_config("LLM_MODEL")

    tools = [
        {
            "type": "function",
            "function": {
                "name": "search_knowledge",
                "description": "搜索医院物业安管知识资料",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "需要检索的问题",
                        }
                    },
                    "required": ["query"],
                    "additionalProperties": False,
                },
            },
        }
    ]

    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": "你是工具调用测试助手。",
            },
            {
                "role": "user",
                "content": "请调用search_knowledge工具，查找医院困梯处置资料。",
            },
        ],
        tools=tools,
        tool_choice={
            "type": "function",
            "function": {
                "name": "search_knowledge",
            },
        },
        extra_body={
            "thinking": {
                "type": "disabled",
            }
        },
        stream=False,
    )

    message = response.choices[0].message
    tool_calls = message.tool_calls or []

    if not tool_calls:
        raise RuntimeError("模型能够聊天，但没有返回工具调用")

    first_call = tool_calls[0]
    arguments = json.loads(first_call.function.arguments or "{}")

    print(f"模型选择的工具：{first_call.function.name}")
    print(
        "模型生成的参数："
        + json.dumps(arguments, ensure_ascii=False)
    )
    print("Agent工具调用测试通过。")
    print()


def test_embedding():
    """测试ModelScope是否能把文字转换为向量。"""
    print("[3/3] 正在测试ModelScope向量接口……")

    client = OpenAI(
        api_key=get_required_config("EMBEDDING_API_KEY"),
        base_url=get_required_config("EMBEDDING_BASE_URL"),
    )

    model = get_required_config("EMBEDDING_MODEL")

    response = client.embeddings.create(
        model=model,
        input=["医院消防通道巡检注意事项"],
    )

    if not response.data:
        raise RuntimeError("向量接口返回成功，但没有向量数据")

    vector = response.data[0].embedding

    if not vector:
        raise RuntimeError("向量接口返回了空向量")

    print(f"模型名称：{model}")
    print(f"向量维度：{len(vector)}")
    print("向量接口测试通过。")
    print()


def main():
    print("=" * 60)
    print("医院物业安管系统——AI接口测试")
    print("=" * 60)
    print()

    try:
        test_normal_chat()
        test_tool_call()
        test_embedding()
    except Exception as error:
        show_error("AI接口连接", error)
        sys.exit(1)

    print("=" * 60)
    print("三个测试全部通过")
    print("DeepSeek聊天：正常")
    print("Agent工具调用：正常")
    print("ModelScope向量：正常")
    print("=" * 60)


if __name__ == "__main__":
    main()
