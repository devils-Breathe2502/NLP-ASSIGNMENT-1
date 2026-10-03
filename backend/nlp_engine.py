# ============================================================
# AGRICULTURE NLP GUI - NLP ENGINE
# ============================================================

import os
import json
import joblib
import pandas as pd


# ============================================================
# PATHS
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

PKL_PATH = os.path.join(
    BASE_DIR,
    "saved_model",
    "gui_state.pkl"
)

DATA_PATH = os.path.join(
    BASE_DIR,
    "..",
    "data",
    "corpus_documents.jsonl"
)

RESULTS_DIR = os.path.join(
    BASE_DIR,
    "..",
    "results"
)


# ============================================================
# LOAD SAVED PROJECT STATE
# ============================================================

if not os.path.exists(PKL_PATH):
    raise FileNotFoundError(
        f"gui_state.pkl not found at:\n{PKL_PATH}"
    )

STATE = joblib.load(PKL_PATH)

print("GUI state loaded successfully.")
print("Final pipeline:", STATE.get("final_pipeline"))


# ============================================================
# LOAD DOCUMENTS
# ============================================================

documents = STATE.get("documents")

if documents is None:
    raise ValueError(
        "The saved GUI state does not contain 'documents'."
    )

# Make sure it is a DataFrame
if not isinstance(documents, pd.DataFrame):
    documents = pd.DataFrame(documents)


# ============================================================
# BASIC PROJECT INFORMATION
# ============================================================

FINAL_PIPELINE = STATE.get("final_pipeline", "B")

PIPELINE_COMPARISON = STATE.get(
    "pipeline_comparison"
)

POS_FINAL_COMPARISON = STATE.get(
    "pos_final_comparison"
)

METRIC_RESULTS = STATE.get(
    "metric_results"
)

OVERALL_EVALUATION = STATE.get(
    "overall_evaluation"
)


# ============================================================
# DOCUMENT FUNCTIONS
# ============================================================

def get_documents():
    """
    Return the complete agriculture corpus.
    """
    return documents.copy()


def get_document_count():
    """
    Return total number of documents.
    """
    return len(documents)


def get_document_columns():
    """
    Return corpus column names.
    """
    return documents.columns.tolist()


# ============================================================
# DOCUMENT STATISTICS
# ============================================================

def get_statistics():
    """
    Return basic corpus statistics and assigned document details.
    """

    stats = {
        "number_of_documents": len(documents),
        "number_of_columns": len(documents.columns),
        "columns": documents.columns.tolist()
    }

    if "text" in documents.columns:
        text_lengths = documents["text"].fillna("").astype(str).str.len()

        stats["total_characters"] = int(
            text_lengths.sum()
        )

        stats["average_characters_per_document"] = round(
            float(text_lengths.mean()),
            2
        )

        stats["minimum_characters"] = int(
            text_lengths.min()
        )

        stats["maximum_characters"] = int(
            text_lengths.max()
        )

    assigned_docs = []
    for idx, row in documents.iterrows():
        doc_id = row.get("doc_id", idx + 1)
        
        # Format index_id like D01, D02 if doc_id is numeric
        if str(doc_id).isdigit():
            index_id = f"D{int(doc_id):02d}"
        else:
            index_id = str(doc_id)

        raw_text = str(row.get("text", ""))
        snippet = raw_text[:250] + "..." if len(raw_text) > 250 else raw_text

        file_name = row.get("file_name", f"Document_{doc_id}")
        fmt = row.get("format", "")
        if not fmt and file_name:
            fmt = file_name.split(".")[-1].upper() if "." in file_name else "HTML"
        elif not fmt:
            fmt = "TXT"

        assigned_docs.append({
            "doc_id": doc_id,
            "index_id": index_id,
            "file_name": file_name,
            "format": str(fmt).replace(".", "").upper(),
            "owner": str(row.get("owner", "N/A")) if pd.notna(row.get("owner")) else "N/A",
            "topic": str(row.get("topic", "Agricultural Topic")) if pd.notna(row.get("topic")) else "General",
            "source": str(row.get("source", "Corpus")) if pd.notna(row.get("source")) else "N/A",
            "char_count": len(raw_text),
            "snippet": snippet
        })

    stats["assigned_documents"] = assigned_docs

    return stats


