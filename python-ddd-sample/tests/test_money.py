"""
Money Value Objectのテスト
"""
import pytest
from domain.shared.money import Money


class TestMoney:
    """Money値オブジェクトのテスト"""
    
    def test_create_money(self):
        """正常な金額の生成"""
        money = Money(1000, 'JPY')
        assert money.amount == 1000
        assert money.currency == 'JPY'
    
    def test_negative_amount_raises_error(self):
        """負の金額はエラー"""
        with pytest.raises(ValueError, match='金額は0以上'):
            Money(-100, 'JPY')
    
    def test_invalid_currency_raises_error(self):
        """不正な通貨コードはエラー"""
        with pytest.raises(ValueError, match='通貨コードは3文字'):
            Money(1000, 'JP')
    
    def test_zero_money(self):
        """ゼロ金額の生成"""
        zero = Money.zero('JPY')
        assert zero.amount == 0
        assert zero.is_zero()
    
    def test_add_money(self):
        """金額の加算"""
        money1 = Money(1000, 'JPY')
        money2 = Money(500, 'JPY')
        result = money1.add(money2)
        
        assert result.amount == 1500
        # 元のオブジェクトは変更されない（不変性）
        assert money1.amount == 1000
        assert money2.amount == 500
    
    def test_subtract_money(self):
        """金額の減算"""
        money1 = Money(1000, 'JPY')
        money2 = Money(300, 'JPY')
        result = money1.subtract(money2)
        
        assert result.amount == 700
    
    def test_subtract_to_negative_raises_error(self):
        """減算で負になる場合はエラー"""
        money1 = Money(100, 'JPY')
        money2 = Money(200, 'JPY')
        
        with pytest.raises(ValueError, match='負の値'):
            money1.subtract(money2)
    
    def test_multiply_money(self):
        """金額の乗算"""
        money = Money(100, 'JPY')
        result = money.multiply(3)
        
        assert result.amount == 300
        # 元のオブジェクトは変更されない
        assert money.amount == 100
    
    def test_different_currency_operations_raise_error(self):
        """異なる通貨の演算はエラー"""
        jpy = Money(1000, 'JPY')
        usd = Money(10, 'USD')
        
        with pytest.raises(ValueError, match='異なる通貨'):
            jpy.add(usd)
    
    def test_equality(self):
        """等価性のテスト"""
        money1 = Money(1000, 'JPY')
        money2 = Money(1000, 'JPY')
        money3 = Money(2000, 'JPY')
        
        assert money1 == money2
        assert money1 != money3
    
    def test_format(self):
        """フォーマット出力"""
        jpy = Money(1000, 'JPY')
        assert jpy.format() == '¥1,000'
        
        usd = Money(1000, 'USD')
        assert usd.format() == 'USD 1,000'