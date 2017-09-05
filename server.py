from flask import Flask, render_template, request, url_for, redirect, abort
import systembolaget

app = Flask(__name__)
app.config['STORES'] = systembolaget.get_stores()

@app.route('/')
def index(stores=None):
    return render_template('index.html', stores=app.config['STORES'])

@app.route('/add_stores', methods=['GET', 'POST'])
def add_stores(stores=None, store1_info=None, store2_info=None):
    store1_id = request.args.get('store1')
    store2_id = request.args.get('store2')
    return render_template(
        'results.html',
        stores=systembolaget.compare_stores(store1_id, store2_id),
        store1_info=systembolaget.get_store_info(app.config['STORES'], store1_id),
        store2_info=systembolaget.get_store_info(app.config['STORES'], store2_id)
    )

if __name__ == "__main__":
    app.run(debug=True)