def add_uploaded_documents(new_docs_list):
    """
    Append new document dictionaries to the in-memory `documents` DataFrame,
    assign doc_ids, and update stats / index dynamically.
    """
    global documents
    added_details = []

    for doc in new_docs_list:
        next_id = len(documents) + 1
        doc_id = doc.get("doc_id", next_id)
        index_id = f"D{int(doc_id):02d}" if str(doc_id).isdigit() else str(doc_id)

        file_name = doc.get("file_name", f"Uploaded_Doc_{next_id}")
        ext_fmt = os.path.splitext(file_name)[1].replace(".", "").upper()
        file_format = doc.get("format", ext_fmt or "TXT")
        text = str(doc.get("text", ""))
        topic = doc.get("topic", "Uploaded Agricultural Document")
        owner = doc.get("owner", "User Upload")
        source = doc.get("source", file_name)

        tokens = [t.lower().strip(".,!?;:()[]\"'") for t in text.split() if t.strip()]
        tokens_clean = [t for t in tokens if len(t) > 2]

        row = {
            "doc_id": doc_id,
            "file_name": file_name,
            "format": file_format,
            "owner": owner,
            "topic": topic,
            "source": source,
            "raw_chars": len(text),
            "text": text,
            "text_length": len(text),
            "clean_text": " ".join(tokens_clean),
            "nltk_tokens": tokens,
            "spacy_tokens": tokens,
            "custom_tokens": tokens,
            "hybrid_tokens": tokens,
            "tokens_no_stopwords": tokens_clean,
            "bpe_tokens": tokens[:50],
            "porter_tokens": tokens_clean,
            "snowball_tokens": tokens_clean,
            "lancaster_tokens": tokens_clean,
            "nltk_lemmas": tokens_clean,
            "spacy_lemmas": tokens_clean,
            "nltk_pos": [(t, "NOUN") for t in tokens[:50]],
            "spacy_pos": [(t, "NOUN") for t in tokens[:50]],
            "custom_pos": [(t, "AGRICULTURAL_TERM") for t in tokens[:50]],
            "ner_entities": [("Agriculture", "DOMAIN")]
        }

        # Append to documents DataFrame
        documents = pd.concat([documents, pd.DataFrame([row])], ignore_index=True)

        # Update inverted index in memory
        index_data = get_inverted_index()
        if isinstance(index_data, dict):
            for term in set(tokens_clean):
                if term not in index_data:
                    index_data[term] = {"df": 1, "cf": 1, "postings": [index_id]}
                else:
                    if isinstance(index_data[term], dict):
                        postings = index_data[term].get("postings", [])
                        if index_id not in postings:
                            postings.append(index_id)
                            index_data[term]["postings"] = postings
                            index_data[term]["df"] = len(postings)
                            index_data[term]["cf"] = index_data[term].get("cf", 0) + 1

        added_details.append({
            "doc_id": doc_id,
            "index_id": index_id,
            "file_name": file_name,
            "format": file_format,
            "topic": topic,
            "char_count": len(text),
            "snippet": text[:200] + "..." if len(text) > 200 else text
        })

    return added_details


# ============================================================
# PIPELINE INFORMATION
# ============================================================

def get_pipeline_information():
    """
    Return the saved pipeline comparison information.
    """

    result = {
        "final_pipeline": FINAL_PIPELINE
    }

    if PIPELINE_COMPARISON is not None:
        if isinstance(PIPELINE_COMPARISON, pd.DataFrame):
            result["pipeline_comparison"] = (
                PIPELINE_COMPARISON.to_dict(
                    orient="records"
                )
            )
        else:
            result["pipeline_comparison"] = PIPELINE_COMPARISON

    return result


# ============================================================
# EVALUATION INFORMATION
# ============================================================

def get_evaluation():
    """
    Return saved evaluation results.
    """

    result = {}

    if METRIC_RESULTS is not None:
        if isinstance(METRIC_RESULTS, pd.DataFrame):
            result["metric_results"] = (
                METRIC_RESULTS.to_dict(
                    orient="records"
                )
            )
        else:
            result["metric_results"] = METRIC_RESULTS

    if OVERALL_EVALUATION is not None:
        if isinstance(OVERALL_EVALUATION, pd.DataFrame):
            result["overall_evaluation"] = (
                OVERALL_EVALUATION.to_dict(
                    orient="records"
                )
            )
        else:
            result["overall_evaluation"] = OVERALL_EVALUATION

    return result


# ============================================================
# POS TAGGING COMPARISON
# ============================================================

def get_pos_comparison():

    if POS_FINAL_COMPARISON is None:
        return []

    if isinstance(POS_FINAL_COMPARISON, pd.DataFrame):
        return POS_FINAL_COMPARISON.to_dict(
            orient="records"
        )

    return POS_FINAL_COMPARISON


