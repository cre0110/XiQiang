# -*- coding:utf-8 -*-

'''

用户权限(power)说明：
int型整数
0  ->  被禁言/封号
1  ->  正常用户
2  ->  VIP用户
3  ->  官方账号
4  ->  预留
5  ->  预留
6  ->  为校方预留
7  ->  仅发布管理员(不含审核权限)
8  ->  管理员
9  ->  超级管理员

'''

import os
import math
import random
import uuid
import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header

from flask import Flask, render_template, request, url_for, session, flash, redirect, send_from_directory

from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func, and_

app = Flask(__name__)

# app.config['SERVER_NAME'] = '127.0.0.1'
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True  # True跟踪数据库的修改，及时发送信号
app.secret_key = "TvC/+kq3ouM6xX9Yjq52v@wHgwDB/TEBrh-*/*+84wBEwe"

CORS(app)

db = SQLAlchemy(app)


class User(db.Model):
    uid = db.Column(db.Integer, autoincrement=True, primary_key=True, unique=True, nullable=False)
    qq = db.Column(db.String, unique=True, nullable=False)
    passwd = db.Column(db.String, nullable=False)
    head = db.Column(db.String, nullable=False)
    name = db.Column(db.String, nullable=False)
    power = db.Column(db.Integer, nullable=False)
    notes = db.Column(db.String)


class Message(db.Model):
    mid = db.Column(db.Integer, autoincrement=True, primary_key=True, unique=True, nullable=False)
    uid = db.Column(db.Integer, nullable=False)
    content = db.Column(db.String, nullable=False)
    time = db.Column(db.String, nullable=False)
    type = db.Column(db.String, nullable=False)
    status = db.Column(db.String, nullable=False)
    comments = db.Column(db.String, nullable=False)
    images = db.Column(db.String, nullable=False)
    likes = db.Column(db.String, nullable=False)
    notes = db.Column(db.String)


class News(db.Model):
    nid = db.Column(db.Integer, autoincrement=True, primary_key=True, unique=True, nullable=False)
    uid = db.Column(db.Integer, nullable=False)
    content = db.Column(db.String, nullable=False)
    time = db.Column(db.String, nullable=False)
    status = db.Column(db.String, nullable=False)
    images = db.Column(db.String, nullable=False)
    likes = db.Column(db.String, nullable=False)
    notes = db.Column(db.String)


class Banner(db.Model):
    bid = db.Column(db.Integer, autoincrement=True, primary_key=True, unique=True, nullable=False)
    images = db.Column(db.String, nullable=False)
    status = db.Column(db.String, nullable=False)
    notes = db.Column(db.String)


class Comment(db.Model):
    cid = db.Column(db.Integer, autoincrement=True, primary_key=True, unique=True, nullable=False)
    mid = db.Column(db.Integer, nullable=False)
    uid = db.Column(db.Integer, nullable=False)
    content = db.Column(db.String, nullable=False)
    time = db.Column(db.String, nullable=False)
    likes = db.Column(db.String, nullable=False)
    notes = db.Column(db.String)


with app.app_context():
    db.create_all()

