import os
import pandas as pd
from neo4j import GraphDatabase
from .schema import *


class Neo4jDatabase:
    def __init__(self, uri, username, password):
        self.driver = GraphDatabase.driver(uri, auth=(username, password))

    def close(self):
        """Close the driver connection."""
        self.driver.close()

    # Premium
    # def create_database(self, db_name):
    #     """Create a new Neo4j database."""
    #     query = f"CREATE DATABASE {db_name} IF NOT EXISTS"
    #     with self.driver.session(database="system") as session:
    #         session.run(query)
    #         print(f"Database '{db_name}' created (if it didn't already exist).")

    # def drop_database(self, db_name):
    #     """Drop an existing Neo4j database."""
    #     query = f"DROP DATABASE {db_name} IF EXISTS"
    #     with self.driver.session(database="system") as session:
    #         session.run(query)
    #         print(f"Database '{db_name}' dropped (if it existed).")

    # def use_database(self, db_name):
    #     """Use a specific database."""
    #     print(f"Switched to database '{db_name}'.")
    #     return self.driver.session(database=db_name)

    # Check node exist with label and id
    def check_node_exists(self, node: BaseNode): 
        with self.driver.session() as session:
            query = (
                f"MATCH (n:{node.label} {{ id: $value }}) "
                "RETURN COUNT(n) > 0 AS exists"
            )
            result = session.run(query, value=node.id)
            record = result.single()
            return record["exists"] if record else False

    # Create Node
    def add_node(self, node: BaseNode):

        label = node.label
        properties = node.model_dump()
        if self.check_node_exists(node):
            return "The node has existed"
        query = f"CREATE (n:{label} {{ {self._format_properties(properties)} }}) RETURN n"
        
        with self.driver.session() as session:
            result = session.run(query, **properties)
            return result.single()[0]

    # Delete Node
    def delete_node(self, label, property_key, property_value):
        query = f"MATCH (n:{label} {{{property_key}: $value}}) DETACH DELETE n"
        with self.driver.session() as session:
            session.run(query, value=property_value)
    
    # Delete all nodes
    def delete_all_nodes(self):
        input_key = input("This command will delete all old data. Press 'Yes' to continue: ")
        if input_key.upper() != 'YES':
            print("Stop delete sucessfully!")
            return 0
        with self.driver.session() as session:
            query = "MATCH (n) DETACH DELETE n"
            session.run(query)
            print("All nodes and relationships have been deleted.")

    # Update Node
    def update_node(self, label, property_key, property_value, updates):
        set_clause = ", ".join([f"n.{k} = ${k}" for k in updates])
        query = f"""
        MATCH (n:{label} {{{property_key}: $value}})
        SET {set_clause}
        RETURN n
        """
        with self.driver.session() as session:
            result = session.run(query, value=property_value, **updates)
            return result.single()[0]

    # Search Node
    def search_node(self, label, filters=None):
        where_clause = self._format_filters(filters) if filters else ""
        query = f"MATCH (n:{label} {where_clause}) RETURN n"
        with self.driver.session() as session:
            return [record["n"] for record in session.run(query)]

    def check_relationship_exists(self, label1, key1, value1, label2, key2, value2, rel_type):
        with self.driver.session() as session:
            query = f"""
                MATCH (a:{label1} {{{key1}: $value1}})-[r:{rel_type}]-(b:{label2} {{{key2}: $value2}})
                RETURN COUNT(r) > 0 AS exists
                """
            result = session.run(query, value1=value1, value2=value2)
            record = result.single()
            return record["exists"] if record else False

    # Add Relationship
    def add_relationship(self, label1, key1, value1, label2, key2, value2, rel_type, rel_properties=None, raise_exception = True):
        if self.check_relationship_exists(label1, key1, value1, label2, key2, value2, rel_type):
            return "The relationship has existed"
        rel_props = f"{{ {self._format_properties(rel_properties)} }}" if rel_properties else ""
        query = f"""
        MATCH (a:{label1} {{{key1}: $value1}})
        MATCH (b:{label2} {{{key2}: $value2}})
        CREATE (a)-[r:{rel_type} {rel_props}]->(b)
        RETURN r
        """
        with self.driver.session() as session:
            if rel_properties is not None:
                result = session.run(query, value1=value1, value2=value2, **rel_properties)
            else:
                result = session.run(query, value1=value1, value2=value2)
            if raise_exception:
                if result.single() is None:
                    raise Exception
            return result.single()
            

    # Delete Relationship
    def delete_relationship(self, label1, key1, value1, label2, key2, value2, rel_type):
        query = f"""
        MATCH (a:{label1} {{{key1}: $value1}})-[r:{rel_type}]-(b:{label2} {{{key2}: $value2}})
        DELETE r
        """
        with self.driver.session() as session:
            session.run(query, value1=value1, value2=value2)
    
    # Get all node with label and properties
    def get_nodes_with_filter(self, label, filters):

        where_clause = ""
        if filters is not None:
            where_clause = "WHERE " + " AND ".join([f"n.{k} = ${k}" for k in filters])

        query = f"MATCH (n:{label}) {where_clause} RETURN n"
        with self.driver.session() as session:
            result = session.run(query, **filters)
            return [record["n"] for record in result]

    # Helper: Format Properties for Cypher Queries
    def _format_properties(self, properties):
        return ", ".join([f"{k}: ${k}" for k in properties])

    # Helper: Format Filters for WHERE Clauses
    def _format_filters(self, filters):
        return "{" + ", ".join([f"{k}: ${k}" for k in filters]) + "}"
    
    def export_data(self, query, filename):
        with self.driver.session() as session:
            result = session.run(query)
            data = [record.data() for record in result]
            if data:
                df = pd.DataFrame(data)
                df.to_csv(filename, index=False)
                print(f"Data exported to {filename}")
            else:
                print("No data found for query:", query)
    
    def export_all_data(self, folder_path):
        self.export_data(
            "MATCH (n) RETURN id(n) AS id, labels(n) AS labels, properties(n) AS properties", 
            os.path.join(folder_path,"nodes.csv")
        )

        self.export_data(
            """
            MATCH (a)-[r]->(b) 
            RETURN id(r) AS id, type(r) AS type, id(a) AS start, id(b) AS end, properties(r) AS properties
            """, 
            os.path.join(folder_path, "relationships.csv")
        )
    
    def import_all_data(self, folder_path):
        self.delete_all_nodes()

        node_file_name = os.path.join(folder_path,"nodes.csv")
        nodes = pd.read_csv(node_file_name)
        with self.driver.session() as session:
            for _, row in nodes.iterrows():
                labels = ':'.join(eval(row['labels']))  # Join multiple labels with ':'
                properties = eval(row['properties'])  # Convert properties from string to dict

                # Build dynamic SET statement from properties dictionary
                set_statements = ', '.join([f"n.{key} = $props['{key}']" for key in properties.keys()])

                query = f"""
                CREATE (n:{labels})
                SET {set_statements}
                """
                session.run(query, props=properties)
        print(f"Nodes imported from {node_file_name}")

        relation_file_name =  os.path.join(folder_path, "relationships.csv")
        relationships = pd.read_csv(relation_file_name)
        with self.driver.session() as session:
            for _, row in relationships.iterrows():
                properties = eval(row['properties'])  # Convert properties from string to dict

                query = f"""
                MATCH (a), (b)
                WHERE id(a) = {row['start']} AND id(b) = {row['end']}
                CREATE (a)-[r:{row['type']}]->(b)
                SET r += $props
                """
                session.run(query, props=properties)
        print(f"Relationships imported from {relation_file_name}")