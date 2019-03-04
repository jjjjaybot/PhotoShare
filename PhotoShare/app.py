######################################
# author ben lawson <balawson@bu.edu> 
# Edited by: Baichuan Zhou (baichuan@bu.edu) and Craig Einstein <einstein@bu.edu>
######################################
# Some code adapted from 
# CodeHandBook at http://codehandbook.org/python-web-application-development-using-flask-and-mysql/
# and MaxCountryMan at https://github.com/maxcountryman/flask-login/
# and Flask Offical Tutorial at  http://flask.pocoo.org/docs/0.10/patterns/fileuploads/
# see links for further understanding
###################################################

import flask
from flask import Flask, Response, request, render_template, redirect, url_for
from flaskext.mysql import MySQL
import flask.ext.login as flask_login
import re
import datetime

# for image uploading
from werkzeug import secure_filename
import os, base64

mysql = MySQL()
app = Flask(__name__)
app.secret_key = 'data'

# These will need to be changed according to your credentials
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = 'caijiazi'
app.config['MYSQL_DATABASE_DB'] = 'photoshare'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql.init_app(app)

# use Flask's Login Manager
login_manager = flask_login.LoginManager()
login_manager.init_app(app)

# Cursor library is used to manage attributes of data
# returned from a data source (a result set). Keeps track of rows.
conn = mysql.connect()


def getUserList():
    cursor = conn.cursor()
    # executes the given database operation (query or command)
    # returns a list of tuples
    cursor.execute("SELECT email from Users")
    return cursor.fetchall()


class User(flask_login.UserMixin):
    pass


# reloading a user from the session
@login_manager.user_loader
def user_loader(email):
    users = getUserList()
    if not (email) or email not in str(users):
        return
    user = User()
    user.id = email
    return user


@login_manager.request_loader
def request_loader(request):
    users = getUserList()
    email = request.form.get('email')
    if not (email) or email not in str(users):
        return
    user = User()
    user.id = email
    cursor = mysql.connect().cursor()
    cursor.execute("SELECT password FROM Users WHERE email = '{0}'".format(email))
    data = cursor.fetchall()
    pwd = str(data[0][0])
    user.is_authenticated = request.form['password'] == pwd
    return user


"""
USER AUTHENTICATION
"""


def isEmailUnique(email):
    # use this to check if a email has already been registered
    cursor = conn.cursor()
    if cursor.execute("SELECT email  FROM Users WHERE email = '{0}'".format(email)):
        # this means there are greater than zero entries with that email
        return False
    else:
        return True


@app.route("/register", methods=['GET'])
def register():
    return render_template('register.html', supress='True')


