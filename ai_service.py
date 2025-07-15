import httpx

RAPIDAPI_URL = 'https://chatgpt-42.p.rapidapi.com/gpt4'
RAPIDAPI_KEY = '2ac44aca25msh901b0ec27b93167p121bacjsnba9e2c3ca446'
RAPIDAPI_HOST = 'chatgpt-42.p.rapidapi.com'

HEADERS = {
    "content-type": "application/json",
    "X-RapidAPI-Key": RAPIDAPI_KEY,
    "X-RapidAPI-Host": RAPIDAPI_HOST
}

class ai_service:
    @staticmethod
    async def get_financial_advice(user_data):
        prompt = f"User data: {user_data}. Give financial advice in Uzbek."
        data = {"messages": [{"role": "user", "content": prompt}]}
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(RAPIDAPI_URL, json=data, headers=HEADERS, timeout=30)
                if response.status_code == 200:
                    result = response.json()
                    return result.get("result", "AI javobini olishda xatolik.")
                else:
                    return f"AI xizmatida xatolik. Status: {response.status_code}, Javob: {response.text}"
            except Exception as e:
                return f"AI xizmatida xatolik: {e}"

    @staticmethod
    async def analyze_spending_patterns(transactions):
        prompt = f"Analyze these transactions and give a summary in Uzbek: {transactions}"
        data = {"messages": [{"role": "user", "content": prompt}]}
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(RAPIDAPI_URL, json=data, headers=HEADERS, timeout=30)
                if response.status_code == 200:
                    result = response.json()
                    return result.get("result", "AI javobini olishda xatolik.")
                else:
                    return f"AI xizmatida xatolik. Status: {response.status_code}, Javob: {response.text}"
            except Exception as e:
                return f"AI xizmatida xatolik: {e}"

    @staticmethod
    def get_default_advice():
        return "Moliyaviy maslahat: Har doim xarajatlaringizni nazorat qiling va tejashga harakat qiling."

    @staticmethod
    async def generate_budget_plan(user_data, transactions):
        prompt = (
            f"Foydalanuvchi ma'lumotlari: {user_data}. "
            f"Tranzaksiyalar tarixi: {transactions}. "
            "Foydalanuvchiga oylik daromad, xarajatlar va maqsadlar asosida optimal byudjet rejasini tuzib bering. "
            "Reja qisqa, aniq va motivatsion bo'lsin. Til: o'zbek."
        )
        data = {"messages": [{"role": "user", "content": prompt}]}
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(RAPIDAPI_URL, json=data, headers=HEADERS, timeout=30)
                if response.status_code == 200:
                    result = response.json()
                    return result.get("result", "AI javobini olishda xatolik.")
                else:
                    return f"AI xizmatida xatolik. Status: {response.status_code}, Javob: {response.text}"
            except Exception as e:
                return f"AI xizmatida xatolik: {e}"

    @staticmethod
    async def monitor_goal_progress(goal_data, transactions):
        prompt = (
            f"Foydalanuvchi maqsadi: {goal_data}. "
            f"Tranzaksiyalar tarixi: {transactions}. "
            "Foydalanuvchining maqsadga erishish progressini tahlil qiling va qisqa motivatsion yoki ogohlantiruvchi xabar bering. Til: o'zbek."
        )
        data = {"messages": [{"role": "user", "content": prompt}]}
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(RAPIDAPI_URL, json=data, headers=HEADERS, timeout=30)
                if response.status_code == 200:
                    result = response.json()
                    return result.get("result", "AI javobini olishda xatolik.")
                else:
                    return f"AI xizmatida xatolik. Status: {response.status_code}, Javob: {response.text}"
            except Exception as e:
                return f"AI xizmatida xatolik: {e}" 