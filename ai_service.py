import requests

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
    def get_financial_advice(user_data):
        """Get financial advice in Uzbek using RapidAPI GPT-4."""
        prompt = f"User data: {user_data}. Give financial advice in Uzbek."
        data = {
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }
        try:
            response = requests.post(RAPIDAPI_URL, json=data, headers=HEADERS, timeout=30)
            if response.status_code == 200:
                result = response.json()
                return result.get("result", "AI javobini olishda xatolik.")
            else:
                return f"AI xizmatida xatolik. Status: {response.status_code}, Javob: {response.text}"
        except Exception as e:
            return f"AI xizmatida xatolik: {e}"

    @staticmethod
    def analyze_spending_patterns(transactions):
        """Analyze spending patterns in Uzbek using RapidAPI GPT-4."""
        prompt = f"Analyze these transactions and give a summary in Uzbek: {transactions}"
        data = {
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }
        try:
            response = requests.post(RAPIDAPI_URL, json=data, headers=HEADERS, timeout=30)
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