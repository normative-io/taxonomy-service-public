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

import json

import jsonschema

with open("taxonomy/schema.json") as f:
    schema = json.load(f)


def buildtree(items: dict) -> list:
    """
    >>> items = {"name": "generic", "version": "1.2.3", "nodes": [{"id": "0", "name": "root", "parent_id": ""}, {"id": "3", "name": "another_root"}, {"id": "1", "name": "desc 1", "parent_id": "0"}, {"id": "2", "name": "desc 2", "parent_id": "0", "metadata": {"description": "some metadata"}}, {"id": "12", "name": "desc 12", "parent_id": "1"}]}
    >>> print(json.dumps(buildtree(items), indent = 3))
    [
       {
          "id": "0",
          "name": "root",
          "children": [
             {
                "id": "1",
                "name": "desc 1",
                "children": [
                   {
                      "id": "12",
                      "name": "desc 12"
                   }
                ]
             },
             {
                "id": "2",
                "name": "desc 2",
                "metadata": {
                   "description": "some metadata"
                }
             }
          ]
       },
       {
          "id": "3",
          "name": "another_root"
       }
    ]
    >>> buildtree({"id": "123", "name": "item with no version"})
    Traceback (most recent call last):
    jsonschema.exceptions.ValidationError: 'version' is a required property...
    >>> buildtree({"id": "no-name", "version": "v1"})
    Traceback (most recent call last):
    jsonschema.exceptions.ValidationError: 'name' is a required property...
    """
    jsonschema.validate(instance=items, schema=schema)
    # In a previous version of this file, the data for the children was allocated beforehand, with:
    # {"children": [None] * MAX_CHILDREN} # MAX_CHILDREN = 256
    # It's unclear whether this was done for performance reasons, but it could be a good thing to try
    # if the performance degrades especially with bigger taxonomies. Note that this would have to be
    # changed here and also when creating every new node below.
    tree: dict = {"children": list()}
    nodes: dict = {}
    for n in items["nodes"]:
        _append(tree, nodes, n)
    return _discardempty(tree)["children"]


def _append(tree: dict, nodes: dict, item: dict) -> None:
    """Append an item to the tree based on the item's parent.

    It copies over the 'id', 'name' and 'metadata' fields.

    Any item with an empty 'parent_id' will be a first level item.

    It performs validation on the items:
    - Any non-empty 'parent_id' must refer to an already known id.
    - Items cannot have duplicate ids.

    If any of the above isn't true, this function throws a ValueError exception.

    # The following are tests. Note that some of these tests are order dependent due to the iterative nature
    # of this method.
    >>> tree = {'children': list()}
    >>> nodes = {}
    >>> item = {"id": "0", "name": "first node", "metadata": "metadata in a top-level node"}
    >>> _append(tree, nodes, item)
    >>> L = tree['children'][0]; L['name']
    'first node'
    >>> L['metadata']
    'metadata in a top-level node'
    >>> item_without_parent_id = {"id": "another_item_without_parent_id", "name": "another_item_without_parent_id"}
    >>> _append(tree, nodes, item_without_parent_id)
    >>> L = tree['children'][1]; L['name']
    'another_item_without_parent_id'
    >>> item_with_unknown_parent_id = {"id": "irrelevant", "name": "irrelevant", "parent_id": "unknown_parent_id"}
    >>> _append(tree, nodes, item_with_unknown_parent_id)
    Traceback (most recent call last):
     ...
    ValueError: Unknown parent id 'unknown_parent_id'; items must be declared before they can be used as parents
    >>> valid_item_with_metadata = {"id": "1", "name": "second node", "metadata": "metadata in another node", "parent_id": "0"}
    >>> _append(tree, nodes, valid_item_with_metadata)
    >>> L = tree['children'][0]['children'][0]; L['name']
    'second node'
    >>> L['metadata']
    'metadata in another node'
    >>> valid_item_no_metadata = {"id": "2", "name": "third node","parent_id": "0"}
    >>> _append(tree, nodes, valid_item_no_metadata)
    >>> L = tree['children'][0]['children'][1]; L['name']
    'third node'
    >>> # Attempt to insert the same item again should result in an Exception
    >>> _append(tree, nodes, valid_item_no_metadata)
    Traceback (most recent call last):
     ...
    ValueError: Duplicate item id '2'
    """
    new_node_id = item["id"]
    new_node = {
        "id": new_node_id,
        "name": item["name"],
        "children": list(),
    }
    if "metadata" in item:
        # "metadata" is an optional field.
        new_node["metadata"] = item["metadata"]
    # By default, assume this is a top-level item.
    parent = tree
    if new_node_id in nodes:
        raise ValueError(f"Duplicate item id '{new_node_id}'")
    if "parent_id" in item and item["parent_id"]:
        parent_id = item["parent_id"]
        if parent_id not in nodes:
            raise ValueError(
                f"Unknown parent id '{parent_id}'; items must be declared before they can be used as parents"
            )
        parent = nodes[parent_id]
    parent["children"].append(new_node)
    nodes[new_node_id] = new_node


