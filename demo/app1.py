from flask import Flask

app = Flask(__name__)


# 定义一个根路由，当用户访问网站根路径时执行
@app.route("/")
def home():
    return "你好，这是首页！"


if __name__ == "__main__":
    # 启动 Flask 服务，开启调试模式
    app.run(debug=True)
