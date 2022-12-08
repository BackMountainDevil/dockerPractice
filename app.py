import redis  # 导入redis 模块
from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy  # 数据库 ORM 包


app = Flask(__name__)
app.config[
    "SQLALCHEMY_DATABASE_URI"
] = "mysql+pymysql://root:root@db:3306/demo?charset=utf8"  # 数据库配置

db = SQLAlchemy(app)
pool = redis.ConnectionPool(host="rds", port=6379, decode_responses=True)
RDS = redis.Redis(host="rds", port=6379, decode_responses=True)


class Table(db.Model):  # 数据库 表模型
    __tablename__ = "table"  # 表名
    key = db.Column(db.String(100), primary_key=True)
    value = db.Column(db.String(100))


@app.cli.command()
def testRM():
    """
    使用方法：flask testrm

    作用： 测试数据库连接 redis 连接

    使用案例：
    $ flask testrm
    DEBUG. you should see runoob:  runoob
    DEBUG. you should see flask v2.2.2 below:
    flask v2.2.2
    """

    try:
        RDS.set("name", "runoob")  # 设置 name 对应的值
        print("DEBUG. you should see 'runoob': ", RDS.get("name"))  # 取出键 name 对应的值

        kv = Table()  # 插入数据库
        kv.key = "flask"
        kv.value = "v2.2.2"
        db.session.add(kv)
        db.session.commit()

        print("DEBUG. you should see flask v2.2.2 below:")  # 取出键 name 对应的值
        kvs = Table.query.filter(Table.key == "flask").all()
        for k in kvs:
            print(k.key, k.value)

    except Exception as ex:
        db.session.rollback()  # 事务回滚
        print("Error: ", repr(ex))


@app.route("/", methods=["GET"])
def index():
    """
    返回视图给用户进行操作
    """
    return render_template("index.html")


@app.route("/api/redis/get", methods=["POST"])
def api_rget():
    """
    根据提供的 key 从 redis 中查询 value，为查询到返回空
    """
    key = request.values.get("key")
    value = RDS.get(key)
    print("DEBUG ckey: %s\tcvalue: %s" % (key, value))
    return {key: value}


@app.route("/api/db/insert", methods=["POST"])
def api_db_insert():
    """
    把提供的 key value 存储到数据库中
    """
    key = request.values.get("key")
    value = request.values.get("value")
    print("DEBUG key: %s\tvalue: %s" % (key, value))

    try:
        kv = Table()
        kv.key = key
        kv.value = value
        db.session.add(kv)
        db.session.commit()
        return {"msg": "insert ok"}
    except Exception as ex:
        db.session.rollback()
        return {"error": repr(ex)}


@app.route("/api/redis/set", methods=["POST"])
def api_rset():
    """
    把提供的 key value 存储到 redis 中
    """
    key = request.values.get("key")
    value = request.values.get("value")
    print("DEBUG key: %s\tvalue: %s" % (key, value))
    RDS.set(key, value)
    return {"msg": "sync to cache ok"}
