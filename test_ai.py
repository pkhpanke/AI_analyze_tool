from openai import OpenAI

# 直接在代码中设置 API 密钥
api_key = "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"  # 替换为您的实际 API 密钥
client = OpenAI(api_key=api_key)

# Non-streaming:
print("----- standard request -----")
completion = client.chat.completions.create(
    model="gpt-4",
    messages=[
        {
            "role": "user",
            "content": "Say this is a test",
        },
    ],
)
print(completion.choices[0].message.content)

# Streaming:
print("----- streaming request -----")
stream = client.chat.completions.create(
    model="gpt-4",
    messages=[
        {
            "role": "user",
            "content": "How do I output all files in a directory using Python?",
        },
    ],
    stream=True,
)
for chunk in stream:
    if not chunk.choices:
        continue

    print(chunk.choices[0].delta.content, end="")
print()

# Response headers:
print("----- custom response headers test -----")
response = client.chat.completions.with_raw_response.create(
    model="gpt-4",
    messages=[
        {
            "role": "user",
            "content": "Say this is a test",
        }
    ],
)
completion = response.parse()
print(response.request_id)
print(completion.choices[0].message.content)