from openai import OpenAI

client = OpenAI(
    api_key="sk-xt-1eb14faeccf46ea52864fb6ff4ea14c88c74c161eec0607b",
    base_url="https://api.xkiro.com/v1",
)

res = client.chat.completions.create(
    model="cohere/command-a-plus",
    messages=[
        {
            "role": "system",
            "content": "Bạn là trợ lý AI nói tiếng Việt tự nhiên, dễ hiểu."
        },
        {
            "role": "user",
            "content": "Tôi thường xuyên bị mất ngủ vào ban đêm, có những cách nào giúp cải thiện giấc ngủ?"
        }
    ],
    temperature=0.7,
)

print("\nAI trả lời:")
print(res.choices[0].message.content)