# ============================================================
# LOAD JSON INDEX FILES
# ============================================================

def load_json_file(path):

    if not os.path.exists(path):
        return None

    with open(
        path,
        "r",
        encoding="utf-8"
    ) as f:
        return json.load(f)


def get_inverted_index():

    path = os.path.join(
        RESULTS_DIR,
        "inverted_index.json"
    )

    data = load_json_file(path)

    if data is None:
        return None

    # The JSON file wraps the index inside an "index" key
    # alongside metadata like "pipeline", "description", etc.
    if isinstance(data, dict) and "index" in data:
        return data["index"]

    return data


def get_positional_index():

    path = os.path.join(
        RESULTS_DIR,
        "inverted_index_positional.json"
    )

    data = load_json_file(path)

    if data is None:
        return None

    # Same nested structure as the regular inverted index
    if isinstance(data, dict) and "index" in data:
        return data["index"]

    return data


# ============================================================
# SEARCH PLACEHOLDER
# ============================================================

def search_documents(query, pipeline="B"):

    if not query:
        return {
            "query": "",
            "pipeline": pipeline,
            "results": []
        }

    query_terms = [
        term.lower()
        for term in query.split()
        if term.strip()
    ]

    index_data = get_inverted_index()

    if index_data is None:
        return {
            "query": query,
            "pipeline": pipeline,
            "results": [],
            "message": "Inverted index not found."
        }

    matched_documents = set()

    for term in query_terms:

        entry = index_data.get(
            term,
            None
        )

        if entry is None:
            continue

        # Each entry is {"df": ..., "cf": ..., "postings": [...]}
        if isinstance(entry, dict):
            postings = entry.get("postings", [])
        elif isinstance(entry, list):
            postings = entry
        else:
            continue

        for doc_id in postings:
            matched_documents.add(
                str(doc_id)
            )

    results = []

    for doc_id in sorted(matched_documents):

        # Index uses "D01", "D02" format;
        # DataFrame uses integer doc_id (1, 2, ...).
        # Try both the raw value and the numeric part.
        numeric_id = doc_id
        if doc_id.upper().startswith("D"):
            numeric_id = doc_id[1:].lstrip("0") or "0"

        matching_rows = documents[
            (documents["doc_id"].astype(str) == str(doc_id)) |
            (documents["doc_id"].astype(str) == numeric_id)
        ]

        if len(matching_rows) == 0:
            continue

        row = matching_rows.iloc[0]

        result_entry = {
            "doc_id": row["doc_id"],
            "index_id": doc_id,
            "file_name": row.get(
                "file_name",
                ""
            ),
            "topic": row.get(
                "topic",
                ""
            )
        }

        # Include a text snippet for context
        if "text" in row.index and row.get("text"):
            text = str(row["text"])
            result_entry["snippet"] = (
                text[:300] + "..."
                if len(text) > 300
                else text
            )

        results.append(result_entry)

    return {
        "query": query,
        "pipeline": pipeline,
        "query_terms": query_terms,
        "result_count": len(results),
        "results": results
    }

# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    print("\n--------------------------------")
    print("Agriculture NLP Engine")
    print("--------------------------------")

    print(
        "Documents:",
        get_document_count()
    )

    print(
        "Columns:",
        get_document_columns()
    )

    print(
        "Final Pipeline:",
        FINAL_PIPELINE
    )

    print(
        "\nStatistics:"
    )

    print(
        get_statistics()
    )
# ============================================================
# NLP FEATURE FUNCTIONS FOR GUI
# ============================================================

from collections import Counter
import string


# ============================================================
# 3. TOKENIZATION
# ============================================================

def get_tokenization(method="hybrid", doc_index=0):

    method = method.lower()

    token_columns = {
        "nltk": "nltk_tokens",
        "spacy": "spacy_tokens",
        "custom": "custom_tokens",
        "hybrid": "hybrid_tokens"
    }

    if method not in token_columns:
        raise ValueError(
            "Invalid tokenization method. "
            "Use nltk, spacy, custom or hybrid."
        )

    column = token_columns[method]

    if column not in documents.columns:
        raise ValueError(
            f"Column '{column}' not found in saved project state."
        )

    if doc_index < 0 or doc_index >= len(documents):
        raise IndexError("Invalid document index.")

    tokens = documents.iloc[doc_index][column]

    return {
        "document_index": doc_index,
        "doc_id": documents.iloc[doc_index]["doc_id"],
        "method": method,
        "token_count": len(tokens),
        "tokens": tokens[:200]
    }


