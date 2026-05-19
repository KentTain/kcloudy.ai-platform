import pytest


@pytest.mark.asyncio
async def test_orjson_performance():
    """
    测试orjson的性能
    """
    import json
    import time

    import orjson

    data = {
        "name": "John",
        "age": 30,
        "is_student": True,
        "scores": [85, 90, 95],
        "address": {
            "city": "Beijing",
            "street": "123 Main St",
        },
        "phone": "+86 1234567890",
        "email": "john@example.com",
        "birthday": "1990-01-01",
        "gender": "male",
        "is_employee": False,
        "salary": 100000,
        "department": "IT",
        "hobbies": ["reading", "traveling", "coding"],
    }

    def benchmark(name, dumps, loads):
        start = time.time()
        for i in range(10000000):
            result = dumps(data)
            if isinstance(result, bytes):
                result = result.decode("utf-8")
            loads(result)
        time_cost = time.time() - start

        return time_cost

    python_time = benchmark("Python", json.dumps, json.loads)
    orjson_time = benchmark(
        "orjson", lambda s: orjson.dumps(s).decode("utf-8"), orjson.loads
    )
    print(f"\nPython: {python_time} seconds")
    print(f"orjson: {orjson_time} seconds")

    assert python_time > orjson_time
