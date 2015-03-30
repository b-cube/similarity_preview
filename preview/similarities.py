import flask
from flask import Flask
from flask import abort
from flask import render_template
from flask import request
from flask import Response
app = Flask(__name__)

import os
import glob
import json
import operator
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
        files = glob.glob('preview/similarities/*_similarities.txt')
        digests = [os.basename(f).replace('_similarities.txt', '') for f in files]

    source_response = ''
    if source_digest:
        similarities = parse_similarities('preview/similarities/%s_similarity.txt' % source_digest)
        source_response = parse_response('preview/responses/%s.json' % source_digest)

    compare_response = ''
    if compare_digest:
        compare_response = parse_response('preview/responses/%s.json' % compare_digest)

    return render_template(
        'index.html',
        digests=digests,
        source=source_response,
        compare_response=compare_response,
        similarities=similarities
    )


@app.route("/similarities")
def get_simlist():
    files = glob.glob('preview/similarities/*_similarities.txt')
    digests = [os.path.basename(f).replace('_similarities.txt', '') for f in files]
    return flask.jsonify(ids=digests, total=len(files))


@app.route("/response/<digest>")
def get_response(digest):
    format = request.args.get('format', 'txt')

    fpath = 'preview/responses/%s_identified.json' % digest
    if not os.path.exists(fpath):
        abort(404)

    do_escape = format == 'txt'
    parsed_xml = parse_response(fpath, do_escape)
    if not parsed_xml:
        abort(500)
    return Response(parsed_xml, mimetype='text/plain')


@app.route("/similarity/<digest>")
def get_similarity(digest):
    sort_order = request.args.get('order', 'asc')
    fpath = 'preview/similarities/%s_similarities.txt' % digest
    if not os.path.exists(fpath):
        abort(404)
    parsed_sim = parse_similarities(fpath, sort_order)
    if not parsed_sim:
        abort(500)
    return flask.jsonify(sorted=parsed_sim)


def parse_similarities(sim_path, sort_order='asc'):
    with open(sim_path, 'r') as f:
        data = f.readlines()
    data = [d.split(',') for d in data if d]
    data = {d[1].strip(): d[0].strip() for d in data[1:] if d}

    sorted_sims = sorted(data.items(), key=operator.itemgetter(1))
    if sort_order == 'desc':
        sorted_sims.reverse()
    return sorted_sims


def parse_response(digest_path, html_escape=True):
    with open(digest_path, 'r') as f:
        data = json.loads(f.read())

    content = data['content'].encode('unicode_escape')
    try:
        xml = etree.fromstring(content)
    except Exception as ex:
        raise ex
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


def generate_diff(source_xml_as_text, comparison_xml_as_text, as_table=True):
    '''
    return the difflib diff as html or as html table
    for the two pretty-printed xml
    '''
    pass


if __name__ == "__main__":
    app.run(debug=True)


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
