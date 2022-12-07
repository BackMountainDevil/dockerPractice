FROM python:3.10.8-slim
RUN pip install python-dotenv pymysql flask flask_sqlalchemy redis gunicorn -i https://pypi.tuna.tsinghua.edu.cn/simple
WORKDIR /usr/src/app
CMD gunicorn -w 4 -b 0.0.0.0:5000 app:app