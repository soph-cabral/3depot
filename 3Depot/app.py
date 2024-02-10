import os

from botocore.exceptions import NoCredentialsError

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from datetime import timedelta
import sqlite3

from helpers import login_required

# Configure application
app = Flask(__name__)

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

MODELS_FOLDER = 'static/models'
ALLOWED_EXTENSIONS = {'glb'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Initialize a new SQL object connected to your database
db = SQL("sqlite:///3depot.db")

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        # Ensure username was submitted
        if not username:
            return render_template("register.html", flash_message="Must provide username")

        # Ensure password was submitted
        elif not password:
            return render_template("register.html", flash_message="Must provide password")

        # Uncomment and update database logic here...
        rows = db.execute("SELECT * FROM users WHERE username = ?", username)

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], password):
            return render_template("login.html", flash_message="Invalid Username or Password")

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]


        # Check if the user's folder is empty
        user_id = str(session.get("user_id", None))
        user_folder = str(os.path.join(MODELS_FOLDER, user_id))

        if os.listdir(user_folder):
            # User has images, redirect to 'mydepot'
            return redirect(url_for('mydepot'))

        # User has no images, redirect to 'no_files_mydepot'
        return redirect(url_for('no_files_mydepot'))

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")



@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    # Display registration form on GET request
    if request.method == "GET":
        return render_template("register.html")
    else:
        # Retrieve form data on POST request
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        # Validate form data
        if not username:
            return render_template("register.html", flash_message="Must provide username")

        if not password:
            return render_template("register.html", flash_message="Must provide password")

        if not confirmation:
            return render_template("register.html", flash_message="Must confirm password")

        if password != confirmation:
            return render_template("register.html", flash_message="Passwords don't match")


        # Hash the password
        hash = generate_password_hash(password)

        # Attempt to insert new user into the database
        try:
            new_user_id = db.execute(
                "INSERT INTO users (username, hash) VALUES (?, ?)", username, hash
            )
        except Exception as e:
            # Handle exceptions (like duplicate username)
            flash("Username already taken or error in database operation")
            return render_template("register.html")

        # Store the user's ID in the session
        session["user_id"] = new_user_id

        # Create a new folder for the user
        user_folder = os.path.join("static/models", str(new_user_id))
        try:
            os.makedirs(user_folder, exist_ok=True)
        except OSError as error:
            flash("Error creating directory for user data")
            return render_template("register.html")

        # Redirect to a different page upon successful registration
        return redirect(url_for('no_files_mydepot'))

@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/upload", methods=["GET", "POST"])
@login_required  # Ensure that only logged-in users can access this route
def upload():
    if request.method == 'GET':
        # If the method is GET, render the upload form template
        return render_template("upload.html")
    else:
        # Handle the POST request for file upload
        if 'file' not in request.files:
            # Redirect to the upload page if no file part in the request
            return redirect(request.url)

        file = request.files['file']

        if file.filename == '':
            # Redirect if no file was selected
            return redirect(request.url)

        if file and allowed_file(file.filename):
            # Check if the file is allowed (based on its extension, presumably)
            user_id = str(session.get("user_id", None))
            user_folder = os.path.join(MODELS_FOLDER, user_id)
            new_filename = request.form.get('new_filename', '')  # Retrieve the new filename from the form

            if not new_filename:
                # Check if the new filename is provided, flash warning if not
                flash("Please provide a new filename", "warning")
                return redirect(url_for('upload'))

            # Secure the filename and check if it already exists
            new_filename_secure = secure_filename(new_filename)
            full_path = os.path.join(user_folder, new_filename_secure)

            if os.path.exists(full_path):
                # Flash warning if file with the same name exists
                flash("File with this name already exists. Please choose a different name.", "warning")
                return redirect(url_for('upload'))

            file.save(full_path)  # Save the file to the server
            description = request.form.get('description', '')  # Retrieve the description from the form

            model_size = os.path.getsize(full_path)  # Get the size of the uploaded file

            try:
                # Insert file details into the database
                db.execute("INSERT INTO models (name, desc, size, path, owner_id) VALUES (?, ?, ?, ?, ?)",
                           new_filename_secure, description, model_size, full_path, user_id)
            except Exception as e:
                # Handle database errors
                print(f"Database error: {e}")
                flash(f"Error in database operation: {e}", "error")
                return redirect(url_for('upload'))

            # Redirect to a different page after successful upload
            return redirect(url_for('mydepot'))
        else:
            # Redirect to the home page if the file is not allowed
            return redirect("/")



