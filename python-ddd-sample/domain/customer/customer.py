"""
Customer Entity
顧客を表現するエンティティ
"""
from enum import Enum
from typing import Optional
from .customer_id import CustomerId
from .email import Email


class CustomerStatus(Enum):
    """顧客ステータス"""
    ACTIVE = 'ACTIVE'
    INACTIVE = 'INACTIVE'
    SUSPENDED = 'SUSPENDED'


class Customer:
    """顧客エンティティ"""
    
    def __init__(self, customer_id: CustomerId, name: str, email: Email):
        """
        顧客を生成
        
        Args:
            customer_id: 顧客ID
            name: 顧客名
            email: メールアドレス
        """
        self._id = customer_id
        self._name = name
        self._email = email
        self._status = CustomerStatus.ACTIVE
        self._loyalty_points = 0
    
    @classmethod
    def create(cls, customer_id: Optional[CustomerId] = None, 
               email: Optional[Email] = None, 
               name: Optional[str] = None) -> 'Customer':
        """新規顧客を作成"""
        if customer_id is None:
            customer_id = CustomerId.generate()
        if email is None:
            email = Email('default@example.com')
        if name is None:
            name = 'Default Customer'
        return cls(customer_id, name, email)
    
    def deactivate(self) -> None:
        """顧客を非アクティブ化"""
        self._status = CustomerStatus.INACTIVE
    
    def change_email(self, new_email: Email) -> None:
        """メールアドレスを変更"""
        if self._email == new_email:
            return
        
        if self._status == CustomerStatus.SUSPENDED:
            raise ValueError('停止中の顧客はメールアドレスを変更できません')
        
        self._email = new_email
    
    def change_name(self, new_name: str) -> None:
        """名前を変更"""
        if not new_name or not new_name.strip():
            raise ValueError('名前は空にできません')
        self._name = new_name
    
    def add_loyalty_points(self, points: int) -> None:
        """ロイヤリティポイントを追加"""
        if points <= 0:
            raise ValueError('ポイントは正の値である必要があります')
        
        if self._status != CustomerStatus.ACTIVE:
            raise ValueError('アクティブな顧客のみポイントを追加できます')
        
        self._loyalty_points += points
    
    def use_loyalty_points(self, points: int) -> None:
        """ロイヤリティポイントを使用"""
        if points <= 0:
            raise ValueError('使用ポイントは正の値である必要があります')
        
        if points > self._loyalty_points:
            raise ValueError('ポイントが不足しています')
        
        self._loyalty_points -= points
    
    def suspend(self) -> None:
        """顧客を停止"""
        if self._status == CustomerStatus.SUSPENDED:
            return
        self._status = CustomerStatus.SUSPENDED
    
    def activate(self) -> None:
        """顧客を有効化"""
        if self._status == CustomerStatus.ACTIVE:
            return
        self._status = CustomerStatus.ACTIVE
    
    @property
    def id(self) -> CustomerId:
        return self._id
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def email(self) -> Email:
        return self._email
    
    @property
    def status(self) -> CustomerStatus:
        return self._status
    
    @property
    def loyalty_points(self) -> int:
        return self._loyalty_points
    
    def is_active(self) -> bool:
        """アクティブかチェック"""
        return self._status == CustomerStatus.ACTIVE
    
    def __eq__(self, other: object) -> bool:
        """IDによる等価性判定"""
        if not isinstance(other, Customer):
            return False
        return self._id == other._id