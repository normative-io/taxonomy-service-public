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

function finish {
    kill $PID
}

trap finish EXIT


# Start app
export TAXONOMY_JSON_FILE_DATA_SOURCES=data/
FLASK_DEBUG=1 python application.py &
PID=$!

HOST=127.0.0.1
PORT=5000
echo "Waiting for ${HOST}:${PORT} to be reachable..."
sleep 5;
timeout 30s bash -c "until curl -I ${HOST}:${PORT} >/dev/null; do sleep 1; done"

./integrationtests.sh
