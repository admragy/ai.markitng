from typing import Dict, List, Optional
from datetime import datetime, timedelta
from database import db
from models import LeadCreate, LeadUpdate

class CRM:
    def __init__(self):
        self.stats_cache = {}
        self.last_update = None
    
    async def create_lead(self, lead_data: LeadCreate, user_id: str) -> Dict:
        try:
            lead = {
                "phone": lead_data.phone,
                "name": lead_data.name,
                "email": lead_data.email,
                "source": lead_data.source,
                "notes": lead_data.notes,
                "status": "new",
                "created_by": user_id,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            result = db.execute(table="leads", operation="insert", data=lead)
            
            return {
                "success": True,
                "lead_id": result.data[0]["id"] if result.data else None,
                "message": "تم إنشاء العميل بنجاح"
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_leads(self, user_id: str, filters: Optional[Dict] = None) -> List[Dict]:
        try:
            query = db.client.table("leads").select("*").eq("created_by", user_id)
            
            if filters:
                if filters.get("status"):
                    query = query.eq("status", filters["status"])
                if filters.get("source"):
                    query = query.eq("source", filters["source"])
                if filters.get("date_from"):
                    query = query.gte("created_at", filters["date_from"])
                if filters.get("date_to"):
                    query = query.lte("created_at", filters["date_to"])
            
            result = query.order("created_at", desc=True).limit(100).execute()
            return result.data
            
        except Exception as e:
            print(f"خطأ في جلب العملاء: {e}")
            return []
    
    async def update_lead(self, lead_id: str, update_data: LeadUpdate, user_id: str) -> Dict:
        try:
            update_data_dict = update_data.dict(exclude_unset=True)
            update_data_dict["updated_at"] = datetime.now().isoformat()
            
            result = db.execute(table="leads", operation="update", id=lead_id, data=update_data_dict)
            return {"success": True, "message": "تم التحديث بنجاح"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_dashboard_stats(self, user_id: str) -> Dict:
        try:
            week_ago = (datetime.now() - timedelta(days=7)).isoformat()
            new_leads = db.client.table("leads").select("id", count="exact").eq("created_by", user_id).gte("created_at", week_ago).execute()
            
            status_counts = {}
            status_result = db.client.table("leads").select("status").eq("created_by", user_id).execute()
            for lead in status_result.data:
                status = lead.get("status", "unknown")
                status_counts[status] = status_counts.get(status, 0) + 1
            
            source_counts = {}
            source_result = db.client.table("leads").select("source").eq("created_by", user_id).execute()
            for lead in source_result.data:
                source = lead.get("source", "unknown")
                source_counts[source] = source_counts.get(source, 0) + 1
            
            return {
                "total_leads": sum(status_counts.values()),
                "new_this_week": new_leads.count or 0,
                "status_distribution": status_counts,
                "source_distribution": source_counts,
                "updated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"خطأ في الإحصائيات: {e}")
            return {"error": "خطأ في جلب الإحصائيات"}
    
    async def assign_lead(self, lead_id: str, assign_to: str, assigned_by: str) -> Dict:
        try:
            result = db.execute(
                table="leads",
                operation="update",
                id=lead_id,
                data={
                    "assigned_to": assign_to,
                    "assigned_by": assigned_by,
                    "assigned_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat()
                }
            )
            return {"success": True, "message": "تم التعيين بنجاح"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_team_leads(self, team_members: List[str]) -> List[Dict]:
        try:
            result = db.client.table("leads").select("*").in_("created_by", team_members).order("created_at", desc=True).limit(200).execute()
            return result.data
            
        except Exception as e:
            print(f"خطأ في جلب عملاء الفريق: {e}")
            return []

crm = CRM()
