# ============================================================
# AGRICULTURE NLP GUI - FLASK BACKEND
# ============================================================

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

import os
import io
import json
import numpy as np

import nlp_engine


# ============================================================
# PATHS
# ============================================================

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))

FRONTEND_DIR = os.path.join(
    BACKEND_DIR,
    "..",
    "frontend"
)


# ============================================================
# JSON SAFETY HELPER
# ============================================================

def make_json_safe(obj):
    """
    Convert NumPy and other non-JSON-serializable objects
    into standard Python types that Flask jsonify can handle.
    """

    # Dictionary
    if isinstance(obj, dict):
        return {
            str(key): make_json_safe(value)
            for key, value in obj.items()
        }

    # List
    if isinstance(obj, list):
        return [
            make_json_safe(value)
            for value in obj
        ]

    # Tuple
    if isinstance(obj, tuple):
        return [
            make_json_safe(value)
            for value in obj
        ]

    # NumPy integer types
    if isinstance(obj, np.integer):
        return int(obj)

    # NumPy floating-point types
    if isinstance(obj, np.floating):
        return float(obj)

    # NumPy boolean
    if isinstance(obj, np.bool_):
        return bool(obj)

    # NumPy arrays
    if isinstance(obj, np.ndarray):
        return obj.tolist()

    # Already JSON-safe
    return obj


# ============================================================
# FLASK APP
# ============================================================

app = Flask(__name__)
CORS(app)


# ============================================================
# FRONTEND SERVING
# ============================================================

@app.route("/")
def serve_frontend():
    return send_from_directory(
        FRONTEND_DIR,
        "index.html"
    )


@app.route("/<path:filename>")
def serve_frontend_files(filename):
    """Serve frontend static files (script.js, style.css, etc.)"""
    frontend_path = os.path.join(
        FRONTEND_DIR,
        filename
    )
    if os.path.isfile(frontend_path):
        return send_from_directory(
            FRONTEND_DIR,
            filename
        )
    # Fall through to API routes
    return jsonify({"error": "Not found"}), 404


@app.route("/api/health")
def health():

    return jsonify(
        make_json_safe({
            "status": "ok",
            "final_pipeline": nlp_engine.FINAL_PIPELINE,
            "documents": nlp_engine.get_document_count()
        })
    )


def parse_uploaded_file(file_storage, filename):
    """
    Extract text and metadata from uploaded PDF, DOCX, CSV, JSON, JSONL, or TXT files.
    """
    ext = os.path.splitext(filename)[1].lower()
    docs = []

    if ext == ".pdf":
        try:
            import pypdf
            reader = pypdf.PdfReader(file_storage)
            pages_text = []
            for page in reader.pages:
                txt = page.extract_text()
                if txt and txt.strip():
                    pages_text.append(txt.strip())
            full_text = "\n\n".join(pages_text) if pages_text else "No extractable text found in PDF."
            docs.append({
                "file_name": filename,
                "format": "PDF",
                "topic": f"PDF Document ({len(reader.pages)} pages)",
                "owner": "User Upload",
                "source": filename,
                "text": full_text
            })
        except Exception as e:
            raise ValueError(f"Failed to parse PDF file: {str(e)}")

    elif ext in [".docx", ".doc"]:
        try:
            import docx
            doc = docx.Document(file_storage)
            paragraphs = [p.text.strip() for p in doc.paragraphs if p.text and p.text.strip()]
            full_text = "\n".join(paragraphs) if paragraphs else "No text found in DOCX."
            docs.append({
                "file_name": filename,
                "format": "DOCX",
                "topic": "DOCX Document",
                "owner": "User Upload",
                "source": filename,
                "text": full_text
            })
        except Exception as e:
            raise ValueError(f"Failed to parse DOCX file: {str(e)}")

    elif ext == ".csv":
        try:
            import pandas as pd
            df = pd.read_csv(file_storage)
            for idx, row in df.iterrows():
                row_dict = row.dropna().to_dict()
                text_val = row_dict.get("text", row_dict.get("content", str(row_dict)))
                docs.append({
                    "file_name": filename,
                    "format": "CSV",
                    "topic": str(row_dict.get("topic", f"CSV Record {idx+1}")),
                    "owner": str(row_dict.get("owner", "User Upload")),
                    "source": filename,
                    "text": str(text_val)
                })
        except Exception as e:
            raise ValueError(f"Failed to parse CSV file: {str(e)}")

    elif ext in [".json", ".jsonl"]:
        try:
            content = file_storage.read().decode("utf-8", errors="ignore")
            if ext == ".jsonl" or ("\n" in content and not content.strip().startswith("[")):
                lines = [l.strip() for l in content.splitlines() if l.strip()]
                for line in lines:
                    try:
                        item = json.loads(line)
                        if isinstance(item, dict):
                            item["file_name"] = item.get("file_name", filename)
                            item["format"] = item.get("format", "JSONL")
                            docs.append(item)
                    except Exception:
                        pass
            else:
                data = json.loads(content)
                if isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict):
                            item["file_name"] = item.get("file_name", filename)
                            item["format"] = item.get("format", "JSON")
                            docs.append(item)
                elif isinstance(data, dict):
                    data["file_name"] = data.get("file_name", filename)
                    data["format"] = data.get("format", "JSON")
                    docs.append(data)
        except Exception as e:
            raise ValueError(f"Failed to parse JSON file: {str(e)}")

    else:
        content = file_storage.read().decode("utf-8", errors="ignore")
        docs.append({
            "file_name": filename,
            "format": ext.replace(".", "").upper() or "TXT",
            "topic": "Uploaded Document",
            "owner": "User Upload",
            "source": filename,
            "text": content
        })

    return docs


