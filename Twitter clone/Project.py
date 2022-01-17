from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_mysqldb import MySQL
from datetime import timedelta, date, datetime
import os
from werkzeug.utils import secure_filename

now = datetime.now()
current_time = now.strftime("%H:%M:%S")
current_date = now.strftime("%y-%m-%d")

app = Flask(__name__)
app.secret_key = "ssss"

app.config["MYSQL_HOST"] = 'localhost'
app.config["MYSQL_USER"] = 'root'
app.config["MYSQL_PASSWORD"] = 'bscs201957'
app.config["MYSQL_DB"] = 'se_project'

mysql = MySQL(app)

path = "static"
app.config["UPLOAD_FOLDER"] = path
path_of_style = os.path.join(path, "style.css")


# ========================================================================INDEX

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == "POST":
        user_data = request.form
        user_First_name = user_data['First-Name']
        user_Last_name = user_data['Last-Name']
        user_email = user_data['email']
        user_password = user_data["Password"]
        user_phone = user_data['Phone Numer']
        user_name = user_data['user-name']
        file = request.files['user-img']

        file_name = file.filename
        file_name = secure_filename(file_name)
        file.save(os.path.join(path, file_name))

        image = os.path.join(path, file_name)
        with open(image, 'rb') as file:
            binaryData = file.read()

        # ------ saving data in database

        cur = mysql.connection.cursor()
        cur.execute('select * from user_data where User_name=%s', [user_name])
        result = cur.fetchall()
        if len(result) != 0:
            flash("user name is already taken")
            redirect(url_for('index'))
        else:
            print("dddd")
            cur.execute('insert into user_data(id,F_name,L_name,User_name,email,pasw,phone_num,image) \
            values (NULL,%s,%s,%s,%s,%s,%s,%s)',
                        (user_First_name, user_Last_name, user_name, user_email, user_password, user_phone, binaryData))
            cur.connection.commit()
            cur.close()
            os.remove(image)
            return redirect("/3rd")
    return render_template('projIndex.html', message="")


# ========================================================================================LOGIN
@app.route("/3rd", methods=['POST', 'GET'])
def login():
    if request.method == "POST":
        login_data = request.form
        name = login_data["User-Name"]
        password = login_data["Password"]
        cur = mysql.connection.cursor()
        cur.execute("select * from user_data where User_Name=%s and pasw = %s", (name, password))
        user = cur.fetchall()
        if len(user) != 0:
            cur.execute("select id,image from user_data where User_Name=%s", [name])
            result = cur.fetchone()
            print(len(result))
            # id = result[0]
            image = result[1]
            filepath = os.path.join(path, (name + '.png'))
            with open(filepath, 'wb') as file:
                file.write(image)

            return redirect(url_for('dashboard', name=name, image=filepath))

    return render_template('login.html', )


# _______________>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Dashboard

@app.route("/dashboard", methods=['GET', 'POST'])
def dashboard():
    name = request.args.get("name")
    image = request.args.get("image")
    posts = []
    if request.method == "POST":
        tweet_data = request.form
        text_ = tweet_data["text_"]
        photo = request.files["img"]

        # ..........checking while tweet is empty?...................................................................

        if len(text_) < 1 and photo.filename == '':
            print("empty tweet")
            return redirect(url_for('dashboard', name=name, image=image))
        else:
            cur = mysql.connection.cursor()
            cur.execute("select F_name,image from user_data where User_Name=%s", [name])
            result = cur.fetchone()
            f_name = result[0]
            user_img = result[1]
            print(user_img)

            if photo.filename == '':
                binaryData = None
            else:
                file_name = photo.filename
                file_name = secure_filename(file_name)
                photo.save(os.path.join(path, file_name))

                image1 = os.path.join(path, file_name)
                with open(image1, 'rb') as file:
                    binaryData = file.read()

            cur.execute('insert into post(post_id,user_img,F_name,user_name,text_,img,date_,time_)\
                        values(NULL,%s,%s,%s,%s,%s,%s,%s)', (user_img, f_name, name, text_, binaryData, current_date,
                                                             current_time))

            cur.execute('insert into notification(id,user_name,message,image,time_,date_,name_)\
                        values(NULL,%s,%s,%s,%s,%s,%s)', (name, "has tweeted on ", user_img, current_time,
                                                          current_date, f_name))
            cur.connection.commit()
            cur.close()

            return redirect(url_for('dashboard', name=name, image=image))

    else:
        cur = mysql.connection.cursor()
        cur.execute('select * from post order by date_ desc,time_ DESC')
        lists = cur.fetchall()

        for i in lists:
            filepath = os.path.join(path, (str(i[0]) + i[3] + '.png'))
            with open(filepath, 'wb') as file:
                file.write(i[1])

            user_img = filepath
            if i[5] is None:
                post_img = None
            else:
                filepath = os.path.join(path, (i[3] + str(i[0]) + '.png'))
                with open(filepath, 'wb') as file:
                    file.write(i[5])
                post_img = filepath
            posts.append((i[0], user_img, i[2], i[3], i[4], post_img, i[6], i[7]))

    return render_template('dashboard1.html', path_of_style=path_of_style, image=image, len=len(posts), name=name,
                           posts=posts)


# @app.before_request
def make_session_permanent():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(seconds=100)


