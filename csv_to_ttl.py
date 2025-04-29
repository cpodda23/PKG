import csv  # For reading CSV files
import re  # For regular expressions
import re as regex  # For additional regex processing
from rdflib import Graph, Namespace, URIRef, Literal, RDF  # For RDF graph handling
import nltk  # For natural language processing (lemmatization)
from nltk.stem import WordNetLemmatizer  # Word lemmatizer from NLTK
import pandas as pd  # For reading and processing tabular data

# Download necessary NLTK resources
nltk.download('wordnet')
nltk.download('omw-1.4')
nltk.download('stopwords')

from nltk.corpus import stopwords  # English stopwords set
stop_words = set(stopwords.words('english'))

# Define the path to the input CSV file
csv_path = "/Users/camilla/Desktop/HDT/extracted_llama4/extracted_scene0_sentences.csv"
# Define the path to the output TTL file
ttl_output_path = "/Users/camilla/Desktop/HDT/output_ttl/output_scene0.ttl"

# Define RDF namespaces for known ontologies
FOAF = Namespace("http://xmlns.com/foaf/0.1/")
PROV = Namespace("http://www.w3.org/ns/prov#")
SCHEMA = Namespace("http://schema.org/")

# Dictionary mapping known predicates to ontologies
predicate_mapping = {
    "knows": (FOAF, "knows"),
    "name": (FOAF, "name"),
    "homepage": (FOAF, "homepage"),
    "mbox": (FOAF, "mbox"),
    "member": (FOAF, "member"),
    "interest": (FOAF, "interest"),
    "based_near": (FOAF, "based_near"),
    "wasgeneratedby": (PROV, "wasGeneratedBy"),
    "wasderivedfrom": (PROV, "wasDerivedFrom"),
    "used": (PROV, "used"),
    "wasattributedto": (PROV, "wasAttributedTo"),
    "wasassociatedwith": (PROV, "wasAssociatedWith"),
    "actedonbehalfof": (PROV, "actedOnBehalfOf"),
    "agent": (PROV, "Agent"),
    "author": (SCHEMA, "author"),
    "creator": (SCHEMA, "creator"),
    "member": (SCHEMA, "member"),
    "worksfor": (SCHEMA, "worksFor"),
    "knowsabout": (SCHEMA, "knowsAbout"),
    "makesoffer": (SCHEMA, "makesOffer"),
    "publisher": (SCHEMA, "publisher"),
    "birthdate": (SCHEMA, "birthDate"),
    "deathdate": (SCHEMA, "deathDate"),
    "gender": (SCHEMA, "gender"),
    "location": (SCHEMA, "location"),
    "colleague": (FOAF, "knows"),
}

# Initialize a lemmatizer instance
lemmatizer = WordNetLemmatizer()

# Define keywords for inferring entity types
person_pronouns = ["i", "we", "he", "she", "they"]
place_keywords = ["place", "city", "country", "room", "location", "village", "town"]
organization_keywords = ["company", "organization", "university", "school", "institute", "corporation"]

# Function to normalize text for URI-safe names
def clean_name(text):
    text = text.strip().lower()  # Remove leading/trailing spaces and lowercase
    text = regex.sub(r'[^a-zA-Z0-9_]', '_', text)  # Replace special characters with underscores
    text = regex.sub(r'_+', '_', text)  # Replace multiple underscores with a single one
    text = text.strip('_')  # Remove underscores at start and end
    return text

# Function to extract triples from a CSV-formatted string
def extract_triples(triple_string):
    triple_pattern = re.compile(r'\(([^,]+),\s*([^,]+),\s*([^\)]+)\)')  # Regex pattern to match (subject, predicate, object)
    matches = triple_pattern.findall(triple_string)
    return [(s.strip(), p.strip(), o.strip()) for s, p, o in matches]

# Function to find or generate the correct predicate URI
def get_valid_predicate(predicate):
    original = predicate.strip().lower().replace(" ", "")
    lemma = lemmatizer.lemmatize(original, pos='v')  # Lemmatize as verb
    if original in predicate_mapping:
        return predicate_mapping[original]
    if lemma in predicate_mapping:
        return predicate_mapping[lemma]
    cleaned_predicate = clean_name(predicate)
    return (SCHEMA, cleaned_predicate)

