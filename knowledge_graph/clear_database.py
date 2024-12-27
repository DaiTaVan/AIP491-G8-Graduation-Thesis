
from neo4j_database import Neo4jDatabase


URI = "neo4j://localhost"
AUTH = ("neo4j", "Abc12345")

db = Neo4jDatabase(
        uri=URI, username=AUTH[0], password=AUTH[1]
    )
db.delete_all_nodes()