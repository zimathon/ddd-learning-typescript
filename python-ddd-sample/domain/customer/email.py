"""
Email Value Object
メールアドレスを表現する値オブジェクト
"""
import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Email:
    """不変のメールアドレス値オブジェクト"""
    
    value: str
    
    def __post_init__(self):
        """生成時のバリデーション"""
        if not self._is_valid(self.value):
            raise ValueError(f'無効なメールアドレス形式: {self.value}')
        
        # 小文字に正規化
        object.__setattr__(self, 'value', self.value.lower())
    
    def _is_valid(self, email: str) -> bool:
        """メールアドレスの形式をチェック"""
        email_regex = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
        return re.match(email_regex, email) is not None
    
    @property
    def domain(self) -> str:
        """ドメイン部分を取得"""
        return self.value.split('@')[1]
    
    @property
    def local_part(self) -> str:
        """ローカル部分を取得"""
        return self.value.split('@')[0]
    
    def __str__(self) -> str:
        return self.value