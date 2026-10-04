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


INVERTED_INDEX_CACHE = None


def get_inverted_index():

    global INVERTED_INDEX_CACHE

    if INVERTED_INDEX_CACHE is not None:
        return INVERTED_INDEX_CACHE

    path = os.path.join(
        RESULTS_DIR,
        "inverted_index.json"
    )

    data = load_json_file(path)

    if data is None:
        INVERTED_INDEX_CACHE = {}
        return INVERTED_INDEX_CACHE

    # The JSON file wraps the index inside an "index" key
    # alongside metadata like "pipeline", "description", etc.
    if isinstance(data, dict) and "index" in data:
        INVERTED_INDEX_CACHE = data["index"]
    else:
        INVERTED_INDEX_CACHE = data

    return INVERTED_INDEX_CACHE


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
# SEARCH ENGINE
# ============================================================

import re

# ============================================================
# SEARCH ENGINE HELPER FOR PIPELINE EVALUATION
# ============================================================

NLTK_ENGLISH_STOPWORDS = {
    "i", "me", "my", "myself", "we", "our", "ours", "ourselves", "you", "your", "yours",
    "yourself", "yourselves", "he", "him", "his", "himself", "she", "her", "hers",
    "herself", "it", "its", "itself", "they", "them", "their", "theirs", "themselves",
    "what", "which", "who", "whom", "this", "that", "these", "those", "am", "is", "are",
    "was", "were", "be", "been", "being", "have", "has", "had", "having", "do", "does",
    "did", "doing", "a", "an", "the", "and", "but", "if", "or", "because", "as", "until",
    "while", "of", "at", "by", "for", "with", "about", "against", "between", "into",
    "through", "during", "before", "after", "above", "below", "to", "from", "up", "down",
    "in", "out", "on", "off", "over", "under", "again", "further", "then", "once"
}


def eval_doc_match_term(term, row, pipeline):
    """
    Check if a single search term matches a document row under the given pipeline rules.
    Uses exact word token sets and regex word boundaries (never loose substring matches).
    """
    term = str(term).strip().lower()
    if not term:
        return False

    if pipeline == "A":
        # PIPELINE A: Standard NLTK Tokenizer + Porter Stemmer + NLTK Stopwords
        if term in NLTK_ENGLISH_STOPWORDS:
            return False

        porter_toks = set(str(t).lower() for t in row.get("porter_tokens", []))
        nltk_toks = set(str(t).lower() for t in row.get("nltk_tokens", []))
        combined_a = porter_toks.union(nltk_toks)

        if term in combined_a:
            return True

        text_str = str(row.get("text", "")).lower()
        if re.search(r'\b' + re.escape(term) + r'\b', text_str):
            return True

        return False

    elif pipeline == "C":
        # PIPELINE C: Aggressive Regex Tokenizer + Lancaster Stemmer
        lancaster_toks = set(str(t).lower() for t in row.get("lancaster_tokens", []))
        snowball_toks = set(str(t).lower() for t in row.get("snowball_tokens", []))
        combined_c = lancaster_toks.union(snowball_toks)

        if term in combined_c:
            return True

        return False

    else:
        # PIPELINE B: Hybrid Agricultural Tokenizer + Lemmatization (Optimal ⭐)
        hybrid_toks = set(str(t).lower() for t in row.get("hybrid_tokens", []))
        clean_toks = set(str(t).lower() for t in row.get("tokens_no_stopwords", []))
        lemmas = set(str(t).lower() for t in row.get("nltk_lemmas", []))
        combined_b = hybrid_toks.union(clean_toks).union(lemmas)

        if term in combined_b:
            return True

        text_str = str(row.get("text", "")).lower()
        clean_str = str(row.get("clean_text", "")).lower()
        if re.search(r'\b' + re.escape(term) + r'\b', text_str) or re.search(r'\b' + re.escape(term) + r'\b', clean_str):
            return True

        return False


