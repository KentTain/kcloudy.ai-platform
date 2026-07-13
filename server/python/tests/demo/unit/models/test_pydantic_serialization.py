"""Pydantic Serialization Tests"""

from datetime import date, datetime

from pydantic import BaseModel


class TestPydanticSerialization:
    """Pydantic model serialization tests"""

    def test_export_to_dict(self):
        """Test model.model_dump() returns dictionary"""
        class User(BaseModel):
            name: str
            age: int

        user = User(name="John", age=30)
        result = user.model_dump()

        assert result == {"name": "John", "age": 30}

    def test_export_to_json(self):
        """Test model.model_dump_json() returns JSON string"""
        class User(BaseModel):
            name: str
            age: int

        user = User(name="John", age=30)
        result = user.model_dump_json()

        assert '"name":' in result
        assert '"John"' in result

    def test_dict_includes_nested_models(self):
        """Test dict includes nested model data"""
        class Address(BaseModel):
            city: str

        class User(BaseModel):
            name: str
            address: Address

        user = User(name="John", address={"city": "Beijing"})
        result = user.model_dump()

        assert result["address"]["city"] == "Beijing"

    def test_json_includes_nested_models(self):
        """Test JSON includes nested model data"""
        class Address(BaseModel):
            city: str

        class User(BaseModel):
            name: str
            address: Address

        user = User(name="John", address={"city": "Beijing"})
        result = user.model_dump_json()

        assert "city" in result

    def test_dump_exclude_none(self):
        """Test excluding None values from dump"""
        class User(BaseModel):
            name: str
            description: str | None = None

        user = User(name="John")
        result = user.model_dump(exclude_none=True)

        assert "description" not in result

    def test_dump_only_fields(self):
        """Test dumping only specified fields"""
        class User(BaseModel):
            name: str
            age: int
            email: str

        user = User(name="John", age=30, email="john@example.com")
        result = user.model_dump(include=["name", "age"])

        assert "name" in result
        assert "age" in result
        assert "email" not in result

    def test_dump_exclude_fields(self):
        """Test excluding specified fields from dump"""
        class User(BaseModel):
            name: str
            age: int
            password: str

        user = User(name="John", age=30, password="secret")
        result = user.model_dump(exclude=["password"])

        assert "name" in result
        assert "password" not in result

    def test_serialize_datetime(self):
        """Test datetime field serialization"""
        class Event(BaseModel):
            name: str
            timestamp: datetime

        event = Event(name="test", timestamp=datetime(2024, 1, 15, 10, 30, 45))
        result = event.model_dump()

        assert "timestamp" in result

    def test_serialize_date(self):
        """Test date field serialization"""
        class Event(BaseModel):
            name: str
            event_date: date

        event = Event(name="test", event_date=date(2024, 1, 15))
        result = event.model_dump()

        assert "event_date" in result

    def test_json_schema_generation(self):
        """Test JSON schema generation"""
        class User(BaseModel):
            name: str
            age: int

        schema = User.model_json_schema()

        assert "properties" in schema
        assert "name" in schema["properties"]