# =================================================================================PROFILE
@app.route("/profile", methods=['GET', 'POST'])
def profile():
    name = request.args.get('name')
    image = request.args.get('image')
    print(name)
    cur = mysql.connection.cursor()
    cur.execute("select * from user_data where User_name = %s", [name])
    profiles = cur.fetchone()
    print(profiles[1])
    user_photo = profiles[7]
    filepath = os.path.join(path, (name + '.png'))
    with open(filepath, 'wb') as file:
        file.write(user_photo)

    list_of_profile = [profiles[1], profiles[2], profiles[4], profiles[5], profiles[6], filepath]

    return render_template("profile.html", path=os.path.join(path, "profile.css"), image=image, name=name,
                           list=list_of_profile)


# =================================================Followers adding in database
@app.route('/friend')
def friend():
    name = request.args.get('name')
    f_name = request.args.get('f_name')
    image = request.args.get('image')

    cur = mysql.connection.cursor()
    cur.execute('select * from friends where (user_name=%s and friend_name=%s)', (name, f_name))
    result = cur.fetchall()
    print(len(result))
    if len(result) != 0:
        cur.execute("delete from friends where( user_name=%s and friend_name=%s)", (name, f_name))
        cur.connection.commit()
        cur.close()
    else:
        cur.execute("select F_name,L_name,image from user_data where User_Name = %s", [f_name])
        result = cur.fetchone()
        cur.execute("insert into friends(id,user_name,friend_name,pic,F_name,L_name) values(NULL,%s,%s,%s,%s,%s)",
                    (name, f_name, result[2], result[0], result[1]))

        cur.connection.commit()
        cur.close()
    return redirect(url_for('dashboard', name=name, image=image))


# =========================================FOLLOWERS ID
@app.route("/ids")
def follower_ids():
    name = request.args.get("name")
    image = request.args.get("image")
    follower_id = request.args.get('id_')
    posts1 = []
    cur = mysql.connection.cursor()
    cur.execute('select F_name,L_name,image from user_data where user_name=%s', [follower_id])
    result = cur.fetchone()

    filepath = os.path.join(path, (follower_id + '.png'))
    with open(filepath, 'wb') as file:
        file.write(result[2])

    friend_img = filepath

    list_of_userID = (result[0], result[1], friend_img, follower_id)
    cur.execute('select * from post where user_name = %s order by date_ desc,time_ DESC', [follower_id])
    lists = cur.fetchall()

    for i in lists:
        filepath = os.path.join(path, (str(i[0]) + i[3] + '.png'))
        with open(filepath, 'wb') as file:
            file.write(i[1])

        user_img = filepath
        if i[5] is None:
            post_img = None
        else:
            filepath = os.path.join(path, (i[3] + str(i[0]) + '.png'))
            with open(filepath, 'wb') as file:
                file.write(i[5])
            post_img = filepath
        posts1.append((i[0], user_img, i[2], i[3], i[4], post_img, i[6], i[7]))

    return render_template('friends_id.html', style=os.path.join(path, 'friend_id.css'), image=image, len=len(posts1),
                           name=name,
                           posts=posts1,
                           list=list_of_userID)


# =======================================================================Followers
@app.route('/followings')
def followings():
    name = request.args.get('name')
    image = request.args.get('image')
    followers = []
    cur = mysql.connection.cursor()
    cur.execute('select * from friends where user_name=%s', [name])
    result = cur.fetchall()

    for i in result:
        filepath = os.path.join(path, (i[2] + '.png'))
        with open(filepath, 'wb') as file:
            file.write(i[3])
        user_img = filepath

        followers.append((user_img, i[4], i[5], i[2]))
    print(followers)
    return render_template('friends.html', name=name, path_of_style1=os.path.join(path, 'friends.css'), image=image,
                           len=len(followers),
                           list=followers)


# ========================================================Notifications
@app.route("/notification")
def notification():
    name = request.args.get("name")
    image = request.args.get("image")
    cur = mysql.connection.cursor()
    cur.execute("select * from notification where NOT user_name = %s order by date_ desc,time_ desc LIMIT 15", [name])
    list_of_notifications = cur.fetchall()
    notifications = []

    for i in list_of_notifications:
        filepath = os.path.join(path, (i[1] + '.png'))
        with open(filepath, 'wb') as file:
            file.write(i[3])
        user_img = filepath

        notifications.append((user_img, i[6], i[4], i[5], i[2], i[1]))

    return render_template('notification.html', name=name, image=image, list=notifications, len=len(notifications),
                           path_of_style2=os.path.join(path, 'notification.css'))


# @app.route('/search')
# def search():
#     name = request.args.get('name')
#     image = request.args.get('image')
#     searched = []
#     cur = mysql.connection.cursor()
#     cur.execute('select * from friends where user_name like %s', (name + "%"))
#     result = cur.fetchall()
#
#     for i in result:
#         filepath = os.path.join(path, (i[2] + '.png'))
#         with open(filepath, 'wb') as file:
#             file.write(i[3])
#         user_img = filepath
#
#         followers.append((user_img, i[4], i[5], i[2]))
#     print(followers)
#     return render_template('search.html', name=name, path_of_style1=os.path.join(path, 'friends.css'), image=image,
#                            len=len(followers),
#                            list=followers)
