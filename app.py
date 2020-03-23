from flask import Flask, render_template, redirect, request, url_for, session
import vk_api
from urllib import parse
from uuid import uuid4

app = Flask(__name__)

app_id = 0
client_secret = '-'
app_url = "http://justanivan.pythonanywhere.com/"
app.secret_key = "12345ABA54321"

vk_sessions = {}

@app.route("/", methods=['GET', 'POST'])
def home():
    if 'uid' not in session or session['uid'] not in vk_sessions:
        uid = uuid4()
        session['uid'] = uid
        vk_session = vk_api.VkApi(app_id=app_id, client_secret=client_secret)
        vk_sessions[uid] = vk_session
    else:
        vk_session = vk_sessions[session['uid']]

    search_result = []
    if request.method == 'POST':
        if request.form.getlist("submit")[0] == "Log in":
            method_params = {"client_id": app_id,
                             "redirect_uri": F"{app_url}{url_for('route_auth')}",
                             "display": "popup",
                             "scope": "friends",
                             "response_type": "code"}
            url = "https://oauth.vk.com/authorize?"
            url += parse.urlencode(method_params)
            return redirect(url, code=302)

        if request.form.getlist("submit")[0] == "search" and vk_session.token['access_token']:
            vk = vk_session.get_api()
            search_text = request.form.getlist('text')[0]
            search_result = vk.friends.search(user_id=vk_session.token['user_id'], q=search_text)
            search_result = [item['first_name'] + ' ' + item['last_name'] for item in search_result['items']]

        if request.form.getlist("submit")[0] == "Log Out":
            del vk_sessions[session['uid']]
            session.pop('uid', None)
            return render_template("index.html")

    if vk_session.token['access_token']:
        vk = vk_session.get_api()
        user_info = vk.users.get(user_id=vk_session.token['user_id'], fields='photo_max_orig')[0]
        user_full_name = user_info['first_name'] + ' ' + user_info['last_name']
        photo = user_info['photo_max_orig']
        vk_friends_count = vk.friends.get()['count']
        return render_template("index.html", photo=photo, search_result=search_result,
                               user_full_name=user_full_name, vk_friends_count=vk_friends_count)

    return render_template("index.html")


@app.route('/auth', methods=['GET', 'POST'])
def route_auth():
    vk_session = vk_sessions[session['uid']]
    if request.method == "GET":
        code = request.args['code']
        redirect_url = F"{app_url}{url_for('route_auth')}"
        try:
            vk_session.code_auth(code, redirect_url)
        except vk_api.AuthError as error_msg:
            print(error_msg)

    return redirect(url_for("home"))


if __name__ == '__main__':
    app.run(debug=True)
