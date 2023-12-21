# TITLE: MBBS CALC
#### Video Demo:  <URL HERE>
#### Description:
See below!

# Project Overview

### Project Description
'MBBS CALC' is a Flask web application designed for use by doctors in hospital emergency departments of tertiary hospitals (that is, hospitals with specialist services available) to calculate the risk of a known COVID-19 positive patient requiring intensive care unit (ICU) admission.

The application enables a doctor to enter clinicial information about a patient's current status (such as their temperature and oxygen saturation) as well as clinical information about a patient's preexisting health status (whether or not they have diabetes or heart disease, their [Charlson Comorbidity Index](https://pubmed.ncbi.nlm.nih.gov/3558716/), etc).

This clincial information is converted into a list of features which are passed to a pre-trained Neural Network, which then generates a probability of the patient requiring ICU level care.
This probability is then compared to a modifiable threshold value to generate a binary statement: the prediction of whether or not the patient should be admitted to ICU.

MBBS CALC, whilst deliberately designed to be accessable without a login required, does have several features hidden behind the login interface. Once logged in, depending on the user's account type (explained below) a user may have the ability to access the app's data management, neural network training and account administrative functions. Each of these functions are explored below.

MBBS CALC is a tongue-in-cheek reference to one of the key inspirations for this web app, [MDCalc](https://www.mdcalc.com/), a tool I have often used as a Medical Student and Doctor.
MBBS is the degree code for 'Bachelor of Medicine, Bachelor of Surgery' - a degree equivalent to the Doctor of Medicine (MD) here in Australia, and the medicine degree offered by my University (The University of Adelaide).

### Project Inspiration

This project was inspired by my experience as a medical student and doctor in Adelaide, South Australia, Australia. I wanted to use my cs50 final project to design a tool that would be relevant to my workplace and global health as a whole, using my (albeit beginner) knowledge in AI.

Essentially, I wanted to create an application which used Machine Learning (ideally a deep Neural Network) to make predictions about a patient's future care pathway based on their currently-available information. I settled upon this application - COVID-19 risk of ICU admission - due to 1) the availability of literature on this topic and 2) the ease of understanding for non-medical personnel. The data and prediction itself are not so important so much as the generalisability of this concept - explored at the end of this file.

#### Growing Demands on Healthcare: Efficiency Must Increase
In our changing health environment, both in my country Australia as well as the United States, a growing population (along with inflation and growing costs of emdical interventions) are increasing the financial pressure on the health system. In Australia particularly, with an ageing population and government-funded public health system, these costs are relevant to policymakers and our society as a whole.

Whilst Australia benefits from many international doctors moving from abroad, this demand outstrips the supply of new doctors. It is therefore increasingly important for doctors to become more efficient, using new data interpretation techniques (such as Machine Learning) and AI tools more broadly to increase the speed at which correct care decisions can be made.
Tools which help doctors decide on the correct course of action, or tools which help medical administrative staff to predict patient flow and patient load, will be paramount in this new age of medicine.

#### Machine Learning in Medicine in Adelaide, South Australia
Adelaide, with its population of ~1.4 million, is Australia's 5th largest city. Relatively isolated in its position as the capital of the state of South Australia, Adelaide (and its doctors) have nonetheless had an outsized impact on the research field of AI in Medicine. Researchers such as Dr Toby Gilbert, Dr Sanjeev Khurana, Dr Stephen Bacchi and Dr Joshua Kovoor have published widely on a number of [use cases of machine learning algorithms in clinical medicine](https://www.adelaidenow.com.au/news/south-australia/adelaide-score-artificial-intelligence-to-predict-when-patients-can-be-discharged-and-break-hospital-bed-gridlocks/news-story/f0603329e7c82bc251517214d0b861ed).

I myself, as a recent med school graduate and now junior doctor, am working closely with the latter three of these doctors on a project which looks to use Machine Learning to understand the link between length of hospital stay and a patient's socioeconomic factors.

#### Personal Experience and Interests
Alongside my role as a doctor, I have found myself fascinated by AI and its applications.
Recently, I have procrastinated my cs50 progress by completing DeepLearningAI and Stanford University Online's [Machine Learning Specialisation](https://www.deeplearning.ai/courses/machine-learning-specialization/) - improving my knowledge of this important field.

I also completed a summer internship in 2022 at [Nous Group](https://nousgroup.com/), a management consulting company, where I helped to design a health outreach system in rural Australia - seeing firsthand the types of data reports generated on patients and potential for tools which increase efficiency.

# File Directory and Explanation

### Project Structure
- project
    - flask_session
    - neural_network
        - trained_nn.h5
    - static
        - apology-script.js
        - index-script.js
        - layout-script.js
        - mbbs.jpg
        - staff-script.js
        - styles.css
    - templates
        - data.html
        - index.html
        - layout.html
        - login.html
        - register.html
        - staff.html
        - train.html
    - app.py
    - database.db
    - helpers.py
    - original_csv_data.csv
    - README.md

### File Explanation

#### [database.db](database.db)

This file stores all necessary staff and account (i.e. user) information, patient (i.e. training dataset), and neural network data.

The schema of database.db is displayed below:
```
CREATE TABLE parameters (
    ID INTEGER PRIMARY KEY,
    Parameter TEXT,
    Value FLOAT
);

CREATE TABLE scaler (
    id INTEGER PRIMARY KEY,
    parameters_table_id INTEGER REFERENCES parameters(ID),
    mean DOUBLE,
    stdev DOUBLE
);

CREATE TABLE staff (
    ID INTEGER PRIMARY KEY,
    username TEXT,
    status TEXT
);

CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    staffid INTEGER REFERENCES staff(ID),
    hash TEXT
);

CREATE TABLE patient_database (
    ID INTEGER PRIMARY KEY,
    temperature FLOAT,
    oxygen_saturation INTEGER,
    lung_auscultation INTEGER,
    crp FLOAT,
    white_cell_count FLOAT,
    age INTEGER,
    news_2_score INTEGER,
    heart_disease INTEGER,
    copd INTEGER,
    renal_failure INTEGER,
    charlson_index INTEGER,
    sex INTEGER,
    obesity INTEGER,
    immunosuppression INTEGER,
    diabetes INTEGER,
    neurological_disorder INTEGER,
    icu INTEGER
);
```
The tables **parameters** and **scaler** store the parameters for the trained neural network and fitted StandardScaler() means and st.devs for the training data, so that these can be used for new predictions.

The table **staff** is a master list of all users who are permitted to register an account. It includes their unique username, which they must use once they register a new account. The column 'status' holds one of three strings which represent the three account types: *engineer*, *admin* and *master* accounts. Each of these have different privileges in the login-protected part of the site: these are explored below.

The table **users** holds all users who have registered at the site. Note that whilst any user can access the '*/register*' route described below, only usernames listed in the **users** database can be used to create accounts, providing an additional layer of security. In addition, once these accounts are created, they inherit the account type as described above.

Finally, the table **patient_database** holds the training data for the neural network.

#### [app.py](app.py)
The main application file. It contains the following key routes:

##### /process_array: Route called by AJAX on index page to dynamically update prediction based on user input
Occurs in context of index.html page.
This route is actioned dynamically in response to a user entering information in the form on the index page.
As soon as the user enters any input, the JavaScript in index-script.js actions an asynchronous request to this route.
The user's input is converted to an array to match the number of input features for the neural network, with missing data replaced by the mean value of the database (a common technique in machine learning), as it is possible that a user may wish to use this application before all patient data is available.
This array is then passed to the neural network and the probability of ICU admission (0-1) and binary guess value (whether probability > threshold or <= threshold) is passed back to the JS as a string which the user can interpret.

##### /: Index route - loads the main MBBS CALC calculator tool
This merely loads the main page for any user, logged in or otherwise. Once any user input occurs, /process_array is called as above.

##### /login: Allows an existing user to log in
Called by GET or POST to login.html page.
Self-explanatory. Post logs user in (remembering their details in session variable) and redirects user to '/' once login successful, provides user with an apology popup and reloads same login.html page if unsuccessful attempt.

##### /register: Enables a new user to register
Called by GET or POST to register.html page.
Initially works very similarly to cs50's finance week 9 problem, with a user having to choose a unique username alongside a password and confirming their password, submitting this form via post to create a new user in the users table in the database.db file.
However, unlike the finance web app, new users can ONLY be registered if their username already exists in the staff table (also in the database.db file).
This ensures that the webpage can be distributed widely, with only existing staff able to register accounts to access the website's login-protected features.

New users have access privilages according to their account type. There are three types of account types:
- engineer: **Software Engineer** account type: these users can train the neural network (and choose parameters) but cannot access nor append the patient database and cannot change staff access privileges
- admin: **Administrative Staff** account type: these users can add to the patient database by uploading .csv files with further patient info but cannot train the neural network (nor choose parameters) and also cannot change staff access privileges
- master: **Master Account** account type: these users have access to all three functions: able to upload new data, train the neural network and control account privileges by adding staff to or deleting staff from the staff table.

##### /logout: Logs a user out and returns them to the index page
This route is pretty self-explanatory, clearing the session variable and redirecting to the index page.

##### /train: Trains a neural network on the database

The user (in this case, someone logged in under the 'engineer' or 'master' acount type) can then alter a number of parameters to affect how the neural network is trained and structured.
The can enter a custom learning rate *(variable learning_rate)*, regulariser *(variable regulariser)*, number of neurons in the first layer (that is, the first layer after the input features themselves) *(variable shape)* and threshold (for the binary prediction value) *(variable threshold)*.
The algorithm is structured as follows:
```
model = tf.keras.Sequential([
            tf.keras.Input(shape=(shape,)),
            Dense(units=shape, activation="relu", kernel_regularizer=L2(regulariser)),
            Dense(units=100, activation="relu", kernel_regularizer=L2(regulariser)),
            Dense(units=25, activation="relu", kernel_regularizer=L2(regulariser)),
            Dense(units=1, activation="linear"),
        ])

        model.compile(
            loss= tf.keras.losses.BinaryCrossentropy(from_logits=True),
            optimizer=tf.keras.optimizers.Adam(learning_rate=learning_rate),
            metrics=['accuracy']
        )
```
This structure was chosen as it had a high level of accuracy on the test data for binary_threshold = 0.5.

This route then stores the trained network so it can be called for the prediction in the /process_array route.
It also stores the scaler variable (an array of shape [1][number of features] holding the mean and st.dev for each feature) in the scaler table in database.db so that this same scaler can be applied to the prediction data.
Finally, it stores the threshold value so this again can be used for the prediciton route.

##### /data: Facilitates the upload of patient data
Two functions are performed by this route, via page data.html:
1. For both GET and POST submissions, the page displays a full list of the patient database - with features shown for all patients. Patients are identified only by their ID.
2. For a POST submission, the route permits uploading of a .csv file with additional patients to add to the training database. The route will check each row to ensure it is not a duplicate of an existing patient ID before it adds it to the database.

Whilst the .csv file has to have the same headings as the **patient_database** table for this upload to work, based on my experience working with real hospitals it is assumed that any patient data report exported to .csv will have a consistent format, meaning the handling of unique data formats is unnecessary.

##### /staff: Displays list of staff and active (registered) users; enables master account(s) to add/delete staff from database
The final route of the app.py file actions staff.html - displaying existing staff and allowing master accounts to edit this staff list.

Thisn route will show the user a table of all existing staff (that is, usernames authorised to create an account) and their corresponding account type (access privileges). It also displays whether or not the user has created an account: It does this by appending a row to the **staff** table by checking if the staff ID is present in the **users** table, and displaying 'Registered' if so. This function is performed for both GET and POST requests.

When a POST request is actioned, the route checks the form to ensure the user has correctly filled it out - choosing an existing staff member to remove or a new staff member to add - and then checks the user's username, password and session login details to ensure these match and are linked to a *master* account type. Once this occurs, the corresponding change to the **staff** table occurs - and if a user is deleted, they are removed from the **users** table too.

#### [helpers.py](helpers.py)
This .py file contains the decorator functions which underpin the login-protected privileges, preventing '*admin*' and '*engineer*' accounts from accessing some pages.

#### [original_csv_data.csv](original_csv_data.csv)
This .csv file is the original patient database which was uploaded to the **patient_database** SQL table, and subsequently used to train the network.
The generation of this data is described below.

#### [trained_nn.h5](neural_network/trained_nn.h5)
The network trained by '*/train*' is stored here.

#### [data.html](templates/data.html)

#### [index.html](templates/index.html)

#### [layout.html](templates/layout.html)

#### [login.html](templates/login.html)

#### [register.html](templates/register.html)

#### [staff.html](templates/staff.html)

#### [train.html](templates/train.html)

#### [apology-script.js](static/apology-script.js)

#### [index-script.js](static/index-script.js)

#### [layout-script.js](static/layout-script.js)

#### [staff-script.js](static/staff-script.js)

#### [mbbs.jpg](static/mbbs.jpg)
A nice little logo of my web app, indended to pay homage to MDCalc.

![MBBS CALC logo](static/mbbs.jpg)

You really can see I am not the artistic type.

#### [styles.css](static/styles.css)
Largely similar to the finance assignment, I did copy some Bootstrap .css into this file (source supplied in file) to alter the navigation bar colour to MDCalc's shade of green, again in an attempt to pay homage to the inspiration for this site.

Some styling was done of containers but I mainly used tables in my .html files to format the site to my preference.
Much more work went into the .js and .py files behind this application and I do confess the .css (and resultant aesthetic appeal) is rather basic.
Hey, if it looks stupid but it works - it ain't stupid!

# Components and Processes of Project

### Machine Learning: Predicting Likelihood of ICU Admission using Neural Network

#### Obtaining and Cleaning Data: Synthetic Data Inspired by Real-World Research
A brief literature review was conducted to discover the patient datapoints relevant to ICU admission risk, for patients with known COVID-19 infection.

Sources revealed the following data points: a mixture of bedside findings, test results and past medical history:
```
temperature,oxygen_saturation,lung_auscultation,crp,white_cell_count,age,news_2_score,heart_disease,copd,renal_failure,charlson_index,sex,obesity,immunosuppression,diabetes,neurological_disorder
```
The [News 2 Score](https://www.mdcalc.com/calc/10083/national-early-warning-score-news-2) and [Charlson Comorbidity Index](https://www.mdcalc.com/calc/3917/charlson-comorbidity-index-cci) can be found, funnily enough, on MDCalc.

Sources used for factors relevant to ICU Admission Risk for COVID-19 Patients were:
1. Vanhems, Philippe, et al. "Factors associated with admission to intensive care units in COVID-19 patients in Lyon-France." PLoS One 16.1 (2021): e0243709.
2. Machado-Alba, Jorge Enrique, et al. "Factors associated with admission to the intensive care unit and mortality in patients with COVID-19, Colombia." PLoS One 16.11 (2021): e0260169.
3. Kim, Lindsay, et al. "Risk factors for intensive care unit admission and in-hospital mortality among hospitalized adults identified through the US coronavirus disease 2019 (COVID-19)-associated hospitalization surveillance network (COVID-NET)." Clinical infectious diseases 72.9 (2021): e206-e214.

From these sources, a synthetic database was created to avoid patient confidentiality issues associated with using a real patient database:
Using results from these studies + my own clinical experience where context was missing, a mean and standard deviation was created for all 'ICU negative' and 'ICU positive' patients.
Using Excel's *=NORMINV(RAND(),mean,stdev)*, random datapoints within these pre-determined ranges were created for each patient.
Finally, some noise was added to the data to ensure the spread was not completely uniform, and then it was exported to a .csv file for use in the MBBS CALC app.
2000 patients were generated, with 100 removed as there was some kind of value error created by the random generation process for these patients. The remaining 1900 formed the original dataset.

Whilst I understand that this data is made-up and will not generate any new findings, it was very useful from the perspective of creating this web application - the main purpose of this assignment.

#### Exploring Data
Though I have learnt about this step from my time in Andrew Ng's [Machine Learning Specialisation](https://www.deeplearning.ai/courses/machine-learning-specialization/), it was not necessary within the context of this project given the synthetically generated dataset.

#### Choosing Algorithm and Altering Parameters
Several variations of the neural network architecture, activation function, regulariser (and other parameters) were considered, with the final 4-layer, ReLu activation function, Adam optimiser network being chosen as it exhibited high accuracy. See */train* subheading above for the exact structure.
Learning Rate was set as 0.01, Input Neurons as 10, Regulariser at 0.01 and Binary Threshold at 0.5 all as default options - these were found to produce the highest accuracy for a constant NN architercture as described above.
It is noted however that the user is free to alter these parameters somewhat as described above.

### User Display: Intuitive, Practical Interface

#### [MDCalc](https://www.mdcalc.com/) - A Common Tool for Clinicians
MDCalc is a real winner for clinicians as it is highly intruitive and provides real-time calculations. Despite the fact I had never used AJAX before to action asynchronous actioning of routes to return (essentially instantaneous) information, learning how to write JavaScript was a key challenge of this project.
Despite all the hours spent learning about neural networks outside of cs50, I think the index-script.js is my proudest achievement of this project as it allowed me to perform these instant calculations for the user's convenience - imitating a tool I have used and loved myself!

#### Reactivity: AJAX vs Form Submission and Means Imputation
The implementation of this asynchronous request means that data will be sent before the user can edit every single field. In an answer to this, as well as the theoretical possibility of a real-life doctor not having access to all of the patient's information, the route was designed to impute database means into missing datafields. This method is common in ML engineering. This ensures that meaningful predictions can still be made for incomplete data.

#### Data Upload: Mirroring Real Workplace Interactions
As described above, the generation of .csv reports on patient data is relatively commonplace in the world of medical administration. It is for this reason that I chose this as the primary data upload method for my application.
I chose a iterative loop to check the existing data for duplicates before the new data is entered into the database - perhaps not the most efficient method, but one I knew how to code.
I did have a fair bit of difficulty creating a form which enabled me to upload a .csv file, but thankfully in the end I succeeded!

#### Handling Errors: Apology
Whilst wanting to maintain the humour of cs50's apology page for the finance problem set, I instead opted for a more user-friendly route which does not redirect the user to another page and instead provides a pop-up message describing the type of error.

### Security: Two-Tiered Structure

#### Staff Database and User Database: Authentication Required

#### Software Engineer vs Administrative Access

#### Master Access

# Applicability: Relevant to Real Practice

### Future Research Direction

### Use Of Similar Web Application