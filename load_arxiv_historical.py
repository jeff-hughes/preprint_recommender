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


connections.create_connection(hosts=[os.getenv("ELASTIC_HOST")], timeout=20)

documents = []
with open(file, "r") as f:
    # i = 0
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
        # i += 1
        # if i >= 10:
        #     break

print(f"Adding {len(data)} documents to database")
bulk(connections.get_connection(), (d.to_dict(True) for d in documents))

# data = []
# oldest_date = None
# newest_date = None
# with open(file, "r") as f:
#     i = 0
#     for line in f:
#         newdata = json.loads(line)
#         data.append(newdata)
#         v1_date = to_datetime(newdata["versions"][0]["created"])
#         vn_date = to_datetime(newdata["versions"][len(newdata["versions"])-1]["created"])
#         if oldest_date is None or v1_date < oldest_date:
#             oldest_date = v1_date
#         if newest_date is None or vn_date > newest_date:
#             newest_date = vn_date
#         i += 1
#         # if i >= 5:
#         #     break

# # print(data[0])
# print(oldest_date)
# print(newest_date)