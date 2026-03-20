from InvertIndex import *

ii = InvertedIndex()

data = [
    { "term": "apple", "documents": [1,2,3] },
    { "term": "banana", "documents": [2,5,6] },
    { "term": "orange", "documents": [4,3,8] },
    { "term": "pear", "documents": [9,2,1] }
]

for d in data:
    ii.update(d["term"], d["documents"])

print(ii.Query(ii.q_not(["apple", "banana"])))

ii.save()

ii = InvertedIndex.load()

print(ii.Query(ii.q_not(["apple", "banana"])))
