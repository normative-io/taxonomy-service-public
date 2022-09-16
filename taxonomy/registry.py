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

from copy import copy
from datetime import datetime
from threading import Lock
from typing import Iterator, Optional

import data_sources.jsonfile
from search.normalizedsearcher import NormalizedSearcher

from taxonomy import parser


class Taxonomy:
    name: str
    version: str
    tree: list[dict]

    _searcher: NormalizedSearcher

    def __init__(self, taxonomy: dict) -> None:
        self.name = taxonomy["name"]
        self.version = taxonomy["version"]
        self.tree = parser.buildtree(taxonomy)
        self._searcher = NormalizedSearcher(
            [
                Taxonomy._remove_children(n)
                for n in Taxonomy._depth_first_traversal(self.tree)
            ]
        )

    def get_node(self, node_id: str) -> dict:
        # Note: if needed, this can be improved in the future
        # by keeping a {node_id -> node} lookup structure.
        if node := Taxonomy._find_node(self.tree, node_id):
            return {
                # "parents" contains all of the ancestors for the node, starting at the root.
                "parents": reversed([p for p in Taxonomy._get_ancestors(self.tree, node_id)]),
                "node": Taxonomy._remove_children(node),
                "children": Taxonomy._get_immediate_children(node),
            }
        return {}

    def get_branch(self, node_id: Optional[str]) -> dict:
        children = []
        if node_id is None:
            # Return the root nodes
            children = list(map(Taxonomy._remove_children, self.tree))
        elif node := Taxonomy._find_node(self.tree, node_id):
            # Find the node and return its children
            children = list(Taxonomy._get_immediate_children(node))
        return {"branch": children}

    def search(self, query: str, max_results: int) -> list:
        return self._searcher(query, max_results)

    def nodecount(self) -> int:
        return Taxonomy._countnodes(self.tree)

    @staticmethod
    def _countnodes(tree: list[dict]) -> int:
        """
        >>> tree = [{'children': [{'children': [{'name': 'me'}]}]},{'name': 'you'}]
        >>> Taxonomy._countnodes(tree)
        4
        """
        return len(tree) + sum(
            Taxonomy._countnodes(c["children"]) for c in tree if "children" in c
        )

    @staticmethod
    def _get_immediate_children(node: dict) -> Iterator[dict]:
        """Return the node's immediate children, without their children.

        >>> node = {'name': 'me', 'children': [{'name': 'you'}, {'name': 'us', 'children': [{'name': 'they'}]}]}
        >>> list(Taxonomy._get_immediate_children(node))
        [{'name': 'you'}, {'name': 'us'}]
        """
        if "children" in node:
            for c in node["children"]:
                yield Taxonomy._remove_children(c)

    @staticmethod
    def _depth_first_traversal(tree: list[dict]) -> Iterator[dict]:
        """Iterate through all nodes recursively using a pre-order depth-first search.

        >>> tree = [
        ...     {
        ...         "id": "1",
        ...         "children": [
        ...             {"id": "2", "children": [{"id": "3"}]},
        ...             {"id": "4"},
        ...         ],
        ...     },
        ...     {"id": "5"},
        ... ]
        >>> list(Taxonomy._depth_first_traversal(tree))
        [{'id': '1', 'children': [{'id': '2', 'children': [{'id': '3'}]}, {'id': '4'}]}, {'id': '2', 'children': [{'id': '3'}]}, {'id': '3'}, {'id': '4'}, {'id': '5'}]
        """
        for child in tree:
            yield child
            if "children" in child:
                yield from Taxonomy._depth_first_traversal(child["children"])

    @staticmethod
    def _find_node(tree: list[dict], node_id: str) -> Optional[dict]:
        """Find a given node in the tree by id
        >>> tree = [
        ...     {
        ...         "id": "1",
        ...         "children": [
        ...             {"id": "2", "children": [{"id": "3"}]},
        ...             {"id": "4"},
        ...         ],
        ...     },
        ...     {"id": "5"},
        ... ]
        >>> Taxonomy._find_node(tree, "2")
        {'id': '2', 'children': [{'id': '3'}]}
        """
        for n in Taxonomy._depth_first_traversal(tree):
            if n["id"] == node_id:
                return n
        return None

    @staticmethod
    def _depth_first_traversal_with_parents(tree: list[dict], parent: dict = None) -> Iterator:
        """Iterate through all nodes recursively using a post-order depth-first search, yielding each node and its parent.

        When using post-order, nodes are emitted before their parents. This enables callers to
        reconstruct the path from a node to the root.

        >>> tree = [
        ...     {
        ...         "id": "1",
        ...         "children": [
        ...             {"id": "2", "children": [{"id": "3"}]},
        ...             {"id": "4"},
        ...         ],
        ...     },
        ...     {"id": "5"},
        ... ]
        >>> list(Taxonomy._depth_first_traversal_with_parents(tree))
        [({'id': '3'}, {'id': '2'}), ({'id': '2', 'children': [{'id': '3'}]}, {'id': '1'}), ({'id': '4'}, {'id': '1'}), ({'id': '1', 'children': [{'id': '2', 'children': [{'id': '3'}]}, {'id': '4'}]}, None), ({'id': '5'}, None)]
        """
        for child in tree:
            if "children" in child:
                yield from Taxonomy._depth_first_traversal_with_parents(child["children"], child)
            yield child, Taxonomy._remove_children(parent) if parent else None

    @staticmethod
    def _get_ancestors(tree: list[dict], node_id: str) -> Iterator:
        """Return a node's ancestors, starting from the most immediate ancestor and finishing at the top-level one.

        Ancestors are returned without their children.

        >>> tree = [
        ...     {
        ...         "id": "1",
        ...         "children": [
        ...             {"id": "2", "children": [{"id": "3"}]},
        ...             {"id": "4"},
        ...         ],
        ...     },
        ...     {"id": "5"},
        ... ]
        >>> list(Taxonomy._get_ancestors(tree, "3"))
        [{'id': '2'}, {'id': '1'}]
        >>> list(Taxonomy._get_ancestors(tree, "2"))
        [{'id': '1'}]
        """
        id_to_find = node_id
        for n, p in Taxonomy._depth_first_traversal_with_parents(tree):
            if n["id"] == id_to_find:
                # We only want to return the ancestors, not the actual node.
                if id_to_find != node_id:
                    yield Taxonomy._remove_children(n)
                if not p:  # We've reached the root.
                    return
                # Since _depth_first_traversal_with_parents returns nodes depth-first and post-order,
                # it's guaranteed that a node's parent will be returned at some point after the node.
                id_to_find = p["id"]

    @staticmethod
    def _remove_children(n: dict) -> dict:
        """
        >>> c = {"children": 1, "foo": "bar"}
        >>> Taxonomy._remove_children(c)
        {'foo': 'bar'}
        """
        return {key: n[key]
                for key in n if key != "children"}