@app.route("/api/upload", methods=["POST"])
def upload():
    """
    Endpoint to receive uploaded PDF, DOCX, CSV, JSON, JSONL or TXT files.
    """
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded. Please select a file."}), 400

    file = request.files["file"]
    if not file or file.filename == "":
        return jsonify({"error": "No selected file."}), 400

    try:
        parsed_docs = parse_uploaded_file(file, file.filename)
        if not parsed_docs:
            return jsonify({"error": "Could not extract any text/documents from the uploaded file."}), 400

        added_details = nlp_engine.add_uploaded_documents(parsed_docs)

        return jsonify(
            make_json_safe({
                "status": "success",
                "message": f"Successfully loaded {len(added_details)} document(s) into the workspace.",
                "file_name": file.filename,
                "format": os.path.splitext(file.filename)[1].replace(".", "").upper(),
                "documents_added": len(added_details),
                "added_documents": added_details,
                "total_corpus_documents": nlp_engine.get_document_count()
            })
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 400


# ============================================================
# DOCUMENTS
# ============================================================

@app.route("/api/documents")
def documents():

    df = nlp_engine.get_documents()

    # Only return useful document-level information
    columns = [
        col for col in [
            "doc_id",
            "file_name",
            "format",
            "owner",
            "topic",
            "source",
            "text"
        ]
        if col in df.columns
    ]

    data = df[columns].fillna("").to_dict(
        orient="records"
    )

    return jsonify(
        make_json_safe({
            "count": len(data),
            "documents": data
        })
    )


# ============================================================
# DOCUMENT STATISTICS
# ============================================================

@app.route("/api/stats")
def stats():

    result = nlp_engine.get_statistics()

    return jsonify(
        make_json_safe(result)
    )


# ============================================================
# PIPELINE INFORMATION
# ============================================================

@app.route("/api/pipelines")
def pipelines():

    result = nlp_engine.get_pipeline_information()

    return jsonify(
        make_json_safe(result)
    )


# ============================================================
# POS COMPARISON
# ============================================================

@app.route("/api/pos")
def pos():

    result = nlp_engine.get_pos_comparison()

    return jsonify(
        make_json_safe({
            "pos_comparison": result
        })
    )


# ============================================================
# INVERTED INDEX
# ============================================================

@app.route("/api/index")
def index():

    pipeline = request.args.get(
        "pipeline",
        "B"
    ).upper()

    if pipeline == "B":
        index_data = nlp_engine.get_inverted_index()

    else:
        index_data = nlp_engine.get_inverted_index()

    if index_data is None:

        return jsonify({
            "error": "Inverted index not found."
        }), 404

    return jsonify(
        make_json_safe({
            "pipeline": pipeline,
            "index": index_data
        })
    )


# ============================================================
# POSITIONAL INDEX
# ============================================================

@app.route("/api/index/positional")
def positional_index():

    index_data = (
        nlp_engine.get_positional_index()
    )

    if index_data is None:

        return jsonify({
            "error":
                "Positional inverted index not found."
        }), 404

    return jsonify(
        make_json_safe({
            "index": index_data
        })
    )


# ============================================================
# INDEX TERM LOOKUP
# ============================================================

@app.route("/api/index/term")
def index_term():

    term = request.args.get(
        "term",
        ""
    ).strip().lower()

    pipeline = request.args.get(
        "pipeline",
        "B"
    ).strip().upper()

    if not term:
        return jsonify({
            "error": "Please provide a term."
        }), 400

    result = nlp_engine.lookup_index_term(term, pipeline)

    return jsonify(
        make_json_safe(result)
    )



# ============================================================
# SEARCH
# ============================================================

@app.route("/api/search")
def search():

    query = request.args.get(
        "q",
        ""
    ).strip()

    pipeline = request.args.get(
        "pipeline",
        "B"
    ).upper()

    if not query:

        return jsonify({
            "error": "Please enter a query."
        }), 400

    result = nlp_engine.search_documents(
        query,
        pipeline
    )

    return jsonify(
        make_json_safe(result)
    )


# ============================================================
# EVALUATION
# ============================================================

@app.route("/api/evaluation")
def evaluation():

    result = nlp_engine.get_evaluation()

    return jsonify(
        make_json_safe(result)
    )


# ============================================================
# 3. TOKENIZATION
# ============================================================

@app.route("/api/tokenization")
def tokenization():

    method = request.args.get(
        "method",
        "hybrid"
    )

    doc_index = int(
        request.args.get(
            "doc",
            0
        )
    )

    try:

        result = nlp_engine.get_tokenization(
            method,
            doc_index
        )

        return jsonify(
            make_json_safe(result)
        )

    except Exception as e:

        return jsonify({
            "error": str(e)
        }), 400


# ============================================================
# 4. PREPROCESSING
# ============================================================

@app.route("/api/preprocessing")
def preprocessing():

    doc_index = int(
        request.args.get(
            "doc",
            0
        )
    )

    try:

        result = nlp_engine.get_preprocessing(
            doc_index
        )

        return jsonify(
            make_json_safe(result)
        )

    except Exception as e:

        return jsonify({
            "error": str(e)
        }), 400


# ============================================================
# 5. POS TAGGING
# ============================================================

@app.route("/api/pos/detail")
def pos_detail():

    method = request.args.get(
        "method",
        "nltk"
    )

    doc_index = int(
        request.args.get(
            "doc",
            0
        )
    )

    try:

        result = nlp_engine.get_pos_tagging(
            doc_index,
            method
        )

        return jsonify(
            make_json_safe(result)
        )

    except Exception as e:

        return jsonify({
            "error": str(e)
        }), 400


# ============================================================
# 6. CUSTOM POS
# ============================================================

@app.route("/api/custom-pos")
def custom_pos():

    doc_index = int(
        request.args.get(
            "doc",
            0
        )
    )

    try:

        result = nlp_engine.get_custom_pos(
            doc_index
        )

        return jsonify(
            make_json_safe(result)
        )

    except Exception as e:

        return jsonify({
            "error": str(e)
        }), 400


# ============================================================
# 7. NER
# ============================================================

@app.route("/api/ner")
def ner():

    doc_index = int(
        request.args.get(
            "doc",
            0
        )
    )

    try:

        result = nlp_engine.get_ner(
            doc_index
        )

        return jsonify(
            make_json_safe(result)
        )

    except Exception as e:

        return jsonify({
            "error": str(e)
        }), 400


# ============================================================
# 8. N-GRAMS
# ============================================================

@app.route("/api/ngrams")
def ngrams():

    n = int(
        request.args.get(
            "n",
            2
        )
    )

    doc_index = request.args.get(
        "doc",
        None
    )

    try:

        result = nlp_engine.get_ngrams(
            n,
            doc_index=doc_index
        )

        return jsonify(
            make_json_safe(result)
        )

    except Exception as e:

        return jsonify({
            "error": str(e)
        }), 400


# ============================================================
# 9. BPE
# ============================================================

@app.route("/api/bpe")
def bpe():

    doc_index = int(
        request.args.get(
            "doc",
            0
        )
    )

    try:

        result = nlp_engine.get_bpe(
            doc_index
        )

        return jsonify(
            make_json_safe(result)
        )

    except Exception as e:

        return jsonify({
            "error": str(e)
        }), 400


# ============================================================
# RUN SERVER
# ============================================================

if __name__ == "__main__":

    print("----------------------------------------")
    print("Agriculture NLP GUI Backend")
    print("----------------------------------------")

    print(
        "Final Pipeline:",
        nlp_engine.FINAL_PIPELINE
    )

    print(
        "Documents:",
        nlp_engine.get_document_count()
    )

    print("----------------------------------------")
    print("Server running at:")
    print("http://127.0.0.1:5000")
    print("----------------------------------------")

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )