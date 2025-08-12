#!/usr/bin/env python3
"""
Railway Deployment Configuration for Catherine AI
本番環境用の設定とヘルスチェック機能
"""

import os
import json
import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import pytz

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

JST = pytz.timezone('Asia/Tokyo')

class RailwayDeploymentManager:
    """Railway デプロイメント管理"""
    
    def __init__(self):
        self.required_env_vars = [
            'DISCORD_BOT_TOKEN',
            'OPENAI_API_KEY',
            'FIREBASE_SERVICE_ACCOUNT_KEY',
            'CLOUD_FUNCTIONS_URL',
            'GCP_PROJECT',
            'GCP_REGION'
        ]
        self.optional_env_vars = {
            'PORT': '8080',
            'AUTO_RESPONSE_CHANNELS': 'todo,catherine,タスク,やること',
            'LOG_LEVEL': 'INFO',
            'TASK_QUEUE_NAME': 'reminder-queue',
            'SERVICE_ACCOUNT_EMAIL': ''
        }
    
    def check_environment(self) -> Dict[str, Any]:
        """環境変数チェック"""
        status = {
            'success': True,
            'missing_required': [],
            'missing_optional': [],
            'configured': {},
            'recommendations': []
        }
        
        # 必須環境変数チェック
        for var in self.required_env_vars:
            value = os.getenv(var)
            if not value:
                status['missing_required'].append(var)
                status['success'] = False
            else:
                # セキュリティのため一部のみ表示
                if 'KEY' in var or 'TOKEN' in var:
                    masked = value[:8] + '...' + value[-4:] if len(value) > 12 else '***'
                    status['configured'][var] = masked
                else:
                    status['configured'][var] = value
        
        # オプション環境変数チェック
        for var, default in self.optional_env_vars.items():
            value = os.getenv(var, default)
            if not value or value == default:
                status['missing_optional'].append(var)
            status['configured'][var] = value
        
        # 推奨設定
        if 'FIREBASE_SERVICE_ACCOUNT_KEY' in status['missing_required']:
            status['recommendations'].append(
                "Firebase サービスアカウントキーを環境変数に設定してください"
            )
        
        if 'CLOUD_FUNCTIONS_URL' in status['missing_required']:
            status['recommendations'].append(
                "Cloud Functions URL を設定してください (例: https://asia-northeast1-project.cloudfunctions.net)"
            )
        
        return status
    
    def generate_env_template(self) -> str:
        """環境変数テンプレート生成"""
        template = "# Catherine AI Environment Variables\n\n"
        template += "# Required Variables\n"
        
        for var in self.required_env_vars:
            if var == 'DISCORD_BOT_TOKEN':
                template += f"{var}=YOUR_DISCORD_BOT_TOKEN_HERE\n"
            elif var == 'OPENAI_API_KEY':
                template += f"{var}=sk-YOUR_OPENAI_API_KEY_HERE\n"
            elif var == 'FIREBASE_SERVICE_ACCOUNT_KEY':
                template += f'{var}={{"type":"service_account","project_id":"YOUR_PROJECT"}}\n'
            elif var == 'CLOUD_FUNCTIONS_URL':
                template += f"{var}=https://asia-northeast1-YOUR_PROJECT.cloudfunctions.net\n"
            elif var == 'GCP_PROJECT':
                template += f"{var}=YOUR_GCP_PROJECT_ID\n"
            elif var == 'GCP_REGION':
                template += f"{var}=asia-northeast1\n"
            else:
                template += f"{var}=\n"
        
        template += "\n# Optional Variables\n"
        for var, default in self.optional_env_vars.items():
            template += f"{var}={default}\n"
        
        return template
    
    async def health_check(self) -> Dict[str, Any]:
        """ヘルスチェック"""
        health_status = {
            'timestamp': datetime.now(JST).isoformat(),
            'status': 'healthy',
            'checks': {}
        }
        
        # 環境変数チェック
        env_check = self.check_environment()
        health_status['checks']['environment'] = {
            'status': 'pass' if env_check['success'] else 'fail',
            'details': env_check
        }
        
        # Firebase接続チェック
        try:
            from firebase_config import firebase_manager
            db_available = firebase_manager.is_available()
            health_status['checks']['firebase'] = {
                'status': 'pass' if db_available else 'fail',
                'details': {'connected': db_available}
            }
        except Exception as e:
            health_status['checks']['firebase'] = {
                'status': 'fail',
                'details': {'error': str(e)}
            }
        
        # OpenAI API チェック
        try:
            from openai import OpenAI
            client = OpenAI(api_key=os.getenv('OPENAI_API_KEY', 'sk-test'))
            # 実際のAPI呼び出しは避け、インスタンス作成のみ
            health_status['checks']['openai'] = {
                'status': 'pass',
                'details': {'api_key_configured': bool(os.getenv('OPENAI_API_KEY'))}
            }
        except Exception as e:
            health_status['checks']['openai'] = {
                'status': 'fail', 
                'details': {'error': str(e)}
            }
        
        # 全体ステータス決定
        failed_checks = [check for check in health_status['checks'].values() 
                        if check['status'] == 'fail']
        if failed_checks:
            health_status['status'] = 'unhealthy'
        
        return health_status
    
    def create_procfile(self) -> str:
        """Procfile生成"""
        return "web: python enhanced_main_v2.py"
    
    def create_railway_toml(self) -> str:
        """railway.toml生成"""
        return """[build]
builder = "NIXPACKS"

[deploy]
healthcheckPath = "/health"
healthcheckTimeout = 300
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 3

[[deploy.environmentVariables]]
name = "PORT"
value = "8080"

[[deploy.environmentVariables]]
name = "PYTHONUNBUFFERED"
value = "1"
"""

    def create_dockerfile(self) -> str:
        """Dockerfile生成"""
        return """FROM python:3.11-slim

WORKDIR /app

# システム依存関係
RUN apt-get update && apt-get install -y \\
    build-essential \\
    git \\
    && rm -rf /var/lib/apt/lists/*

# Python依存関係
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションコード
COPY . .

# ポート設定
EXPOSE 8080

# ヘルスチェック
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD python -c "import requests; requests.get('http://localhost:8080/health')"

# 実行
CMD ["python", "enhanced_main_v2.py"]
"""

