from flask import Flask
app = Flask(__name__)


@app.route("/")
def hello():
    return "Hello World!"

if __name__ == "__main__":
    app.run()


'''
for a given digest:
    get the similarity list
    display score + related digest

    [little parser for the identified json:
        strip out content
        pretty print xml for response
    ]

    on left, display "original" content
    on right, display "related" content


html: pretty syntax highlighting in boxes
'''
