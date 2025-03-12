from rdflib import Graph, Namespace, URIRef, Literal
from rdflib.namespace import RDF, RDFS, FOAF, XSD

# Create an RDF graph
kg = Graph()

# Define namespaces for different ontologies
SCHEMA = Namespace("https://schema.org/")  # Schema.org namespace
EMO = Namespace("https://bioportal.bioontology.org/ontologies/EMO/")  # Emotion Ontology namespace
IOT = Namespace("https://lov4iot.appspot.com/")  # IoT Ontology namespace
LEXINFO = Namespace("https://lexinfo.net/")  # LexInfo Ontology namespace

# Define a person instance
person_uri = URIRef("https://example.org/person/123")  # Unique identifier for the person
kg.add((person_uri, RDF.type, FOAF.Person))  # Declare the instance as a FOAF Person
kg.add((person_uri, FOAF.name, Literal("Alice", datatype=XSD.string)))  # Add name property
kg.add((person_uri, SCHEMA.age, Literal(30, datatype=XSD.integer)))  # Add age property

# Define an emotion instance
emotion_uri = URIRef("https://example.org/emotion/happy")  # Unique identifier for emotion
kg.add((emotion_uri, RDF.type, EMO.Emotion))  # Declare the instance as an Emotion
kg.add((person_uri, SCHEMA.feels, emotion_uri))  # Link the person to their emotion

# Define an IoT device instance
device_uri = URIRef("https://example.org/device/001")  # Unique identifier for the device
kg.add((device_uri, RDF.type, IOT.Device))  # Declare the instance as an IoT Device
kg.add((device_uri, SCHEMA.name, Literal("Smartwatch", datatype=XSD.string)))  # Add device name
kg.add((device_uri, IOT.connectedTo, person_uri))  # Link the device to the person

# SPARQL query to retrieve persons and their emotions
query = """
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX schema: <https://schema.org/>
PREFIX emo: <https://bioportal.bioontology.org/ontologies/EMO/>
PREFIX iot: <https://lov4iot.appspot.com/>

SELECT ?person ?emotion WHERE {
    ?person schema:feels ?emotion .
}
"""

# Execute the query and print the results
for row in kg.query(query):
    print(f"{row.person} feels {row.emotion}")

# Save the Knowledge Graph in Turtle format
kg.serialize("knowledge_graph.ttl", format="turtle")
