# users, comments, files, books

# get users from file -> fill the defaults -> put into database ->
# load from database -> add a comment -> load to mongodb

# books -> embed text content (for search) ->
# put metadata to relational database ->
# put text into other database ->
# load to mongo -> find concepts

# - scientific articles -> load scientific from csv (file):
# metadata and filename -> put into relational database
# -> load from db -> load files from disk -> put into mongodb

# - images

# 0. "data/papers/articles.csv" (csv file)
# 1. lines from CSV
# 2. article objects from SQLAlchemy
# 3. mongo documents

# pandas:
# data.pipe(to_lines).pipe(to_sql).pipe(to_mongo)
#
# "proton collision" -> [0.23, -0.45, 0.78, ...]
# "proton collision happens in LHC" -> [0.23, -0.45, 0.78, ...]
# "proton collision is an operation between two protons" -> [0.21, -0.40, 0.80, ...]
