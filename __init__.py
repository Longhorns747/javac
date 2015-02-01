from flask import Flask, render_template, request, redirect, session
import requests, random, string
import os, shutil, subprocess
from werkzeug import secure_filename
app = Flask(__name__)

ALLOWED_EXTENSIONS = set(['zip'])

junit_name = ""
junit_helper_files = ""
COMP_DIR = "javaComp/"
pwd_dir = COMP_DIR + "pw.cfg"

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/ta")
def ta():
    return render_template("ta.html")

@app.route("/process", methods=['POST'])
def process_java():
    #Make a randomly generated directory for java compilation
    staticFilepath = COMP_DIR + random.choice(string.letters) + random.choice(string.letters) + random.choice(string.letters) + '/'

    d = os.path.dirname(staticFilepath)
    if not os.path.exists(d):
        os.makedirs(d)

    #If directory already exists, throw an error
    else:
        return render_template("error.html", message="Oh no D:! Something went wrong :( Please try again!")

    file = request.files['java']
    filename = ""

    #Get secure_filename for files
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(staticFilepath, filename))
    else:
        return render_template("error.html", message="Oh no D:! Something went wrong :( Please try again!")

    print filename

    java_files = unzip(filename, staticFilepath)
    path = staticFilepath + filename[:-4] #Chop off .zip extension
    compiler_output = compile(java_files, path)
    checkstyle_output = checkstyle(java_files, path)

    if junit_name != "" and junit_helper_files != "":
        junit_output = junit(java_files, junit_name, junit_helper_files, path)
    else:
        junit_output = "No JUnits!"

    #Clean Up
    shutil.rmtree(staticFilepath)
    return render_template("success.html", compiler_msg=compiler_output, checkstyle_msg=checkstyle_output, junit_msg=junit_output)

@app.route("/back", methods=['GET'])
def back_to_input():
    return render_template("index.html")

@app.route("/upload", methods=['POST'])
def ta_upload():
    global junit_name
    global junit_helper_files
    junit = request.files['junit']
    helper = request.files['helper']

    if request.form['password'] != open(pwd_dir, 'r+').read():
        return render_template("error.html", message="You entered the wrong password!")

    #Reset JUnit and Helper variables
    if not junit and not helper:
        #Delete old JUnit Tests
        if os.path.exists(COMP_DIR + junit_name + ".java"):
            os.remove(COMP_DIR + junit_name + ".java")

        #Delete old JUnit Helpers
        for fname in junit_helper_files.split():
            if os.path.exists(COMP_DIR + fname):
                os.remove(COMP_DIR + fname)

        junit_helper_files = ""
        junit_name = ""

        return render_template("index.html")

    #Get secure_filename for files
    if junit:
        #Delete old JUnit Tests
        if os.path.exists(COMP_DIR + junit_name + ".java"):
            os.remove(COMP_DIR + junit_name + ".java")

        #Store new ones
        junit_filename = secure_filename(junit.filename)
        junit.save(os.path.join(COMP_DIR, junit_filename))
        junit_name = junit_filename[:-5] #Chop off .java

    #Delete old JUnit Helpers
    for fname in junit_helper_files.split():
        if os.path.exists(COMP_DIR + fname):
            os.remove(COMP_DIR + fname)

    if helper:
        #Store new ones
        helper_filename = secure_filename(helper.filename)
        helper.save(os.path.join(COMP_DIR, helper_filename))
        junit_helper_files = helper_filename
    else:
        junit_helper_files = ""

    return render_template("index.html")

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

def unzip(filename, filepath):
    print filepath
    if ".zip" in filename:
        #Run Unzip Command
        bashCommand = "unzip " + filename
        import subprocess
        try:
            subprocess.check_output(bashCommand.split(), stderr=subprocess.STDOUT, cwd=filepath)
        except subprocess.CalledProcessError as err:
            output = err.output
            print output

        #Get names of java files in dir
        from os import listdir
        from os.path import isfile, join
        full_path = filepath + filename[:-4]
        onlyfiles = [ f for f in listdir(full_path) if isfile(join(full_path,f)) ]
        print "dir: " + full_path + " Files in dir: " + str(onlyfiles)
        res = ""

        for file in onlyfiles:
            if ".java" in file:
                res += file + " "

        return res
    else:
        return filename

def compile(java_filenames, filepath):
    #Compile Java, catch any errors
    bashCommand = "javac " + java_filenames
    print bashCommand
    output = "No Errors!"

    try:
        subprocess.check_output(bashCommand.split(), stderr=subprocess.STDOUT, cwd=filepath)
    except subprocess.CalledProcessError as err:
        output = err.output

    return output

def checkstyle(java_filenames, filepath):
    bashCommand = "java -jar checkstyle-6.0-all.jar -c cs1331-checkstyle.xml " + java_filenames

    shutil.copy(COMP_DIR + "checkstyle-6.0-all.jar", filepath)
    shutil.copy(COMP_DIR + "cs1331-checkstyle.xml", filepath)

    print bashCommand
    output = "No Errors!"

    try:
        output = subprocess.check_output(bashCommand.split(), stderr=subprocess.STDOUT, cwd=filepath)
    except subprocess.CalledProcessError as err:
        output = err.output

    return output

def junit(java_filenames, junit_name, junit_helpers, filepath):
    shutil.copy(COMP_DIR + "junit-4.11.jar", filepath)
    shutil.copy(COMP_DIR + "hamcrest-core-1.3.jar", filepath)
    shutil.copy(COMP_DIR + junit_helpers, filepath)
    shutil.copy(COMP_DIR + junit_name + ".java", filepath)

    print compile("-cp .:junit-4.11.jar:hamcrest-core-1.3.jar " + java_filenames + junit_helpers + " " + junit_name + ".java", filepath)

    bashCommand = "java -cp .:junit-4.11.jar:hamcrest-core-1.3.jar org.junit.runner.JUnitCore " + junit_name

    print bashCommand
    output = "No Errors!"

    try:
        output = subprocess.check_output(bashCommand.split(), stderr=subprocess.STDOUT, cwd=filepath)
    except subprocess.CalledProcessError as err:
        output = err.output

    return output


if __name__ == "__main__":
    app.run(debug="true")
