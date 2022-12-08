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

# 创建数据卷，你也不想删除容器数据就没有了吧
docker volume create mysql
docker volume create mysql_config

# 启动数据库，设置网络、用户名、密码、端口映射
docker run -d -v mysql:/var/lib/mysql \
  -v mysql_config:/etc/mysql -p 3306:3306 \
  --network dn \
  --name db \
  -e MYSQL_ROOT_PASSWORD=root \
  mariadb

# 连接容器中的数据库，密码 root
docker exec -it db mariadb  -uroot -proot
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

提供缓存查询、缓存同步、数据库插入等用户功能

部署模式时需要在env设置其模式为产品模式，`FLASK_DEBUG`修改为 False ，修改完结果如下 

```bash
FLASK_DEBUG=False
FLASK_ENV = production
FLASK_CONFIG = production
```

Flask默认内置的Web服务器能力较弱，使用能力更强的Gunicorn来配合生产环境中的强度。

```bash
gunicorn -w 4 -b 127.0.0.1:5000 app:app
```

`-w`参数表示进程数目，上面表示启动4个进程服务。  
`-b`参数表示绑定的IP及端口。

## 启动方法

方法二选一，这里是容器练习，选容器办法，为了本地调试，常规方法也写了

```bash
# docker 容器方法，数据库、缓存的 host 在 docker 网络 中可以通过容器名称直接访问
docker build . -t flask:v4	# 创建隔离镜像，安装依赖，标签为flask:v4
docker run -d --network dn -p 5000:5000 --name web -v ${PWD}:/usr/src/app flask:v4	# 启动程序，暴露端口 5000，挂载本地目录到容器中

# 常规方法，在 python 3.10.8 测试通过
python -m venv env
source env/bin/activate
pip install -r requirement.txt
docker network inspect dn	# 获取 redis mariadb 的 ip 地址，修改 app 中对应的 ip 地址
gunicorn -w 4 -b 127.0.0.1:5000 app:app   # 浏览 http://127.0.0.1:5000/
# Ctrl + C 退出flask
```

# nginx

代理Web服务器，监听外部80端口的请求，然后将请求转发给Gunicorn处理。

修改完配置文件文件之后使用Nginx检查一下配置文件语法正确性`sudo nginx -t`，如果显示都是ok、successful则表示配置文件中没有语法错误。然后重启Nginx使其配置生效  

```bash
docker pull nginx
docker run --name ngx --network dn -v ${PWD}/nginx.conf:/etc/nginx/nginx.conf:ro -d -p 80:80 nginx
```

nginx 配置

- `proxy_pass`值的是转发的地址，根据Gunicorn设置进行修改。  
- `location /static`中的路径需要修改为项目静态文件夹中的静态文件路径。

# 四合一

1. 获取每个容器的 ip ：docker network inspect dn
2. 修改 app.py 中 redis、mariadb 的地址
3. 修改 nginx.conf 中 proxy_pass 的 ip 为 gunicorn 的地址
4. 除了 nginx 需要暴露端口供外部访问，其它三个容器都不需要外部访问接口，只需要在同一网络中相互访问即可

```bash
docker rm ngx web rds db -f	# 强制删除这四个容器

# 下面进行重建。不一样的是少了端口设置；多了一个 --restart=always，意思是挂机了会尝试重启
docker run -d -v mysql:/var/lib/mysql \
  -v mysql_config:/etc/mysql \
  --network dn \
  --name db \
  -e MYSQL_ROOT_PASSWORD=root \
   --restart=always mariadb

docker run -d --network dn --name rds --restart=always redis

docker network inspect dn
# 修改 app.py
docker run -d --network dn --name web -v ${PWD}:/usr/src/app --restart=always flask:v4

docker network inspect dn
# 修改 nginx.conf
docker run --name ngx --network dn -v ${PWD}/nginx.conf:/etc/nginx/nginx.conf:ro -d -p 80:80 --restart=always nginx
```

这是在单机上部署的案例，现在只能访问到 http://127.0.0.1/，数据库、redis、guncorn 都与用户隔离了。

# References

[mariadb  dockerhub](https://hub.docker.com/_/mariadb)

[nginx  dockerhub](https://hub.docker.com/_/nginx/)

[docker 的入门笔记](https://backmountaindevil.github.io/#/code/app/docker)

[Connect the application to the database](https://docs.docker.com/language/python/develop/)