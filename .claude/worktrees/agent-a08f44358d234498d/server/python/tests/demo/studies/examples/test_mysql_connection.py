import asyncio

import pytest


@pytest.mark.asyncio
async def test_mysql_connection():
    """
    测试MySQL连接超时异常
    """
    try:
        import aiomysql
    except ImportError:
        pytest.skip("MySQL驱动未安装，跳过测试")
    loop = asyncio.get_event_loop()

    conn = None
    try:
        # 建立连接 - 使用 asyncio.wait_for 确保超时控制
        conn = await asyncio.wait_for(
            aiomysql.connect(
                host="10.0.0.1",
                port=3306,
                user="root",
                password="qWu6jPjs9j",
                db="hzky",
                connect_timeout=1,
            ),
            timeout=10.0,  # 外层超时控制，确保即使 connect_timeout 失效也能抛异常
        )
        # 建立连接 不使用 使用 asyncio.wait_for 程序将一直运行卡死
        # conn = await aiomysql.connect(
        #     host="10.0.0.1",
        #     port=3306,
        #     user="root",
        #     password="qWu6jPjs9j",
        #     db="alon",
        #     connect_timeout=10,
        #     loop=loop,
        # )

        # 执行测试查询
        async with conn.cursor() as cursor:
            await cursor.execute("SELECT VERSION()")
            result = await cursor.fetchone()
            return result[0] if result else None
    except TimeoutError:
        print("连接超时: 无法在指定时间内连接到数据库")
    except Exception as e:
        print(f"连接失败: {str(e)}")
    finally:
        if conn:
            conn.close()
