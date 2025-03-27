import csv
import os
from rdflib import Graph, URIRef, BNode, Literal, Namespace
from rdflib.namespace import RDF, RDFS, XSD, FOAF
from urllib.request import urlopen
from urllib.error import URLError

# Create RDF Graph
kg = Graph()

# Define Namespaces
SCHEMA = Namespace("https://schema.org/")
EMO = Namespace("http://www.semanticweb.org/emotion/")
SAREF = Namespace("https://saref.etsi.org/core/")
kg.bind("schema", SCHEMA)
kg.bind("foaf", FOAF)
kg.bind("emo", EMO)
kg.bind("saref", SAREF)

# CSV file path
csv_path = "ontologies_test_2.csv"

# Load external ontologies with error handling
def load_rdf_ontology(url, format="xml"):
    try:
        print(f"Attempting to load ontology from: {url}")
        ont_graph = Graph()
        
        if url.startswith("file:"):
            # Local file
            file_path = url[5:]  # Remove 'file:' prefix
            if os.path.exists(file_path):
                ont_graph.parse(file_path, format=format)
                print(f"Loaded local ontology from {file_path}")
            else:
                print(f"WARNING: Local ontology file not found: {file_path}")
        else:
            # Remote URL
            try:
                with urlopen(url) as response:
                    ont_graph.parse(response, format=format)
                print(f"Loaded remote ontology from {url}")
            except URLError as e:
                print(f"Error loading ontology from URL {url}: {e}")
        
        return ont_graph
    except Exception as e:
        print(f"Error loading ontology {url}: {e}")
        return Graph()  # Return empty graph on error

# Load ontologies
schema_graph = load_rdf_ontology("https://schema.org/version/latest/schemaorg-current-https.ttl", format="turtle")
print(f"Schema.org ontology loaded with {len(schema_graph)} triples")

# Local EMO ontology - if available use this, otherwise proceed without
emo_graph = Graph()
emo_file = "EMO.owl"
if os.path.exists(emo_file):
    emo_graph.parse(emo_file, format="xml")
    print(f"Local EMO ontology loaded with {len(emo_graph)} triples")
else:
    print("No local EMO ontology found, proceeding without it")

# SAREF ontology
saref_graph = load_rdf_ontology("https://saref.etsi.org/core/saref.ttl", format="turtle")
print(f"SAREF ontology loaded with {len(saref_graph)} triples")

# Entity classification storage
entity_classes = {}

def find_class_in_ontology(term, graph, namespace): # Function to find a class in an ontology
    term = term.lower().replace(" ", "_")
    
    # Try exact match
    for cls in graph.subjects(RDF.type, RDFS.Class):
        cls_name = str(cls).split("/")[-1].lower()
        if cls_name == term:
            return URIRef(cls)
    
    # Try partial match
    for cls in graph.subjects(RDF.type, RDFS.Class):
        cls_name = str(cls).split("/")[-1].lower()
        if term in cls_name or cls_name in term:
            return URIRef(cls)
    
    # Fall back to namespace with term
    return namespace[term]

def get_predicate_uri(predicate): # Function to get the URI of a predicate
    term = predicate.lower().replace(" ", "_")
    
    # Try in Schema.org
    for pred in schema_graph.subjects(RDF.type, RDF.Property):
        pred_name = str(pred).split("/")[-1].lower()
        if pred_name == term:
            return URIRef(pred)
    
    # Try in SAREF
    for pred in saref_graph.subjects(RDF.type, RDF.Property):
        pred_name = str(pred).split("/")[-1].lower()
        if pred_name == term:
            return URIRef(pred)
    
    # Try partial matches in Schema.org
    for pred in schema_graph.subjects(RDF.type, RDF.Property):
        pred_name = str(pred).split("/")[-1].lower()
        if term in pred_name or pred_name in term:
            return URIRef(pred)
    
    # Try partial matches in SAREF
    for pred in saref_graph.subjects(RDF.type, RDF.Property):
        pred_name = str(pred).split("/")[-1].lower()
        if term in pred_name or pred_name in term:
            return URIRef(pred)
    
    # Map some common predicates to known URIs
    predicate_map = {
        "likes": SCHEMA.likes,
        "works_in": SCHEMA.worksFor,
        "interested_in": SCHEMA.interestedIn,
        "friend_of": SCHEMA.knows,
        "watched": SCHEMA.potentialAction,  # Related to watching
        "impressed_by": SCHEMA.reviewRating,  # Related to impression
        "visited": SCHEMA.location,  # Related to visitation
        "hates": SCHEMA.additionalProperty,  # No direct "hates" in schema
        "feels": EMO.hasEmotion,  # Emotional state
        "played": SCHEMA.location  # Activity location
    }
    
    if term in predicate_map:
        return predicate_map[term]
    
    # Default to schema namespace
    return SCHEMA[term]

