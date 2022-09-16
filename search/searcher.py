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
>>> names = ["c", "a", "b", "d", " "]
>>> s = Searcher(names, names)
>>> (best_id, best_names, best_scores) = s("b")
>>> (best_id, best_names, best_scores)
(array(['b'], dtype='<U1'), array(['b'], dtype='<U1'), array([0.97]))

>>> names = ["car", "small car", "medium car", "big car", "carpet", "carbon"]
>>> s = Searcher(names, names)
>>> (best_id, best_names, best_scores) = s("car")
>>> best_names
array(['car', 'big car', 'medium car', 'small car'], dtype='<U10')
>>> best_scores.round(3)
array([0.94, 0.88, 0.85, 0.85])
"""

import numpy as np
import numpy.typing as npt
import spacy
from spacy.vectors import Vectors

import search.stringsimilarity as sim


def memoize(f):
    results = {}

    def helper(n):
        if n not in results:
            results[n] = f(n)
        return results[n]

    return helper


@memoize
def lazyspacy(model="en_core_web_md"):
    # only want 'tok2vec'
    return spacy.load(
        model, disable=["tagger", "parser", "ner",
                        "attribute_ruler", "lemmatizer"]
    )


def normalizestring(s):
    """
    >>> normalizestring("AbcéÅäö-- !")
    'abc !'
    """
    return s.casefold().encode("ascii", "ignore").decode().replace("-", "")


def levels(id):
    """
    >>> levels('00000000')
    0
    >>> levels('30000000')
    1
    >>> levels('12345600')
    3
    >>> levels('12005600')
    2
    >>> levels('03011502030000')
    5
    """
    if len(id) == 0:
        return 0
    return (id[:2] != "00") + levels(id[2:])


def invert_permutation(keys):
    """
    >>> invert_permutation([1, 2, 0])
    array([2, 0, 1])
    """
    keys = np.asarray(keys)
    inv = np.empty_like(keys)
    inv[keys] = np.arange(len(inv), dtype=inv.dtype)
    return inv


class Searcher:
    vectors: Vectors
    ids: npt.ArrayLike
    names: npt.ArrayLike
    nlp = None
    soundex = None
    soundex_names: list
    penalty: npt.ArrayLike
    use_textsim = True

    def __init__(
        self,
        ids,
        names,
        use_nlp=True,
        use_textsim=True,
        nlp=lazyspacy("en_core_web_md"),
    ):
        names = [normalizestring(n) for n in names]
        split_names = [list(sim.splitwords(n)) for n in names]

        # Remove names that are effectively empty
        nonempty = 0 < np.array([len(s) for s in split_names])
        ids = np.asarray(ids)[nonempty]
        names = np.asarray(names)[nonempty]
        split_names = np.array(split_names, dtype=object)
        split_names = split_names[nonempty].tolist()

        if use_nlp:
            data = np.array([x.vector for x in nlp.pipe(names.tolist())])
            self.vectors = Vectors(data=data, keys=range(len(data)))
        else:
            self.vectors = None

        self.ids = ids
        self.penalty = np.asarray([0.03 * levels(id) for id in ids])
        self.names = names
        self.split_names = split_names
        self.nlp = nlp
        self.use_textsim = use_textsim

    def score_nlp(self, name):
        if len(name) < 3 or self.vectors == None:
            return np.zeros(len(self.names))

        query = self.nlp(name).vector
        (keys, best_rows, scores) = self.vectors.most_similar(
            np.asarray([query]), n=len(self.names), sort=False
        )

        invkeys = invert_permutation(keys.flatten())
        return np.maximum(0, scores.flatten()[invkeys])

    def __call__(self, name, n=20, threshold=0.7, relative_threshold=0.8):
        name = normalizestring(name)

        if name == "":
            return ([], [], [])

        scores = self.score_nlp(name)

        if self.use_textsim:
            scores = np.maximum(
                scores, sim.score_jaro_winkler_split_names(
                    name, self.split_names) ** 2
            )

        scores[scores < threshold] = -1
        scores = scores - self.penalty

        # Make response order well defined:
        # Sort ascending by (-score, names, ids)
        # i.e 1) highest score first,
        #     2) then separate by name for equal scores,
        #     3) then separate by id for equal names
        best_rows = np.argsort(self.ids, kind="stable")
        best_rows = best_rows[np.argsort(self.names[best_rows], kind="stable")]
        best_rows = best_rows[np.argsort(-scores[best_rows], kind="stable")]

        best_rows = best_rows[:n]
        best_rows = best_rows[scores[best_rows]
                              > scores.max() * relative_threshold]
        best_rows = best_rows[scores[best_rows] > 0]

        return (self.ids[best_rows], self.names[best_rows], scores[best_rows])
