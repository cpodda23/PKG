import pandas as pd
from rdflib import Graph, Namespace, URIRef, Literal
from rdflib.namespace import XSD, FOAF, PROV, SSN, SOSA, RDFS
import re
import nltk
from nltk.corpus import wordnet
from nltk.stem import WordNetLemmatizer
import string

nltk.download('wordnet')
nltk.download('punkt')
lemmatizer = WordNetLemmatizer()

# Namespaces
SCHEMA = Namespace("http://schema.org/")
SOSA = Namespace("http://www.w3.org/ns/sosa/")
SSN = Namespace("http://www.w3.org/ns/ssn/")
PROV = Namespace("http://www.w3.org/ns/prov#")
FOAF = Namespace("http://xmlns.com/foaf/0.1/")

csv_path = "/Users/camilla/Desktop/HDT/ontologies_test_2.csv"
df = pd.read_csv(csv_path, header=None, dtype=str, engine="python")
df = df[0].str.extract(r'\(([^,]+),\s*([^,]+),\s*([^)]+)\),([\d-]+\s[\d:]+),\"?(.*?)\"?$')
df.columns = ["subject", "predicate", "object", "timestamp", "attributes"]
df = df.fillna("None")

g = Graph()
g.bind("schema", SCHEMA, override=True)
g.bind("foaf", FOAF, override=True)
g.bind("sosa", SOSA, override=True)
g.bind("ssn", SSN, override=True)
g.bind("prov", PROV, override=True)

namespaces = {
    "schema": SCHEMA,
    "foaf": FOAF,
    "sosa": SOSA,
    "ssn": SSN,
    "prov": PROV
}

semantic_categories = {
    "sensor": {
        "ontology": SOSA,
        "keywords": ["sensor", "measure", "observation", "observe", "sensing", "monitor", "detect",
                     "temperature", "humidity", "pressure", "light", "sound", "motion"],
        "properties": {
            "generic": SOSA.observes,
            "sensor": SOSA.Sensor,
            "observation": SOSA.Observation,
            "sample": SOSA.Sample,
            "feature": SOSA.hasFeatureOfInterest,
            "result": SOSA.hasResult,
            "host": SOSA.hosts,
            "platform": SOSA.Platform
        }
    },
    "system": {
        "ontology": SSN,
        "keywords": ["system", "network", "property", "condition", "capability", "feature",
                     "deployment", "device", "node", "gateway"],
        "properties": {
            "generic": SSN.hasProperty,
            "system": SSN.System,
            "property": SSN.Property,
            "deployment": SSN.Deployment,
            "condition": SSN.Condition,
            "implemented": SSN.implementedBy
        }
    },
    "provenance": {
        "ontology": PROV,
        "keywords": ["generate", "create", "produce", "derive", "source", "origin", "author",
                     "attribute", "associate", "time", "start", "end", "initiated", "completed"],
        "properties": {
            "generic": PROV.wasGeneratedBy,
            "agent": PROV.Agent,
            "entity": PROV.Entity,
            "activity": PROV.Activity,
            "generated": PROV.wasGeneratedBy,
            "used": PROV.used,
            "associated": PROV.wasAssociatedWith,
            "time": PROV.generatedAtTime,
            "attribution": PROV.wasAttributedTo
        }
    },
    "person": {
        "ontology": FOAF,
        "keywords": ["person", "people", "user", "name", "contact", "email", "homepage", "profile",
                     "friend", "know", "acquaintance", "group", "organization", "member",
                     "like", "dislike", "emotion", "interest", "relation", "play", "feel"],
        "properties": {
            "generic": FOAF.made,
            "person": FOAF.Person,
            "name": FOAF.name,
            "knows": FOAF.knows,
            "group": FOAF.Group,
            "organization": FOAF.Organization,
            "member": FOAF.member,
            "contact": FOAF.mbox
        }
    },
    "general": {
        "ontology": SCHEMA,
        "keywords": ["description", "identifier", "type", "category", "location", "address", "date",
                     "time", "value", "price", "rating", "review", "comment", "status",
                     "watch", "visit", "wear", "impress", "action", "experience"],
        "properties": {
            "generic": SCHEMA.actionStatus,
            "name": SCHEMA.name,
            "description": SCHEMA.description,
            "value": SCHEMA.value,
            "location": SCHEMA.location,
            "time": SCHEMA.dateTime,
            "identifier": SCHEMA.identifier,
            "url": SCHEMA.url,
            "status": SCHEMA.status
        }
    }
}

