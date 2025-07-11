import os
import aiohttp
import json
from typing import Optional

# AI API konfiguratsiyasi
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
AI_ENABLED = False  # Vaqtinchalik o'chirildi

class AIService:
    def __init__(self):
        self.api_key = OPENAI_API_KEY
        self.base_url = "https://api.openai.com/v1/chat/completions"
    
    async def get_financial_advice(self, user_data: dict) -> str:
        """Foydalanuvchi ma'lumotlari asosida moliyaviy maslahat berish"""
        if not AI_ENABLED:
            return self.get_default_advice()
        
        try:
            prompt = self._create_financial_prompt(user_data)
            response = await self._call_openai_api(prompt)
            return response
        except Exception as e:
            print(f"AI API xatosi: {e}")
            return self.get_default_advice()
    
    def _create_financial_prompt(self, user_data: dict) -> str:
        """Moliyaviy maslahat uchun prompt yaratish"""
        balance = user_data.get('balance', 0)
        income = user_data.get('income', 0)
        expenses = user_data.get('expenses', 0)
        categories = user_data.get('categories', [])

        empty_text = "Ma'lumot yo'q"
        categories_str = ', '.join(categories) if categories else empty_text

        prompt = (
            f"Siz O'zbekistonda yashovchi foydalanuvchiga moliyaviy maslahat beruvchi AI yordamchisiz.\n\n"
            f"Foydalanuvchi ma'lumotlari:\n"
            f"- Balans: {balance} so'm\n"
            f"- Oylik kirim: {income} so'm  \n"
            f"- Oylik chiqim: {expenses} so'm\n"
            f"- Eng ko'p xarajat qilgan kategoriyalar: {categories_str}\n\n"
            "O'zbek tilida qisqa va foydali moliyaviy maslahat bering. Maslahat:\n"
            "1. 2-3 jumladan iborat bo'lsin\n"
            "2. Amaliy va qo'llash mumkin bo'lsin\n"
            "3. Ijobiy va motivatsiyali bo'lsin\n"
            "4. O'zbek tilida yozilsin\n\n"
            "Maslahat:"
        )
        return prompt
    
    async def _call_openai_api(self, prompt: str) -> str:
        """OpenAI API ga so'rov yuborish"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {"role": "system", "content": "Siz O'zbekistonda yashovchi foydalanuvchiga moliyaviy maslahat beruvchi AI yordamchisiz. O'zbek tilida javob bering."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 200,
            "temperature": 0.7
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(self.base_url, headers=headers, json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    return result['choices'][0]['message']['content'].strip()
                else:
                    raise Exception(f"API xatosi: {response.status}")
    
    def get_default_advice(self) -> str:
        """AI yo'q bo'lganda standart maslahat"""
        import random
        
        advice_list = [
            "💡 Moliyaviy maslahat:\n\n"
            "💰 Har oy ma'lum foizini tejash rejangizni tuzing. "
            "Masalan, kirimingizning 20% ni avtomatik tejash hisobiga o'tkazing.",
            
            "💡 Moliyaviy maslahat:\n\n"
            "📊 Xarajatlaringizni kuzatib boring va har oy tahlil qiling. "
            "Bu sizga qaysi kategoriyalarda tejash mumkinligini ko'rsatadi.",
            
            "💡 Moliyaviy maslahat:\n\n"
            "🎯 Qisqa va uzoq muddatli moliyaviy maqsadlar belgilang. "
            "Bu sizga tejash uchun motivatsiya beradi.",
            
            "💡 Moliyaviy maslahat:\n\n"
            "🚫 Impulsiv xarid qilishdan saqlaning. "
            "Har bir xarid oldidan 24 soat kutib, kerakligini aniqlang.",
            
            "💡 Moliyaviy maslahat:\n\n"
            "📈 Daromadlaringizni oshirish uchun qo'shimcha ishlar yoki "
            "biznes imkoniyatlarini ko'rib chiqing."
        ]
        
        return random.choice(advice_list)
    
    async def analyze_spending_patterns(self, transactions: list) -> str:
        """Xarajatlar tahlili"""
        if not AI_ENABLED:
            return "📊 Xarajatlar tahlili uchun AI yoqilgan bo'lishi kerak."
        
        try:
            # Tranzaksiyalarni tahlil qilish
            total_expense = sum(t['amount'] for t in transactions if t['type'] == 'expense')
            categories = {}
            
            for t in transactions:
                if t['type'] == 'expense':
                    cat = t['category']
                    categories[cat] = categories.get(cat, 0) + t['amount']
            
            # Eng ko'p xarajat qilgan kategoriyalar
            top_categories = sorted(categories.items(), key=lambda x: x[1], reverse=True)[:3]
            
            prompt = f"""Foydalanuvchining xarajatlarini tahlil qiling:

Jami xarajat: {total_expense} so'm
Eng ko'p xarajat qilgan kategoriyalar:
{chr(10).join([f"- {cat}: {amount} so'm" for cat, amount in top_categories])}

O'zbek tilida qisqa tahlil bering va tejash maslahatlarini bering."""
            
            response = await self._call_openai_api(prompt)
            return response
            
        except Exception as e:
            return f"Tahlil xatosi: {e}"

# Global AI service instance
ai_service = AIService() 