# PKG Construction

This part of the project builds a **Knowledge Graph (KG)** from CSV files using standard ontologies (e.g., FOAF, Schema.org, SAREF, SOSA, PROV, EMO) and Python libraries. It supports multiple mapping strategies to semantically enrich raw data into structured RDF.

## Main Files

- `integration.py`: manually builds a simple RDF KG using predefined instances.
- `integration2.py`: loads a CSV (subject, predicate, object) and generates an RDF graph.
- `ontologies.py`: loads external ontologies and builds a dynamic KG from an enriched CSV file.
- `ontologies2.py`: uses advanced semantic matching (lemmatization, synonyms, keyword categories) to map predicates and concepts to ontology terms.

## Requirements

Install the required packages using:

```bash
pip install rdflib pandas nltk
```

Make sure to download the necessary `nltk` resources:

```python
import nltk
nltk.download('punkt')
nltk.download('wordnet')
```

## CSV Files

Two example CSV files are used across the scripts:

- `ontologies_test_1.csv` — used by `integration2.py`
- `ontologies_test_2.csv` — used by `ontologies.py` and `ontologies2.py`

Update the file paths in the scripts if necessary.

## Output

Each script exports a Turtle (`.ttl`) RDF file:

- `knowledge_graph.ttl`
- `knowledge_graph_from_csv.ttl`
- `knowledge_graph_dynamic.ttl`
- `output.ttl`

You can view these using tools like [RDF Grapher](https://www.ldf.fi/service/rdf-grapher).

## Ontologies Used

- [FOAF](http://xmlns.com/foaf/0.1/)
- [Schema.org](https://schema.org/)
- [SAREF](https://saref.etsi.org/core/)
- [SOSA/SSN](https://www.w3.org/TR/vocab-ssn/)
- [PROV-O](https://www.w3.org/TR/prov-o/)
- [EMO](https://bioportal.bioontology.org/ontologies/EMO/) (or local file `EMO.owl` if available)

## Advanced Features

- Class inference based on predicate context (`ontologies.py`)
- Semantic predicate matching using lemmatization and WordNet (`ontologies2.py`)
- Timestamp and attribute handling
- Automatic categorization of predicates by domain (e.g., sensor, provenance, people)