# Function to validate if a triple is meaningful
def is_valid_triple(subj, pred, obj):
    if not subj or not pred or not obj:
        print(f"DISCARDED: Subject, predicate, or object is empty -> ({subj}, {pred}, {obj})")
        return False
    if subj.strip().lower() == obj.strip().lower():
        print(f"DISCARDED: Subject and object are identical -> ({subj}, {pred}, {obj})")
        return False
    if len(subj.strip()) < 2 or len(obj.strip()) < 2:
        print(f"DISCARDED: Subject or object is too short -> ({subj}, {pred}, {obj})")
        return False
    if pred.strip().lower() in ["is", "are", "was", "were", "be"]:
        print(f"DISCARDED: Predicate is too generic -> ({subj}, {pred}, {obj})")
        return False
    if re.search(r'[^a-zA-Z0-9_]', pred.strip()):
        print(f"DISCARDED: Predicate contains invalid characters -> ({subj}, {pred}, {obj})")
        return False
    return True

# Function to heuristically assign rdf:type to a subject
def assign_type(subj, subj_uri, g, typed_subjects):
    subj_clean = subj.lower()
    if subj_clean in person_pronouns or (subj_clean not in stop_words and subj_clean[0].isalpha()):
        g.add((subj_uri, RDF.type, SCHEMA.Person))  # Assign as Person
        typed_subjects.add(subj_uri)
        print(f"Assigned rdf:type schema:Person to subject: {subj}")
    elif any(kw in subj_clean for kw in place_keywords):
        g.add((subj_uri, RDF.type, SCHEMA.Place))  # Assign as Place
        typed_subjects.add(subj_uri)
        print(f"Assigned rdf:type schema:Place to subject: {subj}")
    elif any(kw in subj_clean for kw in organization_keywords):
        g.add((subj_uri, RDF.type, SCHEMA.Organization))  # Assign as Organization
        typed_subjects.add(subj_uri)
        print(f"Assigned rdf:type schema:Organization to subject: {subj}")

# Initialize an empty RDF graph
g = Graph()
g.bind("foaf", FOAF)
g.bind("prov", PROV)
g.bind("schema", SCHEMA)

# Read the input CSV file using pandas
df = pd.read_csv(csv_path)

# Initialize counters for statistics
typed_subjects = set()
triples_processed = 0
triples_added = 0
triples_discarded = 0

# Iterate over each row in the CSV
for _, row in df.iterrows():
    sentence = row['Sentences']  # Extract the sentence text
    triple_string = row['Extracted Triples']  # Extract the triple set
    print(f"Processing sentence: {sentence}")
    triples = extract_triples(triple_string)  # Extract triples from the string

    for subj, pred, obj in triples:
        triples_processed += 1
        if is_valid_triple(subj, pred, obj):
            namespace, mapped_pred = get_valid_predicate(pred)  # Get valid predicate URI
            subj_name = clean_name(subj)  # Clean subject name
            obj_name = clean_name(obj)  # Clean object name
            subj_uri = SCHEMA[subj_name]  # Create subject URI
            obj_uri = SCHEMA[obj_name]  # Create object URI
            pred_uri = namespace[mapped_pred]  # Full predicate URI

            g.add((subj_uri, pred_uri, obj_uri))  # Add triple to graph
            triples_added += 1
            print(f"Triple ADDED: ({subj}, {pred}, {obj}) -> Predicate: {pred_uri}")

            if subj_uri not in typed_subjects:
                assign_type(subj, subj_uri, g, typed_subjects)  # Assign rdf:type if needed
        else:
            triples_discarded += 1

# Serialize the RDF graph to Turtle file format
g.serialize(destination=ttl_output_path, format="turtle")

# Reformat Turtle file to add blank lines after each triple
with open(ttl_output_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

with open(ttl_output_path, 'w', encoding='utf-8') as f:
    for line in lines:
        f.write(line)
        if line.strip().endswith('.'):
            f.write('\n')

# Output the final processing report
print("\n=== Final Report ===")
print(f"Total triples processed: {triples_processed}")
print(f"Total triples added: {triples_added}")
print(f"Total triples discarded: {triples_discarded}")
print(f"TTL file saved successfully at: {ttl_output_path}")
