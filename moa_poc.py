# Copyright 2024, Gary Sims

# sudo apt update
# sudo apt install python3-openai

import asyncio
from openai import OpenAI
from openai import AsyncOpenAI

async def talktollm(cl, pr):
    completion = await cl.chat.completions.create(
    model="",
    messages=[
        {"role": "user", "content": "".join(pr)}
    ],
    temperature=0.7,
    )

    return completion

async def main():
    client1 = AsyncOpenAI(base_url="http://192.168.1.209:1234/v1", api_key="lm-studio")
    client2 = AsyncOpenAI(base_url="http://192.168.1.183:1234/v1", api_key="lm-studio")
    client3 = AsyncOpenAI(base_url="http://192.168.1.136:1234/v1", api_key="lm-studio")
    agg = OpenAI(base_url="http://192.168.1.217:1234/v1", api_key="lm-studio")

    prompt = input(">> ")


    t2l1 = talktollm(client1, prompt)
    t2l2 = talktollm(client2, prompt)
    t2l3 = talktollm(client3, prompt)

    results = await asyncio.gather(t2l1, t2l2, t2l3)
    completion1 = results[0]
    completion2 = results[1]
    completion3 = results[2]
    print("\n\n++++ Response 1:\n", completion1.choices[0].message.content)
    print("\n\n++++ Response 2:\n", completion2.choices[0].message.content)
    print("\n\n++++ Response 3:\n", completion3.choices[0].message.content)

    aggprompt = "You have been provided with a set of responses from various large language models to a user query. Your task is to synthesize these responses into a single, high-quality response. It is crucial to critically evaluate the information provided in these responses, recognizing that some of it may be biased or incorrect. Your response should not simply replicate the given answers but should offer a refined, accurate, and comprehensive reply to the instruction. Ensure your response is well-structured, coherent, and adheres to the highest standards of accuracy and reliability. Do not add any extra comments about how you created the response, just synthesize these responses as instructed.\n\nThe query was: "
    aggprompt = aggprompt + prompt
    aggprompt = aggprompt + "\n---\n"
    aggprompt = aggprompt + "Here are the responses from models:\n"
    aggprompt = aggprompt + completion1.choices[0].message.content
    aggprompt = aggprompt + "\n---\n"
    aggprompt = aggprompt + completion2.choices[0].message.content
    aggprompt = aggprompt + "\n---\n"
    aggprompt = aggprompt + completion3.choices[0].message.content

    aggcompletion = agg.chat.completions.create(
    model="",
    messages=[
        {"role": "user", "content": "".join(aggprompt)}
    ],
    temperature=0.7,
    )

    print("++++ Aggregated reponse:\n")
    print(aggcompletion.choices[0].message.content)

#
#
#

asyncio.run(main())