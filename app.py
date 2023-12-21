# Libraries for Flask as per cs50 projects
import os
from flask import (
    Flask,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

# Database and file management libraries
from cs50 import SQL
from fileinput import filename
import csv
import numpy as np
import pandas as pd
from io import TextIOWrapper

# Libraries for neural network
import tensorflow as tf
from tensorflow.keras.layers import Dense
from tensorflow.keras.regularizers import L2
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

# Login functions
from helpers import engineer_login_required, admin_login_required, master_login_required

# Configure application
app = Flask(__name__)

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
ALLOWED_EXTENSIONS = {"csv"}
app.secret_key = "cs50_final_project"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///database.db")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Route called by AJAX on index page to dynamically update prediction based on user input
@app.route("/process_array", methods=["POST"])
def process_array():
    # convert AJAX's input to JSON to list
    new_example = request.json["new_example"]
    new_example_list = list(new_example)
    print("JSON list:", new_example)

    # load pandas dataframe to return means of database: used as default inputs where data not entered
    data_list = db.execute("SELECT * FROM patient_database")
    df = pd.DataFrame(data_list)

    # Troubleshooting in terminal window if required
    print(f"Number of Rows: {df.shape[0]}")
    print(f"Number of Columns: {df.shape[1]}")
    print(f"Title of Columns: {df.columns}")

    # Remove patient ID and Y value (prediciton) from list of means
    X_columns = df.iloc[:, 1:-1]
    means = X_columns.mean().tolist()
    print(f"new example size: {len(new_example)}")
    print(f"means size: {len(means)}")

    # iterate over list to look for unentered data (replaced by mean) and then convert to numerical value
    for i in range(len(new_example)):
        if new_example[i] == "" or new_example[i] == None:
            new_example[i] = means[i]
        try:
            float(new_example[i])
        except ValueError:
            return render_template(
                "index.html",
                apology_status="true",
                apology_message="incorrect data entry",
            )
    print("Python list, means inserted:", new_example)

    # convert to np array and process for predict algorithm
    new_example_array = np.array(new_example)
    new_example_reshaped = np.reshape(new_example_array, (1, 16))
    print("Reshaped input:", new_example_reshaped)

    # retrieve scaler from SQL database
    scaler_params = db.execute("SELECT * FROM scaler")
    mean_values = []
    stdev_values = []
    for row in scaler_params:
        mean_values.append(row["mean"])
        stdev_values.append(row["stdev"])
    mean_array = np.array(mean_values)
    stdev_array = np.array(stdev_values)
    scaler_retrieved = StandardScaler()
    scaler_retrieved.mean_ = mean_array
    scaler_retrieved.scale_ = stdev_array

    # apply to new example
    new_example_scaled = scaler_retrieved.transform(new_example_reshaped)

    # make prediction and convert probability to float
    loaded_model = tf.keras.models.load_model(
        "/workspaces/130820531/project/neural_network/trained_nn.h5"
    )
    print(loaded_model.summary())
    prediction = loaded_model.predict(new_example_scaled)
    probability = tf.keras.activations.sigmoid(prediction)
    float_probability = probability.numpy().item()
    print("probability:", float_probability)

    # Retrieve threshold from database
    threshold_select = db.execute(
        "SELECT ID FROM parameters WHERE Parameter = ?", "threshold"
    )
    for i in threshold_select:
        threshold_id = i["ID"]
    threshold_parameter = db.execute(
        "SELECT Value FROM parameters WHERE ID = ?", threshold_id
    )
    for i in threshold_parameter:
        threshold = i["Value"]

    # Set and return binary value: if probability is greater than threshold
    binary = 0
    if float_probability > threshold:
        binary += 1

    # turn binary value to string
    if binary == 1:
        binary_prediction = "Admit to ICU"
    elif binary == 0:
        binary_prediction = "Does not require admission to ICU"

    # return to route
    response_data = {
        "binary_prediction": binary_prediction,
        "float_probability": float_probability,
    }

    return jsonify(response_data)


@app.route("/", methods=["GET"])
def index():
    # Default view of index page before user input entered
    binary_prediction = "Enter patient data"
    float_probability = ""
    return render_template(
        "index.html",
        binary_prediction=binary_prediction,
        float_probability=float_probability,
        apology_status="false",
    )


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return render_template(
                "login.html",
                apology_status="true",
                apology_message="must provide username",
            )

        # Ensure password was submitted
        elif not request.form.get("password"):
            return render_template(
                "login.html",
                apology_status="true",
                apology_message="must provide password",
            )

        # Query database for username
        user_check_row = db.execute(
            "SELECT * FROM staff WHERE username = ?", request.form.get("username")
        )
        password_check_row = db.execute(
            "SELECT * FROM users WHERE staffid = ?", user_check_row[0]["ID"]
        )
        if len(password_check_row) != 1:
            return render_template(
                "login.html",
                apology_status="true",
                apology_message="user not yet registered",
            )

        # Ensure username exists and password is correct
        if not check_password_hash(
            password_check_row[0]["hash"], request.form.get("password")
        ):
            return render_template(
                "login.html",
                apology_status="true",
                apology_message="invalid username and/or password",
            )

        # Remember which user has logged in
        session["user_id"] = user_check_row[0]["ID"]
        print(user_check_row[0]["ID"])
        session["status"] = user_check_row[0]["status"]
        print(user_check_row[0]["status"])

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username entered
        if not request.form.get("username"):
            return render_template(
                "register.html",
                apology_status="true",
                apology_message="must register a username",
            )

        # Ensure username, given it is new, exists in master staff list and only one copy exists
        user_check = db.execute(
            "SELECT * FROM staff WHERE username = ?", request.form.get("username")
        )
        if len(user_check) == 0:
            return render_template(
                "register.html",
                apology_status="true",
                apology_message="username not in staff directory",
            )
        elif len(user_check) != 1:
            return render_template(
                "register.html",
                apology_status="true",
                apology_message=">1 username in staff directory",
            )

        # Ensure account type matches
        if user_check[0]["status"] != request.form.get("status"):
            return render_template(
                "register.html",
                apology_status="true",
                apology_message="account type does not match staff directory",
            )

        # Ensure both password and password confirmation are entered
        if not request.form.get("password"):
            return render_template(
                "register.html",
                apology_status="true",
                apology_message="must enter password",
            )
        if not request.form.get("confirmation"):
            return render_template(
                "register.html",
                apology_status="true",
                apology_message="must confirm password",
            )

        # Ensure password and confirmation match
        if request.form.get("password") != request.form.get("confirmation"):
            return render_template(
                "register.html",
                apology_status="true",
                apology_message="passwords do not match",
            )

        # Create password hash
        username = request.form.get("username")
        password = request.form.get("password")
        hash = generate_password_hash(password, method="pbkdf2", salt_length=16)
        staffid = user_check[0]["ID"]

        # Store user in database
        if (
            db.execute("INSERT INTO users (staffid, hash) VALUES(?, ?)", staffid, hash)
            is None
        ):
            return render_template(
                "register.html",
                apology_status="true",
                apology_message="error storing user registration",
            )

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to homepage
    return redirect("/")


@app.route("/staff", methods=["GET", "POST"])
@master_login_required
def staff():
    # Append registration status to main staff list (i.e. whether user has created an account themselves yer)
    existing_staff = db.execute("SELECT * FROM staff")
    for row in existing_staff:
        if len(db.execute("SELECT * FROM users WHERE staffid = ?", row["ID"])) == 1:
            row["registered"] = "Registered"
        else:
            row["registered"] = "Not Yet Registered"

    if request.method == "POST":
        # If improper values for delete/enter user are entered then render apology
        if (
            not request.form.get("staff_username")
            and not request.form.get("new_status")
            and not request.form.get("delete_staff_username")
            and not request.form.get("delete_status")
        ):
            return render_template(
                "staff.html",
                existing_staff=existing_staff,
                apology_status="true",
                apology_message="must choose form action",
            )
        elif not request.form.get("delete_staff_username") and not request.form.get(
            "delete_status"
        ):
            if (
                request.form.get("staff_username") is not None
                and not request.form.get("new_status")
                or not request.form.get("staff_username")
                and request.form.get("new_status") is not None
            ):
                return render_template(
                    "staff.html",
                    existing_staff=existing_staff,
                    apology_status="true",
                    apology_message="new user must have username and account type",
                )
        elif not request.form.get("staff_username") and not request.form.get(
            "new_status"
        ):
            if (
                request.form.get("delete_staff_username") is not None
                and not request.form.get("delete_status")
                or not request.form.get("delete_staff_username")
                and request.form.get("delete_status") is not None
            ):
                return render_template(
                    "staff.html",
                    existing_staff=existing_staff,
                    apology_status="true",
                    apology_message="deleting user must have username and account type",
                )

        # Ensure user who submits form is a master user
        master_username = request.form.get("master_username")
        master_password = request.form.get("master_password")

        master_main_acc = db.execute(
            "SELECT * FROM staff WHERE username = ? AND status = ?",
            master_username,
            "master",
        )
        master_check = db.execute(
            "SELECT * FROM users WHERE staffid = ?", master_main_acc[0]["ID"]
        )

        # Ensure username exists and password is correct
        if (
            len(master_check) != 1
            or len(master_main_acc) != 1
            or not check_password_hash(
                master_check[0]["hash"], request.form.get("master_password")
            )
        ):
            return render_template(
                "staff.html",
                existing_staff=existing_staff,
                apology_status="true",
                apology_message="invalid master username and/or password",
            )

        # Ensure master acc logged in is the same one as the credentials being entered
        if session.get("user_id") != master_main_acc[0]["ID"]:
            return render_template(
                "staff.html",
                existing_staff=existing_staff,
                apology_status="true",
                apology_message="mismatch between login account and master account details",
            )

        # Pathway to enter new user
        if (
            request.form.get("staff_username") is not None
            and request.form.get("new_status") is not None
            and not request.form.get("delete_staff_username")
            and not request.form.get("delete_status")
        ):
            # Obtain variables to insert into staff table
            username = request.form.get("staff_username")
            status = request.form.get("status")

            # Ensure username does not already exist
            rows = db.execute("SELECT * FROM staff WHERE username = ?", username)
            if len(rows) != 0:
                return render_template(
                    "staff.html",
                    existing_staff=existing_staff,
                    apology_status="true",
                    apology_message="username already exists",
                )

            # Insert into staff table
            db.execute(
                "INSERT INTO staff (username, status) VALUES(?, ?)", username, status
            )

            return render_template("staff.html", existing_staff=existing_staff)

        # Pathway to delete user
        if (
            not request.form.get("staff_username")
            and not request.form.get("new_status")
            and request.form.get("delete_staff_username") is not None
            and request.form.get("delete_status") is not None
        ):
            # Obtain variables to delete from staff table
            username = request.form.get("delete_staff_username")
            status = request.form.get("delete_status")

            # Ensure username already exists
            rows = db.execute("SELECT * FROM staff WHERE username = ?", username)
            if len(rows) != 1:
                return render_template(
                    "staff.html",
                    existing_staff=existing_staff,
                    apology_status="true",
                    apology_message="username does not exist",
                )

            # delete from staff table
            id = rows[0]["ID"]
            delete_user = db.execute("DELETE FROM users WHERE staffid = ?", id)
            delete_staff = db.execute("DELETE FROM staff WHERE ID = ?", id)

            # perform check
            user_check = db.execute("SELECT * FROM users WHERE staffid = ?", id)
            if user_check != 0 and delete_staff != 1:
                return render_template(
                    "staff.html",
                    existing_staff=existing_staff,
                    apology_status="true",
                    apology_message="error with deleting staff",
                )

            return render_template("staff.html", existing_staff=existing_staff)

        else:
            return render_template(
                "staff.html",
                existing_staff=existing_staff,
                apology_status="true",
                apology_message="unknown error",
            )

    else:
        return render_template("staff.html", existing_staff=existing_staff)


@app.route("/train", methods=["GET", "POST"])
@engineer_login_required
def train():
    # Take user to train.html if navigating via link
    if request.method == "GET":
        return render_template("train.html")

    if request.method == "POST":
        # Mechanism for loading data into pandas dataframe
        data_list = db.execute("SELECT * FROM patient_database")
        df = pd.DataFrame(data_list)
        print(f"Number of Rows: {df.shape[0]}")
        print(f"Number of Columns: {df.shape[1]}")
        print(f"Title of Columns: {df.columns}")

        # Split database into training, cross validation and test sets
        X = df.iloc[:, 1:-1]
        y = df.iloc[:, -1]
        X_train, X_, y_train, y_ = train_test_split(
            X, y, test_size=0.40, random_state=1999
        )
        X_cv, X_test, y_cv, y_test = train_test_split(
            X_, y_, test_size=0.5, random_state=1999
        )
        scaler = StandardScaler()
        scaler.fit(X_train)

        # Ensure scaler in database
        if (
            db.execute("UPDATE parameters SET Value = 1 WHERE Parameter = ?", "scaler")
            == 0
        ):
            insert = db.execute(
                "INSERT INTO parameters (Parameter, Value) VALUES(?, ?)", "scaler", 1
            )
        elif (
            db.execute("UPDATE parameters SET Value = 1 WHERE Parameter = ?", "scaler")
            > 1
        ):
            return render_template(
                "train.html",
                apology_status="true",
                apology_message="error interacting with parameters database",
            )
        select = db.execute("SELECT ID FROM parameters WHERE Parameter = ?", "scaler")
        for i in select:
            scaler_id = i["ID"]

        # store means and stdevs from scaler in separate table
        for i in range(scaler.mean_.shape[0]):
            update = db.execute(
                "UPDATE scaler SET mean = ?, stdev = ? WHERE id = ?",
                scaler.mean_[i],
                scaler.scale_[i],
                (i + 1),
            )
            if update == 1:
                print("successful update of row:", i)
            if update == 0:
                insert = db.execute(
                    "INSERT INTO scaler (parameters_table_id, mean, stdev) VALUES (?, ?, ?)",
                    scaler_id,
                    scaler.mean_[i],
                    scaler.scale_[i],
                )
                if insert != i:
                    print("mismatch in row:", i)
            elif update != 1:
                return render_template(
                    "train.html",
                    apology_status="true",
                    apology_message="error with standardscaler storage: more than one row updated",
                )

        # Perform feature scaling on data
        X_train_scaled = scaler.transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        X_cv_scaled = scaler.transform(X_cv)

        # Key initialisation parameters returned from user form - return apology if datatype incorrect
        try:
            learning_rate = float(request.form.get("learning_rate"))
            regulariser = float(request.form.get("regulariser"))
            threshold = float(request.form.get("threshold"))
        except ValueError:
            return render_template(
                "train.html",
                apology_status="true",
                apology_message="please enter floating point values for learning rate, regulariser and threshold",
            )
        try:
            input_neurons = int(request.form.get("input_neurons"))
        except ValueError:
            return render_template(
                "train.html",
                apology_status="true",
                apology_message="please enter integer for number of input neurons",
            )
        if (
            learning_rate <= 0
            or regulariser <= 0
            or threshold <= 0
            or input_neurons <= 0
        ):
            return render_template(
                "train.html",
                apology_status="true",
                apology_message="please use positive number for all parameters",
            )
        shape = X_train.shape[1]

        # update threshold into SQL database
        threshold_update = db.execute(
            "UPDATE parameters SET Value = ? WHERE Parameter = ?",
            threshold,
            "threshold",
        )
        if threshold_update == 0:
            if (
                db.execute(
                    "INSERT INTO parameters (Parameter, Value) VALUES(?, ?)",
                    "threshold",
                    threshold,
                )
                == None
            ):
                return render_template(
                    "train.html",
                    apology_status="true",
                    apology_message="error updating new threshold value",
                )
        elif threshold_update != 1:
            return render_template(
                "train.html",
                apology_status="true",
                apology_message="error inserting single new threshold value",
            )

        # Defining model
        model = tf.keras.Sequential(
            [
                tf.keras.Input(shape=(shape,)),
                Dense(
                    units=shape, activation="relu", kernel_regularizer=L2(regulariser)
                ),
                Dense(units=100, activation="relu", kernel_regularizer=L2(regulariser)),
                Dense(units=25, activation="relu", kernel_regularizer=L2(regulariser)),
                Dense(units=1, activation="linear"),
            ]
        )

        model.compile(
            loss=tf.keras.losses.BinaryCrossentropy(from_logits=True),
            optimizer=tf.keras.optimizers.Adam(learning_rate=learning_rate),
            metrics=["accuracy"],
        )

        early_stopping = tf.keras.callbacks.EarlyStopping(
            monitor="val_accuracy",  # Metric to monitor (e.g., 'val_loss', 'val_accuracy')
            patience=5,  # Number of epochs with no improvement after which training will be stopped
            restore_best_weights=True,  # Restore model weights from the epoch with the best value of the monitored metric
        )
        print(model.summary())

        # Training model
        model.fit(
            x=X_train_scaled,
            y=y_train,
            batch_size=100,
            epochs=100,
            verbose=1,
            validation_data=(X_cv_scaled, y_cv),
            callbacks=[early_stopping],
        )

        # Evaluating model on the test dataset
        results = model.evaluate(X_test_scaled, y_test)

        # Printing the test loss and metrics
        print("Test Loss:", results[0])
        print("Test Metrics:", results[1:])

        # Saving model
        model.save("/workspaces/130820531/project/neural_network/trained_nn.h5")

        return redirect("/")


@app.route("/data", methods=["GET", "POST"])
@admin_login_required
def data():
    # Upload pathway for .csv file
    if request.method == "POST":
        f = request.files.get("file")
        if f is None:
            return render_template(
                "data.html",
                apology_status="true",
                apology_message="please submit valid file",
            )

        # Ensure file opened as text
        text_file = TextIOWrapper(f, encoding="utf-8")

        # Create reader and headers object
        reader = csv.reader(text_file)
        headers = next(reader)

        for row in reader:
            # Create dictionary for each patient
            row_dict = dict(zip(headers, row))

            # Ensure patient ID not a duplicate before inserting patient data into new row
            if (
                len(
                    db.execute(
                        "SELECT * FROM patient_database WHERE ID = ?",
                        row_dict["patient_id"],
                    )
                )
                == 0
            ):
                insert = db.execute(
                    """
                    INSERT INTO patient_database (
                        ID, temperature, oxygen_saturation, lung_auscultation, crp, white_cell_count, age, news_2_score,
                        heart_disease, copd, renal_failure, charlson_index, sex, obesity, immunosuppression, diabetes,
                        neurological_disorder, icu
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    row_dict["patient_id"],
                    row_dict["temperature"],
                    row_dict["oxygen_saturation"],
                    row_dict["lung_auscultation"],
                    row_dict["crp"],
                    row_dict["white_cell_count"],
                    row_dict["age"],
                    row_dict["news_2_score"],
                    row_dict["heart_disease"],
                    row_dict["copd"],
                    row_dict["renal_failure"],
                    row_dict["charlson_index"],
                    row_dict["sex"],
                    row_dict["obesity"],
                    row_dict["immunosuppression"],
                    row_dict["diabetes"],
                    row_dict["neurological_disorder"],
                    row_dict["icu"],
                )
                if insert == None:
                    return render_template(
                        "data.html",
                        apology_status="true",
                        apology_message="database append error",
                    )

        # Select database to display on page, post-update from .csv file
        patient_database = db.execute("SELECT * FROM patient_database")

        return render_template(
            "data.html",
            patient_database=patient_database,
            apology_status="true",
            apology_message="file upload success!",
        )

    else:
        # Select database to display on page
        patient_database = db.execute("SELECT * FROM patient_database")

        return render_template(
            "data.html", form="form", patient_database=patient_database
        )
