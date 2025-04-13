from flask import Flask, request

app = Flask(__name__)


# 同一个视图函数可以绑定多个路由
@app.route("/")
@app.route("/index")
def index():
    return "欢迎来到主页！"


# 指定请求方法为 POST 和 GET
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        return "正在处理登录请求..."
    else:
        return "请通过表单提交登录信息"


if __name__ == "__main__":
    app.run(debug=True)