@app.route("/register", methods=['POST'])
def register_user():
    try:
        password = request.form.get('password')
        email = request.form.get('email')
        firstName = request.form.get('firstName')
        lastName = request.form.get('lastName')
        hometown = request.form.get('hometown')
        gender = request.form.get('gender')
        dateOfBirth = request.form.get('dateOfBirth')
    except:
        print("couldn't find all tokens")
        return flask.redirect(flask.url_for('register'))
    cursor = conn.cursor()
    test = isEmailUnique(email)
    if test:
        print(cursor.execute(
            "INSERT INTO Users (email, password, firstName, lastName, hometown, gender, dateOfBirth) VALUES ('{0}', '{1}', '{2}', '{3}', '{4}', '{5}', '{6}')".format(
                email, password, firstName, lastName, hometown, gender, dateOfBirth)))
        conn.commit()
        # log user in
        user = User()
        user.id = email
        flask_login.login_user(user)
        return flask.redirect(flask.url_for('protected'))
    else:
        print("email is not unique")
        return flask.redirect(flask.url_for('register'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if flask.request.method == 'GET':
        return '''
    			   <form action='login' method='POST'>
    				<input type='text' name='email' id='email' placeholder='email'></input>
    				<input type='password' name='password' id='password' placeholder='password'></input>
    				<input type='submit' name='submit'></input>
    			   </form></br>
    		   <a href='/'>Home</a>
    			   '''
    email = flask.request.form.get('email')
    cursor = conn.cursor()
    if cursor.execute("SELECT password FROM Users WHERE email = '{0}'".format(email)):
        data = cursor.fetchall()
        pwd = str(data[0][0])
        if flask.request.form['password'] == pwd:
            user = User()
            user.id = email
            flask_login.login_user(user)  # okay login in user
            return flask.redirect(flask.url_for('protected'))  # protected is a function defined in this file

    # information did not match
    return "<a href='/login'>Try again</a>\
    			</br><a href='/register'>or make an account</a>"


@app.route('/logout')
def logout():
    flask_login.logout_user()
    return render_template('hello.html', message = 'Logged out')


@login_manager.unauthorized_handler
def unauthorized_handler():
    return render_template('unauth.html')


"""
MAIN PAGE
"""


def getAllPhotos():
    cursor = conn.cursor()
    # get the imfdata and caption
    cursor.execute("SELECT imgdata, caption, user_id FROM Pictures");
    R = cursor.fetchall()
    row = [(item[0], item[1]) for item in R]
    # get the owners of the pictures
    userNames = [getUserNameFromId(item[2]) for item in R]
    # get pictire ids
    cursor.execute("SELECT picture_id FROM Pictures");
    I = cursor.fetchall()
    ids = [item[0] for item in I]
    return row, userNames, ids


def getUserNameFromId(user_id):
    cursor = conn.cursor()
    cursor.execute("SELECT firstName  FROM Users WHERE user_id = '{0}'".format(user_id))
    return cursor.fetchone()[0]


@app.route("/", methods=['GET'])
def hello():
    p = userActivity()
    print(getLikes(getAllPhotos()[2])[0])
    return render_template('hello.html',
                           photos=getAllPhotos()[0],
                           userNames=getAllPhotos()[1],
                           picture_ids=getAllPhotos()[2],
                           comments=getComments(getAllPhotos()[2]),
                           mostPopularTags=mostPopularTags(),
                           likes=getLikes(getAllPhotos()[2])[0],
                           usersLiked=getLikes(getAllPhotos()[2])[1]
                           )


"""
PROFILE PAGE
"""


@app.route("/profile", methods=['GET'])
@flask_login.login_required
def protected():
    email = flask_login.current_user.id
    uid = getUserIdFromEmail(email)
    print(flask_login.current_user.id)
    return render_template('profile.html',
                           name=email,
                           albums=getUsersAlbums(uid),
                           friends=getFriendsList(uid),
                           recommendedPhotos=picturesRecommendation(),
                           activeUsers=userActivity())


"""
FRIENDS MANAGEMENT
"""


def getFriendsList(uid):
    cursor = conn.cursor()
    cursor.execute("SELECT friend_id  FROM Friends WHERE user_id = '{0}'".format(uid))
    R = cursor.fetchall()
    friendsIds = [item[0] for item in R]
    F = []
    for i in friendsIds:
        cursor.execute("SELECT firstName, lastName FROM Users WHERE user_id = '{0}'".format(i))
        F.append(cursor.fetchone())
    friendsList = [(str(item[0]), str(item[1])) for item in F]
    return friendsList


def getUserNameFromEmail(email):
    cursor = conn.cursor()
    cursor.execute("SELECT firstName, lastName  FROM Users WHERE email = '{0}'".format(email))
    T = cursor.fetchone()
    T = [str(item) for item in T]
    return T


# This method takes an email and returns the first and last names of the user
@app.route('/results', methods=['POST', 'GET'])
@flask_login.login_required
def results():
    if request.method == 'POST':
        friendsEmail = request.form.get('friendsEmail')
        credentials = getUserNameFromEmail(friendsEmail)
        friend_id = getUserIdFromEmail(friendsEmail)
        return render_template('profile.html', credentials=credentials, friend_id=friend_id)
    else:
        return flask.redirect(flask.url_for('protected'))


@app.route('/add_friend', methods=['POST'])
@flask_login.login_required
def add_friend():
    friend_id = request.form.get('friend_id')
    user_id = getUserIdFromEmail(flask_login.current_user.id)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO Friends (user_id, friend_id) VALUES ('{0}', '{1}')".format(user_id, friend_id))
    conn.commit()
    return flask.redirect(flask.url_for('protected'))


"""
COMMENTS MANAGEMENT
"""


def getComments(pids):
    cursor = conn.cursor()
    Comments = []
    for id in pids:
        cursor.execute("SELECT content, owner FROM Comments WHERE picture_id = '{0}'".format(id))
        T = cursor.fetchall()
        C = [(str(item[0]), str(getUserNameFromId(int(item[1])))) for item in T]
        Comments.append(C)
    return Comments


@app.route('/add_comment', methods=['GET', 'POST'])
def picture_id():
    pid = request.form.get('picture_id')
    picture_id = int(pid)
    if request.method == 'POST':
        user_id = getUserIdFromEmail(flask_login.current_user.id)
        content = request.form.get('comment')
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO Comments (content, owner, picture_id) VALUES ('{0}', '{1}', '{2}')".format(content, user_id,
                                                                                                    picture_id))
        conn.commit()
        return flask.redirect(flask.url_for('hello'))
    else:
        return flask.redirect(flask.url_for('hello'))


