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

import Levenshtein
import re
import numpy as np
import math


_splitwordsre = re.compile(r"[^a-zA-Z]")


def score_jaro_winkler_split_names(name, split_names):
    """
    >>> score_jaro_winkler_split_names('car', [['big','car']])[0]
    1.0
    >>> round(score_jaro_winkler_split_names('big car', [['car']])[0], 2)
    0.84
    >>> round(score_jaro_winkler_split_names('klorid metyl', [['methyl','chloride']])[0], 2)
    0.9
    >>> round(score_jaro_winkler_split_names('metyl klorid', [['methyl','chloride']])[0], 2)
    0.9
    >>> round(score_jaro_winkler_split_names('chl', [['methyl','chloride']])[0], 2)
    0.85
    >>> score_jaro_winkler_split_names('chlo', [['methyl','chloride']])[0]
    0.9
    """
    return cmdsplitsarray_split_names(
        lambda x: x, Levenshtein.jaro_winkler, name, split_names
    )


def cmdsplitsarray(f1, f2, name, names):
    names1 = [f1(w) for w in splitwords(name)]
    names2 = (list(map(f1, splitwords(n))) for n in names)
    return np.asarray([cmpsplits(f2, names1, n) for n in names2])


def cmdsplitsarray_split_names(f1, f2, name, split_names):
    names1 = [f1(w) for w in splitwords(name)]
    return np.asarray([cmpsplits(f2, names1, n) for n in split_names])


def splitwords(name):
    """
    >>> list(splitwords('uafygwe#;3! (iuf) hui :)'))
    ['uafygwe', 'iuf', 'hui']
    """
    return (n for n in _splitwordsre.split(name) if n)


def cmpsplits(f2, names1, names2):
    """
    >>> f = lambda a,b: len(a) + len(b)
    >>> round(cmpsplits(f, ['a','bc','def'], ['g', 'hi','jkl']), 2)
    5.19
    >>> ((np.asarray([4, 5, 6])**4).mean()**(1/4)).round(2)
    5.19
    """
    a = [max(f2(n, c) for c in names2) for n in names1]
    return (np.asarray(a) ** 4).mean() ** (1 / 4)
