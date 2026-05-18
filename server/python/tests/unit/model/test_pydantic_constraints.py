"""Pydantic Constraint Tests"""

import pytest
from pydantic import BaseModel, Field, ValidationError, constr, conint


class TestPydanticConstraints:
    """Pydantic constraint validation tests"""

    def test_string_min_length_constraint(self):
        """Test string below min_length raises error"""
        class User(BaseModel):
            name: str = Field(min_length=1)

        with pytest.raises(ValidationError):
            User(name="")

    def test_string_max_length_constraint(self):
        """Test string above max_length raises error"""
        class User(BaseModel):
            name: str = Field(max_length=10)

        with pytest.raises(ValidationError):
            User(name="a" * 11)

    def test_string_length_in_range(self):
        """Test string within length constraints"""
        class User(BaseModel):
            name: str = Field(min_length=1, max_length=10)

        user = User(name="John")

        assert user.name == "John"

    def test_numeric_min_value_constraint(self):
        """Test number below minimum raises error"""
        class User(BaseModel):
            age: int = Field(ge=0)

        with pytest.raises(ValidationError):
            User(age=-1)

    def test_numeric_max_value_constraint(self):
        """Test number above maximum raises error"""
        class User(BaseModel):
            age: int = Field(le=150)

        with pytest.raises(ValidationError):
            User(age=151)

    def test_numeric_range_constraint(self):
        """Test number within range passes"""
        class User(BaseModel):
            age: int = Field(ge=0, le=150)

        user = User(age=30)

        assert user.age == 30

    def test_float_precision_constraint(self):
        """Test float with precision constraints"""
        class Price(BaseModel):
            value: float = Field(gt=0, le=1000000)

        price = Price(value=99.99)

        assert price.value == 99.99

    def test_email_format_constraint(self):
        """Test email format validation"""
        from pydantic import EmailStr

        class User(BaseModel):
            email: EmailStr

        user = User(email="test@example.com")

        assert user.email == "test@example.com"

    def test_email_invalid_format(self):
        """Test invalid email format raises error"""
        from pydantic import EmailStr

        class User(BaseModel):
            email: EmailStr

        with pytest.raises(ValidationError):
            User(email="not_an_email")

    def test_url_format_constraint(self):
        """Test URL format validation"""
        from pydantic import HttpUrl

        class Link(BaseModel):
            url: HttpUrl

        link = Link(url="https://example.com")

        assert str(link.url) == "https://example.com"

    def test_constrained_string(self):
        """Test using constr for string constraints"""
        class Username(constr(min_length=3, max_length=20)):
            pass

        username = Username("john_doe")

        assert username == "john_doe"

    def test_constrained_integer(self):
        """Test using conint for integer constraints"""
        class Age(conint(ge=0, le=150)):
            pass

        age = Age(25)

        assert age == 25

    def test_regex_pattern_constraint(self):
        """Test regex pattern validation"""
        class Code(BaseModel):
            code: str = Field(pattern=r"^[A-Z]{3}-\d{3}$")

        code = Code(code="ABC-123")

        assert code.code == "ABC-123"

    def test_regex_pattern_mismatch(self):
        """Test regex pattern mismatch raises error"""
        class Code(BaseModel):
            code: str = Field(pattern=r"^[A-Z]{3}-\d{3}$")

        with pytest.raises(ValidationError):
            Code(code="invalid")
