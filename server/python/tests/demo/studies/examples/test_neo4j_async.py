# """
# Neo4j异步驱动示例

# 演示如何使用Neo4j Python异步驱动进行CRUD操作
# """

# import asyncio

# import pytest


# # 测试前需要安装: uv add neo4j
# # 需要先启动Neo4j服务，可以使用Docker:
# # docker run -d --name neo4j \
# #   -p 7474:7474 -p 7687:7687 \
# #   -e NEO4J_AUTH=neo4j/password123 \
# #   neo4j:latest


# class TestNeo4jAsync:
#     """Neo4j异步驱动测试示例"""

#     NEO4J_URI = "bolt://localhost:7687"
#     NEO4J_USER = "neo4j"
#     NEO4J_PASSWORD = "password123"

#     @pytest.fixture
#     async def neo4j_driver(self):
#         """创建Neo4j异步驱动"""
#         from neo4j import AsyncGraphDatabase

#         driver = AsyncGraphDatabase.driver(
#             self.NEO4J_URI, auth=(self.NEO4J_USER, self.NEO4J_PASSWORD)
#         )

#         # 验证连接
#         await driver.verify_connectivity()

#         yield driver

#         # 清理测试数据
#         async with driver.session() as session:
#             await session.run("MATCH (n:TestPerson) DETACH DELETE n")

#         await driver.close()

#     async def test_create_person(self, neo4j_driver):
#         """测试创建节点"""
#         async with neo4j_driver.session() as session:
#             # 创建一个Person节点
#             result = await session.run(
#                 """
#                 CREATE (p:TestPerson {name: $name, age: $age})
#                 RETURN p.name as name, p.age as age
#                 """,
#                 name="Alice",
#                 age=30,
#             )

#             record = await result.single()
#             assert record["name"] == "Alice"
#             assert record["age"] == 30

#     async def test_read_person(self, neo4j_driver):
#         """测试读取节点"""
#         async with neo4j_driver.session() as session:
#             # 先创建节点
#             await session.run(
#                 "CREATE (p:TestPerson {name: $name, age: $age})", name="Bob", age=25
#             )

#             # 读取节点
#             result = await session.run(
#                 "MATCH (p:TestPerson {name: $name}) RETURN p.name as name, p.age as age",
#                 name="Bob",
#             )

#             record = await result.single()
#             assert record["name"] == "Bob"
#             assert record["age"] == 25

#     async def test_update_person(self, neo4j_driver):
#         """测试更新节点"""
#         async with neo4j_driver.session() as session:
#             # 创建节点
#             await session.run(
#                 "CREATE (p:TestPerson {name: $name, age: $age})", name="Charlie", age=35
#             )

#             # 更新节点
#             result = await session.run(
#                 """
#                 MATCH (p:TestPerson {name: $name})
#                 SET p.age = $new_age
#                 RETURN p.name as name, p.age as age
#                 """,
#                 name="Charlie",
#                 new_age=36,
#             )

#             record = await result.single()
#             assert record["age"] == 36

#     async def test_delete_person(self, neo4j_driver):
#         """测试删除节点"""
#         async with neo4j_driver.session() as session:
#             # 创建节点
#             await session.run(
#                 "CREATE (p:TestPerson {name: $name, age: $age})", name="David", age=40
#             )

#             # 删除节点
#             await session.run("MATCH (p:TestPerson {name: $name}) DELETE p", name="David")

#             # 验证删除
#             result = await session.run(
#                 "MATCH (p:TestPerson {name: $name}) RETURN p", name="David"
#             )
#             record = await result.single()
#             assert record is None

#     async def test_create_relationship(self, neo4j_driver):
#         """测试创建关系"""
#         async with neo4j_driver.session() as session:
#             # 创建两个节点和它们之间的关系
#             result = await session.run(
#                 """
#                 CREATE (p1:TestPerson {name: $name1, age: $age1})
#                 CREATE (p2:TestPerson {name: $name2, age: $age2})
#                 CREATE (p1)-[r:KNOWS {since: $since}]->(p2)
#                 RETURN p1.name as name1, p2.name as name2, r.since as since
#                 """,
#                 name1="Eve",
#                 age1=28,
#                 name2="Frank",
#                 age2=32,
#                 since=2020,
#             )

#             record = await result.single()
#             assert record["name1"] == "Eve"
#             assert record["name2"] == "Frank"
#             assert record["since"] == 2020

#     async def test_query_with_relationship(self, neo4j_driver):
#         """测试查询关系"""
#         async with neo4j_driver.session() as session:
#             # 创建数据
#             await session.run(
#                 """
#                 CREATE (p1:TestPerson {name: 'Grace', age: 27})
#                 CREATE (p2:TestPerson {name: 'Henry', age: 29})
#                 CREATE (p1)-[:KNOWS {since: 2019}]->(p2)
#                 """
#             )