"""
LIKES MANAGEMENT
"""


def getLikes(pids):
    cursor = conn.cursor()
    Likes = []
    Users = []
    for id in pids:
        cursor.execute("SELECT COUNT(*) FROM Likes WHERE picture_id = '{0}'".format(id))
        L = cursor.fetchone()
        L = int(L[0])
        Likes.append(L)
        cursor.execute("SELECT user_id FROM Likes WHERE picture_id = '{0}'".format(id))
        U = cursor.fetchall()
        U = [str(getUserNameFromId(int(item[0]))) for item in U]
        Users.append(U)
    print(Users)
    return Likes, Users


@app.route('/add_like', methods=['GET', 'POST'])
def add_like():
    pid = request.form.get('picture_id')
    picture_id = int(pid)
    if request.method == 'POST':
        user_id = getUserIdFromEmail(flask_login.current_user.id)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO Likes (picture_id, user_id) VALUES ('{0}', '{1}')".format(picture_id, user_id))
        conn.commit()
        return flask.redirect(flask.url_for('hello'))
    else:
        return flask.redirect(flask.url_for('hello'))


"""
ALBUM MANAGEMENT
"""


def getUserIdFromEmail(email):
    cursor = conn.cursor()
    cursor.execute("SELECT user_id  FROM Users WHERE email = '{0}'".format(email))
    return cursor.fetchone()[0]


def getUsersAlbums(uid):
    cursor = conn.cursor()
    cursor.execute("SELECT albumName FROM Albums WHERE user_id = '{0}'".format(uid))
    R = cursor.fetchall()
    row = [item[0] for item in R]
    return row


@app.route('/album_creation', methods=['GET', 'POST'])
@flask_login.login_required
def create_album():
    if request.method == 'POST':
        user_id = getUserIdFromEmail(flask_login.current_user.id)
        albumName = request.form.get('albumName')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO Albums (albumName, user_id) VALUES ('{0}', '{1}')".format(albumName, user_id))
        conn.commit()
        return flask.redirect(flask.url_for('protected'))
    else:
        return flask.redirect(flask.url_for('protected'))


"""
PHOTO MANAGEMENT
"""
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


def getAlbumIdFromName(albumName, user_id):
    cursor = conn.cursor()
    cursor.execute(
        "SELECT album_id  FROM Albums WHERE albumName = '{0}' AND user_id = '{1}'".format(albumName, user_id))
    return cursor.fetchone()[0]


def getAlbumsPhotos(aid):
    cursor = conn.cursor()
    cursor.execute("SELECT imgdata, caption FROM Pictures WHERE album_id = '{0}'".format(aid))
    Photos = cursor.fetchall()
    P = cursor.execute("SELECT picture_id FROM Pictures WHERE album_id = '{0}'".format(aid))
    p = cursor.fetchall()
    pids = [item[0] for item in p]
    return Photos, pids


@app.route("/photos/<albumName>", methods=['GET'])
@flask_login.login_required
def show_photos(albumName):
    user_id = getUserIdFromEmail(flask_login.current_user.id)
    album_id = getAlbumIdFromName(albumName, user_id)
    tags = getTags(getAlbumsPhotos(album_id)[1])
    return render_template('photos.html',
                           albumName=albumName,
                           message='Photo uploaded!',
                           photos=getAlbumsPhotos(album_id)[0],
                           pids=getAlbumsPhotos(album_id)[1],
                           tags=getTags(getAlbumsPhotos(album_id)[1])
                           )


@app.route('/delete_photo', methods=['POST'])
@flask_login.login_required
def delete_photo():
    albumName = request.values.get('albumName')
    print(albumName)
    pic_id = request.values.get('pic_id')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Pictures WHERE picture_id = '{0}'".format(pic_id))
    conn.commit()
    return flask.redirect(flask.url_for('show_photos', albumName=albumName))

# Test Showing Photos
@app.route("/showPhotos", methods=['GET'])
def showPhotos():
    # get photopath from the database: SELECT photopath FROM PHOTOS WHERE USER_ID = .....
    photopath = "/static/1.jpg"
    return render_template('testShowPhoto.html', photopath = photopath)


