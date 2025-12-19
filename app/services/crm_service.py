"""
CRM Service - الدماغ المركزي للنظام 🧠
يدمج: Database + المحاور الذكي + WhatsApp
"""
import logging
from typing import Dict, Any, List
from datetime import datetime, timedelta

from app.services.crm_database import db
from app.services.smart_conversational_ai import SmartConversationalAI
from app.services.whatsapp_service import WhatsAppService
from app.models.crm_models import LeadCreate, LeadUpdate, get_lead_quality

logger = logging.getLogger(__name__)

class CRMService:
    """خدمة CRM المتكاملة"""
    
    def __init__(self):
        self.db = db
        self.ai_agent = SmartConversationalAI()
        self.whatsapp = WhatsAppService()
        self.auto_respond = True
        self.auto_score = True
    
    async def create_lead(self, lead_data: LeadCreate) -> Dict:
        """إنشاء عميل مع معالجة ذكية"""
        try:
            lead_dict = lead_data.dict()
            lead_dict['created_at'] = datetime.now().isoformat()
            lead_id = self.db.create_lead(lead_dict)
            
            # حساب النقاط الأولية
            if self.auto_score:
                score = self._calculate_initial_score(lead_dict)
                quality = get_lead_quality(score)
                self.db.update_lead(lead_id, {'score': score, 'quality': quality.value})
            
            # إنشاء مهمة متابعة
            self._create_follow_up_task(lead_id, lead_dict)
            
            # إرسال رسالة ترحيب واتساب
            if lead_dict.get('phone'):
                await self.whatsapp.send_message(
                    lead_dict['phone'],
                    f"مرحباً {lead_dict['name']}! شكراً لتواصلك مع Brilliox 🚀\nنحن هنا لمساعدتك في تحقيق أهدافك التسويقية."
                )
            
            lead = self.db.get_lead(lead_id)
            return {'success': True, 'lead_id': lead_id, 'lead': lead}
        except Exception as e:
            logger.error(f"Create lead error: {e}")
            return {'success': False, 'error': str(e)}
    
    async def get_lead(self, lead_id: int) -> Dict:
        """الحصول على بيانات عميل مع تحليلات"""
        lead = self.db.get_lead(lead_id)
        if not lead:
            return {'success': False, 'error': 'Lead not found'}
        interactions = self.db.get_lead_interactions(lead_id)
        trend = await self.ai_agent.analyze_conversation_trend(lead_id)
        return {'success': True, 'lead': lead, 'interactions': interactions, 'conversation_trend': trend}
    
    async def update_lead(self, lead_id: int, updates: LeadUpdate) -> Dict:
        """تحديث بيانات عميل"""
        try:
            update_dict = {k: v for k, v in updates.dict().items() if v is not None}
            if not update_dict:
                return {'success': False, 'error': 'No updates'}
            success = self.db.update_lead(lead_id, update_dict)
            if success:
                lead = self.db.get_lead(lead_id)
                return {'success': True, 'lead': lead}
            return {'success': False, 'error': 'Lead not found'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def search_leads(self, filters: Dict = None, limit: int = 50, offset: int = 0) -> Dict:
        """البحث في العملاء"""
        try:
            leads = self.db.search_leads(filters, limit, offset)
            return {'success': True, 'leads': leads, 'count': len(leads)}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def handle_incoming_message(self, lead_id: int, message: str, channel: str = 'whatsapp') -> Dict:
        """معالجة رسالة واردة بذكاء خارق 🚀"""
        try:
            lead = self.db.get_lead(lead_id)
            if not lead:
                return {'success': False, 'error': 'Lead not found'}
            
            interactions = self.db.get_lead_interactions(lead_id)
            conv_history = [
                {'role': 'user' if i['direction'] == 'inbound' else 'assistant', 'content': i['description']}
                for i in interactions[-10:]
            ]
            
            # معالجة بالمحاور الذكي
            ai_result = await self.ai_agent.process_message(message, lead_id, lead, conv_history)
            
            # حفظ الرسالة الواردة
            self.db.create_interaction({
                'lead_id': lead_id,
                'type': 'whatsapp' if channel == 'whatsapp' else 'note',
                'direction': 'inbound',
                'description': message,
                'created_at': datetime.now().isoformat()
            })
            
            # حفظ رد النظام
            self.db.create_interaction({
                'lead_id': lead_id,
                'type': 'whatsapp' if channel == 'whatsapp' else 'note',
                'direction': 'outbound',
                'description': ai_result['response'],
                'created_at': datetime.now().isoformat()
            })
            
            # تحديث نقاط العميل
            new_score = min(lead['score'] + ai_result.get('lead_score_change', 0), 5.0)
            new_quality = get_lead_quality(new_score)
            self.db.update_lead(lead_id, {
                'score': new_score,
                'quality': new_quality.value,
                'last_contact_at': datetime.now().isoformat()
            })
            
            # إرسال الرد على واتساب
            if channel == 'whatsapp' and self.auto_respond:
                await self.whatsapp.send_message(lead['phone'], ai_result['response'])
            
            # إنشاء مهمة عاجلة إذا لزم الأمر
            if ai_result.get('should_alert_team'):
                self._create_urgent_task(lead_id, ai_result.get('recommended_action'), 
                                        'urgent' if ai_result.get('readiness') == 'hot' else 'high')
            
            return {
                'success': True,
                'response': ai_result['response'],
                'intent': ai_result.get('intent'),
                'sentiment': ai_result.get('sentiment'),
                'readiness': ai_result.get('readiness'),
                'opportunity_score': ai_result.get('opportunity_score'),
                'lead_score': new_score,
                'lead_quality': new_quality.value,
                'should_alert_team': ai_result.get('should_alert_team')
            }
        except Exception as e:
            logger.error(f"Handle message error: {e}")
            return {'success': False, 'error': str(e)}
    
    async def send_message_to_lead(self, lead_id: int, message: str, channel: str = 'whatsapp') -> Dict:
        """إرسال رسالة لعميل"""
        try:
            lead = self.db.get_lead(lead_id)
            if not lead:
                return {'success': False, 'error': 'Lead not found'}
            
            if channel == 'whatsapp':
                result = await self.whatsapp.send_message(lead['phone'], message)
            else:
                result = {'success': True}
            
            self.db.create_interaction({
                'lead_id': lead_id,
                'type': 'whatsapp' if channel == 'whatsapp' else 'note',
                'direction': 'outbound',
                'description': message,
                'created_at': datetime.now().isoformat()
            })
            
            return {'success': True, 'message': '✅ تم إرسال الرسالة', 'details': result}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def get_dashboard(self) -> Dict:
        """لوحة التحكم الرئيسية"""
        try:
            stats = self.db.get_dashboard_stats()
            ai_stats = self.ai_agent.get_stats()
            return {'success': True, 'stats': stats, 'ai_performance': ai_stats, 'timestamp': datetime.now().isoformat()}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def get_my_tasks(self, user_id: int = None) -> Dict:
        """الحصول على المهام"""
        pending = self.db.get_pending_tasks(user_id)
        return {'success': True, 'pending_tasks': pending, 'total_pending': len(pending)}
    
    def _calculate_initial_score(self, lead_data: Dict) -> float:
        score = 0.0
        if lead_data.get('name') and lead_data.get('phone'):
            score += 1.0
        if lead_data.get('email'):
            score += 0.5
        if lead_data.get('company'):
            score += 0.3
        high_quality_sources = ['facebook_ad', 'google_ad', 'linkedin_ad', 'referral']
        if lead_data.get('source') in high_quality_sources:
            score += 2.0
        else:
            score += 1.0
        return min(round(score, 1), 5.0)
    
    def _create_follow_up_task(self, lead_id: int, lead_data: Dict):
        due_date = datetime.now() + timedelta(hours=24)
        self.db.create_task({
            'title': f'متابعة مع {lead_data["name"]}',
            'description': f'متابعة أولية من {lead_data.get("source", "مصدر غير محدد")}',
            'type': 'follow_up',
            'priority': 'high',
            'status': 'pending',
            'lead_id': lead_id,
            'due_date': due_date.isoformat(),
            'created_at': datetime.now().isoformat()
        })
    
    def _create_urgent_task(self, lead_id: int, reason: str, priority: str = 'urgent'):
        lead = self.db.get_lead(lead_id)
        due_date = datetime.now() + timedelta(minutes=15)
        self.db.create_task({
            'title': f'⚡ عاجل: {lead["name"]}',
            'description': f'فرصة ساخنة! {reason}',
            'type': 'urgent_follow_up',
            'priority': priority,
            'status': 'pending',
            'lead_id': lead_id,
            'due_date': due_date.isoformat(),
            'created_at': datetime.now().isoformat()
        })

crm_service = CRMService()
