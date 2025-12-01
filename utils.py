import re
import csv
import json
from datetime import datetime
from typing import List, Dict, Any

class Utils:
    @staticmethod
    def extract_phones(text: str) -> List[str]:
        patterns = [r'(01[0125][0-9]{8})', r'(\+20|0020)?1[0125][0-9]{8}']
        phones = []
        for pattern in patterns:
            matches = re.findall(pattern, text)
            phones.extend(matches)
        
        cleaned = []
        for phone in phones:
            clean = re.sub(r'\D', '', phone)
            if len(clean) == 11 and clean.startswith(('010', '011', '012', '015')):
                cleaned.append(clean)
        return list(set(cleaned))
    
    @staticmethod
    def analyze_text(text: str) -> Dict[str, Any]:
        text_lower = text.lower()
        
        analysis = {
            "has_phone": len(Utils.extract_phones(text)) > 0,
            "is_buyer": any(word in text_lower for word in ["مطلوب", "شراء", "أبحث"]),
            "is_seller": any(word in text_lower for word in ["للبيع", "عرض", "سمسار"]),
            "word_count": len(text.split()),
            "contains_email": "@" in text,
            "quality_score": 0
        }
        
        if analysis["is_buyer"]:
            analysis["quality_score"] += 3
        if analysis["has_phone"]:
            analysis["quality_score"] += 2
        if not analysis["is_seller"]:
            analysis["quality_score"] += 1
        
        return analysis
    
    @staticmethod
    def import_csv(file_path: str) -> List[Dict]:
        data = []
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                data.append(row)
        return data
    
    @staticmethod
    def export_csv(data: List[Dict], file_path: str):
        if not data:
            return
        
        fieldnames = data[0].keys()
        with open(file_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
    
    @staticmethod
    def format_date(date_str: str, format_from: str = "%Y-%m-%d", format_to: str = "%d/%m/%Y"):
        try:
            date = datetime.strptime(date_str, format_from)
            return date.strftime(format_to)
        except:
            return date_str
    
    @staticmethod
    def validate_phone(phone: str) -> bool:
        if not phone:
            return False
        clean = re.sub(r'\D', '', phone)
        if len(clean) != 11:
            return False
        return clean.startswith(('010', '011', '012', '015'))
    
    @staticmethod
    def generate_id(prefix: str = "lead") -> str:
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        random_part = str(hash(timestamp))[-4:]
        return f"{prefix}_{timestamp}_{random_part}"

utils = Utils()