def lookup_index_term(term, pipeline="B"):
    """
    Lookup a term in the inverted index for the specified pipeline (A, B, or C).
    Returns term statistics (df, cf) and list of document IDs (postings).
    """
    term = str(term).strip().lower()
    pipeline = str(pipeline).strip().upper()
    if pipeline not in ["A", "B", "C"]:
        pipeline = "B"

    if not term:
        return {
            "term": term,
            "pipeline": pipeline,
            "df": 0,
            "cf": 0,
            "documents": [],
            "count": 0
        }

    postings = []
    cf = 0

    if pipeline == "B":
        inv_index = get_inverted_index()
        if isinstance(inv_index, dict) and term in inv_index:
            entry = inv_index[term]
            if isinstance(entry, dict):
                postings = list(entry.get("postings", []))
                cf = entry.get("cf", len(postings))
            elif isinstance(entry, list):
                postings = list(entry)
                cf = len(postings)

    formatted_postings = []
    seen = set()
    for p in postings:
        p_str = f"D{int(p):02d}" if str(p).isdigit() else str(p)
        if p_str not in seen:
            seen.add(p_str)
            formatted_postings.append(p_str)

    global documents
    if documents is not None and not documents.empty:
        for idx, row in documents.iterrows():
            doc_id = row.get("doc_id", idx + 1)
            index_id = f"D{int(doc_id):02d}" if str(doc_id).isdigit() else str(doc_id)

            if eval_doc_match_term(term, row, pipeline):
                text_str = str(row.get("text", "")).lower()
                term_freq = len(re.findall(r'\b' + re.escape(term) + r'\b', text_str)) or 1

                if index_id not in seen:
                    seen.add(index_id)
                    formatted_postings.append(index_id)
                    cf += term_freq
                elif pipeline != "B":
                    cf += term_freq

    def sort_key(x):
        s = str(x)
        if s.startswith("D") and s[1:].isdigit():
            return (0, int(s[1:]))
        return (1, s)

    formatted_postings.sort(key=sort_key)

    return {
        "term": term,
        "pipeline": pipeline,
        "df": len(formatted_postings),
        "cf": max(cf, len(formatted_postings)),
        "documents": formatted_postings,
        "count": len(formatted_postings)
    }