@app.route("/mydepot")
@login_required
def mydepot():
    image_data = []

    user_id = str(session.get("user_id", None))
    user_folder = str(os.path.join(MODELS_FOLDER, user_id))

    # Get information about uploaded images
    for filename in os.listdir(user_folder):
        path = os.path.join(user_folder, filename)
        name = filename.split('.')[0]  # Assuming filenames are unique

        # Ensure it's a file, not a directory
        if os.path.isfile(path):
            # Fetch the description, size, and id from the database
            description_results = db.execute("SELECT desc FROM models WHERE path = ?", path)
            size_results = db.execute("SELECT size FROM models WHERE path = ?", path)
            id_results = db.execute("SELECT id FROM models WHERE path = ?", path)

            description = description_results[0]['desc'] if description_results else 'No description found'
            size = round(size_results[0]['size'] / (1024 ** 2), 2) if size_results else None  # Size in megabytes

            # Format the size appropriately
            if size is not None:
                if size >= 1:
                    size_formatted = '{:.2f} MB'.format(size)
                else:
                    size_formatted = '{:.2f} KB'.format(size * 1024)
            else:
                size_formatted = 'No size found'

            id = id_results[0]['id'] if id_results else 'No ID found'

            image_data.append({
                'path': path,
                'name': name,
                'description': description,
                'size': size_formatted,
                'id': id
            })

    if not image_data:
        # Redirect to the "no files" page for mydepot
        return redirect(url_for('no_files_mydepot'))

    return render_template('mydepot.html', image_data=image_data)

@app.route("/no_files_mydepot")
def no_files_mydepot():
    # Render the "You have no files yet" page for mydepot
    return render_template('no_files_mydepot.html')

if __name__ == '__main__':
    app.run(debug=True)

@app.route("/feed")
@login_required
def feed():
    image_data = []

    # Iterate over each user-specific folder in MODELS_FOLDER
    for user_folder in os.listdir(MODELS_FOLDER):
        user_folder_path = os.path.join(MODELS_FOLDER, user_folder)

        # Check if it's a directory
        if os.path.isdir(user_folder_path):
            # Iterate over each file in the user-specific folder
            for filename in os.listdir(user_folder_path):
                path = os.path.join(user_folder_path, filename)

                # Ensure it's a file, not a directory
                if os.path.isfile(path):
                    name = filename.split('.')[0]  # Assuming filenames are unique

                    # Fetch the description
                    description_results = db.execute("SELECT desc FROM models WHERE path = ?", path)
                    if description_results:
                        description = description_results[0]['desc']
                    else:
                        description = 'No description found'

                    # Fetch the owner
                    owner_results = db.execute("SELECT username FROM users WHERE id = (SELECT owner_id FROM models WHERE path = ?)", path)
                    if owner_results:
                        owner = owner_results[0]['username']
                    else:
                        owner = 'No owner found'

                    # Fetch the size
                    size_results = db.execute("SELECT size FROM models WHERE path = ?", path)
                    if size_results:
                        size = round(size_results[0]['size'] / 1000000, 1)
                    else:
                        size = 'No size found'

                    # Fetch the id
                    id_results = db.execute("SELECT id FROM models WHERE path = ?", path)
                    if id_results:
                        id = id_results[0]['id']
                    else:
                        id = 'No ID found'



                    image_data.append({
                        'path': path,
                        'name': name,
                        'description': description,
                        'file_size': size,
                        'owner': owner,
                        'id' : id
                    })

    return render_template('feed.html', image_data=image_data)

if __name__ == '__main__':
    app.run(debug=True)

@app.route("/view")
def view():
    id= request.args.get('image_id')
     # Fetch the description
    description_results = db.execute("SELECT desc FROM models WHERE id = ?", id)
    if description_results:
        description = description_results[0]['desc']
    else:
        description = 'No description found'

    # Fetch the owner
    owner_results = db.execute("SELECT username FROM users WHERE id = (SELECT owner_id FROM models WHERE id = ?)", id)
    if owner_results:
        owner = owner_results[0]['username']
    else:
        owner = 'No owner found'

    # Fetch the size
    size_results = db.execute("SELECT size FROM models WHERE id = ?", id)
    if size_results:
        size = round(size_results[0]['size'] / 1000000, 1)
    else:
        size = 'No size found'

    # Fetch the name
    name_results = db.execute("SELECT name FROM models WHERE id = ?", id)
    if name_results:
        name = name_results[0]['name']
    else:
        name = 'No ID found'

    # Fetch the path
    path_results = db.execute("SELECT path FROM models WHERE id = ?", id)
    if path_results:
        path = path_results[0]['path']
    else:
        path = 'No ID found'



    return render_template('view.html', path=path, name=name, description=description, size=size, owner=owner, id=id)
