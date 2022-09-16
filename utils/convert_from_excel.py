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

import argparse
import json
import math
import pandas as pd


def _get_parent_id(id: str, nr_digits_per_level: int, null_char: chr) -> str:
    """Returns the parent key, or empty if there's no parent.

    A parent id clears (setting null_char) the rightmost populated level.
    After that, no other level must be already null.

    >>> _get_parent_id("01034056", 2, '0')
    '01034000'
    >>> _get_parent_id("01041000", 2, '0')
    '01040000'
    >>> _get_parent_id("01000000", 2, '0')
    '00000000'
    >>> _get_parent_id("00000000", 2, '0')
    ''
    >>> # The following fails because there's a null level "00" before a non-null level "04".
    >>> _get_parent_id("01004000", 2, '0')
    Traceback (most recent call last):
    ...
    ValueError: Found null level 00 in id 01004000, but at least one lower (right) level is not null
    """
    key_length = len(id)
    if key_length % nr_digits_per_level != 0:
        raise ValueError(
            f"Key length {key_length} is not divisible by {nr_digits_per_level}"
        )

    null_level = null_char * nr_digits_per_level
    # Split the id into levels of "nr_digits_per_level" digits, e.g.,
    # if id='01034056', levels=['01', '03', '40', '56']
    levels = [
        id[i : i + nr_digits_per_level] for i in range(0, len(id), nr_digits_per_level)
    ]

    # Iterate in reverse (start from the right-most level) to find the rightmost non-null level,
    # and then make it null.
    for i in range(len(levels) - 1, -1, -1):
        if levels[i] == null_level:
            continue

        levels[i] = null_level
        parent_id = "".join(levels)

        # Make sure no previous levels are null; this is just a safety check as having
        # multiple nulls in a tree can cause problems with ancestors.
        has_null_levels = len(list(filter(lambda x: x == null_level, levels[:i]))) > 0

        if has_null_levels:
            raise ValueError(
                f"Found null level {null_level} in id {id}, but at least one lower (right) level is not null"
            )

        if id != parent_id:
            return parent_id
        return ""

    return ""


def _get_all_nodes_in_path(
    node: dict,
    id_column: str,
    name_columns: list,
    metadata_column: str,
    nr_digits_per_level: int,
    null_char: chr,
) -> list:
    """Returns all the nodes in the path from the root to 'node', starting from the root.

    >>> current_node = {"code": "010367", "category_1": "Raw Materials", "category_2": "Live Animals", "category_3": "Mink"}
    >>> _get_all_nodes_in_path(current_node, "code", ["category_1", "category_2", "category_3"], "", 2, '0')
    [{'id': '010000', 'name': 'Raw Materials'}, {'id': '010300', 'name': 'Live Animals'}, {'id': '010367', 'name': 'Mink'}]
    >>> current_node = {"code": "010067", "category_1": "Raw Materials", "category_2": "Live Animals", "category_3": "Mink"}
    >>> _get_all_nodes_in_path(current_node, "code", ["category_1", "category_2", "category_3"], "", 2, '0')
    Traceback (most recent call last):
    ...
    ValueError: Found null level 00 in id 010067, but at least one lower (right) level is not null
    """
    ancestors = []
    id = node[id_column]
    for column in name_columns[::-1]:
        if f"{node[column]}" == f"{math.nan}":
            continue
        item = {"id": id, "name": node[column].strip()}
        if (
            metadata_column in node
            and node[metadata_column]
            and f"{node[metadata_column]}" != f"{math.nan}"
        ):
            item["metadata"] = node[metadata_column]
        ancestors.append(item)

        # Update the key for the remaining items.
        id = _get_parent_id(id, nr_digits_per_level, null_char)
        if id == null_char * len(id):
            # If the parent_id is the null key, we've reached a top-level node.
            break
    return ancestors[::-1]