@app.route('/photos/upload/<albumName>/', methods=['GET', 'POST'])
@flask_login.login_required
def upload_file(albumName):
    if request.method == 'POST':
        uid = getUserIdFromEmail(flask_login.current_user.id)
        imgfile = request.files['photo']
        album_id = getAlbumIdFromName(albumName, uid)
        caption = request.form.get('caption')
        photo_data = base64.standard_b64encode(imgfile.read())
        photopath = 
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO Pictures (imgdata, user_id, caption, album_id) VALUES ('{0}', '{1}', '{2}', '{3}')".format(
                photo_data, uid, caption, album_id))
        conn.commit()
        return render_template('photos.html', name=flask_login.current_user.id, message='Photo uploaded!',
                               photos=getAlbumsPhotos(album_id)[0], album=albumName)
    # The method is GET so we return a  HTML form to upload the a photo.
    else:
        return render_template('upload.html', album=albumName)


@app.route("/photos/remove_album/<albumName>", methods=['GET', 'POST'])
@flask_login.login_required
def remove_album(albumName):
    if request.method == 'POST':
        uid = getUserIdFromEmail(flask_login.current_user.id)
        album_id = getAlbumIdFromName(albumName, uid)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM Albums WHERE album_id = '{0}'".format(album_id))
        conn.commit()
        return render_template('profile.html', name=flask_login.current_user.id, album=albumName)
    # The method is GET so we return a  HTML form to upload the a photo.
    else:
        return render_template('remove_album.html', album=albumName)


"""
TAG MANAGEMENT
"""


def getTags(pids):
    cursor = conn.cursor()
    Tags = []
    for id in pids:
        cursor.execute("SELECT word FROM Tags WHERE picture_id = '{0}'".format(id))
        T = cursor.fetchall()
        C = [(str(item[0])) for item in T]
        Tags.append(C)
    return Tags


# returns all the pictures with a given tag
def allTags(word):
    cursor = conn.cursor()
    cursor.execute("SELECT picture_id FROM Tags WHERE word = '{0}'".format(word))
    P = cursor.fetchall()
    pids = [(int(item[0])) for item in P]
    photos = []
    for id in pids:
        cursor.execute("SELECT imgdata FROM Pictures WHERE picture_id = '{0}'".format(id));
        R = cursor.fetchall()
        C = [item[0] for item in R]
        photos.append(C)
    return photos


def UsersTags(word, uid):
    cursor = conn.cursor()
    cursor.execute("SELECT picture_id FROM Tags WHERE word = '{0}'".format(word))
    P = cursor.fetchall()
    pids = [(int(item[0])) for item in P]
    photos = []
    for id in pids:
        cursor.execute("SELECT imgdata FROM Pictures WHERE user_id = '{0}' AND picture_id = '{1}'".format(uid, id));
        C = cursor.fetchone()
        if C is not None:
            photos.append(C)
    return photos


@app.route('/add_tag', methods=['GET', 'POST'])
@flask_login.login_required
def add_tag():
    if request.method == 'POST':
        user_id = getUserIdFromEmail(flask_login.current_user.id)
        albumName = request.values.get('albumName')
        album_id = getAlbumIdFromName(albumName, user_id)

        p = request.values.get('pid')
        picture_id = int(p)
        word = request.form.get('word')

        cursor = conn.cursor()
        cursor.execute("INSERT INTO Tags (word, picture_id) VALUES ('{0}', '{1}')".format(word, picture_id))
        conn.commit()
        return render_template('profile.html', albums=getUsersAlbums(user_id))
    else:
        return render_template('profile.html', albums=getUsersAlbums(user_id))


@app.route("/photos/tags/<word>", methods=['GET'])
@flask_login.login_required
def alltags(word):
    user_id = getUserIdFromEmail(flask_login.current_user.id)
    word = str(word)
    photos = allTags(word)
    return render_template('tags.html',
                           photos=allTags(word),
                           usersPhotos=UsersTags(word, user_id),
                           word=word)


# returns 5 most popular tags
def mostPopularTags():
    cursor = conn.cursor()
    cursor.execute("SELECT word FROM Tags GROUP BY (word) HAVING COUNT(*)>0 ORDER BY COUNT(*) DESC LIMIT 5")
    T = cursor.fetchall()
    tags = [(str(item[0])) for item in T]
    return tags


# show the pictures with a certain tag
@app.route("/public_tags/<word>", methods=['GET'])
def public_tags(word):
    word = str(word)
    return render_template('public_tags.html',
                           photos=allTags(word),
                           word=word
                           )


