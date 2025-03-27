import csv
from rdflib import Graph, URIRef, Literal, Namespace
from rdflib.namespace import RDF, XSD
import os

# Define Namespace
EX = Namespace("https://example.org/")

# Create an RDF Graph
kg = Graph()
kg.bind("ex", EX)

# CSV file path
csv_path = "/Users/camilla/Desktop/HDT/ontologies_test_1.csv"

# Check if file exists
if not os.path.exists(csv_path):
    print(f"Error: File not found at {csv_path}")
    exit()

# Read CSV file
with open(csv_path, newline='', encoding='utf-8') as csvfile:
    csv_reader = csv.reader(csvfile)

    # Ignore header
    next(csv_reader)

    for row in csv_reader:
        print(f"RAW ROW: {row}")  # Debugging - Print raw (unprocessed) row from CSV

        if len(row) < 3:
            print("Empty or invalid row, skipping...")
            continue

        # Join first three columns (subject, predicate, object)
        triple_str = ", ".join(row[:3]).strip()
        triple_str = triple_str.strip("()")  # Remove surrounding parentheses
        elements = [e.strip() for e in triple_str.split(",")]

        # Ensure exactly 3 elements
        if len(elements) != 3:
            print(f"Skipping invalid row: {row}")  # Debugging message
            continue

        subject, predicate, obj = elements

        # Create RDF URIs
        subj_uri = URIRef(EX[subject.replace(" ", "_")])
        pred_uri = URIRef(EX[predicate.replace(" ", "_")])

        # Object handling
        if obj.istitle():
            obj_literal = URIRef(EX[obj.replace(" ", "_")])
        else:
            obj_literal = Literal(obj, datatype=XSD.string)

        # Add triple to Knowledge Graph
        kg.add((subj_uri, pred_uri, obj_literal))
        print(f"Added: ({subject}, {predicate}, {obj})")  # Debugging print

# Save Knowledge Graph to Turtle format
kg.serialize("knowledge_graph_from_csv.ttl", format="turtle")

print("Knowledge Graph saved as 'knowledge_graph_from_csv.ttl'")
