import httpx
from utils import get_user_language

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
    async def get_financial_advice(user_data, user_id=None):
        language = get_user_language(user_id) if user_id else 'uz'
        lang_map = {'uz': "o'zbek tilida", 'ru': "на русском языке", 'en': "in English"}
        prompt = (
            f"Foydalanuvchi ma'lumotlari: {user_data}. "
            "Moliyaviy holatni qisqacha tahlil qilib, 2-3 ta aniq va amaliy maslahat bering. "
            "Tejash, xarajatlarni optimallashtirish va daromadni oshirishga e'tibor qarating. "
            f'Javobingiz {lang_map.get(language, "o\'zbek tilida")}, qisqa va motivatsion bo\'lsin. Emojilar ishlating.'
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
    async def analyze_spending_patterns(transactions, user_id=None):
        language = get_user_language(user_id) if user_id else 'uz'
        lang_map = {'uz': "o'zbek tilida", 'ru': "на русском языке", 'en': "in English"}
        prompt = (
            f"Tranzaksiyalar: {transactions}. "
            "Xarajatlar va daromadlar patternini tahlil qiling. "
            "Keraksiz xarajatlarni aniqlang va 2-3 ta tejash usulini taklif qiling. "
            f'Javobingiz {lang_map.get(language, "o\'zbek tilida")}, qisqa, aniq va emojilar bilan bo\'lsin.'
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
    def get_default_advice():
        return "Moliyaviy maslahat: Har doim xarajatlaringizni nazorat qiling va tejashga harakat qiling."

    @staticmethod
    async def generate_budget_plan(user_data, transactions, user_id=None):
        language = get_user_language(user_id) if user_id else 'uz'
        lang_map = {'uz': "o'zbek tilida", 'ru': "на русском языке", 'en': "in English"}
        prompt = (
            f"Foydalanuvchi ma'lumotlari: {user_data}. "
            f"Tranzaksiyalar tarixi: {transactions}. "
            "Oylik daromad, xarajat va kategoriyalar asosida oddiy, amaliy va qisqa byudjet rejasini tuzing. "
            "50/30/20 qoidasi, tejash va optimallashtirish bo'yicha 2-3 ta tavsiya bering. "
            f'Javobingiz {lang_map.get(language, "o\'zbek tilida")}, qisqa va motivatsion bo\'lsin.'
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
    async def monitor_goal_progress(goal_data, transactions, user_id=None):
        language = get_user_language(user_id) if user_id else 'uz'
        lang_map = {'uz': "o'zbek tilida", 'ru': "на русском языке", 'en': "in English"}
        prompt = (
            f"Foydalanuvchi maqsadi: {goal_data}. "
            f"Tranzaksiyalar tarixi: {transactions}. "
            "Maqsadga erishish progressini tahlil qiling va 2 ta motivatsion maslahat bering. "
            f'Javobingiz {lang_map.get(language, "o\'zbek tilida")}, qisqa va aniq bo\'lsin.'
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