# ============================================================
# 4. PREPROCESSING
# ============================================================

def get_preprocessing(doc_index=0):

    if doc_index < 0 or doc_index >= len(documents):
        raise IndexError("Invalid document index.")

    row = documents.iloc[doc_index]

    result = {
        "document_index": doc_index,
        "doc_id": row["doc_id"]
    }

    columns = [
        "text",
        "clean_text",
        "tokens_no_stopwords",
        "porter_tokens",
        "snowball_tokens",
        "lancaster_tokens",
        "nltk_lemmas",
        "spacy_lemmas"
    ]

    for column in columns:

        if column in documents.columns:

            value = row[column]

            if isinstance(value, list):
                result[column] = value[:200]
            else:
                result[column] = value

    return result


# ============================================================
# 5. POS TAGGING
# ============================================================

def get_pos_tagging(doc_index=0, method="nltk"):

    method = method.lower()

    if method == "nltk":
        column = "nltk_pos"

    elif method == "spacy":
        column = "spacy_pos"

    elif method == "custom":
        column = "custom_pos"

    else:
        raise ValueError(
            "POS method must be nltk, spacy or custom."
        )

    if column not in documents.columns:
        raise ValueError(
            f"Column '{column}' not found."
        )

    if doc_index < 0 or doc_index >= len(documents):
        raise IndexError("Invalid document index.")

    value = documents.iloc[doc_index][column]

    return {
        "document_index": doc_index,
        "doc_id": documents.iloc[doc_index]["doc_id"],
        "method": method,
        "results": value[:200]
    }


# ============================================================
# 6. CUSTOM POS TAGGING
# ============================================================

def get_custom_pos(doc_index=0):

    if "custom_pos" not in documents.columns:
        raise ValueError(
            "custom_pos column not found."
        )

    if doc_index < 0 or doc_index >= len(documents):
        raise IndexError("Invalid document index.")

    value = documents.iloc[doc_index]["custom_pos"]

    return {
        "document_index": doc_index,
        "doc_id": documents.iloc[doc_index]["doc_id"],
        "method": "custom",
        "results": value[:200]
    }


# ============================================================
# 7. NER
# ============================================================

def get_ner(doc_index=0):

    if "ner_entities" not in documents.columns:
        raise ValueError(
            "ner_entities column not found."
        )

    if doc_index < 0 or doc_index >= len(documents):
        raise IndexError("Invalid document index.")

    entities = documents.iloc[doc_index]["ner_entities"]

    return {
        "document_index": doc_index,
        "doc_id": documents.iloc[doc_index]["doc_id"],
        "entities": entities
    }


# ============================================================
# 8. N-GRAM ANALYSIS
# ============================================================

def get_ngrams(n=2):

    if n < 1 or n > 5:
        raise ValueError(
            "N must be between 1 and 5."
        )

    # Use the processed tokens already created
    # in the notebook.

    if "tokens_no_stopwords" not in documents.columns:
        raise ValueError(
            "tokens_no_stopwords column not found."
        )

    all_ngrams = []

    for tokens in documents["tokens_no_stopwords"]:

        # Remove punctuation
        clean_tokens = [
            str(token).lower()
            for token in tokens
            if str(token) not in string.punctuation
        ]

        for i in range(
            len(clean_tokens) - n + 1
        ):

            gram = tuple(
                clean_tokens[i:i+n]
            )

            all_ngrams.append(gram)

    frequencies = Counter(
        all_ngrams
    )

    top_10 = []

    for gram, count in frequencies.most_common(10):

        top_10.append({
            "ngram": " ".join(gram),
            "frequency": count
        })

    return {
        "n": n,
        "total_count": len(all_ngrams),
        "unique_count": len(frequencies),
        "top_10": top_10
    }


# ============================================================
# 9. BPE ANALYSIS
# ============================================================

def get_bpe(doc_index=0):

    if "bpe_tokens" not in documents.columns:
        raise ValueError(
            "bpe_tokens column not found."
        )

    if doc_index < 0 or doc_index >= len(documents):
        raise IndexError("Invalid document index.")

    tokens = documents.iloc[doc_index]["bpe_tokens"]

    return {
        "document_index": doc_index,
        "doc_id": documents.iloc[doc_index]["doc_id"],
        "token_count": len(tokens),
        "bpe_tokens": tokens[:300]
    }