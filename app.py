import redis  # 导入redis 模块
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy  # 数据库 ORM 包


app = Flask(__name__)
app.config[
    "SQLALCHEMY_DATABASE_URI"
] = "mysql+pymysql://root:root@:3306/demo?charset=utf8"  # 数据库配置

db = SQLAlchemy(app)


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
        pool = redis.ConnectionPool(host="localhost", port=6379, decode_responses=True)
        r = redis.Redis(host="localhost", port=6379, decode_responses=True)
        r.set("name", "runoob")  # 设置 name 对应的值
        print("DEBUG. you should see 'runoob': ", r.get("name"))  # 取出键 name 对应的值

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
    return render_template("index.html")
