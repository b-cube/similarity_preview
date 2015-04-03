# -*- coding: utf-8 -*-

import flask
from flask import Flask
from flask import abort
from flask import render_template
from flask import request
from flask import Response
from flask import Markup
app = Flask(__name__)

import os
import glob
import json
import operator
import difflib
from itertools import chain
from lxml import etree
# from xml.sax.saxutils import escape


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

    # digests = []
    # if not source_digest and not compare_digest:
    #     files = glob.glob('preview/similarities/*_similarities.txt')
    #     digests = [os.basename(f).replace('_similarities.txt', '') for f in files]

    source_response = ''
    if source_digest:
        similarities = parse_similarities(
            'preview/similarities/%s_similarities.txt' % source_digest,
            'desc'
        )
        # add the identification info for the first ten
        similarities = append_identities(similarities[:10])

        source_response = parse_response(
            'preview/responses/%s_identified.json' % source_digest,
            False
        )

    compare_response = ''
    if compare_digest:
        compare_response = parse_response(
            'preview/responses/%s_identified.json' % compare_digest,
            False
        )

    diff = ''
    if source_response and compare_response:
        diff = difflib.HtmlDiff().make_table(source_response.split('\n'),
                                             compare_response.split('\n'),
                                             '',
                                             '',
                                             True, 4)

    return render_template(
        'index.html',
        source_response=source_response,
        compare_response=compare_response,
        similarities=similarities,
        diff=diff
    )


@app.route("/view/<process>/<digest>")
def get_parsed(process, digest):
    # just show a nice view of the json response
    # by process level (raw, identify, parsed)

    if process not in ['cleaned', 'identified', 'parsed']:
        abort(404)

    fpath = 'preview/responses/{0}_{1}.json'.format(digest, process)


    return render_template(
        'response.html',
        response=response
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


def append_identities(tuples):
    # digest, similarity
    new_sims = []
    for t in tuples:
        with open('preview/responses/%s_identified.json' % t[0], 'r') as f:
            data = json.loads(f.read())
        identity = data.get('identity', {})
        d = {'id': t[0], 'sim': t[1]}
        d = dict(chain(d.items(), identity.items()))
        new_sims.append(d)
    return new_sims


def parse_similarities(sim_path, sort_order='asc'):
    with open(sim_path, 'r') as f:
        data = f.readlines()
    data = [d.split(',') for d in data if d]
    data = {d[1].strip(): "%.3f" % float(d[0].strip()) for d in data[1:] if d}

    sorted_sims = sorted(data.items(), key=operator.itemgetter(1))
    if sort_order == 'desc':
        sorted_sims.reverse()
    return sorted_sims


def parse_response(digest_path, html_escape=True):
    with open(digest_path, 'r') as f:
        data = json.loads(f.read())

    content = data['content'].encode('unicode_escape')
    try:
        parser = etree.XMLParser(
            encoding='utf-8',
            remove_blank_text=True,
            recover=True
        )
        xml = etree.fromstring(content, parser=parser)
    except Exception as ex:
        raise ex
    text = etree.tostring(xml, pretty_print=True)

    # html encode it
    if html_escape:
        text = Markup.escape(text)

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
