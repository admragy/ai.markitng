"""CRM Database Service - قاعدة بيانات SQLite ذكية"""
import sqlite3
import json
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

class CRMDatabase:
    def __init__(self, db_path: str = "brilliox_crm.db"):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # جدول العملاء
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT,
                phone TEXT NOT NULL,
                company TEXT,
                status TEXT DEFAULT 'new',
                source TEXT DEFAULT 'other',
                quality TEXT,
                score REAL DEFAULT 0.0,
                notes TEXT,
                tags TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_contact_at TIMESTAMP
            )
        ''')
        
        # جدول التفاعلات
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lead_id INTEGER NOT NULL,
                type TEXT NOT NULL,
                direction TEXT DEFAULT 'outbound',
                description TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (lead_id) REFERENCES leads(id)
            )
        ''')
        
        # جدول المهام
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                type TEXT NOT NULL,
                description TEXT,
                priority TEXT DEFAULT 'medium',
                status TEXT DEFAULT 'pending',
                lead_id INTEGER,
                due_date TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (lead_id) REFERENCES leads(id)
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info(f"✅ Database initialized: {self.db_path}")
    
    def create_lead(self, lead_data: Dict) -> int:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        if 'tags' in lead_data and isinstance(lead_data['tags'], list):
            lead_data['tags'] = json.dumps(lead_data['tags'])
        columns = ', '.join(lead_data.keys())
        placeholders = ', '.join(['?' for _ in lead_data])
        query = f"INSERT INTO leads ({columns}) VALUES ({placeholders})"
        cursor.execute(query, list(lead_data.values()))
        lead_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return lead_id
    
    def get_lead(self, lead_id: int) -> Optional[Dict]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM leads WHERE id = ?", (lead_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            lead = dict(row)
            if lead.get('tags'):
                try:
                    lead['tags'] = json.loads(lead['tags'])
                except:
                    lead['tags'] = []
            return lead
        return None
    
    def update_lead(self, lead_id: int, updates: Dict) -> bool:
        updates['updated_at'] = datetime.now().isoformat()
        if 'tags' in updates and isinstance(updates['tags'], list):
            updates['tags'] = json.dumps(updates['tags'])
        set_clause = ', '.join([f"{k} = ?" for k in updates.keys()])
        values = list(updates.values()) + [lead_id]
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        query = f"UPDATE leads SET {set_clause} WHERE id = ?"
        cursor.execute(query, values)
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return success
    
    def search_leads(self, filters: Dict = None, limit: int = 50, offset: int = 0) -> List[Dict]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        query = "SELECT * FROM leads WHERE 1=1"
        params = []
        if filters:
            if filters.get('status'):
                query += f" AND status IN ({','.join(['?' for _ in filters['status']])})"
                params.extend(filters['status'])
            if filters.get('source'):
                query += f" AND source IN ({','.join(['?' for _ in filters['source']])})"
                params.extend(filters['source'])
            if filters.get('search'):
                search = f"%{filters['search']}%"
                query += " AND (name LIKE ? OR email LIKE ? OR phone LIKE ?)"
                params.extend([search, search, search])
        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    def get_lead_interactions(self, lead_id: int) -> List[Dict]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM interactions WHERE lead_id = ? ORDER BY created_at DESC", (lead_id,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    def create_interaction(self, interaction_data: Dict) -> int:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        columns = ', '.join(interaction_data.keys())
        placeholders = ', '.join(['?' for _ in interaction_data])
        query = f"INSERT INTO interactions ({columns}) VALUES ({placeholders})"
        cursor.execute(query, list(interaction_data.values()))
        interaction_id = cursor.lastrowid
        cursor.execute("UPDATE leads SET last_contact_at = ? WHERE id = ?", 
                      (datetime.now().isoformat(), interaction_data['lead_id']))
        conn.commit()
        conn.close()
        return interaction_id
    
    def create_task(self, task_data: Dict) -> int:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        columns = ', '.join(task_data.keys())
        placeholders = ', '.join(['?' for _ in task_data])
        query = f"INSERT INTO tasks ({columns}) VALUES ({placeholders})"
        cursor.execute(query, list(task_data.values()))
        task_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return task_id
    
    def get_pending_tasks(self, assigned_to: Optional[int] = None) -> List[Dict]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        if assigned_to:
            cursor.execute("SELECT * FROM tasks WHERE status = 'pending' AND assigned_to = ? ORDER BY due_date ASC", (assigned_to,))
        else:
            cursor.execute("SELECT * FROM tasks WHERE status = 'pending' ORDER BY due_date ASC")
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    def get_dashboard_stats(self) -> Dict:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM leads")
        total_leads = cursor.fetchone()[0]
        today = datetime.now().date().isoformat()
        cursor.execute("SELECT COUNT(*) FROM leads WHERE DATE(created_at) = ?", (today,))
        new_leads_today = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM leads WHERE quality = 'hot'")
        hot_leads = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM leads WHERE status = 'won'")
        total_conversions = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM tasks WHERE status = 'pending'")
        pending_tasks = cursor.fetchone()[0]
        cursor.execute("SELECT source, COUNT(*) as count FROM leads GROUP BY source")
        leads_by_source = {row[0]: row[1] for row in cursor.fetchall()}
        cursor.execute("SELECT status, COUNT(*) as count FROM leads GROUP BY status")
        leads_by_status = {row[0]: row[1] for row in cursor.fetchall()}
        conn.close()
        avg_conversion_rate = (total_conversions / total_leads * 100) if total_leads > 0 else 0
        return {
            'total_leads': total_leads,
            'new_leads_today': new_leads_today,
            'hot_leads': hot_leads,
            'total_conversions': total_conversions,
            'avg_conversion_rate': round(avg_conversion_rate, 2),
            'pending_tasks': pending_tasks,
            'leads_by_source': leads_by_source,
            'leads_by_status': leads_by_status
        }

db = CRMDatabase()
