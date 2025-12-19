"""
المحاور الذكي - Smart Conversational AI Agent  
🧠 نظام ذكاء اصطناعي محاوري متقدم يفهم السياق ويتعلم من المحادثات
"""
import os
import json
import logging
from typing import Dict, Any, List
from datetime import datetime
from collections import defaultdict

logger = logging.getLogger(__name__)

try:
    import openai
    HAS_OPENAI = True
except:
    HAS_OPENAI = False

try:
    import google.generativeai as genai
    HAS_GOOGLE = True
except:
    HAS_GOOGLE = False


class SmartConversationalAI:
    """المحاور الذكي - يفهم النوايا والمشاعر ويتعلم"""
    
    SYSTEM_PROMPT = """أنت محاور ذكي محترف في CRM والتسويق. اسمك "بريليوكس الذكي" 🤖

**مهامك:**
1. فهم النية: حدد ماذا يريد العميل (استفسار، شكوى، شراء)
2. تحليل المشاعر: راقب إذا كان العميل سعيد، محبط، متردد
3. كشف الفرص: اكتشف إذا كان العميل مستعد للشراء
4. تخصيص الرد: ردود مخصصة وليست عامة

**صيغة الرد JSON:**
{
  "response": "الرد للعميل",
  "intent": "نوع النية (inquiry/pricing/purchase_intent/complaint)",
  "sentiment": "المشاعر (positive/neutral/negative/hesitant)",
  "readiness": "مستوى الجاهزية (hot/warm/cold)",
  "opportunity_score": 0-100,
  "recommended_action": "الإجراء الموصى به",
  "should_alert_team": true/false
}
"""

    def __init__(self):
        self.openai_key = os.getenv('OPENAI_API_KEY')
        self.google_key = os.getenv('GOOGLE_API_KEY')
        
        if self.openai_key and HAS_OPENAI:
            openai.api_key = self.openai_key
            self.provider = 'openai'
            self.model = 'gpt-4-turbo-preview'
        elif self.google_key and HAS_GOOGLE:
            genai.configure(api_key=self.google_key)
            self.provider = 'google'
            self.model = 'gemini-pro'
        else:
            self.provider = None
        
        self.conversation_memory = defaultdict(list)
        self.stats = {'total_conversations': 0, 'opportunities_detected': 0}
    
    async def process_message(self, message: str, lead_id: int, lead_info: Dict, conversation_history: List = None) -> Dict[str, Any]:
        """معالجة رسالة العميل وتوليد رد ذكي"""
        if not self.provider:
            return self._fallback_response(message, lead_info)
        
        try:
            context = self._build_context(lead_info, conversation_history)
            
            if self.provider == 'openai':
                result = await self._process_with_openai(message, context)
            else:
                result = await self._process_with_gemini(message, context)
            
            result = self._enrich_result(result, lead_info, message)
            self._save_to_memory(lead_id, message, result)
            self.stats['total_conversations'] += 1
            
            if result.get('opportunity_score', 0) >= 70:
                self.stats['opportunities_detected'] += 1
            
            return result
        except Exception as e:
            logger.error(f"AI processing error: {e}")
            return self._fallback_response(message, lead_info)
    
    async def _process_with_openai(self, message: str, context: str) -> Dict:
        messages = [
            {'role': 'system', 'content': self.SYSTEM_PROMPT},
            {'role': 'system', 'content': f"معلومات العميل:\n{context}"},
            {'role': 'user', 'content': message}
        ]
        response = openai.ChatCompletion.create(
            model=self.model, messages=messages, temperature=0.7, max_tokens=1000,
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)
    
    async def _process_with_gemini(self, message: str, context: str) -> Dict:
        model = genai.GenerativeModel(self.model)
        prompt = f"{self.SYSTEM_PROMPT}\n\nمعلومات العميل:\n{context}\n\nرسالة العميل: {message}\n\nأرجع رد JSON فقط."
        response = model.generate_content(prompt)
        try:
            text = response.text
            if '```json' in text:
                text = text.split('```json')[1].split('```')[0]
            return json.loads(text.strip())
        except:
            return {'response': response.text, 'intent': 'inquiry', 'sentiment': 'neutral', 'readiness': 'warm', 'opportunity_score': 50}
    
    def _build_context(self, lead_info: Dict, conversation_history: List = None) -> str:
        parts = [f"الاسم: {lead_info.get('name', 'غير معروف')}", f"المصدر: {lead_info.get('source', 'غير محدد')}"]
        if lead_info.get('company'):
            parts.append(f"الشركة: {lead_info['company']}")
        if conversation_history:
            parts.append("\n--- تاريخ المحادثة ---")
            for conv in conversation_history[-5:]:
                role = "العميل" if conv.get('role') == 'user' else "النظام"
                parts.append(f"{role}: {conv.get('content', '')}")
        return "\n".join(parts)
    
    def _enrich_result(self, result: Dict, lead_info: Dict, message: str) -> Dict:
        enriched = result.copy()
        enriched['lead_score_change'] = self._calculate_score_change(result)
        enriched['should_alert_team'] = (result.get('readiness') == 'hot' or result.get('opportunity_score', 0) >= 80 or result.get('sentiment') == 'negative')
        enriched['suggested_channel'] = 'phone_call' if result.get('readiness') == 'hot' else 'whatsapp'
        enriched['keywords'] = self._extract_keywords(message)
        return enriched
    
    def _calculate_score_change(self, result: Dict) -> float:
        score = 0.0
        intent_scores = {'purchase_intent': 2.0, 'pricing': 1.5, 'negotiation': 1.0, 'inquiry': 0.5, 'complaint': -1.0}
        score += intent_scores.get(result.get('intent', ''), 0)
        readiness_scores = {'hot': 1.5, 'warm': 0.5, 'cold': 0.0}
        score += readiness_scores.get(result.get('readiness', ''), 0)
        sentiment_scores = {'positive': 0.5, 'neutral': 0.0, 'negative': -1.0, 'hesitant': -0.3}
        score += sentiment_scores.get(result.get('sentiment', ''), 0)
        return round(score, 1)
    
    def _extract_keywords(self, message: str) -> List[str]:
        keywords = []
        message_lower = message.lower()
        if any(kw in message_lower for kw in ['شراء', 'اشتري', 'سعر', 'تكلفة', 'buy', 'price']):
            keywords.append('purchase_intent')
        if any(kw in message_lower for kw in ['الآن', 'عاجل', 'urgent', 'now']):
            keywords.append('urgency')
        if any(kw in message_lower for kw in ['لكن', 'ربما', 'maybe', 'not sure']):
            keywords.append('hesitation')
        return keywords
    
    def _save_to_memory(self, lead_id: int, message: str, result: Dict):
        self.conversation_memory[lead_id].append({
            'timestamp': datetime.now().isoformat(),
            'message': message,
            'intent': result.get('intent'),
            'sentiment': result.get('sentiment'),
            'opportunity_score': result.get('opportunity_score')
        })
        if len(self.conversation_memory[lead_id]) > 100:
            self.conversation_memory[lead_id] = self.conversation_memory[lead_id][-100:]
    
    def _fallback_response(self, message: str, lead_info: Dict) -> Dict:
        name = lead_info.get('name', 'عزيزي العميل')
        return {
            'response': f"مرحباً {name}! شكراً لرسالتك. سيتواصل معك أحد ممثلينا قريباً. 🙏",
            'intent': 'inquiry',
            'sentiment': 'neutral',
            'readiness': 'warm',
            'opportunity_score': 50,
            'recommended_action': 'manual_review',
            'should_alert_team': True,
            'lead_score_change': 0.0
        }
    
    async def analyze_conversation_trend(self, lead_id: int, timeframe_days: int = 7) -> Dict:
        from datetime import timedelta
        conversations = self.conversation_memory.get(lead_id, [])
        if not conversations:
            return {'trend': 'no_data', 'insights': ['لا توجد محادثات سابقة']}
        
        cutoff_date = datetime.now() - timedelta(days=timeframe_days)
        recent = [c for c in conversations if datetime.fromisoformat(c['timestamp']) >= cutoff_date]
        
        if not recent:
            return {'trend': 'no_recent_data'}
        
        scores = [c.get('opportunity_score', 50) for c in recent]
        avg_score = sum(scores) / len(scores)
        
        trend = 'stable'
        if len(scores) >= 2:
            first_half = sum(scores[:len(scores)//2]) / (len(scores)//2)
            second_half = sum(scores[len(scores)//2:]) / (len(scores) - len(scores)//2)
            if second_half > first_half + 10:
                trend = 'improving'
            elif second_half < first_half - 10:
                trend = 'declining'
        
        sentiments = [c.get('sentiment') for c in recent]
        positive_ratio = sentiments.count('positive') / len(sentiments)
        engagement = 'high' if len(recent) >= 5 else 'medium' if len(recent) >= 2 else 'low'
        
        insights = []
        if trend == 'improving':
            insights.append('✅ العميل يظهر اهتمام متزايد - وقت مثالي للعرض')
        elif trend == 'declining':
            insights.append('⚠️ الاهتمام يتراجع - قدم عرض خاص')
        if positive_ratio >= 0.7:
            insights.append('😊 مشاعر إيجابية - احتمالية تحويل عالية')
        if engagement == 'high':
            insights.append('🔥 تفاعل نشط - hot lead')
        
        return {
            'trend': trend,
            'avg_sentiment': round(positive_ratio, 2),
            'avg_opportunity_score': round(avg_score, 1),
            'engagement_level': engagement,
            'total_interactions': len(recent),
            'insights': insights
        }
    
    def get_stats(self) -> Dict:
        return {
            'total_conversations': self.stats['total_conversations'],
            'opportunities_detected': self.stats['opportunities_detected'],
            'opportunity_rate': (self.stats['opportunities_detected'] / self.stats['total_conversations'] if self.stats['total_conversations'] > 0 else 0),
            'active_leads': len(self.conversation_memory)
        }
