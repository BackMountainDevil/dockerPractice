# 介绍

docker 实践篇

nginx+redis+mariadb+python

1. 四个部分分别放在不同的容器，组成一套完成的 web 服务体系

2. 实现向 mariadb 数据库写入数据，并读取展示到网页

3. 实现向 redis 数据写入数据，并读取显示到网页

4. 通过页面交互，实现数据库数据到缓存的更新

# 数据库 mariadb

```bash
docker pull mariadb # 拉取 mariadb 最新镜像，现在是 10.10.2

docker network create dn    # 创建网络 dn
# 启动数据库，设置网络、用户名、密码、端口映射
docker run -d --network dn  --name db --env MARIADB_USER=admin --env MARIADB_PASSWORD=admin --env MARIADB_ROOT_PASSWORD=root -p 3306:3306 mariadb
# 连接容器中的数据库，密码 root
docker exec -it db mariadb  -uroot -p
MariaDB [(none)]> create database demo;
Query OK, 1 row affected (0.001 sec)

MariaDB [(none)]> use demo;
Database changed
```

建表，插入数据测试

```sql
CREATE TABLE demo.`table` (
	`key` varchar(100) ,
	`value` varchar(100) 
);

INSERT INTO demo.`table` (`key`, `value`) VALUES('name', 'nobody');
INSERT INTO demo.`table` (`key`, `value`) VALUES('age', '18');
```

# 缓存 redis

```bash
docker pull redis   # 拉取镜像
docker run -d --network dn --name rds -p 6379:6379 redis    # 运行 redis,加入 dn 网络，暴露端口
docker exec -it rds redis-cli   # 进入 redis 容器，运行 redis-cli
127.0.0.1:6379> set name mifen
OK
127.0.0.1:6379> get name
"mifen"
127.0.0.1:6379> quit
```

# python flask

```bash
pip install -r requirement.txt
flask run   # 浏览 http://127.0.0.1:5000/
# Ctrl + C 退出flask
```

# References

[mariadb  dockerhub](https://hub.docker.com/_/mariadb)

