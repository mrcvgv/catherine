#!/usr/bin/env python3
"""
Production Configuration - Catherine AI 本番環境設定
Railway、Cloud Functions、Firestore の統合設定管理
"""

import os
import json
from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import pytz

JST = pytz.timezone('Asia/Tokyo')

@dataclass
class ProductionConfig:
    """本番環境設定"""
    
    # Discord設定（必須）
    discord_token: str
    auto_response_channels: list
    
    # OpenAI設定（必須）
    openai_api_key: str
    
    # Firebase設定（必須）
    firebase_credentials: str
    firestore_project_id: str
    
    # Cloud Functions設定（必須）
    functions_base_url: str
    gcp_project: str
    
    # オプション設定（デフォルト値あり）
    command_prefix: str = 'C!'
    model_name: str = 'gpt-4'
    temperature: float = 0.1
    max_tokens: int = 500
    gcp_region: str = 'asia-northeast1'
    
    # Cloud Tasks設定
    task_queue_name: str = 'reminder-queue'
    service_account_email: str = ''
    
    # Railway設定
    port: int = 8080
    environment: str = 'production'
    log_level: str = 'INFO'
    
    # システム設定
    timezone: str = 'Asia/Tokyo'
    default_mention: str = '@everyone'
    confidence_threshold: float = 0.7
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式で出力"""
        result = {}
        for key, value in self.__dict__.items():
            if isinstance(value, list):
                result[key] = ','.join(value) if value else ''
            else:
                result[key] = value
        return result

class ConfigManager:
    """設定管理クラス"""
    
    def __init__(self):
        self.config: Optional[ProductionConfig] = None
        self._load_config()
    
    def _load_config(self):
        """環境変数から設定読み込み"""
        try:
            # 必須設定チェック
            required_vars = [
                'DISCORD_BOT_TOKEN',
                'OPENAI_API_KEY', 
                'FIREBASE_SERVICE_ACCOUNT_KEY',
                'CLOUD_FUNCTIONS_URL',
                'GCP_PROJECT'
            ]
            
            missing_vars = []
            for var in required_vars:
                if not os.getenv(var):
                    missing_vars.append(var)
            
            if missing_vars:
                print(f"WARNING: Missing environment variables: {missing_vars}")
                self.config = None
                return
            
            # 設定オブジェクト作成
            self.config = ProductionConfig(
                # Discord
                discord_token=os.getenv('DISCORD_BOT_TOKEN'),
                auto_response_channels=self._parse_list(os.getenv('AUTO_RESPONSE_CHANNELS', 'todo,catherine')),
                command_prefix=os.getenv('COMMAND_PREFIX', 'C!'),
                
                # OpenAI
                openai_api_key=os.getenv('OPENAI_API_KEY'),
                model_name=os.getenv('OPENAI_MODEL', 'gpt-4'),
                temperature=float(os.getenv('OPENAI_TEMPERATURE', '0.1')),
                max_tokens=int(os.getenv('OPENAI_MAX_TOKENS', '500')),
                
                # Firebase
                firebase_credentials=os.getenv('FIREBASE_SERVICE_ACCOUNT_KEY'),
                firestore_project_id=os.getenv('GCP_PROJECT'),
                
                # Cloud Functions
                functions_base_url=os.getenv('CLOUD_FUNCTIONS_URL'),
                gcp_project=os.getenv('GCP_PROJECT'),
                gcp_region=os.getenv('GCP_REGION', 'asia-northeast1'),
                
                # Cloud Tasks
                task_queue_name=os.getenv('TASK_QUEUE_NAME', 'reminder-queue'),
                service_account_email=os.getenv('SERVICE_ACCOUNT_EMAIL', ''),
                
                # Railway
                port=int(os.getenv('PORT', '8080')),
                environment=os.getenv('ENVIRONMENT', 'production'),
                log_level=os.getenv('LOG_LEVEL', 'INFO'),
                
                # システム
                timezone=os.getenv('TIMEZONE', 'Asia/Tokyo'),
                default_mention=os.getenv('DEFAULT_MENTION', '@everyone'),
                confidence_threshold=float(os.getenv('CONFIDENCE_THRESHOLD', '0.7'))
            )
            
            print(f"Configuration loaded successfully for {self.config.environment} environment")
            
        except Exception as e:
            print(f"Configuration loading failed: {e}")
            self.config = None
    
    def _parse_list(self, value: str) -> list:
        """文字列をリストに変換"""
        if not value:
            return []
        return [item.strip() for item in value.split(',')]
    
    def get_config(self) -> Optional[ProductionConfig]:
        """設定取得"""
        return self.config
    
    def is_valid(self) -> bool:
        """設定が有効かチェック"""
        return self.config is not None
    
    def get_firebase_config(self) -> Dict[str, Any]:
        """Firebase設定取得"""
        if not self.config:
            return {}
        
        try:
            return {
                'credentials': json.loads(self.config.firebase_credentials),
                'project_id': self.config.firestore_project_id
            }
        except json.JSONDecodeError:
            print("WARNING: Invalid Firebase credentials format")
            return {}
    
    def get_discord_config(self) -> Dict[str, Any]:
        """Discord設定取得"""
        if not self.config:
            return {}
        
        return {
            'token': self.config.discord_token,
            'command_prefix': self.config.command_prefix,
            'auto_response_channels': self.config.auto_response_channels
        }
    
    def get_openai_config(self) -> Dict[str, Any]:
        """OpenAI設定取得"""
        if not self.config:
            return {}
        
        return {
            'api_key': self.config.openai_api_key,
            'model': self.config.model_name,
            'temperature': self.config.temperature,
            'max_tokens': self.config.max_tokens
        }
    
    def get_cloud_config(self) -> Dict[str, Any]:
        """Cloud設定取得"""
        if not self.config:
            return {}
        
        return {
            'functions_url': self.config.functions_base_url,
            'project': self.config.gcp_project,
            'region': self.config.gcp_region,
            'queue_name': self.config.task_queue_name,
            'service_account': self.config.service_account_email
        }
    
    def validate_configuration(self) -> Dict[str, Any]:
        """設定検証"""
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'recommendations': []
        }
        
        if not self.config:
            validation_result['valid'] = False
            validation_result['errors'].append('Configuration not loaded')
            return validation_result
        
        # Discord Token チェック
        if not self.config.discord_token.startswith('MTA') and not self.config.discord_token.startswith('ODc'):
            validation_result['warnings'].append('Discord token format may be incorrect')
        
        # OpenAI API Key チェック
        if not self.config.openai_api_key.startswith('sk-'):
            validation_result['warnings'].append('OpenAI API key format may be incorrect')
        
        # Firebase認証情報チェック
        try:
            firebase_creds = json.loads(self.config.firebase_credentials)
            if 'type' not in firebase_creds or firebase_creds['type'] != 'service_account':
                validation_result['warnings'].append('Firebase credentials may not be service account')
        except:
            validation_result['errors'].append('Invalid Firebase credentials JSON')
            validation_result['valid'] = False
        
        # Cloud Functions URL チェック
        if not self.config.functions_base_url.startswith('https://'):
            validation_result['warnings'].append('Cloud Functions URL should use HTTPS')
        
        # 推奨設定
        if self.config.confidence_threshold < 0.6:
            validation_result['recommendations'].append('Consider increasing confidence threshold to 0.7+')
        
        if self.config.log_level == 'DEBUG' and self.config.environment == 'production':
            validation_result['recommendations'].append('Use INFO log level in production')
        
        return validation_result
    
    def generate_health_check(self) -> Dict[str, Any]:
        """ヘルスチェック情報生成"""
        health = {
            'timestamp': datetime.now(JST).isoformat(),
            'status': 'healthy',
            'config_loaded': self.is_valid(),
            'services': {}
        }
        
        if not self.config:
            health['status'] = 'unhealthy'
            health['services']['config'] = {'status': 'fail', 'message': 'Configuration not loaded'}
            return health
        
        # 各サービスの設定チェック
        services_to_check = {
            'discord': bool(self.config.discord_token),
            'openai': bool(self.config.openai_api_key),
            'firebase': bool(self.config.firebase_credentials),
            'cloud_functions': bool(self.config.functions_base_url),
            'gcp': bool(self.config.gcp_project)
        }
        
        for service, configured in services_to_check.items():
            health['services'][service] = {
                'status': 'pass' if configured else 'fail',
                'configured': configured
            }
        
        # 全体ステータス決定
        failed_services = [s for s, info in health['services'].items() if info['status'] == 'fail']
        if failed_services:
            health['status'] = 'degraded' if len(failed_services) < len(services_to_check) else 'unhealthy'
            health['failed_services'] = failed_services
        
        return health

# グローバル設定マネージャー
config_manager = ConfigManager()

# 便利関数
def get_config() -> Optional[ProductionConfig]:
    """設定取得（グローバル関数）"""
    return config_manager.get_config()

def is_production() -> bool:
    """本番環境判定"""
    config = get_config()
    return config and config.environment == 'production'

def get_timezone():
    """タイムゾーン取得"""
    config = get_config()
    if config:
        return pytz.timezone(config.timezone)
    return JST

# 使用例・テスト
if __name__ == "__main__":
    def main():
        print("Catherine AI Production Configuration")
        print("=" * 50)
        
        # 設定チェック
        if config_manager.is_valid():
            config = config_manager.get_config()
            print(f"Environment: {config.environment}")
            print(f"Port: {config.port}")
            print(f"Log Level: {config.log_level}")
            
            # 検証実行
            validation = config_manager.validate_configuration()
            print(f"\nValidation: {'PASS' if validation['valid'] else 'FAIL'}")
            
            if validation['errors']:
                print(f"Errors: {validation['errors']}")
            if validation['warnings']:
                print(f"Warnings: {validation['warnings']}")
            if validation['recommendations']:
                print(f"Recommendations: {validation['recommendations']}")
            
            # ヘルスチェック
            health = config_manager.generate_health_check()
            print(f"\nHealth: {health['status'].upper()}")
            for service, info in health['services'].items():
                print(f"  {service}: {info['status']}")
                
        else:
            print("Configuration not loaded - check environment variables")
            print("\nRequired variables:")
            required = [
                'DISCORD_BOT_TOKEN',
                'OPENAI_API_KEY',
                'FIREBASE_SERVICE_ACCOUNT_KEY', 
                'CLOUD_FUNCTIONS_URL',
                'GCP_PROJECT'
            ]
            for var in required:
                status = "SET" if os.getenv(var) else "MISSING"
                print(f"  {var}: {status}")
    
    main()