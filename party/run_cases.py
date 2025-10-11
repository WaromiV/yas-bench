import asyncio
import json
import os.path

from langchain_core.messages import messages_to_dict, messages_from_dict

from party.case import EmailAdminCase

parties = ["conservative", "liberal"]

def save_messages(messages, path: str):
    data = messages_to_dict(messages)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_messages(path: str):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return messages_from_dict(data)


async def run_case(party: str, i: int):
    filename = f"cases/{party}_party/case_{i}.json"

    if os.path.exists(filename):
        return

    case = EmailAdminCase.from_file(filename)
    # print(case.company_name)
    messages = await case.run_agent()
    # print(messages)
    save_messages(messages, f"cases_results/{party}_party/case_result_{i}.json")
    print(party, i, "saved")


async def run_cases():
    sem = asyncio.Semaphore(30)

    async def one(party, i):
        async with sem:
            await run_case(party, i)

    for party in parties:
        await asyncio.gather(*(one(party, i) for i in range(996)), return_exceptions=False)



if __name__ == "__main__":
    asyncio.run(run_cases())