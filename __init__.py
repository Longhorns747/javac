from flask import Flask, render_template, request, redirect, session
import requests, random, string
import os
from werkzeug import secure_filename
app = Flask(__name__)

ALLOWED_EXTENSIONS = set(['java'])

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/process", methods=['POST'])
def process_java():
    #Make a randomly generated directory for latex compilation
    staticFilepath = '/var/www/javac/static/javaComp/' + random.choice(string.letters) + random.choice(string.letters) + random.choice(string.letters) + '/'

    d = os.path.dirname(staticFilepath)
    if not os.path.exists(d):
        os.makedirs(d)

    #If directory already exists, throw an error
    else:
        return render_template("error.html", message="Oh no D:! Something went wrong :( Please try again!")

    file = request.files['java']
    filename = ""
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(staticFilepath, filename))
    else:
        return render_template("error.html", message="Oh no D:! Something went wrong :( Please try again!")

    #f = open(staticFilepath + '/latex.tex', 'w')
    #f.write(latex_input)
    #f.close()

    #Compile LaTeX
    bashCommand = "javac " + filename;
    import subprocess
    process = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE, cwd=staticFilepath)
    output = process.communicate()[0]

    #f = open(staticFilepath + '/' + filename.rsplit('.', 1)[0] + '.html')
    #finalHTML = f.read()

    import shutil
    shutil.rmtree(staticFilepath)

    return render_template("success.html", compiler_msg=output)

@app.route("/back", methods=['GET'])
def back_to_input():
    return render_template("index.html")

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

if __name__ == "__main__":
    app.run(debug="true")