class Registry:
    # ID -> {Version -> Taxonomy}
    _taxonomies: dict[str, dict[str, Taxonomy]]
    _last_load_time: datetime
    _reload_mutex: Lock = Lock()

    def __init__(self) -> None:
        self.reload_data_sources()

    def available_taxonomies(self) -> dict:
        taxonomies = {}
        for t, versions in self._taxonomies.items():
            taxonomies[t] = {"versions": sorted(versions.keys())}
        return {
            "last_load_time": self._last_load_time,
            "taxonomies": taxonomies,
        }

    def get(self, id: str, version: str = "") -> Taxonomy:
        """Returns the specified version of the taxonomy.
        If version is not specified, uses the alphabetically-latest version.
        """
        if id not in self._taxonomies:
            raise ValueError(
                f"Taxonomy {id} does not exist. Available: {self._taxonomies.keys()}"
            )
        if version and version not in self._taxonomies[id]:
            raise ValueError(
                f"Version {version} does not exist for taxonomy {id}. Available: {self._taxonomies[id].keys()}"
            )
        if not version:
            version = sorted(self._taxonomies[id].keys())[-1]
        return self._taxonomies[id][version]

    def reload_data_sources(self) -> None:
        with self._reload_mutex:
            print("Reloading registry with latest taxonomies...")
            self._taxonomies = self._parse_data_sources()
            self._last_load_time = datetime.now()

    def _parse_data_sources(self) -> dict[str, dict[str, Taxonomy]]:
        taxonomies: dict[str, dict[str, Taxonomy]] = {}
        # Note: currently the available data_sources is hard-coded.
        # In the future, we may want to dynamically discover all
        # DataSources in the data_sources/ folder.
        ds = data_sources.jsonfile.JsonFileDataSource()
        for data in ds.load_taxonomies():
            t = Taxonomy(data)
            versions = taxonomies.get(t.name, {})
            versions[t.version] = t
            taxonomies[t.name] = versions
            print(
                f"Registered: taxonomy={t.name} version={t.version} nodes={t.nodecount()}"
            )
        return taxonomies