# returns pids of pictures with given tags
def searchByTagPid(tags):
    tags = re.split("\s|,|:|\.|!|\?|@|#|$|%|\(|\)|-|_|\+|=|{|}|\[|\]|\"", tags)
    cursor = conn.cursor()
    pic_ids = []
    for tag in tags:
        cursor.execute("SELECT picture_id FROM Tags WHERE word = '{0}'".format(tag));
        T = cursor.fetchall()
        T = [item[0] for item in T]
        pic_ids.append(T)
    intersection = []
    if len(pic_ids) >= 2:
        intersection = list(set(pic_ids[0]) & set(pic_ids[1]))
    else:
        intersection = pic_ids[0]
    for i in range(len(pic_ids) - 2):
        intersection = list(set(intersection) & set(pic_ids[i]))
    return intersection


def searchByTag(tags):
    cursor = conn.cursor()
    intersection = searchByTagPid(tags);
    photos = []
    for id in intersection:
        cursor.execute("SELECT imgdata FROM Pictures WHERE picture_id = '{0}'".format(id));
        R = cursor.fetchall()
        C = [item[0] for item in R]
        photos.append(C)
    return photos


@app.route('/search_by_tag', methods=['GET', 'POST'])
def search_by_tag():
    if request.method == 'POST':
        word = request.form.get('tag_name')
        word = str(word)
        return render_template('hello.html', search_tags=searchByTag(word))
    else:
        return render_template('hello.html')


"""
RECOMMENDATIONS
"""


def mostPopularUsersTags():
    uid = getUserIdFromEmail(flask_login.current_user.id)
    cursor = conn.cursor()
    # select only current user's tags
    cursor.execute(
        "SELECT word FROM Tags, Pictures WHERE Tags.picture_id = Pictures.picture_id and user_id='{0}' GROUP BY (word) HAVING COUNT(*)>0 ORDER BY COUNT(*) DESC LIMIT 5".format(
            uid))
    T = cursor.fetchall()
    T = [str(item[0]) for item in T]
    return T


def picturesRecommendation():
    uid = getUserIdFromEmail(flask_login.current_user.id)
    popTags = mostPopularUsersTags()
    cursor = conn.cursor()
    cursor.execute("SELECT picture_id FROM Pictures");
    T = cursor.fetchall()
    pids = [int(item[0]) for item in T]
    Count = [0] * len(pids)  # store the rating of pictures
    photos = []
    for i in range(len(pids)):
        for tag in popTags:
            # make sure that a picture has a tag and the word is equal to one of the popular tags
            cursor.execute("SELECT COUNT(*) FROM Tags WHERE picture_id = '{0}' AND word = '{1}'".format(pids[i], tag));
            C = cursor.fetchone()
            C = int(C[0])
            if C > 0:
                Count[i] = Count[i] + 1
    # (pid, rating) sorted in the descending order
    picRating = [(pids[i], Count[i]) for i in range(len(pids))]
    picRating = sorted(picRating, key=lambda x: (-x[1], x[0]))
    picRating = picRating[:5]  # pic 5 most popular ones
    for i in range(len(picRating)):
        cursor.execute("SELECT imgdata FROM Pictures WHERE picture_id = '{0}'".format(picRating[i][0]))
        R = cursor.fetchall()
        C = [item[0] for item in R]
        photos.append(C)
    return photos


def tagRecommendation(tags):
    cursor = conn.cursor()
    # show pids of pictures that have given tags
    pids = searchByTagPid(tags)
    # take the tags of these photos
    tags = []
    for id in pids:
        cursor.execute("SELECT word FROM Tags WHERE picture_id = '{0}'".format(id))
        T = cursor.fetchall()
        T = [str(item[0]) for item in T]
        tags = tags + T
    print(tags)
    return 0


@app.route('/tag_recommend', methods=['GET', 'POST'])
@flask_login.login_required
def tag_recommend():
    if request.method == 'POST':
        tags = request.form.get('words')
        print(tags)
        recommendedTags = tagRecommendation(tags)
        return render_template('photos.html', tagsRecommended=tagRecommendation(tags))
    else:
        return render_template('photos.html', tagsRecommended=tagRecommendation(tags))


"""
USER ACTIVITY 
"""


def userActivity():
    cursor = conn.cursor()
    # returns a list of tuples (uid, count of pictures posted)
    cursor.execute(
        "SELECT Users.user_id, COUNT(picture_id) FROM Users, Pictures WHERE Users.user_id=Pictures.user_id GROUP BY Users.user_id ORDER BY COUNT(picture_id) DESC LIMIT 5")
    T = cursor.fetchall()
    T = [getUserNameFromId(item[0]) for item in T]
    return T


if __name__ == "__main__":
    # this is invoked when in the shell you run
    # $ python app.py
    app.run(port=5000, debug=True)





