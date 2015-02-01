from flask import Flask, render_template, request, redirect, session
import requests, random, string
import os, shutil, subprocess
from werkzeug import secure_filename
app = Flask(__name__)

ALLOWED_EXTENSIONS = set(['zip'])

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/process", methods=['POST'])
def process_java():
    #Make a randomly generated directory for java compilation
    staticFilepath = 'javaComp/' + random.choice(string.letters) + random.choice(string.letters) + random.choice(string.letters) + '/'

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
    junit_output = junit(java_files, "LinearAlgebraTest", "Solution.java", path)

    #Clean Up
    shutil.rmtree(staticFilepath)
    return render_template("success.html", compiler_msg=compiler_output, checkstyle_msg=checkstyle_output, junit_msg=junit_output)

@app.route("/back", methods=['GET'])
def back_to_input():
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

    shutil.copy("javaComp/checkstyle-6.0-all.jar", filepath)
    shutil.copy("javaComp/cs1331-checkstyle.xml", filepath)

    print bashCommand
    output = "No Errors!"

    try:
        output = subprocess.check_output(bashCommand.split(), stderr=subprocess.STDOUT, cwd=filepath)
    except subprocess.CalledProcessError as err:
        output = err.output

    return output

def junit(java_filenames, junit_name, junit_helpers, filepath):
    shutil.copy("javaComp/junit-4.11.jar", filepath)
    shutil.copy("javaComp/hamcrest-core-1.3.jar", filepath)
    shutil.copy("javaComp/" + junit_helpers, filepath)
    shutil.copy("javaComp/" + junit_name + ".java", filepath)

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
