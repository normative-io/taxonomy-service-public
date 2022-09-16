#!/bin/bash
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

set -e

HOST=127.0.0.1
PORT=5000

function test {
    QUERY="$1"
    GOLD="$2"

    echo "curl http://${HOST}:${PORT}$QUERY"
    RESPONSE=$(curl http://${HOST}:${PORT}$QUERY)

    PRETTY_RESPONSE="$(jq '.' <<< "$RESPONSE" || echo "$RESPONSE")"
    PRETTY_GOLD="$(jq '.' <<< "$GOLD" || echo "$GOLD")"

    if [ "$PRETTY_GOLD" != "$PRETTY_RESPONSE" ]; then
        echo "Expected:"
        echo "$PRETTY_GOLD"
        echo "Got:"
        echo "$PRETTY_RESPONSE"
        echo ""
        echo "$RESPONSE" | jq -cM .
    fi

    [ "$PRETTY_GOLD" == "$PRETTY_RESPONSE" ]
}

EXAMPLE_SEARCH='{"matches":[{"id":"CDE","name":"CDE is another top-level item of the tree","score":0.94}]}'
test "/taxonomy/example/search?query=cde" "$EXAMPLE_SEARCH"

EXAMPLE_BRANCH='{"branch":[{"id":"EFG","name":"EFG is a child of BCD"},{"id":"FGH","name":"FGH is a child of BCD"}]}'
test "/taxonomy/example/branch/BCD" "$EXAMPLE_BRANCH"

EXAMPLE_BRANCH_ROOT='{"branch":[{"id": "ABC","name": "ABC is a top-level item of the tree"},{"id": "CDE","name": "CDE is another top-level item of the tree"}]}'
test "/taxonomy/example/branch/" "$EXAMPLE_BRANCH_ROOT"

EXAMPLE_NODE='{"children": [{"id":"EFG","name":"EFG is a child of BCD"}, {"id":"FGH","name":"FGH is a child of BCD"}], "node": {"id":"BCD","metadata":{"description":"We can add arbitrary metadata to nodes"},"name":"BCD is a child of ABC"}, "parents": [{"id": "ABC","name": "ABC is a top-level item of the tree"}]}'
test "/taxonomy/example/node/BCD" "$EXAMPLE_NODE"

EXAMPLE_NODE_WITHOUT_PARENT='{"children": [{"id":"BCD","metadata":{"description":"We can add arbitrary metadata to nodes"},"name":"BCD is a child of ABC"}], "node": {"id":"ABC","name":"ABC is a top-level item of the tree"}, "parents": []}'
test "/taxonomy/example/node/ABC" "$EXAMPLE_NODE_WITHOUT_PARENT"

EXAMPLE_NODE_MULTIPLE_ANCESTORS='{"children": [], "node": {"id":"EFG","name":"EFG is a child of BCD"}, "parents": [{"id": "ABC","name": "ABC is a top-level item of the tree"}, {"id":"BCD","metadata":{"description":"We can add arbitrary metadata to nodes"},"name":"BCD is a child of ABC"}]}'
test "/taxonomy/example/node/EFG" "$EXAMPLE_NODE_MULTIPLE_ANCESTORS"

CPA='{"matches":[{"id":"21","name":"Basic pharmaceutical products and pharmaceutical preparations","score":1},{"id":"21.10","name":"Basic pharmaceutical products","score":0.64},{"id":"21.10.9","name":"Sub-contracted operations as part of manufacturing of basic pharmaceutical products","score":0.46},{"id":"21.10.99","name":"Sub-contracted operations as part of manufacturing of basic pharmaceutical products","score":0.46},{"id":"46.46.11","name":"Wholesale trade services of basic pharmaceutical products and pharmaceutical preparations","score":0.46},{"id":"20.20","name":"Pesticides and other agrochemical products","score":0}]}'
test "/taxonomy/cpa/search?query=pharmaceutical%20products" "$CPA"

echo ""
echo "ok"
