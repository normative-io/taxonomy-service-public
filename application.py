# Copyright 2022 Meta Mind AB
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os

import flask_monitoringdashboard
from flask import Flask, abort, request, send_from_directory
from flask_cors import CORS
from flask_json import FlaskJSON

from taxonomy.registry import Registry

app = Flask(__name__)
app.debug = True
FlaskJSON(app)
CORS(app)

# Monitoring dashboard can be found at /dashboard.
flask_monitoringdashboard.bind(app)

print("Initializing taxonomy registry...")
registry = Registry()
print("Ready!")
print("")


@app.route("/taxonomy/")
def available_taxonomies():
    return registry.available_taxonomies()


@app.route("/taxonomy/<taxonomy>/<version>/tree")
def taxonomy_tree(taxonomy, version):
    return {"tree": registry.get(taxonomy, version).tree}


@app.route("/taxonomy/<taxonomy>/tree")
def taxonomy_tree_unversioned(taxonomy):
    return taxonomy_tree(taxonomy, "")


@app.route("/taxonomy/<taxonomy>/<version>/branch/<node_id>")
def taxonomy_branch(taxonomy, version, node_id=None):
    return registry.get(taxonomy, version).get_branch(node_id) or abort(
        404, f"Node {node_id} does not exist."
    )


@app.route("/taxonomy/<taxonomy>/branch/<node_id>")
def taxonomy_branch_unversioned(taxonomy, node_id):
    return taxonomy_branch(taxonomy, "", node_id)


@app.route("/taxonomy/<taxonomy>/<version>/branch/")
def taxonomy_branch_root(taxonomy, version):
    return registry.get(taxonomy, version).get_branch() or abort(
        404, f"Taxonomy or version does not exist."
    )


@app.route("/taxonomy/<taxonomy>/branch/")
def taxonomy_branch_root_unversioned(taxonomy):
    return taxonomy_branch(taxonomy, "")


@app.route("/taxonomy/<taxonomy>/<version>/node/<node_id>")
def taxonomy_node(taxonomy, version, node_id):
    return registry.get(taxonomy, version).get_node(node_id) or abort(
        404, f"Node {node_id} does not exist."
    )


@app.route("/taxonomy/<taxonomy>/node/<node_id>")
def taxonomy_node_unversioned(taxonomy, node_id):
    return taxonomy_node(taxonomy, "", node_id)


@app.route("/taxonomy/<taxonomy>/<version>/search")
def taxonomy_search(taxonomy, version):
    query = request.args.get("query")
    max_results = int(request.args.get("n", 50))
    return {"matches": registry.get(taxonomy, version).search(query, max_results)}


@app.route("/taxonomy/<taxonomy>/search")
def taxonomy_search_unversioned(taxonomy):
    return taxonomy_search(taxonomy, "")


@app.route("/reload_data_sources/", methods=["POST"])
def reload_data_sources():
    """Triggers a refresh to the taxonomy registry.
    If successful, returns the results that `GET /taxonomy` would."""
    registry.reload_data_sources()
    return available_taxonomies()


@app.route("/version")
def version():
    with open(".commit_hash") as f:
        return f.read()


@app.route("/web/<path:path>")
def send_web(path):
    return send_from_directory(os.getcwd() + "/web", path)


@app.route("/")
def send_index():
    return send_from_directory(os.getcwd() + "/web", "index.html")


if __name__ == "__main__":
    app.run(debug=True)
