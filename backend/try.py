from openai import OpenAI

client = OpenAI(
  base_url="https://openrouter.ai/api/v1",
  api_key="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",
)

completion = client.chat.completions.create(
#   extra_headers={
#     "HTTP-Referer": "<YOUR_SITE_URL>", # Optional. Site URL for rankings on openrouter.ai.
#     "X-Title": "<YOUR_SITE_NAME>", # Optional. Site title for rankings on openrouter.ai.
#   },
  extra_body={},
  model="deepseek/deepseek-chat-v3.1:free",
  #model="deepseek-chat",
  messages=[
    {
      "role": "user",
      "content": "What is the meaning of life?"
    }
  ]
)
print(completion.choices[0].message.content)
# import requests
# import json

# response = requests.post(
#   url="https://openrouter.ai/api/v1/chat/completions",
#   headers={
#     "Authorization": "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",
#     "Content-Type": "application/json",
#     # "HTTP-Referer": "<YOUR_SITE_URL>", # Optional. Site URL for rankings on openrouter.ai.
#     # "X-Title": "<YOUR_SITE_NAME>", # Optional. Site title for rankings on openrouter.ai.
#   },
#   data=json.dumps({
#     "model": "deepseek/deepseek-chat-v3.1:free",
#     "messages": [
#       {
#         "role": "user",
#         "content": "What is the meaning of life?"
#       }
#     ],
    
#   })
# )
# print(response)



# from openai import OpenAI

# # 初始化客户端
# client = OpenAI(
#     api_key="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",  # 替换为你的API密钥
#     base_url="https://openrouter.ai/api/v1"
# )

# # 调用
# response = client.chat.completions.create(
#     #model="deepseek/deepseek-chat-v3.1",
#     messages=[
#         {"role": "system", "content": "You are a helpful assistant"},
#         {"role": "user", "content": "你是deepseek的哪个版本？"},
#     ],
#     stream=False
# )

# print(response.choices[0].message.content)



# import openrouter

# client = openrouter.Client(
#     api_key="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",
#     base_url="https://openrouter.ai/api/v1",
#     default_model="deepseek-ai/deepseek-v3:free",
#     temperature=0.7,
#     max_tokens=2048
# )

# def ask_deepseek(prompt):
#     response = client.chat.completions.create(
#         messages=[{"role": "user", "content": prompt}],
#         temperature=0.8,
#         max_tokens=1024
#     )
#     return response.choices[0].message.content

# # 示例调用
# result = ask_deepseek("用Python实现快速排序算法")
# print(result)

# import requests
# import json

# # OpenRouter API 配置
# API_KEY = "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"  # 替换为您的 API 密钥
# API_URL = "https://openrouter.ai/api/v1/chat/completions"

# # 请求头
# headers = {
#     "Authorization": f"Bearer {API_KEY}",
#     "Content-Type": "application/json"
# }

# # 请求数据
# data = {
#     "model": "deepseek/deepseek-chat",  # DeepSeek 模型标识符
#     "messages": [
#         {"role": "system", "content": "You are a helpful assistant."},
#         {"role": "user", "content": "你好，请介绍一下你自己"}
#     ],
#     "temperature": 0.7,
#     "max_tokens": 1000
# }

# # 发送请求
# try:
#     response = requests.post(API_URL, headers=headers, json=data)
#     result = response.json()
    
#     if response.status_code == 200:
#         print("回答:", result['choices'][0]['message']['content'])
#     else:
#         print("错误:", result)
        
# except Exception as e:
#     print("请求失败:", str(e))