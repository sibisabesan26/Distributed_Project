from flask import Flask, render_template

# Tell Flask explicitly where to find templates
app = Flask(__name__, template_folder="templates")

@app.route("/")
def index():
    return render_template("index.html")

if __name__ == "__main__":
    app.run(port=8050, debug=True)
