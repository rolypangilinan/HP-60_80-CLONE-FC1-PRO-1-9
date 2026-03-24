# Import tools needed to build a website
# Flask: The main tool that creates our website
# request: Helps handle user clicks and form submissions (not used yet)
# render_template: Shows our HTML pages to visitors
from flask import Flask, request, render_template


# Create our website using Flask
# This line starts up our web application
app = Flask(__name__)

# This is the homepage route
# When someone visits our website's main address, this code runs
@app.route("/")
def home():
    # Show the homepage to the visitor
    # This is like opening the front door of our website
    return render_template('home.html')

# Page for Process 1
# When someone goes to website.com/process1, they see this page
@app.route("/process1")
def process1():
    # Show the Process 1 monitoring page
    return render_template('process1.html')

# Page for Process 2
# When someone goes to website.com/process2, they see this page
@app.route("/process2")
def process2():
    # Show the Process 2 monitoring page
    return render_template('process2.html')

# Page for Process 3
# When someone goes to website.com/process3, they see this page
@app.route("/process3")
def process3():
    # Show the Process 3 monitoring page
    return render_template('process3.html')

# Page for Process 4
# When someone goes to website.com/process4, they see this page
@app.route("/process4")
def process4():
    # Show the Process 4 monitoring page
    return render_template('process4.html')

# Page for Process 5
# When someone goes to website.com/process5, they see this page
@app.route("/process5")
def process5():
    # Show the Process 5 monitoring page
    return render_template('process5.html')

# Page for Process 6
# When someone goes to website.com/process6, they see this page
@app.route("/process6")
def process6():
    # Show the Process 6 monitoring page
    return render_template('process6.html')

# Page for Process 7
# When someone goes to website.com/process7, they see this page
@app.route("/process7")
def process7():
    # Show the Process 7 monitoring page
    return render_template('process7.html')

# Page for Process 8
# When someone goes to website.com/process8, they see this page
@app.route("/process8")
def process8():
    # Show the Process 8 monitoring page
    return render_template('process8.html')

# Page for Process 9
# When someone goes to website.com/process9, they see this page
@app.route("/process9")
def process9():
    # Show the Process 9 monitoring page
    return render_template('process9.html')

# Start the website when this file is run
# This code only runs when you click "Run" on this file
if __name__ == "__main__":
    # Turn on the web server so people can visit the site
    # host="0.0.0.0": Anyone on the network can visit (not just you)
    # port=5000: The website "door number" - like apartment 5000
    # debug=True: Shows helpful error messages if something breaks
    app.run(host="0.0.0.0", port=5000 ,debug=True)  #host="0.0.0.0", port=5000 for porthost