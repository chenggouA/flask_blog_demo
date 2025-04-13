from flask import Flask

app = Flask(__name__)


# 动态路由，通过URL传入用户名参数
@app.route("/user/<username>")
def show_user_profile(username):
    # 返回一个包含用户名字的字符u串
    return f"用户页面：{username}"


# 动态路由传入整数参数
@app.route("/post/<int:post_id>")
def show_post(post_id):
    return f"文章ID：{post_id}"


if __name__ == "__main__":
    app.run(debug=True)
