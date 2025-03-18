import json
import os
from datetime import datetime
from jinja2 import Environment, FileSystemLoader
from app.database.models import Following, FollowHistory, db

class ReportGenerator:
    def __init__(self, app):
        self.app = app
        template_dir = os.path.join(os.path.dirname(__file__), 'templates')
        self.env = Environment(loader=FileSystemLoader(template_dir))
        
    def generate_report(self, output_path='reports/report.html'):
        with self.app.app_context():
            # 獲取所有追蹤資料
            following_data = Following.query.all()
            history_data = FollowHistory.query.order_by(FollowHistory.event_date.desc()).all()
            
            # 準備報告數據
            report_data = {
                'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'total_following': len(following_data),
                'active_following': len([f for f in following_data if f.current_status]),
                'mutual_following': len([f for f in following_data if f.follows_me]),
                'following_list': [
                    {
                        'username': f.username,
                        'follows_me': f.follows_me,
                        'first_seen': f.first_seen.strftime('%Y-%m-%d'),
                        'last_seen': f.last_seen.strftime('%Y-%m-%d'),
                        'current_status': f.current_status
                    } for f in following_data
                ],
                'recent_events': [
                    {
                        'username': h.username,
                        'event_type': h.event_type,
                        'event_date': h.event_date.strftime('%Y-%m-%d %H:%M:%S')
                    } for h in history_data[:50]  # 最近50筆事件
                ]
            }
            
            # 確保輸出目錄存在
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # 渲染模板
            template = self.env.get_template('report.html')
            html_content = template.render(
                report=report_data,
                report_json=json.dumps(report_data, ensure_ascii=False, indent=2)
            )
            
            # 寫入檔案
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            return output_path