def dump_to_generic_file(
    tree: dict, taxonomy_name: str, taxonomy_version: str, dest_file: str
) -> None:
    """Stores the given tree into a taxonomy tree file.

    The generic taxonomy loader expects a specific file format, with nodes having 'id' and 'name',
    and referring to their parent via a 'parent_id' field.

    This method coverts a tree structure with 'children' into a list of nodes with explicit
    parent references, and stores it into a file that can be loaded as a taxonomy tree.

    >>> import tempfile
    >>> tree = [{"id": "0", "name": "Zero", "children": [{"id": "1", "name": "One"}]}, {"id": "2", "name": "Two"}]
    >>> with tempfile.NamedTemporaryFile() as tmpfile:
    ...   dump_to_generic_file(tree, "taxonomy", "version", tmpfile.name)
    ...   with open(tmpfile.name, 'r') as f:
    ...      loaded_data = json.load(f)
    ...      print(loaded_data)
    ...      print(buildtree(loaded_data))
    {'name': 'taxonomy', 'version': 'version', 'nodes': [{'id': '0', 'name': 'Zero'}, {'id': '2', 'name': 'Two'}, {'id': '1', 'name': 'One', 'parent_id': '0'}]}
    [{'id': '0', 'name': 'Zero', 'children': [{'id': '1', 'name': 'One'}]}, {'id': '2', 'name': 'Two'}]
    """
    generic_tree = {
        "name": taxonomy_name,
        "version": taxonomy_version,
        "nodes": _to_generic_nodes(tree),
    }
    with open(dest_file, "w") as outfile:
        json.dump(generic_tree, outfile, indent=2)


def _to_generic_nodes(tree: dict, metadata_field: str = "comments") -> list:
    current = tree
    to_visit = list()
    # Map from node id to parent id.
    parents: dict = {}
    nodes = list()

    # Add the top-level nodes.
    for c in tree:
        to_visit.append(c)

    while len(to_visit) > 0:
        current = to_visit.pop(0)
        id = current["id"]

        new_node = {"id": id, "name": current["name"]}
        if metadata_field in current:
            new_node["metadata"] = {metadata_field: current[metadata_field]}

        # Do we know this node's parent?
        if id in parents:
            new_node["parent_id"] = parents[id]

        nodes.append(new_node)

        if "children" in current:
            for c in current["children"]:
                to_visit.append(c)
                parents[c["id"]] = id

    return nodes


def _discardempty(c: dict) -> dict:
    """
    >>> a = {'children':
    ...  [
    ...    {'name': 'a', 'children': []},
    ...    {'name': 'b', 'children': [
    ...      {'name': 'c', 'children': [None]}
    ...      ]},
    ...    None
    ...  ]}
    >>> _discardempty(a)
    {'children': [{'name': 'a'}, {'name': 'b', 'children': [{'name': 'c'}]}]}
    """
    if "children" not in c:
        return c

    c["children"] = [_discardempty(x) for x in c["children"] if x]
    c["children"] = [x for x in c["children"]]
    if len(c["children"]) == 0:
        del c["children"]
    return c
