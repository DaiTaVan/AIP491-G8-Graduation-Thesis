from neo4j_database import Neo4jDatabase

URI = "neo4j://localhost"
AUTH = ("neo4j", "Abc12345")

db = Neo4jDatabase(
        uri=URI, username=AUTH[0], password=AUTH[1]
    )

db.export_all_data(folder_path='/media/tavandai/DATA6/fpt_university/Graduation_Thesis/AIP491-G8-Graduation-Thesis/knowledge_graph/backup')