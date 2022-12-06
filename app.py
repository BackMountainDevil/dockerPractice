import redis  # 导入redis 模块

pool = redis.ConnectionPool(host="localhost", port=6379, decode_responses=True)
r = redis.Redis(host="localhost", port=6379, decode_responses=True)
r.set("name", "runoob")  # 设置 name 对应的值
print(r.get("name"))  # 取出键 name 对应的值