def preprocess_term(term):
    term = term.lower()
    term = ''.join([c for c in term if c not in string.punctuation])
    term = re.sub(r'\s+', ' ', term).strip()
    return term

def get_synonyms(word):
    synonyms = set()
    for syn in wordnet.synsets(word):
        for lemma in syn.lemmas():
            synonyms.add(lemma.name().lower().replace('_', ' '))
    return list(synonyms)

def find_category_for_term(term):
    best_category = None
    best_score = 0
    term = preprocess_term(term)
    lemmatized_term = lemmatizer.lemmatize(term)

    for category_name, category_info in semantic_categories.items():
        score = 0
        for keyword in category_info["keywords"]:
            if keyword in term:
                score += 5
            elif any(part == keyword for part in term.split()):
                score += 3
            elif lemmatizer.lemmatize(keyword) == lemmatized_term:
                score += 2
            else:
                synonyms = get_synonyms(keyword)
                if any(syn in term for syn in synonyms):
                    score += 2

        if score > best_score:
            best_score = score
            best_category = category_name

    if best_score >= 1:
        return semantic_categories[best_category]
    else:
        return semantic_categories["general"]

def find_best_property_in_category(term, category):
    term = preprocess_term(term)
    lemmatized_term = lemmatizer.lemmatize(term)
    best_property = None
    best_score = 0

    for prop_name, prop_uri in category["properties"].items():
        score = 0
        if prop_name == term:
            score += 10
        elif prop_name in term:
            score += 5
        elif term in prop_name:
            score += 3
        elif any(part == prop_name for part in term.split()):
            score += 2
        elif lemmatizer.lemmatize(prop_name) == lemmatized_term:
            score += 2

        if score > best_score:
            best_score = score
            best_property = prop_uri

    if best_property and best_score >= 1:
        return best_property
    else:
        # Fallback alla proprietà 'generic' della categoria
        return category["properties"].get("generic", None)


def clean_uri(value):
    return URIRef(re.sub(r'[^a-zA-Z0-9_:/.-]', '_', value.strip()))

def fix_datetime(date_str):
    try:
        match = re.match(r"(\d{4})-(\d{1,2})-(\d{1,2}) (\d{2}:\d{2}:\d{2})", date_str)
        if match:
            year, month, day, time = match.groups()
            return f"{year}-{int(month):02d}-{int(day):02d}T{time}"
    except Exception:
        pass
    return None

def get_ontology_name(uri):
    for ns_name, namespace in namespaces.items():
        if str(uri).startswith(str(namespace)):
            return ns_name
    return "custom"

for _, row in df.iterrows():
    subj = clean_uri(row["subject"])
    original_pred = row["predicate"]
    pred_str = original_pred.lower().strip()
    obj = clean_uri(row["object"])

    category = find_category_for_term(pred_str)
    pred = find_best_property_in_category(pred_str, category)

    if pred is None or pred_str == "none":
        print(f"[SKIP] No property for predicate: '{original_pred}'")
        continue

    timestamp_fixed = fix_datetime(row["timestamp"])
    if timestamp_fixed is None:
        print(f"[SKIP] Invalid date: {row['timestamp']}")
        continue

    timestamp_literal = Literal(timestamp_fixed, datatype=XSD.dateTime)
    g.add((subj, pred, obj))
    # if pred is equal to the generic property of the category, add the original predicate
    if pred == category["properties"]["generic"]:
        g.add((subj, RDFS.label, Literal(original_pred)))
        g.add((obj, RDFS.label, Literal(original_pred)))
    g.add((subj, PROV.generatedAtTime, timestamp_literal))
    g.add((pred, PROV.generatedAtTime, timestamp_literal))
    g.add((obj, PROV.generatedAtTime, timestamp_literal))
    print(f"[ADD] {subj.split('/')[-1]} -- {original_pred} --> {obj.split('/')[-1]} ({get_ontology_name(pred)})")

ttl_output = "/Users/camilla/Desktop/HDT/output.ttl"
g.serialize(destination=ttl_output, format="turtle")
print(f"Turtle file saved at: {ttl_output}")