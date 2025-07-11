import os
import requests

HUGGINGFACE_API_TOKEN = os.getenv("HUGGINGFACE_API_TOKEN")
API_URL = "https://api-inference.huggingface.co/models/google/flan-t5-small"
HEADERS = {"Authorization": f"Bearer {HUGGINGFACE_API_TOKEN}"}

class ai_service:
    @staticmethod
    def get_financial_advice(user_data):
        prompt = f"User data: {user_data}. Give financial advice in Uzbek."
        response = requests.post(API_URL, headers=HEADERS, json={"inputs": prompt})
        print("Status code:", response.status_code)
        print("Response:", response.text)
        if response.status_code == 200:
            result = response.json()
            if isinstance(result, list) and "generated_text" in result[0]:
                return result[0]["generated_text"]
            elif isinstance(result, dict) and "generated_text" in result:
                return result["generated_text"]
            else:
                return f"AI maslahatini olishda xatolik. To'liq javob: {response.text}"
        else:
            return f"AI xizmatida xatolik. Status: {response.status_code}, Javob: {response.text}"

    @staticmethod
    def analyze_spending_patterns(transactions):
        # Prompt hajmini cheklash: faqat oxirgi 10 ta tranzaksiya
        if isinstance(transactions, list) and len(transactions) > 10:
            transactions = transactions[:10]
        prompt = f"Analyze these transactions and give a summary in Uzbek: {transactions}"
        response = requests.post(API_URL, headers=HEADERS, json={"inputs": prompt})
        print("Status code:", response.status_code)
        print("Response:", response.text)
        if response.status_code == 200:
            result = response.json()
            if isinstance(result, list) and "generated_text" in result[0]:
                return result[0]["generated_text"]
            elif isinstance(result, dict) and "generated_text" in result:
                return result["generated_text"]
            else:
                return f"AI tahlilini olishda xatolik. To'liq javob: {response.text}"
        else:
            return f"AI xizmatida xatolik. Status: {response.status_code}, Javob: {response.text}"

    @staticmethod
    def get_default_advice():
        return "Moliyaviy maslahat: Har doim xarajatlaringizni nazorat qiling va tejashga harakat qiling." 