#             # 查询关系
#             result = await session.run(
#                 """
#                 MATCH (p1:TestPerson {name: 'Grace'})-[r:KNOWS]->(p2:TestPerson)
#                 RETURN p1.name as name1, p2.name as name2, r.since as since
#                 """
#             )

#             record = await result.single()
#             assert record["name1"] == "Grace"
#             assert record["name2"] == "Henry"
#             assert record["since"] == 2019

#     async def test_transaction(self, neo4j_driver):
#         """测试事务"""
#         async with neo4j_driver.session() as session:

#             async def create_person_tx(tx, name, age):
#                 result = await tx.run(
#                     "CREATE (p:TestPerson {name: $name, age: $age}) RETURN p.name as name",
#                     name=name,
#                     age=age,
#                 )
#                 record = await result.single()
#                 return record["name"]

#             # 使用事务
#             name = await session.execute_write(create_person_tx, "Ivy", 31)
#             assert name == "Ivy"

#             # 验证数据
#             result = await session.run(
#                 "MATCH (p:TestPerson {name: 'Ivy'}) RETURN p.age as age"
#             )
#             record = await result.single()
#             assert record["age"] == 31

#     async def test_batch_operations(self, neo4j_driver):
#         """测试批量操作"""
#         async with neo4j_driver.session() as session:
#             # 批量创建节点
#             persons = [
#                 {"name": "Jack", "age": 22},
#                 {"name": "Kelly", "age": 24},
#                 {"name": "Leo", "age": 26},
#             ]

#             result = await session.run(
#                 """
#                 UNWIND $persons as person
#                 CREATE (p:TestPerson {name: person.name, age: person.age})
#                 RETURN count(p) as count
#                 """,
#                 persons=persons,
#             )

#             record = await result.single()
#             assert record["count"] == 3

#             # 批量查询
#             result = await session.run(
#                 """
#                 MATCH (p:TestPerson)
#                 WHERE p.name IN ['Jack', 'Kelly', 'Leo']
#                 RETURN p.name as name
#                 ORDER BY p.name
#                 """
#             )

#             names = [record["name"] async for record in result]
#             assert names == ["Jack", "Kelly", "Leo"]

#     async def test_concurrent_queries(self, neo4j_driver):
#         """测试并发查询"""

#         async def create_and_read(name: str):
#             async with neo4j_driver.session() as session:
#                 # 创建
#                 await session.run(
#                     "CREATE (p:TestPerson {name: $name, age: $age})",
#                     name=name,
#                     age=20,
#                 )

#                 # 读取
#                 result = await session.run(
#                     "MATCH (p:TestPerson {name: $name}) RETURN p.name as name",
#                     name=name,
#                 )
#                 record = await result.single()
#                 return record["name"]

#         # 并发执行多个操作
#         tasks = [create_and_read(f"Person{i}") for i in range(5)]
#         results = await asyncio.gather(*tasks)

#         assert len(results) == 5
#         assert all(name.startswith("Person") for name in results)


# @pytest.mark.asyncio
# async def test_basic_connection():
#     """基本连接测试（独立测试）"""
#     from neo4j import AsyncGraphDatabase

#     uri = "bolt://localhost:7687"
#     auth = ("neo4j", "password123")

#     driver = AsyncGraphDatabase.driver(uri, auth=auth)

#     try:
#         # 验证连接
#         await driver.verify_connectivity()

#         # 执行简单查询
#         async with driver.session() as session:
#             result = await session.run("RETURN 1 as num")
#             record = await result.single()
#             assert record["num"] == 1

#     finally:
#         await driver.close()


# if __name__ == "__main__":
#     # 运行单个测试示例
#     async def main():
#         from neo4j import AsyncGraphDatabase

#         driver = AsyncGraphDatabase.driver(
#             "bolt://localhost:7687", auth=("neo4j", "password123")
#         )

#         try:
#             await driver.verify_connectivity()
#             print("✓ 成功连接到Neo4j")

#             async with driver.session() as session:
#                 # 创建示例
#                 result = await session.run(
#                     "CREATE (p:Person {name: $name, age: $age}) RETURN p",
#                     name="测试用户",
#                     age=25,
#                 )
#                 record = await result.single()
#                 print(f"✓ 创建节点: {record['p']}")

#                 # 查询示例
#                 result = await session.run(
#                     "MATCH (p:Person {name: $name}) RETURN p.name as name, p.age as age",
#                     name="测试用户",
#                 )
#                 record = await result.single()
#                 print(f"✓ 查询结果: name={record['name']}, age={record['age']}")

#                 # 清理
#                 await session.run("MATCH (p:Person {name: $name}) DELETE p", name="测试用户")
#                 print("✓ 清理测试数据")

#         finally:
#             await driver.close()

#     asyncio.run(main())