# デプロイ用スクリプト生成
def generate_deployment_files():
    """デプロイ用ファイル一括生成"""
    manager = RailwayDeploymentManager()
    
    files = {
        'Procfile': manager.create_procfile(),
        'railway.toml': manager.create_railway_toml(),
        'Dockerfile': manager.create_dockerfile(),
        '.env.example': manager.generate_env_template()
    }
    
    for filename, content in files.items():
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Generated: {filename}")
    
    return files

if __name__ == "__main__":
    async def main():
        manager = RailwayDeploymentManager()
        
        print("Catherine AI Railway Deployment Manager")
        print("=" * 50)
        
        # 環境チェック
        env_status = manager.check_environment()
        print(f"\nEnvironment Check: {'[PASS]' if env_status['success'] else '[FAIL]'}")
        
        if env_status['missing_required']:
            print(f"Missing required: {env_status['missing_required']}")
        
        if env_status['recommendations']:
            print("\nRecommendations:")
            for rec in env_status['recommendations']:
                print(f"  - {rec}")
        
        # ヘルスチェック
        print("\nRunning health check...")
        health = await manager.health_check()
        print(f"Health Status: {health['status'].upper()}")
        
        for check_name, check_result in health['checks'].items():
            status_icon = "[PASS]" if check_result['status'] == 'pass' else "[FAIL]"
            print(f"  {status_icon} {check_name}: {check_result['status']}")
        
        # デプロイファイル生成
        print("\nGenerating deployment files...")
        generate_deployment_files()
        
        print("\nDeployment preparation complete!")
        print("\nNext steps:")
        print("1. Set environment variables in Railway dashboard")
        print("2. Deploy using: railway up")
        print("3. Monitor logs: railway logs")
    
    asyncio.run(main())