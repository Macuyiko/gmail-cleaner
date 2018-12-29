from model import *
from flask import *
from diffcluster import *
from fill_database import get_service


app = Flask(__name__)
app.secret_key = 'something unique and secret'


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = EmailDB(db_path)
    return db


def emails_combiner(clusters):
    representations = []
    for cluster in clusters:
        representation = cluster
        while len(representation) > 1:
            a = representation.pop()
            b = representation.pop()
            representation.append((a[0] + b[0], combine_strings(a[1], b[1])))
        representations.append(representation[0])
    return representations


def emails_matcher(clusters, ratio_threshold):
    s = SequenceMatcher()
    best_abval = (None, None, 0)
    for i in range(len(clusters) - 1):
        for j in range(i + 1, len(clusters)):
            r = min([get_ratio(a[1], b[1]) for a in clusters[i] for b in clusters[j]])
            if r > best_abval[2] and r >= ratio_threshold:
                best_abval = (i, j, r)
    return best_abval


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.conn.close()
        db = g._database = None


@app.route("/trash/<path:header_from>/", methods=['POST'])
def trash(header_from):
    def chunks(l, n):
        for i in range(0, len(l), n):
            yield l[i:i + n]
    ids = request.form.get('ids', '').split(',')
    service = get_service()
    for chunk in chunks(ids, 500):
        service.users().messages().batchModify(userId='me', body={
            'removeLabelIds': [],
            'addLabelIds': ['TRASH'],
            'ids': chunk
        }).execute()
    get_db().trash_emails([(id,) for id in ids])
    flash('Trashed message(s)')
    return redirect(url_for('header_from', header_from=header_from))


@app.route("/from/<path:header_from>/")
def header_from(header_from):
    result = get_db().select_byfrom_emails(header_from)
    print('Starting clustering...')
    representations, clusters = cluster_strings([([r['id']], r['header_subject']) for r in result], 
                                    combiner=emails_combiner, matcher=emails_matcher)
    all_ids = [x[0] for cluster in clusters for x in cluster ]
    return render_template('from.html', header_from=header_from, table=result, 
        clusters=representations, 
        all_ids=all_ids, amount=len(result))


@app.route("/")
def index():
    result = get_db().select_grouped_emails()
    return render_template('index.html', table=result)


if __name__ == "__main__":
    app.run(debug=True)