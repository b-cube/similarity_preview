from flask import Flask
from flask import abort
from flask import render_template
from flask import request
app = Flask(__name__)

import os
import glob
import json
from lxml import etree
from xml.sax.saxutils import escape


@app.route("/view")
def get_page():
    '''
    params:
        source
        compare

        if no source, run the list
        if source and no compare, show possibilities
        if source and compare, show comparison
    '''

    source_digest = request.args.get('source', '')
    compare_digest = request.args.get('compare', '')

    digests = []
    if not source_digest and not compare_digest:
        files = glob.glob('similarities/*_similarities.txt')
        digests = [os.basename(f).replace('_similarities.txt', '') for f in files]

    source_response = ''
    if source_digest:
        similarities = parse_similarities('similarities/%s_similarity.txt' % source_digest)
        source_response = parse_response('responses/%s.json' % source_digest)

    compare_response = ''
    if compare_digest:
        compare_response = parse_response('responses/%s.json' % compare_digest)

    return render_template(
        'index.html',
        digests=digests,
        source=source_response,
        compare_response=compare_response,
        similarities=similarities
    )


@app.route("/similarities")
def get_simlist():
    files = glob.glob('similarities/*_similarities.txt')
    digests = [os.basename(f).replace('_similarities.txt', '') for f in files]
    return digests


@app.route("/response/<digest>")
def get_response(digest):
    fpath = 'responses/%s_identified.json' % digest
    if not os.path.exists(fpath):
        abort(404)

    parsed_xml = parse_response(fpath)
    if not parsed_xml:
        abort(500)
    return parsed_xml


@app.route("/similarity/<digest>")
def get_similarity(digest):
    fpath = 'similarities/%s_similarity.txt' % digest
    if not os.path.exists(fpath):
        abort(404)
    parsed_sim = parse_similarities(fpath)
    if not parsed_sim:
        abort(500)
    return parsed_sim


def parse_similarities():
    pass


def parse_response(digest_path, html_escape=True):
    with open(digest_path, 'r') as f:
        data = json.loads(f.read())

    content = data['content']
    try:
        xml = etree.fromstring(content)
    except:
        return None
    text = etree.tostring(xml, pretty_print=True)

    # html encode it
    if html_escape:
        html_escape_table = {
            '"': "&quot;",
            "'": "&apos;"
        }
        new_lines = []
        for line in text.split('\n'):
            new_lines.append(escape(line, html_escape_table))
        return '\n'.join(new_lines)

    # just return the pretty-printed xml
    return text


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
