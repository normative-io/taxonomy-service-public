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
import os

import boto3

# The environment flag that this data loader expects.
# Comma-separated list of locations to load files from. Accepted formats:
#
# path/to/local/file.json
# path/to/local/recursive/directory/
# s3://bucket_name/
# s3://bucket_name/path/to/file.json
# s3://bucket_name/path/to/prefix/
ENV_FLAG_NAME = "TAXONOMY_JSON_FILE_DATA_SOURCES"
S3_SOURCE = "s3://"


class JsonFileDataSource:
    def __init__(self) -> None:
        self.s3 = boto3.client("s3")

    def load_taxonomies(self) -> list[dict]:
        sources = os.environ.get(ENV_FLAG_NAME, "")
        print(f"JsonFileDataSource will be based on: {ENV_FLAG_NAME}={sources}")
        if not sources:
            return []
        taxonomies = []
        for source in sources.split(","):
            if source.startswith(S3_SOURCE):
                parts = source.removeprefix(S3_SOURCE).split("/", 1)
                if len(parts) != 2:
                    raise ValueError(
                        f"Invalid S3 source: `{source}`; must be in format `s3://bucket_name/...` "
                    )
                bucket, s3_path = parts[0], parts[1]
                if source.endswith("/"):
                    taxonomies.extend(self._from_s3_prefix(bucket, s3_path))
                else:
                    taxonomies.append(self._from_s3_key(bucket, s3_path))
            else:
                if source.endswith("/"):
                    taxonomies.extend(self._from_local_dir(source))
                else:
                    taxonomies.append(self._from_local_file(source))
        return taxonomies

    def _from_local_dir(self, dir: str) -> list[dict]:
        taxonomies = []
        for dirpath, _, files in os.walk(dir):
            for filename in files:
                filepath = os.path.join(dirpath, filename)
                if filepath.endswith(".json"):
                    taxonomies.append(self._from_local_file(filepath))
        return taxonomies

    def _from_local_file(self, filepath: str) -> dict:
        print(f"Reading taxonomy from local file: {filepath}")
        with open(filepath) as f:
            return json.load(f)

    def _from_s3_prefix(self, bucket: str, prefix: str) -> list[dict]:
        list_resp = self.s3.list_objects_v2(Bucket=bucket, Prefix=prefix)
        taxonomies = []
        for content in list_resp["Contents"]:
            key = content["Key"]
            if key.endswith(".json"):
                taxonomies.append(self._from_s3_key(bucket, key))
        return taxonomies

    def _from_s3_key(self, bucket: str, key: str) -> dict:
        print(f"Reading taxonomy from S3: {key}")
        obj = self.s3.get_object(Bucket=bucket, Key=key)
        return json.loads(obj["Body"].read().decode("utf-8"))