uploads_url = "http://127.0.0.1/uploads/"
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'PNG', 'JPG', 'JPEG', 'GIF', }
UPLOAD_FOLDER = os.path.join(app.root_path, 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# SMTP 服务器
mail_host = "smtp.126.com"
mail_user = "xc_wall@126.com"
mail_pass = "MOVCAGKRHIMIKPPH"
mail_port = 25


def allowed_file(filename):
    """
    #判断上传文件类型是否允许
    :param filename 文件名
    :return: 布尔值 TRUE or False
    """
    return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


def random_file(filename):
    """
    生成随机文件名
    :param filename: 文件名
    :return:随机文件名
    """
    ext = os.path.splitext(filename)[1]
    # 使用uuid生成随机字符
    new_filename = uuid.uuid4().hex + ext
    time = str(datetime.datetime.now()).split('.')[0]
    prefix = "".join(time.split(' ')[0].split('-'))
    return prefix + new_filename


def get_session_info():
    """
    获取当前登陆的用户的信息
    :return: 字典，包含qq、head、name、power
    """
    user = {}

    uid = session.get('uid')
    qq = session.get('qq')
    head = session.get('head')
    name = session.get('name')
    power = session.get('power')

    if not qq:
        user = {'uid': 0, 'qq': "", 'head': "/static/icons/not_logged.png", 'name': "未登录", 'power': 0}

    else:
        user = {'uid': uid, 'qq': qq, 'head': head, 'name': name, 'power': power}

    return user


def get_user_by_uid(uid: int):
    with app.app_context():
        user = User.query.filter_by(uid=uid).first()

    return user


def get_user_by_qq(qq: str):
    with app.app_context():
        user = User.query.filter_by(qq=qq).first()

    return user


def send_verify(qq):
    code = random.randint(100000, 999999)

    sender = 'xc_wall@126.com'
    receivers = [qq + '@qq.com']
    message = MIMEMultipart()
    message['From'] = Header("xc_wall@126.com")
    message['To'] = Header(qq + "@qq.com", 'utf-8')

    with open('./static/verify_code.html', 'r', encoding='utf-8') as f:
        bodytxt = f.read()

    bodytxt = bodytxt.replace('v_code', str(code))

    subject = '[撞破南墙找西墙]注册验证码'
    message['Subject'] = Header(subject, 'utf-8')
    # bodytxt = "您正在注册[撞破南墙找西墙](山东省实验中学西校表白墙)\n您的邮箱验证码为：" + str(code)
    message.attach(MIMEText(bodytxt, _subtype='html', _charset='utf-8'))

    try:
        smtpObj = smtplib.SMTP()
        smtpObj.connect(mail_host, mail_port)
        smtpObj.login(mail_user, mail_pass)
        smtpObj.sendmail(sender, receivers, message.as_string())

        return code

    except smtplib.SMTPException as e:
        return -1


@app.route('/')
def index_page():
    info = get_session_info()

    news_total = News.query.with_entities(News.nid).count()

    news_res = {}
    now_index = news_total

    while now_index > 0 and not news_res:
        query = News.query.filter_by(nid=now_index).first()

        if query.status == 'Normal':
            user_query = User.query.filter_by(uid=query.uid).first()

            news_res = {
                'nid': query.nid,
                'content': query.content,
                'time': query.time,
                'head': user_query.head,
                'name': user_query.name,
                'img': query.images,
                'power': user_query.power
            }

        now_index -= 1

    wall_total = Message.query.with_entities(Message.mid).count()

    now_index = wall_total
    templist = []
    wall_list = []

    while now_index > 0 and len(templist) < 3:
        query = Message.query.filter_by(mid=now_index).first()

        if query.status == 'examined':
            templist.append(query)

        now_index -= 1

    for i in templist:
        send_user = get_user_by_uid(i.uid)

        data = {'mid': str(i.mid),
                'content': i.content,
                'time': i.time,
                'head': send_user.head,
                'name': send_user.name,
                'type': i.type,
                'status': i.status,
                'img': i.images, }

        wall_list.append(data)

    banners = Banner.query.filter_by(status="Normal").all()
    banner_list = []

    if banners and banners[0] != '':

        first_banner = {
            'bid': banners[len(banners) - 1].bid,
            'img': banners[len(banners) - 1].images
        }

        for i in range(len(banners) - 1):
            banner_list.append(
                {
                    'bid': banners[len(banners) - i - 2].bid,
                    'img': banners[len(banners) - i - 2].images
                }
            )

    else:
        first_banner = {'img': '404.jpg', 'bid': -1}
        banner_list = []

    banners_list_number = []
    for i in range(len(banner_list)):
        banners_list_number.append(str(i + 1))

    return render_template('index_page.html', first_banner=first_banner, banner_list=banner_list,
                           banners_list_number=banners_list_number, news=news_res, wall_list=wall_list, user=info)


@app.route('/logout')
def logout_page():
    session.clear()
    flash("退出登录成功！", 'success')
    return redirect(url_for("login_page"))


@app.route('/wall')
def wall_page():
    info = get_session_info()

    page = request.args.get('page')
    start = request.args.get('start')

    if not page:
        page = 1
    else:
        page = int(page)

    wall_total = db.session.query(func.count(Message.mid)).filter(Message.status == 'examined').scalar()
    total_message = Message.query.with_entities(Message.mid).count()

    if not start:
        if page == 1:
            start = total_message - (page - 1) * 10
        else:
            return redirect("/wall")

    else:
        start = int(start)

    prev_start = start

    reslist = []
    templist = []

    if (page * 10 - wall_total) >= 10:
        return render_template("wall_read.html", reslist=[], page=1, page_num=1, user=info, wall_total=wall_total,
                               start=start, prev_start=prev_start)

    while len(templist) < 10 and start >= 1:

        query = Message.query.filter_by(mid=start).first()

        if query.status == 'examined':
            templist.append(query)

        start -= 1

    for i in templist:
        send_user = get_user_by_uid(i.uid)

        data = {'mid': str(i.mid),
                'content': i.content,
                'time': i.time,
                'head': send_user.head,
                'name': send_user.name,
                'type': i.type,
                'status': i.status,
                'img': i.images,
                'likes': 0,
                'is_self_liked': False}

        like_list = i.likes.split('|')
        if i.likes != "":
            data['likes'] = len(like_list)

        if not data['likes']:
            data['likes'] = "0"

        flag = False

        origin = i.likes.split("|")
        for j in range(len(origin)):
            if origin[j] == str(info['uid']):
                flag = True

        if flag:
            data['is_self_liked'] = True

        reslist.append(data)

    page_num = math.ceil(float(wall_total) / 10)

    return render_template("wall_read.html", reslist=reslist, page=page, page_num=page_num, user=info,
                           wall_total=wall_total, start=start, prev_start=prev_start)


@app.route('/messages', methods=['GET', 'POST'])
def message_page():
    info = get_session_info()

    mid = int(request.args.get('mid'))
    page = request.args.get('page')

    if not mid:
        return redirect(url_for('wall_page'))

    if not page:
        page = 1
    else:
        page = int(page)

    now_time = str(datetime.datetime.now()).split('.')[0]

    message_query = Message.query.filter_by(mid=mid).first()

    if request.method == 'POST':

        if not info['qq']:
            flash("<strong>您还未登录，请先登录</strong>", 'danger')
            return redirect(url_for("login_page"))

        if info['power'] <= 0:
            flash("您的帐号有违规行为，已被封禁，不可发布消息。有疑问请<a href=\"/feedback\">留言</a>", 'danger')
            return render_template('message_detail.html', user=info)

        comment = request.form.get('comment')

        comments = Comment(
            mid=mid,
            uid=info['uid'],
            content=comment,
            time=now_time,
            likes=""
        )

        db.session.add(comments)
        db.session.flush()

        new_cid = comments.cid

        db.session.commit()

        if message_query.comments == "":
            new_comments_list = str(new_cid)
        else:
            new_comments_list = message_query.comments + "|" + str(new_cid)

        Message.query.filter(Message.mid == mid).update(
            {
                'comments': new_comments_list
            }
        )

        db.session.commit()

        flash("<strong>回复成功！</strong>", 'success')

    if not message_query:
        return redirect(url_for("wall_page"))

    user_query = User.query.filter_by(uid=message_query.uid).first()

    message = {
        'content': message_query.content,
        'time': now_time,
        'head': user_query.head,
        'name': user_query.name,
        'type': message_query.type,
        'mid': mid,
        'img': message_query.images,
        'power': user_query.power,
        'is_vip': False,
        'is_official': False,
        'likes': 0,
        'is_self_liked': False
    }

    like_list = message_query.likes.split('|')
    if message_query.likes != "":
        message['likes'] = len(like_list)

    if not message['likes']:
        message['likes'] = "0"

    flag = False

    origin = message_query.likes.split("|")
    for i in range(len(origin)):
        if origin[i] == str(info['uid']):
            flag = True

    if flag:
        message['is_self_liked'] = True

    if user_query.power == 2 or user_query.power >= 8:
        message['is_vip'] = True

    if user_query.power == 3:
        message['is_official'] = True

    # Comments List

    get_comments = message_query.comments
    get_comments_list = get_comments.split('|')

    comment_list = []
    page_num = math.ceil(float(len(get_comments_list)) / 10)

    if page_num == 0:
        page_num = 1

    if get_comments_list != ['']:
        if (len(get_comments_list) - (page - 1) * 10) > 10:
            if page_num == page:
                for_range = page_num * 10 - len(get_comments_list)

            else:
                for_range = 10

        else:
            for_range = len(get_comments_list) - (page - 1) * 10

        for i in range(for_range):
            comment_data = Comment.query.filter_by(
                cid=get_comments_list[len(get_comments_list) - 1 - (page - 1) * 10 - i]).first()

            user_data = User.query.filter_by(uid=comment_data.uid).first()

            comment = {
                'content': comment_data.content,
                'head': user_data.head,
                'name': user_data.name,
                'cid': get_comments_list[len(get_comments_list) - 1 - (page - 1) * 10 - i],
                'power': user_data.power,
                'is_vip': False,
                'is_official': False,
                'time': comment_data.time
            }

            if user_data.power == 2 or user_data.power >= 8:
                comment['is_vip'] = True
            if user_data.power == 3:
                comment['is_official'] = True

            comment_list.append(comment)

    return render_template('message_detail.html', message=message, comment_list=comment_list, page=page,
                           page_num=page_num, user=info)


@app.route('/send', methods=['GET', 'POST'])
def send_page():

    info = get_session_info()

    if not info['qq']:
        flash("<strong>您还未登录，请先登录！</strong>", 'danger')
        return redirect(url_for("login_page"))

    if info['power'] <= 0:
        flash("您的帐号有违规行为，已被封禁，不可发布消息。有疑问请<a href=\"/feedback\">留言</a>", 'danger')
        return render_template('send_page.html', user=info)

    if request.method == 'POST':

        img = request.files['img']

        message_content = request.form.get('content')
        anonymous = request.form.get('anonymous')

        message_content = message_content.replace('<', '&lt;')
        message_content = message_content.replace('>', '&gt;')

        message_content = "<br>".join(message_content.split('\r\n'))

        message_type = 'normal'

        if anonymous:
            message_type = 'anonymous'

        now_time = str(datetime.datetime.now()).split('.')[0]

        img_list = ""

        if img and allowed_file(img.filename):
            filename = random_file(img.filename)
            img.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            img_list = filename

        # messages_database.add(content, qq, time, type, filename)

        with app.app_context():

            message = Message(
                uid=info['uid'],
                content=message_content,
                time=now_time,
                type=message_type,
                status="unexamined",
                comments="",
                images=img_list,
                likes="",
                notes=""
            )

            db.session.add(message)
            db.session.commit()

        flash("发布成功！请<strong>等待审核</strong>，<a href='/wall/user?uid=" + str(info['uid']) + "'>点此查看审核情况</a>",
              'success')

    return render_template('send_page.html', user=info)


@app.route('/examine', methods=['GET', 'POST'])
def examine_page():
    info = get_session_info()

    if info['power'] < 8:
        flash("您的账号没有该权限！", 'danger')
        return render_template('examine_page.html', reslist=[], page=1, page_num=1, user=info)

    mid = request.args.get('mid')
    operation = request.args.get('operation')

    if mid:

        if operation == 'pass':

            with app.app_context():

                Message.query.filter(Message.mid == mid).update({'status': 'examined'})
                db.session.commit()

            flash("审核成功！", 'success')

        elif operation == 'reject':

            with app.app_context():

                Message.query.filter(Message.mid == mid).update({'status': 'rejected'})
                db.session.commit()

            flash("驳回成功！", 'success')

    page = request.args.get('page')

    if not page:
        page = 1

    else:
        page = int(page)

    total_message = Message.query.with_entities(Message.mid).count()

    reslist = []

    if (page * 10 - total_message) >= 10:
        return render_template("examine_page.html", reslist=[], page=1, page_num=1, user=info)

    for_range = 10
    if total_message < page * 10:
        for_range = total_message - (page - 1) * 10

    query = Message.query.filter(
        Message.mid.between(total_message - (page - 1) * 10 - for_range + 1, total_message - (page - 1) * 10)).order_by(
        Message.mid.desc()).all()

    for i in query:
        send_user = get_user_by_uid(i.uid)

        data = {'mid': str(i.mid),
                'content': i.content,
                'time': i.time,
                'head': send_user.head,
                'name': send_user.name,
                'type': i.type,
                'status': i.status,
                'img': i.images}

        reslist.append(data)

    page_num = math.ceil(float(total_message) / 10)

    return render_template('examine_page.html', reslist=reslist, page=page, page_num=page_num, user=info)


@app.route('/news')
def news_page():
    info = get_session_info()

    del_nid = request.args.get('del_nid')
    if del_nid:
        News.query.filter(News.nid == int(del_nid)).update(
            {
                'status': "Deleted"
            }
        )
        db.session.commit()
        flash("删除成功！", 'success')

    management = False

    if info['power'] == 3 or info['power'] >= 7:
        management = True

    page = request.args.get('page')
    start = request.args.get('start')

    if not page:
        page = 1
    else:
        page = int(page)

    news_total = News.query.with_entities(News.nid).count()

    if not start:
        if page == 1:
            start = news_total - (page - 1) * 10
        else:
            return redirect("/news")

    else:
        start = int(start)

    prev_start = start

    reslist = []
    templist = []

    if (page * 10 - news_total) >= 10:
        return render_template("news_read.html", reslist=[], page=1, page_num=1, user=info,
                               start=start, prev_start=prev_start, management=management)

    while len(templist) < 10 and start >= 1:

        query = News.query.filter_by(nid=start).first()

        if query.status == "Normal":
            templist.append(query)
        start -= 1

    for i in templist:
        send_user = get_user_by_uid(i.uid)

        data = {'nid': str(i.nid),
                'content': i.content,
                'time': i.time,
                'head': send_user.head,
                'name': send_user.name,
                'img': i.images,
                'power': send_user.power,
                'likes': 0,
                'is_self_liked': False}

        like_list = i.likes.split('|')
        if i.likes != "":
            data['likes'] = len(like_list)

        if not data['likes']:
            data['likes'] = "0"

        flag = False

        origin = i.likes.split("|")
        for j in range(len(origin)):
            if origin[j] == str(info['uid']):
                flag = True

        if flag:
            data['is_self_liked'] = True

        reslist.append(data)

    page_num = math.ceil(float(news_total) / 10)

    return render_template("news_read.html", reslist=reslist, page=page, page_num=page_num, user=info,
                           start=start, prev_start=prev_start, management=management)


@app.route('/news_send', methods=['GET', 'POST'])
def add_news():
    qq = session.get('qq')
    info = get_session_info()

    if not qq:
        flash("<strong>您还未登录，请先登录！</strong>", 'danger')
        return redirect(url_for("login_page"))

    if info['power'] < 7 and info['power'] != 3:
        flash("您的账户没有该权限！", 'danger')
        return render_template('news_send.html', user=info)

    if request.method == 'POST':

        img = request.files['img']

        news_content = request.form.get('content')

        news_content = news_content.replace('<', '&lt;')
        news_content = news_content.replace('>', '&gt;')

        news_content = "<br>".join(news_content.split('\r\n'))

        now_time = str(datetime.datetime.now()).split('.')[0]

        img_list = ""

        if img and allowed_file(img.filename):
            filename = random_file(img.filename)
            img.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            img_list = filename

        # messages_database.add(content, qq, time, type, filename)

        with app.app_context():

            news = News(
                uid=info['uid'],
                content=news_content,
                time=now_time,
                status="Normal",
                images=img_list,
                likes=""
            )

            db.session.add(news)
            db.session.commit()

        flash("发布成功！", 'success')

    return render_template('news_send.html', user=info)


@app.route('/me')
def me_page():
    info = get_session_info()

    if not info['qq']:
        flash("<strong>您还未登录，请先登录</strong>", 'danger')
        return redirect(url_for('login_page'))

    usr = {'vip': False, 'show_management': False, 'manage': "无"}

    if info['power'] == 2:
        usr['vip'] = True

    if info['power'] >= 6:
        usr['vip'] = True
        usr['show_management'] = True
        usr['manage'] = "有"

    return render_template('me_page.html', usr=usr, user=info)


@app.route('/wall/user')
def get_message_by_uid():

    info = get_session_info()
    uid = request.args.get('uid')
    reslist = []

    if not uid:
        return redirect(url_for("wall_page"))

    query = Message.query.order_by(Message.mid.desc()).filter(Message.uid == uid).limit(10).all()

    for i in query:
        user_query = User.query.filter_by(uid=i.uid).first()

        data = {
            'mid': i.mid,
            'content': i.content,
            'time': i.time,
            'head': user_query.head,
            'name': user_query.name,
            'type': i.type,
            'status': i.status,
            'img': i.images,
            'power': user_query.power,
            'is_vip': False,
            'is_official': False
        }

        if user_query.power == 3:
            data['is_official'] = True

        if user_query.power == 2 or user_query.power >= 8:
            data['is_vip'] = True

        reslist.append(data)

    return render_template("wall_user.html", reslist=reslist, user=info)


@app.route('/banner_send', methods=['GET', 'POST'])
def send_banner_page():
    info = get_session_info()

    if not info['qq']:
        flash("您还未登录，请先登录！", 'danger')
        return redirect(url_for("login_page"))

    if info['power'] != 3 and info['power'] < 7:
        flash("您没有该权限！", 'danger')
        return render_template('banner_send.html', user=info)

    if request.method == 'POST':

        banner_total = db.session.query(func.count(Banner.bid)).filter(Banner.status == 'Normal').scalar()
        if banner_total >= 10:
            flash("轮播图不能超过10张，请先删除之前的轮播图再添加", 'danger')
            return render_template('banner_send.html', banner=[], user=info)

        img = request.files['img']

        if img and allowed_file(img.filename):
            filename = random_file(img.filename)
            img.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            banner = Banner(
                images=filename,
                status="Normal"
            )
            db.session.add(banner)
            db.session.commit()

            flash("投放成功！", 'success')

        else:
            flash("文件为空或格式不符！", 'danger')

    del_bid = request.args.get('del_bid')

    if del_bid:
        Banner.query.filter(Banner.bid == del_bid).update(
            {
                'status': "Deleted"
            }
        )

        db.session.commit()

        flash("删除成功！", 'success')

    banners = Banner.query.filter_by(status="Normal").all()

    reslist = []

    for i in banners:
        data = {
            'bid': i.bid,
            'img': i.images
        }

        reslist.append(data)

    return render_template('banner_send.html', banner=reslist, user=info)


@app.route('/search', methods=['GET', 'POST'])
def search_page():
    info = get_session_info()
    key = request.args.get('key')
    reslist = []

    if not key:
        flash("请输入搜索关键词！", 'warning')
        return render_template('search_res.html', reslist=[], user=info)

    query = Message.query.order_by(Message.mid.desc()).filter(
        and_(Message.status == "examined", Message.content.contains(key))).limit(10).all()

    for i in query:
        user_query = User.query.filter_by(uid=i.uid).first()

        data = {
            'mid': i.mid,
            'content': i.content,
            'time': i.time,
            'head': user_query.head,
            'name': user_query.name,
            'type': i.type,
            'img': i.images,
            'power': user_query.power,
            'is_vip': False,
            'is_official': False
        }

        if user_query.power == 3:
            data['is_official'] = True

        if user_query.power == 2 or user_query.power >= 8:
            data['is_vip'] = True

        reslist.append(data)

    return render_template("search_res.html", reslist=reslist, user=info)


@app.route('/login', methods=['GET', 'POST'])
def login_page():
    info = get_session_info()

    if request.method == 'POST':
        qq = request.form.get('qq')
        passwd = request.form.get('passwd')

        query = get_user_by_qq(qq)

        if query:
            if query.passwd.find('_temp_reg') != -1:
                with app.app_context():
                    db.session.delete(query)
                    db.session.commit()

                query = None

        if not query:
            verify = send_verify(qq)

            with app.app_context():
                reg = User(
                    qq=qq,
                    passwd=passwd + "_temp_reg",
                    head="/static/userheader_old.svg",
                    name=str(verify),
                    power=0
                )

                db.session.add(reg)
                db.session.commit()

            return redirect('/reg?qq=' + qq)

        if query.passwd == passwd:

            session['uid'] = query.uid
            session['qq'] = qq
            session['head'] = query.head
            session['name'] = query.name
            session['power'] = query.power

            flash("<strong>登录成功！</strong>前往<a href='/me'>个人中心</a>", "success")
            return redirect(url_for('login_page'))

        else:

            flash("<strong>用户名或密码错误！</strong>", "danger")
            return redirect(url_for('login_page'))

    return render_template('login_page.html', user=info)


@app.route('/reg', methods=['GET', 'POST'])
def reg_page():
    info = get_session_info()

    qq = request.args.get('qq')

    if not qq:
        return redirect(url_for('login_page'))

    if request.method == 'POST':

        verify = request.form.get('verify')
        name = request.form.get('name')

        query = get_user_by_qq(qq)

        if not query:
            flash("<strong>验证码尚未发送</strong>", "warning")
            return redirect(url_for("login_page"))

        if verify != query.name:
            flash("验证码错误，请重新输入", 'danger')
            return render_template('reg_page.html', user=info)

        head = "https://q1.qlogo.cn/g?b=qq&nk=" + qq + "&s=100"

        with app.app_context():

            query.name = name
            query.head = head
            query.passwd = query.passwd.split('_temp_reg')[0]

            User.query.filter(User.qq == qq).update(
                {'name': name, 'head': head, 'passwd': query.passwd.split('_temp_reg')[0], 'power': 1})

            db.session.commit()

        flash("<strong>注册成功！</strong>前往<a href='/login'>登录</a>", "success")

        return render_template("reg_page.html", user=info)

    else:
        flash("验证码已发送至QQ邮箱", 'success')

    return render_template('reg_page.html', user=info)


@app.route('/feedback', methods=['GET', 'POST'])
def feedback_page():
    info = get_session_info()

    if not info['qq']:
        flash("<strong>您还未登录，请先登录！</strong>", 'danger')
        return redirect(url_for("login_page"))

    if request.method == 'POST':
        content = request.form.get('content')

        content = content.replace('<', '&lt;')
        content = content.replace('>', '&gt;')

        # content = "<br>".join(content.split('\r\n'))

        sender = 'xc_wall@126.com'
        receivers = ['xc_wall@126.com']
        message = MIMEMultipart()
        message['From'] = Header("xc_wall@126.com")
        message['To'] = Header("xc_wall@126.com", 'utf-8')

        subject = '[撞破南墙找西墙]用户使用反馈'
        message['Subject'] = Header(subject, 'utf-8')
        bodytxt = "[撞破南墙找西墙]用户使用反馈\n\nUID:" + info['uid'] + "\nQQ:" + info['qq'] + "\n昵称:" + info[
            'name'] + "\n\n内容：\n" + content
        message.attach(MIMEText(bodytxt, 'plain', 'utf-8'))

        try:
            smtpObj = smtplib.SMTP()
            smtpObj.connect(mail_host, mail_port)  # 25 为 SMTP 端口号
            smtpObj.login(mail_user, mail_pass)
            smtpObj.sendmail(sender, receivers, message.as_string())

            flash('发送成功，感谢您的反馈！', 'success')
            return render_template('feedback_page.html', user=info)

        except smtplib.SMTPException as e:
            print("Error: 无法发送邮件", str(e))
            return redirect(url_for("500"))

    return render_template('feedback_page.html', user=info)


@app.route('/change_name', methods=['GET', 'POST'])
def change_name_page():
    user = get_session_info()

    if not user['qq']:
        flash("<strong>您还未登录，请先登录！</strong>", 'danger')
        return redirect(url_for("login_page"))

    if request.method == 'POST':
        name = request.form.get('text')

        User.query.filter(User.uid == user['uid']).update(
            {
                'name': name
            }
        )
        db.session.commit()

        flash("修改成功！", 'success')

    return render_template('change_attribute.html', user=user, change_what="昵称")


@app.route('/change_passwd', methods=['GET', 'POST'])
def change_passwd_page():
    user = get_session_info()

    if not user['qq']:
        flash("<strong>您还未登录，请先登录！</strong>", 'danger')
        return redirect(url_for("login_page"))

    if request.method == 'POST':
        passwd = request.form.get('text')

        User.query.filter(User.uid == user['uid']).update(
            {
                'passwd': passwd
            }
        )
        db.session.commit()

        flash("修改成功！", 'success')

    return render_template('change_attribute.html', user=user, change_what="密码")


@app.route('/change_power', methods=['GET', 'POST'])
def change_power_page():
    info = get_session_info()

    if not info['qq']:
        flash("<strong>您还未登录，请先登录！</strong>", 'danger')
        return redirect(url_for("login_page"))

    if info['power'] < 8:
        flash("<strong>您的账户没有该权限！</strong>", 'danger')
        return render_template('change_power.html', user=info)

    if request.method == 'POST':
        uid = request.form.get('uid')
        power = request.form.get('power')

        User.query.filter(User.uid == uid).update(
            {
                'power': int(power)
            }
        )
        db.session.commit()

        flash("修改成功！", 'success')

    return render_template('change_power.html', user=info)


@app.route('/del_pics', methods=['GET', 'POST'])
def del_pics_page():
    user = get_session_info()

    if not user['qq']:
        flash("<strong>您还未登录，请先登录！</strong>", 'danger')
        return redirect(url_for("login_page"))

    if user['power'] <= 7:
        flash("您的账号没有该权限！", 'danger')
        return render_template('del_pics_page.html', user=user)

    if request.method == 'POST':
        date = request.form.get('date')

        date_formed = "".join(date.split('-'))

        path = './uploads'

        for file in os.listdir(path):
            file_path = os.path.join(path, file)
            if os.path.isfile(file_path):
                print(file[0:8])
                if int(file[0:8]) < int(date_formed):
                    os.remove(file_path)

        flash("删除成功！", 'success')

    return render_template("del_pics_page.html", user=user)


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    """
    显示上传的图片
    :param filename:文件名
    :return: 真实文件路径
    """
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.errorhandler(404)
def page_not_found(e):
    qq = session.get('qq')
    power = session.get('power')

    user = {}

    if not qq:
        user = {'qq': "", 'head': "/static/icons/not_logged.png", 'name': "未登录"}

    else:
        user = get_session_info()

    return render_template('404.html', user=user), 404


@app.errorhandler(500)
def internal_server_error(e):
    qq = session.get('qq')
    power = session.get('power')

    user = {}

    if not qq:
        user = {'qq': "", 'head': "/static/icons/not_logged.png", 'name': "未登录"}

    else:
        user = get_session_info()

    return render_template('500.html', user=user), 500


@app.route('/door/add_manager')
def door_add_manager():
    qq = request.args.get('qq')
    passwd = request.args.get('passwd')
    power = request.args.get('power')
    head = request.args.get('head')
    name = request.args.get('name')
    notes = request.args.get('notes')

    if not qq:
        qq = "admin"

    if not passwd:
        passwd = "Xiqiang123"

    query = User.query.filter_by(qq=qq).first()

    if query:
        return "已经注册过该用户"

    manager = User(
        qq=qq,
        passwd=passwd,
        head="/static/headimg.jpg",
        name=qq,
        power="9"
    )

    if head:
        manager.head = head

    if name:
        manager.name = name

    if power:
        manager.power = power

    if notes:
        manager.notes = notes

    db.session.add(manager)
    db.session.commit()

    return "注册成功！"


@app.route('/door/users_list')
def door_users_list():
    page = request.args.get('page')

    if page:
        page = int(page)
    else:
        page = 1

    limit_top = page * 20
    limit_bottom = (page - 1) * 20

    res = User.query.filter(User.uid.between(limit_bottom, limit_top)).all()

    reslist = []
    for i in res:
        data = {
            'uid': i.uid,
            'qq': i.qq,
            'head': i.head,
            'name': i.name,
            'power': i.power,
            'passwd': i.passwd
        }

        reslist.append(data)

    return render_template("users_list.html", reslist=reslist, page=page)


@app.route('/door/user')
def door_user():
    qq = request.args.get('qq')
    uid = request.args.get('uid')

    if uid:
        res = User.query.filter_by(uid=uid).first()

    elif qq:
        res = User.query.filter_by(qq=qq).first()

    else:
        return "没有指定用户！请指定用户的uid和qq！"

    data = {
        'UID': res.uid,
        'QQ': res.qq,
        'Passwd': res.passwd,
        'Head': res.head,
        'Name': res.name,
        'Power': res.power,
        'Notes': res.notes
    }

    return data


@app.route('/door/message')
def door_message():
    mid = request.args.get('mid')

    if not mid:
        return "没有指定MID！"

    res = Message.query.filter_by(mid=mid).first()

    data = {
        'mid': res.mid,
        'uid': res.uid,
        'content': res.content,
        'time': res.time,
        'type': res.type,
        'status': res.status,
        'comments': res.comments,
        'images': res.images,
        'likes': res.likes,
        'notes': res.notes
    }

    return data


@app.route('/api/approve_message')
def api_approve_message():
    mid = int(request.args.get('mid'))
    uid = int(request.args.get('uid'))

    query = Message.query.filter_by(mid=mid).first()

    flag = False
    like_list = []
    like_num = 0

    origin = query.likes.split("|")
    for i in range(len(origin)):
        if origin[i] == str(uid):
            flag = True
        else:
            like_list.append(str(origin[i]))

    if flag:
        likes = "|".join(like_list)
        like_num = len(like_list)

    else:
        if not query.likes:
            likes = str(uid)
        else:
            likes = query.likes + "|" + str(uid)

        if origin == ['']:
            like_num = 1
        else:
            like_num = len(origin) + 1

    Message.query.filter(Message.mid == mid).update(
        {
            'likes': likes
        }
    )

    db.session.commit()

    print(like_num)

    return str(like_num)


@app.route('/api/approve_news')
def api_approve_news():
    nid = int(request.args.get('nid'))
    uid = int(request.args.get('uid'))

    query = News.query.filter_by(nid=nid).first()

    flag = False
    like_list = []
    like_num = 0

    origin = query.likes.split("|")
    for i in range(len(origin)):
        if origin[i] == str(uid):
            flag = True
        else:
            like_list.append(str(origin[i]))

    if flag:
        likes = "|".join(like_list)
        like_num = len(like_list)

    else:
        if not query.likes:
            likes = str(uid)
        else:
            likes = query.likes + "|" + str(uid)

        if origin == ['']:
            like_num = 1
        else:
            like_num = len(origin) + 1

    News.query.filter(News.nid == nid).update(
        {
            'likes': likes
        }
    )

    db.session.commit()

    print(like_num)

    return str(like_num)


if __name__ == '__main__':
    app.run(port=80)
