# taxonomy-service

An extensible rest API (with a light web UI on top) serving taxonomy data.

Includes text search of names in taxonomies. The main part is an API for fuzzy search but this service also provides a reference implementation of a client that uses the API to search in a tree.

## Method

Responses are ranked with a combination of:

- Fuzzy search (find partial near matches, favour matches in the beginning of names. "pas" matches "peas" but "pass" matches "passenger" and "get" matches (hotel stay in) "germany")
- Semantic search ("tiny" also matches "small")

Taxonomies:

- CPA
- UNSPSCS
- NACES

## Setup environment for local development

    make dev-setup

## Serve locally

This starts the application locally that you can navigate to with a web browser where you can search the taxonomy.

    make up

## Test

    make -j 8 test

This make target runs both unit tests with pytest and integration tests.

When taxonomy-service is served locally (see above) the integration tests can then be executed with:

    ./integrationtests.sh

## Export a taxonomy from an Excel file into a loadable taxonomy json file

You can run a script to export a taxonomy from an Excel tab into a file that the taxonomy-service can load.

The Excel file needs to have the following format:

- Each row contains an item.
- The name of the nodes must be specified in multiple columns, one per level of the tree.
- The id must be present in one column.
- The length of the id is the same for all items.
- The id of each node is composed by the concatenation of the partial ids of the previous node.

The script creates the intermediate nodes along the way. For instance, imagine you have the
following data where each level defines two digits in the identifier:

| category_1    | category_2    | category_3   | category_4 | identifier |
| ------------- | ------------- | ------------ | ---------- | ---------- |
| Raw Materials | Live Plant... | Live animals | Dogs       | 10101502   |
| Raw Materials | Live Plant... | Live animals | Mink       | 10101504   |

If you run the script assuming 00 is a null level, it will create a tree with the following structure:

- Raw Materials (id 10000000)
  - Live Plant... (id 10100000)
    - Live Animals (id 10101500)
      - Dogs (id 10101502)
      - Mink (id 10101504)

Example run:

    pipenv run python utils/convert_from_excel.py \
        --input_file "./data/My Sheet.xlsx" \
        --input_tab "my_tab_name" \
        --id_column "my_id" \
        --name_columns "level_1,level_2,level_3,level_4,level_5" # comma-separated
        --metadata_column "note"
        --null_char '0'
        --nr_digits_per_level 2
        --taxonomy_name "my-taxonomy"
        --taxonomy_version "converted-from-excel"
        --dest_file "data/my_destination_file.json"

## Contributing

This project is maintained by Normative but currently not actively seeking external contributions. If you however are interested in contributing to the project please [sign up here](https://docs.google.com/forms/d/e/1FAIpQLSe80c9nrHlAq6w2vUbeFSPVGG7IPqorKMkizhHJ98viwnT-OA/viewform?usp=sf_link) or come [join us](https://normative.io/jobs/).

Thank you to all the people from Google.org who were critical in making this project a reality!
- Carmen Ruiz Vicente: ([@carmrui](https://github.com/carmrui))
- Dan Radion: ([@danradion](https://github.com/danradion))

## License
Copyright (c) Meta Mind AB. All rights reserved.

Licensed under the [Apache-2.0 license](/LICENSE)