def search_documents(query, pipeline="B"):

    if not query or not str(query).strip():
        return {
            "query": "",
            "pipeline": pipeline,
            "results": []
        }

    pipeline = str(pipeline).strip().upper()
    if pipeline not in ["A", "B", "C"]:
        pipeline = "B"

    raw_query = str(query).strip()
    matched_doc_ids = set()

    # Detect Boolean Query Structure
    has_or = bool(re.search(r'\bOR\b|\bor\b', raw_query))
    has_and = bool(re.search(r'\bAND\b|\band\b', raw_query))
    has_not = bool(re.search(r'\bNOT\b|\bnot\b', raw_query))

    if has_or and not (has_and or has_not):
        # Evaluate OR query: term1 OR term2
        sub_terms = [t.strip() for t in re.split(r'\bOR\b|\bor\b', raw_query, flags=re.IGNORECASE) if t.strip()]
        for idx, row in documents.iterrows():
            doc_id = row.get("doc_id", idx + 1)
            if any(eval_doc_match_term(st, row, pipeline) for st in sub_terms):
                matched_doc_ids.add(doc_id)

    elif has_and and not (has_or or has_not):
        # Evaluate AND query: term1 AND term2
        sub_terms = [t.strip() for t in re.split(r'\bAND\b|\band\b', raw_query, flags=re.IGNORECASE) if t.strip()]
        for idx, row in documents.iterrows():
            doc_id = row.get("doc_id", idx + 1)
            if all(eval_doc_match_term(st, row, pipeline) for st in sub_terms):
                matched_doc_ids.add(doc_id)

    elif has_not:
        # Evaluate NOT query: term1 NOT term2
        parts = [t.strip() for t in re.split(r'\bNOT\b|\bnot\b', raw_query, flags=re.IGNORECASE) if t.strip()]
        pos_terms = parts[0].split() if parts else []
        neg_terms = parts[1:] if len(parts) > 1 else []

        for idx, row in documents.iterrows():
            doc_id = row.get("doc_id", idx + 1)
            pos_match = any(eval_doc_match_term(pt, row, pipeline) for pt in pos_terms) if pos_terms else True
            neg_match = any(eval_doc_match_term(nt, row, pipeline) for nt in neg_terms) if neg_terms else False
            if pos_match and not neg_match:
                matched_doc_ids.add(doc_id)

    else:
        # Multi-term / Keyword Query: Match documents containing query terms
        query_terms = [t.lower().strip() for t in raw_query.split() if t.strip()]
        for idx, row in documents.iterrows():
            doc_id = row.get("doc_id", idx + 1)
            if any(eval_doc_match_term(qt, row, pipeline) for qt in query_terms):
                matched_doc_ids.add(doc_id)

    # Retrieve matching rows and format output uniquely
    results = []
    seen_doc_ids = set()

    sorted_ids = sorted(
        matched_doc_ids,
        key=lambda x: (0, int(x)) if isinstance(x, int) or str(x).isdigit() else (1, str(x))
    )

    for doc_id_key in sorted_ids:
        numeric_str = str(doc_id_key)
        formatted_index_id = f"D{int(doc_id_key):02d}" if numeric_str.isdigit() else numeric_str

        matching_rows = documents[
            (documents["doc_id"].astype(str) == numeric_str) |
            (documents["doc_id"].astype(str) == formatted_index_id) |
            (documents.index.astype(str) == numeric_str)
        ]

        if len(matching_rows) == 0:
            continue

        row = matching_rows.iloc[0]
        actual_doc_id = row["doc_id"]

        if actual_doc_id in seen_doc_ids:
            continue
        seen_doc_ids.add(actual_doc_id)

        index_id = f"D{int(actual_doc_id):02d}" if str(actual_doc_id).isdigit() else str(actual_doc_id)

        result_entry = {
            "doc_id": actual_doc_id,
            "index_id": index_id,
            "file_name": row.get("file_name", ""),
            "topic": row.get("topic", "")
        }

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
        "results": results,
        "result_count": len(results)
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
    doc_id = row.get("doc_id", doc_index + 1)
    index_id = f"D{int(doc_id):02d}" if str(doc_id).isdigit() else str(doc_id)

    raw_text = str(row.get("text", ""))
    clean_text = str(row.get("clean_text", ""))

    raw_tokens = [t.lower().strip(".,!?;:()[]\"'") for t in raw_text.split() if t.strip()]
    stopwords_removed = [t for t in raw_tokens if t in NLTK_ENGLISH_STOPWORDS]

    tokens_no_sw = row.get("tokens_no_stopwords", [])
    if isinstance(tokens_no_sw, list) and tokens_no_sw:
        clean_tokens = [str(t) for t in tokens_no_sw]
    else:
        clean_tokens = [t for t in raw_tokens if t not in NLTK_ENGLISH_STOPWORDS and len(t) > 2]

    raw_vocab = set(raw_tokens)
    clean_vocab = set(clean_tokens)

    raw_token_count = len(raw_tokens)
    clean_token_count = len(clean_tokens)
    stopwords_count = len(stopwords_removed)
    raw_vocab_count = len(raw_vocab)
    clean_vocab_count = len(clean_vocab)

    vocab_reduction_pct = round(((raw_vocab_count - clean_vocab_count) / max(raw_vocab_count, 1)) * 100, 2) if raw_vocab_count > 0 else 0.0

    sw_counts = Counter(stopwords_removed).most_common(12)
    top_stopwords = [{"word": word, "count": count} for word, count in sw_counts]

    # Corpus-level Aggregates across all active documents
    all_raw_tokens = []
    all_clean_tokens = []
    all_sw_removed = []
    for idx, r in documents.iterrows():
        t_raw = [t.lower().strip(".,!?;:()[]\"'") for t in str(r.get("text", "")).split() if t.strip()]
        all_raw_tokens.extend(t_raw)
        all_sw_removed.extend([t for t in t_raw if t in NLTK_ENGLISH_STOPWORDS])
        c_toks = r.get("tokens_no_stopwords", [])
        if isinstance(c_toks, list) and c_toks:
            all_clean_tokens.extend([str(t) for t in c_toks])
        else:
            all_clean_tokens.extend([t for t in t_raw if t not in NLTK_ENGLISH_STOPWORDS and len(t) > 2])

    corpus_raw_vocab = set(t for t in all_raw_tokens if t and not t.isdigit())
    corpus_clean_vocab = set(all_clean_tokens)
    raw_v_size = len(corpus_raw_vocab)
    clean_v_size = len(corpus_clean_vocab)
    corpus_vocab_reduction_pct = round(((raw_v_size - clean_v_size) / max(raw_v_size, 1)) * 100, 2) if raw_v_size > clean_v_size else round(((clean_v_size - raw_v_size) / max(raw_v_size, 1)) * 100, 2)
    corpus_top_sw = [{"word": word, "count": count} for word, count in Counter(all_sw_removed).most_common(12)]

    return {
        "document_index": doc_index,
        "doc_id": doc_id,
        "index_id": index_id,
        "text": raw_text,
        "clean_text": clean_text,
        "raw_token_count": raw_token_count,
        "clean_token_count": clean_token_count,
        "stopwords_count": stopwords_count,
        "raw_vocab_count": raw_vocab_count,
        "clean_vocab_count": clean_vocab_count,
        "vocab_reduction_pct": vocab_reduction_pct,
        "top_stopwords": top_stopwords,
        "tokens_no_stopwords": clean_tokens[:200],
        "porter_tokens": [str(t) for t in row.get("porter_tokens", [])][:20],
        "snowball_tokens": [str(t) for t in row.get("snowball_tokens", [])][:20],
        "lancaster_tokens": [str(t) for t in row.get("lancaster_tokens", [])][:20],
        "nltk_lemmas": [str(t) for t in row.get("nltk_lemmas", [])][:20],
        "spacy_lemmas": [str(t) for t in row.get("spacy_lemmas", [])][:20],
        "hybrid_tokens": [str(t) for t in row.get("hybrid_tokens", [])][:20],
        "corpus_stats": {
            "corpus_raw_tokens": len(all_raw_tokens),
            "corpus_clean_tokens": len(all_clean_tokens),
            "corpus_stopwords_removed": len(all_sw_removed),
            "corpus_raw_vocab": len(corpus_raw_vocab),
            "corpus_clean_vocab": len(corpus_clean_vocab),
            "corpus_vocab_reduction_pct": corpus_vocab_reduction_pct,
            "corpus_top_stopwords": corpus_top_sw
        }
    }


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

def get_ngrams(n=2, doc_index=None):

    if n < 1 or n > 5:
        raise ValueError(
            "N must be between 1 and 5."
        )

    if "tokens_no_stopwords" not in documents.columns:
        raise ValueError(
            "tokens_no_stopwords column not found."
        )

    all_ngrams = []

    if doc_index is not None and str(doc_index).strip().lower() not in ["all", "", "none"]:
        try:
            doc_idx = int(doc_index)
            if doc_idx < 0 or doc_idx >= len(documents):
                raise IndexError(f"Invalid document index: {doc_index}")
            token_sources = [documents.iloc[doc_idx]["tokens_no_stopwords"]]
        except (ValueError, TypeError):
            token_sources = documents["tokens_no_stopwords"]
    else:
        token_sources = documents["tokens_no_stopwords"]

    for tokens in token_sources:

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
        "document_index": doc_index,
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