def infer_class(entity, predicate=None): # Function to infer class of an entity
    if entity in entity_classes:
        return entity_classes[entity]
    
    # Default class is Thing
    inferred_class = SCHEMA.Thing
    
    # Try to infer class based on predicate context
    context_map = {
        "visited": SCHEMA.Place,
        "works in": SCHEMA.Place,
        "watched": SCHEMA.CreativeWork,
        "impressed by": SCHEMA.CreativeWork,
        "interested in": SCHEMA.CreativeWork,
        "likes": SCHEMA.Thing,
        "hates": SCHEMA.Thing,
        "played": SCHEMA.SportsEvent,
        "feels": EMO.Emotion
    }
    
    if predicate and predicate in context_map:
        inferred_class = context_map[predicate]
    else:
        # Try finding entity in ontologies
        entity_term = entity.lower().replace(" ", "_")
        
        # Check in Schema.org
        for cls in schema_graph.subjects(RDF.type, RDFS.Class):
            cls_name = str(cls).split("/")[-1].lower()
            if entity_term == cls_name or entity_term in cls_name:
                inferred_class = URIRef(cls)
                break
        
        # Check in EMO ontology
        if inferred_class == SCHEMA.Thing:
            for cls in emo_graph.subjects(RDF.type, RDFS.Class):
                cls_name = str(cls).split("/")[-1].lower()
                if entity_term == cls_name or entity_term in cls_name:
                    inferred_class = URIRef(cls)
                    break
    
    entity_classes[entity] = inferred_class
    return inferred_class

def parse_triple(triple_str): # Function to parse a triple string
    if not triple_str.startswith("(") or ")" not in triple_str: # Check if the string is a valid triple
        return None, None, None
        
    # Extract contents within parentheses
    content = triple_str.split(")")[0][1:]
    parts = content.split(",")
    
    if len(parts) < 3:
        return None, None, None
        
    subject = parts[0].strip()
    predicate = parts[1].strip()
    obj = parts[2].strip()
    
    return subject, predicate, obj

# Function to extract attributes from a CSV row
def extract_attributes(row):
    attributes = []
    
    if isinstance(row, list) and len(row) == 1: # Check if the row is a list and has only one element
        row = row[0].split(",")  # Split the element by comma

    if len(row) > 4: # Check if the row has more than 4 elements
        raw_attr = row[4:]  

        # Clean attributes from quotes and spaces
        raw_attr = [attr.strip().strip('"') for attr in raw_attr if attr.strip()]

        # If there is only one attribute it will be a string
        attributes = raw_attr[0] if len(raw_attr) == 1 else raw_attr

    return attributes

# Process the CSV file
try:
    with open(csv_path, 'r', newline='', encoding='utf-8') as csvfile:
        # Detect CSV format
        sample = csvfile.read(1024)
        csvfile.seek(0)
                
        # CSV reader with appropriate configuration
        csv_reader = csv.reader(csvfile, quotechar='"', doublequote=True)
        header = next(csv_reader)  # Skip header
        
        for row in csv_reader:
            if not row:
                continue
                
            print(f"Processing row: {row}")
            
            # Parse triple from first column
            subject, predicate, obj = parse_triple(row[0])
            
            if not all([subject, predicate, obj]):
                print(f"Skipping invalid row - could not parse triple: {row}")
                continue
                
            # Extract timestamp (second column)
            timestamp = row[1] if len(row) > 1 else None
            
            # stamp subject, predicate, object and attributes
            attributes = extract_attributes(row) # Extract attributes
            print(f"Parsed: Subject={subject}, Predicate={predicate}, Object={obj}, Timespamp={timestamp} Attributes={attributes}")
            
            # Create URIs
            subj_class = infer_class(subject)
            obj_class = infer_class(obj, predicate)
            
            # Use appropriate namespace based on class
            if subj_class == FOAF.Person:
                subj_uri = URIRef(f"https://example.org/{subject.replace(' ', '_')}")
            else:
                subj_uri = SCHEMA[subject.replace(" ", "_")]
                
            if obj_class == FOAF.Person:
                obj_uri = URIRef(f"https://example.org/{obj.replace(' ', '_')}")
            else:
                obj_uri = SCHEMA[obj.replace(" ", "_")]
            
            # Get predicate URI from ontologies
            pred_uri = get_predicate_uri(predicate)
            
            # Add type triples
            kg.add((subj_uri, RDF.type, subj_class))
            kg.add((obj_uri, RDF.type, obj_class))
            
            # Add base relationship
            kg.add((subj_uri, pred_uri, obj_uri))
            
            # Handle attributes if present
            if attributes:
                relationship_node = BNode()  # Blank node to represent relationship
                kg.add((subj_uri, pred_uri, relationship_node))  # union between subject and relationship
                kg.add((relationship_node, RDF.type, SCHEMA.QualitativeValue))
                kg.add((relationship_node, SCHEMA.relatedTo, obj_uri))  # relationship with object

                # Add every attribute to the relationship
                for attr in attributes:
                    attr_literal = Literal(attr.strip(), datatype=XSD.string)
                    kg.add((relationship_node, SCHEMA.qualifierValue, attr_literal))
                    print(f"Added Attribute to Relationship: ({relationship_node}, schema:qualifierValue, {attr_literal})")
            else:
                # Normal triple without additional properties
                kg.add((subj_uri, pred_uri, obj_uri))
    
    # Print graph statistics
    print(f"Knowledge Graph contains {len(kg)} triples")
    
    # Save graph to TTL file
    kg.serialize("knowledge_graph_dynamic.ttl", format="turtle")
    print("Knowledge Graph saved as 'knowledge_graph_dynamic.ttl'")
    
except Exception as e:
    print(f"Error processing data: {e}")
    import traceback
    traceback.print_exc()