def _get_nodes_from_excel(
    input_file: str,
    tab: str,
    id_column: str,
    name_columns: list,
    metadata_column: str,
    nr_digits_per_level: int,
    null_char: chr = "0",
) -> list:
    """Loads data from an Excel file.

    Returns a list of nodes, with parent references when applicable.
    """
    xls = pd.ExcelFile(input_file)

    print(f"Converting tab {tab} from {input_file}")

    df = pd.read_excel(xls, tab, converters={id_column: str})

    nodes = []
    node_ids = set()

    for _, row in df.iterrows():
        all_nodes_in_path = _get_all_nodes_in_path(
            row,
            id_column,
            name_columns,
            metadata_column,
            nr_digits_per_level,
            null_char,
        )

        for idx, n in enumerate(all_nodes_in_path):
            id = n["id"]
            if id in node_ids:
                continue  # We already know about this node.

            new_node = {"id": id, "name": n["name"]}
            if "metadata" in n:
                new_node[metadata_column] = n["metadata"]

            if idx > 0:
                # Nodes are traversed from the root to the leaf, so the previous
                # node (idx-1) is the parent.
                parent = all_nodes_in_path[idx - 1]
                new_node["parent_id"] = parent["id"]

            nodes.append(new_node)
            node_ids.add(id)

    return nodes


def from_excel_to_json(
    input_file: str,
    input_tab: str,
    id_column: str,
    name_columns: list,
    metadata_column: str,
    null_char: chr,
    nr_digits_per_level: int,
    taxonomy_name: str,
    taxonomy_version: str,
    dest_file: str,
) -> None:
    nodes = _get_nodes_from_excel(
        input_file,
        input_tab,
        id_column,
        name_columns,
        metadata_column,
        nr_digits_per_level,
        null_char,
    )

    # Store the nodes sorted by their id; this does not change the logic but it makes
    # file comparison and diffs easier.
    nodes_dict = {}  # For sorting.
    sorted_nodes = []
    for n in nodes:
        nodes_dict[n["id"]] = n
    for key in sorted(nodes_dict):
        sorted_nodes.append(nodes_dict[key])

    generic_tree = {
        "name": taxonomy_name,
        "version": taxonomy_version,
        "nodes": sorted_nodes,
    }
    print(f"Writing {len(nodes)} nodes in {dest_file}")
    with open(dest_file, "w") as outfile:
        json.dump(generic_tree, outfile, indent=2, sort_keys=True)


def main():
    parser = argparse.ArgumentParser(description="Update normIds")
    parser.add_argument("--input_file", help="the input xlsx file", required=True)
    parser.add_argument(
        "--input_tab", help="the name of the tab to read", required=True
    )
    parser.add_argument(
        "--id_column", help="the name of the column that contains the id", required=True
    )
    parser.add_argument(
        "--name_columns",
        help="comma-separated list of columns that contain the names of the nodes at the different levels",
        required=True,
    )
    parser.add_argument(
        "--metadata_column",
        help="the name of the column that contains the metadata",
        default="note",
    )
    parser.add_argument(
        "--null_char", help="the null character in the ids", default="0"
    )
    parser.add_argument(
        "--nr_digits_per_level", help="the number of digits per level", default="2"
    )
    parser.add_argument(
        "--taxonomy_name", help="the name of the taxonomy", required=True
    )
    parser.add_argument(
        "--taxonomy_version", help="the version of the taxonomy", required=True
    )
    parser.add_argument(
        "--dest_file", help="the destination file for the taxonomy", required=True
    )

    args = parser.parse_args()

    from_excel_to_json(
        input_file=args.input_file,
        input_tab=args.input_tab,
        id_column=args.id_column,
        name_columns=args.name_columns.split(","),
        metadata_column=args.metadata_column,
        null_char=args.null_char,
        nr_digits_per_level=int(args.nr_digits_per_level),
        taxonomy_name=args.taxonomy_name,
        taxonomy_version=args.taxonomy_version,
        dest_file=args.dest_file,
    )

    print("Done!")


if __name__ == "__main__":
    main()
