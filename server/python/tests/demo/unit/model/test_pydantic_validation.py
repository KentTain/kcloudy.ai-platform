"""Pydantic Validation Tests"""

import pytest
from pydantic import BaseModel, ValidationError, Field


class TestPydanticValidation:
    """Pydantic model validation tests"""

    def test_valid_data_passes_validation(self):
        """Test valid data creates model instance"""
        class User(BaseModel):
            name: str
            age: int

        user = User(name="John", age=30)

        assert user.name == "John"
        assert user.age == 30

    def test_invalid_type_raises_error(self):
        """Test wrong type raises ValidationError"""
        class User(BaseModel):
            name: str
            age: int

        with pytest.raises(ValidationError):
            User(name="John", age="not_a_number")

    def test_missing_required_field_raises_error(self):
        """Test missing required field raises ValidationError"""
        class User(BaseModel):
            name: str
            age: int

        with pytest.raises(ValidationError):
            User(name="John")

    def test_optional_field_defaults_to_none(self):
        """Test optional field defaults to None"""
        class User(BaseModel):
            name: str
            description: str | None = None

        user = User(name="John")

        assert user.description is None

    def test_field_with_default_value(self):
        """Test field with default value"""
        class User(BaseModel):
            name: str
            active: bool = True

        user = User(name="John")

        assert user.active is True

    def test_nested_model_validation(self):
        """Test nested model validation"""
        class Address(BaseModel):
            city: str
            country: str

        class User(BaseModel):
            name: str
            address: Address

        user = User(
            name="John",
            address={"city": "Beijing", "country": "China"}
        )

        assert user.address.city == "Beijing"

    def test_list_field_validation(self):
        """Test list field validation"""
        class User(BaseModel):
            name: str
            tags: list[str]

        user = User(name="John", tags=["admin", "user"])

        assert user.tags == ["admin", "user"]

    def test_dict_field_validation(self):
        """Test dict field validation"""
        class User(BaseModel):
            name: str
            metadata: dict

        user = User(
            name="John",
            metadata={"key": "value", "count": 123}
        )

        assert user.metadata["key"] == "value"
