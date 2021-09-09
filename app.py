from mysql.connector import connect, Error
from flask import Flask, jsonify, request

OPTIONS_FILE_PATH = "options.txt"
DB_NAME = "sample_database"


class ControllerRAM:
    def __init__(self, options):
        self.options = options
        self.db = []
        self.init_db()

    def init_db(self):
        self.db = []
        return self.db

    def get_user(self, user_id):
        for entry in self.db:
            if entry["id"] == user_id:
                return entry
        return -1

    def get_users(self):
        result = self.db
        if len(result) != 0:
            return result
        return -1

    def add_user(self, user_id, title):
        new_user = {"id": user_id, "title": title}
        if self.get_user(user_id) == -1:
            self.db.append(new_user)
            return 0
        return -1

    def get_index(self, user_id):
        for i in range(len(self.db)):
            entry = self.db[i]
            if entry["id"] == user_id:
                return i
        return -1

    def del_user(self, user_id):
        i = self.get_index(user_id)
        if i != -1:
            del self.db[i]
            return 0
        return -1

    def upd_user(self, user_id, title):
        new_user = {"id": user_id, "title": title}
        i = self.get_index(user_id)
        if i != -1:
            self.db[i] = new_user
            return 0
        return -1


class ControllerDB:
    def __init__(self, options):
        self.options = options
        self.init_db()

    def get_db_connection(self):
        try:
            return connect(
                    host="localhost",
                    user=self.options["username"],
                    password=self.options["password"],
                    database=DB_NAME,
            )
        except Error as e:
            print(e)

    def make_query(self, query):
        conn = self.get_db_connection()
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute(query)
            result = cursor.fetchall()
            cursor.close()
        conn.commit()
        conn.close()
        return result

    def init_db(self):
        self.make_query(f"CREATE DATABASE IF NOT EXISTS {DB_NAME};")
        self.make_query("DROP TABLE IF EXISTS users;")
        self.make_query("""CREATE TABLE users (
                           id INT PRIMARY KEY,
                           title VARCHAR(255) NOT NULL);""")
        return 0

    def get_user(self, user_id):
        result = self.make_query(f"SELECT * FROM users WHERE id = {user_id}")
        if len(result) == 0:
            return -1
        return result[0]

    def get_users(self):
        result = self.make_query("SELECT * FROM users")
        if len(result) == 0:
            return -1
        return result

    def add_user(self, user_id, title):
        if self.get_user(user_id) == -1:
            self.make_query(f"INSERT INTO users (id, title) VALUES ('{user_id}', '{title}');")
            return 0
        return -1

    def del_user(self, user_id):
        if self.get_user(user_id) == -1:
            return -1
        result = self.make_query(f"DELETE FROM users WHERE id = {user_id};")
        return result

    def upd_user(self, user_id, title):
        if self.get_user(user_id) == -1:
            return -1
        result = self.make_query(f"""UPDATE users 
                                     SET title = '{title}'  
                                     WHERE id = '{user_id}'""")
        return result


class Repo:
    def __init__(self):
        self.options = self.get_options()
        if self.options["use_db_repo"]:
            self.controller = ControllerDB(self.options)
        else:
            self.controller = ControllerRAM(self.options)

    def get_options(self):
        """
        It reads parameters from file at OPTIONS_FILE_PATH
        Input: se comments in options file
        Output: dict of options
        """

        options = {"use_db_repo": False, "username": None, "password": None}

        try:
            s = open(OPTIONS_FILE_PATH, "rt", encoding="utf-8")
            stream = list(s)
            s.close()
        except:
            print("Got exception while reading options from file")
            return options

        for line in stream:
            if line.lstrip().startswith("#"):  # do not read comments
                continue
            # read content of string
            line = line.rstrip("\n")
            fragments = line.split(":")
            # do we use db?
            if "use_db_repo" in fragments[0]:
                if "True" in fragments[1]:
                    options["use_db_repo"] = True
            # username to connect to db
            elif "username" in fragments[0]:
                options["username"] = fragments[1]
            # password to connect to db
            elif "password" in fragments[0]:
                options["password"] = fragments[1]

        return options

    def get_user(self, user_id):
        result = self.controller.get_user(user_id)
        return result

    def get_users(self):
        result = self.controller.get_users()
        return result

    def add_user(self, user_id, title):
        result = self.controller.add_user(user_id, title)
        return result

    def del_user(self, user_id):
        result = self.controller.del_user(user_id)
        return result

    def upd_user(self, user_id, title):
        result = self.controller.upd_user(user_id, title)
        return result


app = Flask(__name__)
app.config['SECRET_KEY'] = 'gh5ng843bh68hfi4nfc6h3ndh4xc53b56lk89gm4bf2gc6ehm'
repo = Repo()


# @app.route('/')
# def index():
#     users = repo.get_users()
#     return render_template('index.html', users=users)


@app.route('/user/<int:user_id>', methods=['GET'])
def get_user(user_id):
    user = repo.get_user(user_id)
    if user == -1:
        return "Rejected. No user with id=" + str(user_id), 404
    return jsonify(user), 200

@app.route('/users', methods=['GET'])
def get_users():
    users = repo.get_users()
    if users == -1:
        return "Rejected. DB is empty", 404
    return jsonify(users), 200

@app.route('/user/<int:user_id>', methods=['POST'])
def add_user(user_id):
    # title = request.get_json()['title']
    title = request.args.get('title')
    if repo.add_user(user_id, title) == -1:
        return "Rejected. User with id=" + str(user_id) + " already exists", 422
    return 'Success. User created', 204

@app.route('/user/<int:user_id>', methods=['DELETE'])
def del_user(user_id):
    result = repo.del_user(user_id)
    if result == -1:
        return "Rejected. No user with id=" + str(user_id), 404
    return 'Success. User deleted', 204

@app.route('/user/<int:user_id>', methods=['PATCH'])
def upd_user(user_id):
    # title = request.get_json()['title']
    title = request.args.get('title')
    result = repo.upd_user(user_id, title)
    if result == -1:
        return "Rejected. No user with id=" + str(user_id), 404
    return 'Success. User updated', 204


# @app.route('/create', methods=('GET', 'POST'))
# def create():
#     if request.method == 'POST':
#         title = request.form['title']
#         description = request.form['description']
#
#         if not title:
#             flash('Title is required!')
#         else:
#             repo.add_user(title, description)
#             return redirect(url_for('index'))
#
#     return render_template('create.html')


# @app.route('/<int:user_id>/edit', methods=('GET', 'POST'))
# def edit(user_id):
#     user = repo.get_user(user_id)
#
#     if request.method == 'POST':
#         title = request.form['title']
#         description = request.form['description']
#
#         if not title:
#             flash('Title is required!')
#         else:
#             repo.upd_user(user_id, title, description)
#             return redirect(url_for('index'))
#
#     return render_template('edit.html', user=user)


# @app.route('/<int:user_id>/delete', methods=('GET', 'POST',))
# def delete(user_id):
#     user = repo.get_user(user_id)
#     repo.del_user(user_id)
#     flash(f'{user["title"]} was successfully deleted!')
#     return redirect(url_for('index'))


if __name__ == '__main__':
    """
    Тестовый запуск сервиса
    """
    repo.add_user(1, "Pyotr Pervy")
    repo.add_user(2, "Aleksandr Sergeevich Pushkin")
    app.run(host="127.0.0.1", port=80)
