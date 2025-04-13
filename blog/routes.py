from flask import Blueprint, request, jsonify, redirect, url_for, current_app
from blog.models import User, db, Post
from datetime import datetime, timedelta
import jwt

bp = Blueprint("api", __name__, url_prefix="/api")


@bp.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    if not data or not data.get("username") or not data.get("password"):
        return jsonify({"message": "用户名和密码是必需的"}), 400
    username = data["username"]
    password = data["password"]
    # 检查用户名是否已存在
    if User.query.filter_by(username=username).first():
        return jsonify({"message": "用户名已存在"}), 400
    # 创建新用户
    user = User(username=username)
    user.set_password(password)  # 哈希密码后保存
    db.session.add(user)
    db.session.commit()
    current_app.logger.info(f"New user registered: {username}")
    return jsonify({"message": "用户注册成功，请登录"}), 201


@bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    if not data or not data.get("username") or not data.get("password"):
        return jsonify({"message": "用户名和密码是必需的"}), 400
    username = data["username"]
    password = data["password"]
    user = User.query.filter_by(username=username).first()
    if not user or not user.check_password(password):
        current_app.logger.info(f"Failed login attempt for username: {username}")
        return jsonify({"message": "用户名或密码错误"}), 401
    # 生成 JWT Token
    token = jwt.encode(
        {
            "user_id": user.id,
            "exp": datetime.utcnow() + timedelta(hours=1),  # Token 1小时后过期
        },
        current_app.config["SECRET_KEY"],
        algorithm="HS256",
    )
    current_app.logger.info(f"User logged in: {username}")
    return (
        jsonify({"message": "登录成功", "token": token, "username": user.username}),
        200,
    )


def get_current_user_from_token():
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None, jsonify({"message": "缺少认证令牌"}), 401
    token = auth_header.split(" ")[1]  # 提取 "Bearer " 之后的实际token
    try:
        payload = jwt.decode(
            token, current_app.config["SECRET_KEY"], algorithms=["HS256"]
        )
    except jwt.ExpiredSignatureError:
        return None, jsonify({"message": "令牌已过期"}), 401
    except jwt.InvalidTokenError:
        return None, jsonify({"message": "无效的令牌"}), 401
    user = User.query.get(payload["user_id"])
    if not user:
        return None, jsonify({"message": "用户不存在"}), 401
    return user, None, None


@bp.route("/posts", methods=["POST"])
def create_post():
    user, error_response, status = get_current_user_from_token()
    if not user:
        return error_response, status
    data = request.get_json()
    if not data or not data.get("title") or not data.get("content"):
        return jsonify({"message": "标题和内容是必需的"}), 400
    title = data["title"]
    content = data["content"]
    # 创建 Post 对象
    post = Post(title=title, content=content, author=user)
    db.session.add(post)
    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(f"Error creating post: {e}")
        return jsonify({"message": "无法发布文章"}), 500
    current_app.logger.info(f"Post created (id={post.id}) by user: {user.username}")
    return (
        jsonify(
            {
                "message": "文章发布成功",
                "post": {
                    "id": post.id,
                    "title": post.title,
                    "content": post.content,
                    "author": user.username,
                    "created_at": post.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                },
            }
        ),
        201,
    )


@bp.route("/posts", methods=["GET"])
def get_posts():
    posts = Post.query.order_by(Post.created_at.desc()).all()
    result = []
    for post in posts:
        result.append(
            {
                "id": post.id,
                "title": post.title,
                "content": post.content,
                "author": post.author.username if post.author else None,
                "created_at": post.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            }
        )
    return jsonify(result), 200


@bp.route("/posts/<int:post_id>", methods=["GET"])
def get_post(post_id):
    post = Post.query.get(post_id)
    if not post:
        return jsonify({"message": "文章未找到"}), 404
    return (
        jsonify(
            {
                "id": post.id,
                "title": post.title,
                "content": post.content,
                "author": post.author.username if post.author else None,
                "created_at": post.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            }
        ),
        200,
    )


@bp.route("/posts/<int:post_id>", methods=["PUT"])
def update_post(post_id):
    user, error_response, status = get_current_user_from_token()
    if not user:
        return error_response, status
    post = Post.query.get(post_id)
    if not post:
        return jsonify({"message": "文章未找到"}), 404
    # 权限检查：只有作者本人可以编辑
    if post.author != user:
        return jsonify({"message": "没有权限编辑这篇文章"}), 403
    data = request.get_json()
    if not data:
        return jsonify({"message": "缺少要更新的数据"}), 400
    # 根据提供的数据更新字段
    if "title" in data:
        post.title = data["title"]
    if "content" in data:
        post.content = data["content"]
    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(f"Error updating post {post_id}: {e}")
        return jsonify({"message": "更新文章失败"}), 500
    current_app.logger.info(f"Post id={post.id} updated by user: {user.username}")
    return (
        jsonify(
            {
                "message": "文章更新成功",
                "post": {
                    "id": post.id,
                    "title": post.title,
                    "content": post.content,
                    "author": user.username,
                    "created_at": post.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                },
            }
        ),
        200,
    )


@bp.route("/posts/<int:post_id>", methods=["DELETE"])
def delete_post(post_id):
    user, error_response, status = get_current_user_from_token()
    if not user:
        return error_response, status
    post = Post.query.get(post_id)
    if not post:
        return jsonify({"message": "文章未找到"}), 404
    if post.author != user:
        return jsonify({"message": "没有权限删除这篇文章"}), 403
    db.session.delete(post)
    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(f"Error deleting post {post_id}: {e}")
        return jsonify({"message": "删除文章失败"}), 500
    current_app.logger.info(f"Post id={post.id} deleted by user: {user.username}")
    return jsonify({"message": "文章已删除"}), 200


@bp.app_errorhandler(404)
def handle_404(error):
    return jsonify({"message": "接口不存在"}), 404


@bp.app_errorhandler(500)
def handle_500(error):
    current_app.logger.error(f"Internal server error: {error}, path: {request.path}")
    return jsonify({"message": "服务器内部错误"}), 500
