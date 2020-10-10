"""Loads all historical arXiv data into database

This script only needs to be run once when the database is being set up;
it reads in historical data from a JSON file (downloaded in bulk) and
feeds it into the database. Database must already be running and the
document schema/mapping already created.
"""

import os
import json
from datetime import datetime

from elasticsearch_dsl import connections
from elasticsearch.helpers import bulk

from elastic.elastic_mapping import Preprint

# this is historical arXiv data, downloaded from Kaggle:
# https://www.kaggle.com/Cornell-University/arxiv
# containing 1,761,194 articles from 1986-04-25 to 2020-09-11
file = "data/arxiv-metadata-oai-snapshot.json"

def strip_newlines(text):
    lines = text.splitlines()
    newtext = ' '.join([l.strip() for l in lines])
    return newtext

def to_datetime(date_string):
    return datetime.strptime(date_string, "%a, %d %b %Y %H:%M:%S %Z")


elastic_host = f"{os.getenv('ELASTIC_ADMIN_USER')}:{os.getenv('ELASTIC_ADMIN_PASS')}@{os.getenv('ELASTIC_HOST')}"
connections.create_connection(hosts=[elastic_host], timeout=20)

with open(file, "r") as f:
    documents = []
    i = 0
    for line in f:
        data = json.loads(line)
        preprint = Preprint(
            url=f"https://arxiv.org/abs/{data['id']}",
            source="arXiv",
            source_id=data['id'],
            publish_date=to_datetime(data['versions'][0]['created']),
            modified_date=to_datetime(data['versions'][len(data['versions'])-1]['created']),
            stored_date=datetime.now(),
            title=strip_newlines(data['title']),
            # TODO: Need to figure out how to deal with LaTeX code
            abstract=strip_newlines(data['abstract']),
            # TODO: Format authors appropriately;
            # also deal with special characters
            authors=data['authors'],
            # TODO: We will need to standardize the category labels
            # somehow
            categories=data['categories'].split(' ')
        )
        documents.append(preprint)
        i += 1
        if i % 1000 == 0:
            print(f"Adding {len(documents)} documents ({i} so far) to database [{datetime.now()}]")
            bulk(connections.get_connection(), (d.to_dict(True) for d in documents))
            documents = []
    
    print(f"Adding {len(data)} documents to database [{datetime.now()}]")
    bulk(connections.get_connection(), (d.to_dict(True) for d in documents))