FROM python:3.10.8-slim
RUN pip install python-dotenv pymysql flask flask_sqlalchemy redis -i https://pypi.tuna.tsinghua.edu.cn/simple
WORKDIR /usr/src/app
CMD ["flask", "run", "--host", "0.0.0.0", "--port", "5000"]