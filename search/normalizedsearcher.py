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

"""
>>> tree = [{"id": "1", "name": "a"},
...         {"id": "2", "name": "b", "unitDividers": ["kg"]},
...         {"id": "3", "name": "c"}
...         ]
>>> ns = NormalizedSearcher(tree)
>>> ns("b")
[{'score': 0.97, 'id': '2', 'name': 'b', 'unitDividers': ['kg']}]
>>> ns("b")[0]["id"]
'2'
>>> ns("b")[0]["name"]
'b'
>>> type(ns("b")[0]["score"])
<class 'numpy.float64'>
"""

from search.searcher import Searcher


class NormalizedSearcher:
    docs: list

    def __init__(self, N, use_nlp=True, use_textsim=True):
        self.docs = N
        self.searcher = Searcher(
            [n["id"] for n in N],
            [n["name"] for n in N],
            use_nlp=use_nlp,
            use_textsim=use_textsim,
        )

    def lookup(self, id):
        D = [n for n in self.docs if n["id"] == id]

        if len(D) > 1:
            # It was a mistake to use 0 both for 'Uncategorized' and for an unspecified subtree
            if D[0]["name"] == "Uncategorized":
                D = [D[0]]

        assert len(D) == 1
        return D[0]

    def buildResponse(obj, score):
        S = {"score": round(score, 3)}
        S.update(obj)
        return S

    def __call__(self, text, max_results: int = 20, threshold: float = 0.7):
        (ids, names, scores) = self.searcher(text, max_results, threshold)
        if len(scores) > 0 and scores.max() - scores.min() > 0:
            scores = (scores - scores.min()) / (scores.max() - scores.min())
        return [
            NormalizedSearcher.buildResponse(self.lookup(id), score)
            for (id, score) in zip(ids, scores)
        ]
