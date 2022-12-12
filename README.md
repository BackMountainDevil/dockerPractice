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

除了 nginx 需要暴露端口供外部访问，其它三个容器都不需要外部访问接口，只需要在同一网络中相互访问即可

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

docker run -d --network dn --name web -v ${PWD}:/usr/src/app --restart=always flask:v4

docker run --name ngx --network dn -v ${PWD}/nginx.conf:/etc/nginx/nginx.conf:ro -d -p 80:80 --restart=always nginx
```

这是在单机上部署的案例，现在只能访问到 http://127.0.0.1/，数据库、redis、guncorn 都与用户隔离了。

## compose

上面要敲四条命令太不优雅了，docker-compose 提供了另一种解决方案

```bash
docker-compose up -d  # -d 表示后台启动
docker-compose stop # 暂停项目中所有容器
```

从启动和暂停看，web都最慢
# Problem
## nginx proxy_pass 待解决

本地浏览器访问发现还是 nginx 默认的首页，按理说应该是自定义的网站首页，后面起一个 alpine 加入网络，在 alpine 上用 `curl http://web:5000` 获取到的内容是 flask 返回的内容，而我本地通过 `curl http://localhost/` 获取到的内容确是 nginx 默认首页，通过 docker logs ngx 也确认了这一事实

```bash
$ docker logs ngx
172.20.0.1 - - [08/Dec/2022:03:15:26 +0000] "GET / HTTP/1.1" 200 615 "-" "curl/7.86.0" "-"
172.20.0.1 - - [08/Dec/2022:03:15:32 +0000] "GET / HTTP/1.1" 200 2127 "-" "curl/7.86.0" "-"
```

搜索一波以为是设置问题，proxy_pass 为 http://web:5000/ 和 http://web:5000 的区别，现在这样设置可以正常访问，后面突然又不行了。说明这个末尾的斜杠不影响转发地址。

然后是通过浏览器地址栏给出了下一步的方向，发现是 http://127.0.0.1/ 和 http://localhost/ 的区别，前者正常返回 flask 内容，后者返回的却是 nginx 默认页面。在我本机的 host 里面，有这么几条设置（好像有一条设置错误 - hp）

```bash
$ cat /etc/hosts 
# Standard host addresses
127.0.0.1  localhost
::1        localhost ip6-localhost ip6-loopback
ff02::1    ip6-allnodes
ff02::2    ip6-allrouters
# This host address
127.0.1.1  hp

$ nslookup 127.0.0.1
1.0.0.127.in-addr.arpa	name = localhost.

$ nslookup localhost
Server:		10.6.39.2
Address:	10.6.39.2#53

Non-authoritative answer:
Name:	localhost
Address: 127.0.0.1
Name:	localhost
Address: ::1
```

通过阅读发现，127.0.0.1–127.255.255.255 都是指本地主机，实测 127.0.0.127 和 127.255.255.254 返回的都是 flask 网页，关闭 nginx 容器之后无论是 localhost 还是 127.0.0.1 都没法访问到内容了，也就是说可以确认这两个返回的内容都是来自 nginx，那么就是说 nginx 解析设置存在问题，在 nginx 容器里面返回内容也是不同

```bash
$ docker stop ngx
ngx
$ curl localhost
curl: (7) Failed to connect to localhost port 80 after 14 ms: Couldn't connect to server
$ curl 127.0.0.1
curl: (7) Failed to connect to 127.0.0.1 port 80 after 23 ms: Couldn't connect to server
```

# References

[mariadb  dockerhub](https://hub.docker.com/_/mariadb)

[nginx  dockerhub](https://hub.docker.com/_/nginx/)

[docker 的入门笔记](https://backmountaindevil.github.io/#/code/app/docker)

[Connect the application to the database](https://docs.docker.com/language/python/develop/)

[Alpine 镜像使用帮助](https://mirrors.tuna.tsinghua.edu.cn/help/alpine/)：然后 apk add curl
> sed -i 's/dl-cdn.alpinelinux.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apk/repositories

[What Is 127.0.0.1 Localhost? February 17, 2022](https://phoenixnap.com/kb/127-0-0-1-localhost)