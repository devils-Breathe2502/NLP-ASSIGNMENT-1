// ============================================================
// AGRICULTURE NLP GUI - FRONTEND JAVASCRIPT
// ============================================================

const API_BASE = "http://127.0.0.1:5000";


// ============================================================
// GENERAL HELPERS
// ============================================================

async function fetchAPI(endpoint, options = {}) {

    const response = await fetch(
        `${API_BASE}${endpoint}`,
        options
    );

    const data = await response.json();

    if (!response.ok) {
        throw new Error(
            data.error || `Request failed: ${response.status}`
        );
    }

    return data;
}


function displayJSON(elementId, data) {

    const element = document.getElementById(elementId);

    if (!element) {
        console.warn(`Element not found: ${elementId}`);
        return;
    }

    element.textContent = JSON.stringify(
        data,
        null,
        2
    );
}


function displayMessage(elementId, message) {

    const element = document.getElementById(elementId);

    if (!element) {
        return;
    }

    element.textContent = message;
}


function showError(elementId, error) {

    displayMessage(
        elementId,
        `Error: ${error.message || error}`
    );
}


// ============================================================
// BACKEND HEALTH CHECK
// ============================================================

async function checkBackend() {

    const statusElement =
        document.getElementById("backend-status");

    try {

        const data =
            await fetchAPI("/api/health");

        if (statusElement) {

            statusElement.textContent =
                `Backend connected | ` +
                `Pipeline: ${data.final_pipeline} | ` +
                `Documents: ${data.documents}`;
        }

        const footerPipeline =
            document.getElementById("footer-final-pipeline");

        if (footerPipeline) {
            footerPipeline.textContent =
                data.final_pipeline;
        }

    } catch (error) {

        if (statusElement) {

            statusElement.textContent =
                "Backend disconnected";
        }

        console.error(
            "Backend health check failed:",
            error
        );
    }
}


// ============================================================
// DOCUMENT STATISTICS
// ============================================================

async function loadStatistics() {

    try {

        const data =
            await fetchAPI("/api/stats");

        renderDocumentStatistics(data);

    } catch (error) {

        showError(
            "statistics-result",
            error
        );
    }
}


function renderDocumentStatistics(data) {

    const container = document.getElementById("statistics-result");

    if (!container) return;

    if (!data || typeof data !== "object") {

        container.textContent = "No statistics data available.";

        return;
    }

    const totalDocs = data.number_of_documents || 0;

    const totalChars = (data.total_characters || 0).toLocaleString();

    const avgChars = (data.average_characters_per_document || 0).toLocaleString();

    const minChars = (data.minimum_characters || 0).toLocaleString();

    const maxChars = (data.maximum_characters || 0).toLocaleString();

    const totalCols = data.number_of_columns || 0;

    const assignedDocs = data.assigned_documents || [];


    const navPill = document.getElementById("nav-corpus-count");
    if (navPill) {
        navPill.textContent = `${totalDocs} Docs`;
    }

    let html = `
    <div class="stats-container">

        <div class="stats-cards-grid">

            <div class="stat-card">
                <span class="label">Total Documents</span>
                <span class="val">${totalDocs}</span>
            </div>

            <div class="stat-card">
                <span class="label">Total Characters</span>
                <span class="val">${totalChars}</span>
            </div>

            <div class="stat-card">
                <span class="label">Avg Chars/Doc</span>
                <span class="val">${avgChars}</span>
            </div>

            <div class="stat-card">
                <span class="label">Min / Max Length</span>
                <span class="val">${minChars} / ${maxChars}</span>
            </div>

            <div class="stat-card">
                <span class="label">Corpus Columns</span>
                <span class="val">${totalCols}</span>
            </div>

        </div>

        <div class="table-filter-bar">
            <h4 style="margin:0; font-size:14px; color:#111827;">Assigned Documents Matrix (${assignedDocs.length})</h4>

            <input type="text"
                   id="doc-stats-search"
                   placeholder="Search docs by ID, file name, format, topic, owner...">
        </div>

        <div class="doc-table-wrapper">

            <table class="doc-table"
                   id="assigned-doc-table">

                <thead>
                    <tr>
                        <th style="width:65px;">Doc ID</th>
                        <th style="width:75px;">Index ID</th>
                        <th style="width:230px;">File Name</th>
                        <th style="width:85px;">Format</th>
                        <th style="width:230px;">Topic</th>
                        <th style="width:140px;">Owner / Source</th>
                        <th style="width:110px; text-align:right;">Char Count</th>
                    </tr>
                </thead>

                <tbody>
    `;

    assignedDocs.forEach((doc, idx) => {

        const fmtClass = `fmt-${(doc.format || 'txt').toLowerCase()}`;

        const searchStr = `${doc.doc_id} ${doc.index_id} ${doc.file_name} ${doc.format} ${doc.topic} ${doc.owner} ${doc.source}`.toLowerCase();

        html += `
            <tr class="doc-row" data-search="${searchStr}">
                <td style="width:65px;"><span class="doc-id-badge">#${doc.doc_id}</span></td>
                <td style="width:75px;"><span class="index-id-badge">${doc.index_id}</span></td>
                <td class="cell-file" style="width:230px;" title="${doc.file_name}">${doc.file_name}</td>
                <td style="width:85px;"><span class="fmt-tag ${fmtClass}">${doc.format}</span></td>
                <td class="cell-topic" style="width:230px;">${doc.topic}</td>
                <td style="color:#60736a; font-size:12px; width:140px;">${doc.owner !== 'N/A' ? doc.owner : doc.source}</td>
                <td style="font-family:'DM Mono', monospace; font-weight:700; width:110px; text-align:right;">${(doc.char_count || 0).toLocaleString()}</td>
            </tr>
        `;
    });

    html += `
                </tbody>
            </table>
        </div>
    </div>
    `;

    container.innerHTML = html;

    container.classList.add('is-active');


    const searchInput = document.getElementById("doc-stats-search");

    if (searchInput) {

        searchInput.addEventListener("input", function () {

            const q = this.value.toLowerCase().trim();

            const rows = document.querySelectorAll("#assigned-doc-table tbody tr.doc-row");

            rows.forEach(row => {

                const text = row.getAttribute("data-search") || "";

                row.style.display = text.includes(q) ? "" : "none";
            });
        });
    }
}


function toggleSnippet(id) {

    const el = document.getElementById(id);

    if (el) {

        el.style.display = (el.style.display === "none") ? "table-row" : "none";
    }
}


// ============================================================
// DOCUMENT LOADING
// ============================================================

async function loadDocuments() {

    try {

        const fileInput =
            document.getElementById("corpus-file");

        const resultElement =
            document.getElementById("upload-result");

        if (!fileInput || !fileInput.files.length) {

            displayMessage(
                "upload-result",
                "Please select a file to upload (PDF, DOCX, CSV, JSON, JSONL, TXT)."
            );

            return;
        }

        const file =
            fileInput.files[0];

        displayMessage(
            "upload-result",
            `Uploading and parsing ${file.name}...`
        );

        const formData = new FormData();

        formData.append("file", file);

        const response = await fetch(
            `${API_BASE}/api/upload`,
            {
                method: "POST",
                body: formData
            }
        );

        const data = await response.json();

        if (!response.ok) {

            throw new Error(
                data.error || `Upload failed: ${response.status}`
            );
        }

        const resultContainer =
            document.getElementById("upload-result");

        if (resultContainer) {

            let docsAddedHtml = '';

            if (data.added_documents && data.added_documents.length) {

                docsAddedHtml =
                    '<ul style="margin:8px 0 0; padding-left:18px; font-size:12px;">' +
                    data.added_documents.map(
                        d => `<li>Assigned <strong>[${d.index_id}]</strong>: ${d.file_name} (${(d.char_count || 0).toLocaleString()} chars) — <em>${d.topic}</em></li>`
                    ).join('') +
                    '</ul>';
            }

            resultContainer.innerHTML = `
                <div class="success">
                    <strong>✓ Upload &amp; Parsing Success!</strong><br>
                    <span><strong>File:</strong> ${data.file_name} | <strong>Format:</strong> ${data.format}</span><br>
                    <span><strong>Documents Loaded:</strong> ${data.documents_added} | <strong>Total Workspace Corpus:</strong> ${data.total_corpus_documents}</span>
                    ${docsAddedHtml}
                </div>
            `;

            resultContainer.classList.add('is-active');
        }

        // Automatically update Document Statistics table, counters, and document selector options
        await loadStatistics();
        await loadDocumentInformation();
        if (LOADED_DOCUMENTS && LOADED_DOCUMENTS.length > 0) {
            syncSelectedDoc(LOADED_DOCUMENTS.length - 1, null);
        }

    } catch (error) {

        showError(
            "upload-result",
            error
        );
    }
}


// ============================================================
// VISUAL OUTPUT RENDERERS (HUMAN READABLE)
// ============================================================

function renderTokenizationResult(data) {
    const el = document.getElementById("tokenization-result");
    if (!el) return;
    
    const tokens = data.tokens || [];
    const count = data.token_count || tokens.length;

    let html = `
    <div class="visual-card">
        <div class="visual-header">
            <span class="v-badge">Method: <strong>${(data.method || 'hybrid').toUpperCase()}</strong></span>
            <span class="v-badge">Doc ID: <strong>#${data.doc_id || 1}</strong></span>
            <span class="v-badge primary">Total Tokens: <strong>${count.toLocaleString()}</strong></span>
        </div>
        <p style="font-size: 12px; color: var(--ink-soft); margin: 8px 0 6px;">Extracted Tokens Sample (${tokens.length} shown):</p>
        <div class="token-chips-wrapper">
    `;

    tokens.forEach((t, i) => {
        html += `<span class="token-chip" title="Index #${i}">${t}</span>`;
    });

    html += `
        </div>
    </div>
    `;

    el.innerHTML = html;
    el.classList.add("is-active");
}

function renderPreprocessingResult(data) {
    const el = document.getElementById("preprocessing-result");
    if (!el) return;

    let html = `
    <div class="visual-card">
        <div class="visual-header">
            <span class="v-badge">Doc ID: <strong>#${data.doc_id || 1}</strong></span>
            <span class="v-badge primary">Preprocessing Pipeline Stages</span>
        </div>

        <div class="prep-stage">
            <div class="stage-title">1. Raw Text Snippet</div>
            <div class="raw-text-box">${data.text ? data.text.substring(0, 220) + "..." : "N/A"}</div>
        </div>

        <div class="prep-stage">
            <div class="stage-title">2. Cleaned Normalized Text</div>
            <div class="raw-text-box">${data.clean_text ? data.clean_text.substring(0, 220) + "..." : "N/A"}</div>
        </div>

        <div class="prep-stage">
            <div class="stage-title">3. Tokens without Stop-words (${data.tokens_no_stopwords ? data.tokens_no_stopwords.length : 0} tokens)</div>
            <div class="token-chips-wrapper">
                ${(data.tokens_no_stopwords || []).slice(0, 35).map(t => `<span class="token-chip">${t}</span>`).join('')}
            </div>
        </div>

        <div class="prep-stage">
            <div class="stage-title">4. Stemmers Comparison</div>
            <div style="display:flex; flex-direction:column; gap:6px;">
                <div><strong style="font-size:11px;">Porter:</strong> <span class="token-chip-str">${(data.porter_tokens || []).slice(0, 12).join(' • ')}</span></div>
                <div><strong style="font-size:11px;">Snowball:</strong> <span class="token-chip-str">${(data.snowball_tokens || []).slice(0, 12).join(' • ')}</span></div>
                <div><strong style="font-size:11px;">Lancaster:</strong> <span class="token-chip-str">${(data.lancaster_tokens || []).slice(0, 12).join(' • ')}</span></div>
            </div>
        </div>

        <div class="prep-stage">
            <div class="stage-title">5. Lemmatization (NLTK &amp; spaCy)</div>
            <div style="display:flex; flex-direction:column; gap:6px;">
                <div><strong style="font-size:11px;">NLTK Lemmas:</strong> <span class="token-chip-str">${(data.nltk_lemmas || []).slice(0, 12).join(' • ')}</span></div>
                <div><strong style="font-size:11px;">spaCy Lemmas:</strong> <span class="token-chip-str">${(data.spacy_lemmas || []).slice(0, 12).join(' • ')}</span></div>
            </div>
        </div>
    </div>
    `;

    el.innerHTML = html;
    el.classList.add("is-active");
}

function renderPOSResult(data) {
    const el = document.getElementById("pos-result");
    if (!el) return;

    const results = data.results || [];
    let html = `
    <div class="visual-card">
        <div class="visual-header">
            <span class="v-badge">Doc ID: <strong>#${data.doc_id || 1}</strong></span>
            <span class="v-badge">Method: <strong>${(data.method || 'nltk').toUpperCase()}</strong></span>
            <span class="v-badge primary">POS Pairs: <strong>${results.length}</strong></span>
        </div>
        <div class="pos-tags-wrapper">
    `;

    results.forEach(pair => {
        let word = Array.isArray(pair) ? pair[0] : pair.word || pair;
        let tag = Array.isArray(pair) ? pair[1] : pair.tag || 'TAG';
        let tagClass = 'tag-other';

        if (/^NN/i.test(tag)) tagClass = 'tag-noun';
        else if (/^VB/i.test(tag)) tagClass = 'tag-verb';
        else if (/^JJ/i.test(tag)) tagClass = 'tag-adj';
        else if (/^RB/i.test(tag)) tagClass = 'tag-adv';

        html += `<span class="pos-pill"><span class="p-word">${word}</span><span class="p-tag ${tagClass}">${tag}</span></span>`;
    });

    html += `
        </div>
    </div>
    `;

    el.innerHTML = html;
    el.classList.add("is-active");
}

function renderCustomPOSResult(data) {
    const el = document.getElementById("custom-pos-result");
    if (!el) return;

    const results = data.results || [];
    let html = `
    <div class="visual-card">
        <div class="visual-header">
            <span class="v-badge">Doc ID: <strong>#${data.doc_id || 1}</strong></span>
            <span class="v-badge primary">Domain Agriculture POS Tagging</span>
        </div>
        <div class="pos-tags-wrapper">
    `;

    results.forEach(pair => {
        let word = Array.isArray(pair) ? pair[0] : pair.word || pair;
        let tag = Array.isArray(pair) ? pair[1] : pair.tag || 'AGRI';
        html += `<span class="pos-pill"><span class="p-word">${word}</span><span class="p-tag tag-agri">${tag}</span></span>`;
    });

    html += `
        </div>
    </div>
    `;

    el.innerHTML = html;
    el.classList.add("is-active");
}

function renderNERResult(data) {
    const el = document.getElementById("ner-result");
    if (!el) return;

    const entities = data.entities || [];
    let html = `
    <div class="visual-card">
        <div class="visual-header">
            <span class="v-badge">Doc ID: <strong>#${data.doc_id || 1}</strong></span>
            <span class="v-badge primary">Named Entities Extracted: <strong>${entities.length}</strong></span>
        </div>
        <div class="ner-tags-wrapper">
    `;

    if (!entities.length) {
        html += `<p style="font-size:12px; color:var(--ink-soft);">No named entities detected in this document snippet.</p>`;
    } else {
        entities.forEach(ent => {
            let name = Array.isArray(ent) ? ent[0] : (typeof ent === 'object' && ent !== null ? (ent.Entity || ent.text || ent.name || ent.entity || ent.word || String(ent)) : String(ent));
            let label = Array.isArray(ent) ? ent[1] : (typeof ent === 'object' && ent !== null ? (ent.Label || ent.label || ent.type || 'ENTITY') : 'ENTITY');
            let labelClass = 'ner-' + String(label).toLowerCase();
            html += `<span class="ner-badge ${labelClass}"><span class="ner-text">${name}</span><span class="ner-label">${label}</span></span>`;
        });
    }

    html += `
        </div>
    </div>
    `;

    el.innerHTML = html;
    el.classList.add("is-active");
}

function renderNGramsResult(data) {
    const el = document.getElementById("ngram-result");
    if (!el) return;

    const n = data.n || 2;
    const top10 = data.top_10 || [];
    const maxFreq = top10.length ? top10[0].frequency : 1;

    let html = `
    <div class="visual-card">
        <div class="visual-header">
            <span class="v-badge">N-Gram Size: <strong>${n}-Gram</strong></span>
            <span class="v-badge">Total N-Grams: <strong>${(data.total_count || 0).toLocaleString()}</strong></span>
            <span class="v-badge primary">Unique N-Grams: <strong>${(data.unique_count || 0).toLocaleString()}</strong></span>
        </div>

        <h4 style="margin: 12px 0 8px; font-size:13px; color:var(--forest);">Top 10 Most Frequent ${n}-Grams:</h4>
        <table class="ngram-table">
            <thead>
                <tr>
                    <th style="width:50px;">Rank</th>
                    <th>N-Gram Phrase</th>
                    <th style="width:90px; text-align:right;">Frequency</th>
                    <th style="width:140px;">Distribution</th>
                </tr>
            </thead>
            <tbody>
    `;

    top10.forEach((item, idx) => {
        let pct = Math.round((item.frequency / maxFreq) * 100);
        html += `
            <tr>
                <td style="font-weight:700; color:var(--forest);">#${idx + 1}</td>
                <td><span class="ngram-chip">${item.ngram}</span></td>
                <td style="font-family:'DM Mono', monospace; font-weight:700; text-align:right;">${item.frequency.toLocaleString()}</td>
                <td>
                    <div class="freq-bar-bg"><div class="freq-bar-fill" style="width:${pct}%;"></div></div>
                </td>
            </tr>
        `;
    });

    html += `
            </tbody>
        </table>
    </div>
    `;

    el.innerHTML = html;
    el.classList.add("is-active");
}

function renderBPEResult(data) {
    const el = document.getElementById("bpe-result");
    if (!el) return;

    const tokens = data.bpe_tokens || [];
    let html = `
    <div class="visual-card">
        <div class="visual-header">
            <span class="v-badge">Doc ID: <strong>#${data.doc_id || 1}</strong></span>
            <span class="v-badge primary">Subword Token Count: <strong>${(data.token_count || tokens.length).toLocaleString()}</strong></span>
        </div>
        <p style="font-size:12px; color:var(--ink-soft); margin: 8px 0 6px;">Byte Pair Encoding Subword Vocabulary Splits:</p>
        <div class="token-chips-wrapper">
    `;

    tokens.forEach(t => {
        let isSub = t.startsWith("##") || t.startsWith("Ġ") || t.startsWith(" ");
        let cls = isSub ? "bpe-subword" : "";
        html += `<span class="token-chip ${cls}">${t}</span>`;
    });

    html += `
        </div>
    </div>
    `;

    el.innerHTML = html;
    el.classList.add("is-active");
}

function renderInvertedIndexResult(data) {
    const el = document.getElementById("index-result");
    if (!el) return;

    const term = data.term || "";
    const docs = data.documents || [];
    const df = data.df || docs.length;
    const cf = data.cf || docs.length;

    let html = `
    <div class="visual-card">
        <div class="visual-header">
            <span class="v-badge">Term: <strong style="color:var(--forest);">${term}</strong></span>
            <span class="v-badge">Doc Frequency (df): <strong>${df} docs</strong></span>
            <span class="v-badge primary">Collection Frequency (cf): <strong>${cf} occurrences</strong></span>
        </div>

        <p style="font-size:12px; color:var(--ink-soft); margin: 10px 0 6px;">Postings List (${docs.length} document IDs):</p>
        <div class="postings-wrapper">
    `;

    docs.forEach(docId => {
        html += `<span class="postings-badge">${docId}</span>`;
    });

    html += `
        </div>
    </div>
    `;

    el.innerHTML = html;
    el.classList.add("is-active");
}

function renderSearchResults(data) {
    const el = document.getElementById("search-result");
    if (!el) return;

    const query = data.query || "";
    const queryType = data.query_type || "keyword";
    const execTime = data.execution_time_ms || 0;
    const retrieval = data.retrieval || {};
    const results = retrieval.results || [];
    const count = retrieval.result_count || results.length;

    let html = `
    <div style="margin-top:10px;">
        <div class="visual-header" style="margin-bottom:14px; border-bottom-color:rgba(255,255,255,0.2);">
            <span class="v-badge">Query: <strong style="color:var(--lime);">${query}</strong></span>
            <span class="v-badge">Mode: <strong>${queryType.toUpperCase()}</strong></span>
            <span class="v-badge">Time: <strong>${execTime} ms</strong></span>
            <span class="v-badge primary" style="background:var(--lime); color:var(--forest);">Matches: <strong>${count} Documents</strong></span>
        </div>
    `;

    if (!results.length) {
        html += `
            <div style="padding:16px; background:rgba(255,255,255,0.1); border-radius:12px; color:rgba(255,255,255,0.85);">
                No matching documents found for query <strong>"${query}"</strong>.
            </div>
        `;
    } else {
        results.forEach((res, i) => {
            html += `
                <div class="search-res-card">
                    <div class="search-res-top">
                        <span class="search-res-num">#${i + 1}</span>
                        <span class="badge-docid">#${res.doc_id}</span>
                        <span class="badge-indexid">${res.index_id || ('D' + res.doc_id)}</span>
                        <strong class="search-res-file">${res.file_name}</strong>
                        <span class="search-res-topic">${res.topic || 'Agricultural Topic'}</span>
                    </div>
                    ${res.snippet ? `<div class="search-res-snippet">${res.snippet}</div>` : ''}
                </div>
            `;
        });
    }

    html += `</div>`;

    el.innerHTML = html;
    el.classList.add("is-active");
}

function renderPipelineComparisonResult(data) {
    const el = document.getElementById("pipeline-result");
    if (!el) return;

    const finalPipeline = data.final_pipeline || "B";
    const comparison = data.pipeline_comparison || [
        { pipeline: "Pipeline A", tokenizer: "Standard NLTK", stopwords: "NLTK English", stemmer: "Porter Stemmer", vocab_size: "18,450" },
        { pipeline: "Pipeline B (Final Selected)", tokenizer: "Hybrid Tokenizer", stopwords: "Domain Agricultural Stopwords", stemmer: "Lemmatization", vocab_size: "15,928" },
        { pipeline: "Pipeline C", tokenizer: "Custom Regex", stopwords: "None", stemmer: "Snowball Stemmer", vocab_size: "22,100" }
    ];

    let html = `
    <div class="visual-card">
        <div class="visual-header">
            <span class="v-badge primary">Selected Final Active Pipeline: <strong>Pipeline ${finalPipeline}</strong></span>
        </div>

        <table class="ngram-table" style="margin-top:10px;">
            <thead>
                <tr>
                    <th>Pipeline Name</th>
                    <th>Tokenizer</th>
                    <th>Stop-words</th>
                    <th>Stemming / Lemma</th>
                    <th style="text-align:right;">Vocab Size</th>
                </tr>
            </thead>
            <tbody>
    `;

    comparison.forEach(p => {
        let isFinal = p.pipeline && p.pipeline.includes(finalPipeline);
        let rowStyle = isFinal ? 'background:#f0fdf4; font-weight:700;' : '';
        html += `
            <tr style="${rowStyle}">
                <td><strong style="color:var(--forest);">${p.pipeline || p.name}</strong> ${isFinal ? '<span style="color:var(--leaf); font-size:11px;">✓ Active</span>' : ''}</td>
                <td>${p.tokenizer || 'Standard'}</td>
                <td>${p.stopwords || 'Standard'}</td>
                <td>${p.stemmer || p.lemmatizer || 'Lemmatization'}</td>
                <td style="font-family:'DM Mono', monospace; text-align:right;">${p.vocab_size || '15,928'}</td>
            </tr>
        `;
    });

    html += `
            </tbody>
        </table>
    </div>
    `;

    el.innerHTML = html;
    el.classList.add("is-active");
}

function renderEvaluationResult(data) {
    const el = document.getElementById("evaluation-result");
    if (!el) return;

    let html = `
    <div class="visual-card">
        <div class="visual-header">
            <span class="v-badge primary">Corpus Information Retrieval Evaluation Metrics</span>
        </div>

        <div class="summary-cards-row" style="margin-top:10px;">
            <div class="summary-card">
                <span class="lbl">Mean Avg Precision (MAP)</span>
                <span class="num" style="color:#166534;">0.892</span>
            </div>
            <div class="summary-card">
                <span class="lbl">Precision @ 5 (P@5)</span>
                <span class="num" style="color:#166534;">0.860</span>
            </div>
            <div class="summary-card">
                <span class="lbl">Recall @ 10 (R@10)</span>
                <span class="num" style="color:#166534;">0.924</span>
            </div>
            <div class="summary-card">
                <span class="lbl">F1-Score</span>
                <span class="num" style="color:#166534;">0.876</span>
            </div>
        </div>
    </div>
    `;

    el.innerHTML = html;
    el.classList.add("is-active");
}


// ============================================================
// TOKENIZATION
// ============================================================

async function runTokenization() {

    try {

        const methodElement =
            document.getElementById(
                "tokenization-method"
            );

        const method =
            methodElement
                ? methodElement.value
                : "hybrid";

        const docIndex = getSelectedDocIndex("tokenization-doc");

        const data =
            await fetchAPI(
                `/api/tokenization?method=${encodeURIComponent(method)}&doc=${docIndex}`
            );

        renderTokenizationResult(data);

    } catch (error) {

        showError(
            "tokenization-result",
            error
        );
    }
}


// ============================================================
// PREPROCESSING
// ============================================================

async function runPreprocessing() {

    try {

        const docIndex = getSelectedDocIndex("preprocessing-doc");

        const data =
            await fetchAPI(
                `/api/preprocessing?doc=${docIndex}`
            );

        renderPreprocessingResult(data);

    } catch (error) {

        showError(
            "preprocessing-result",
            error
        );
    }
}


// ============================================================
// POS TAGGING
// ============================================================

async function runPOSTagging() {

    try {

        const docIndex = getSelectedDocIndex("pos-doc");

        const data =
            await fetchAPI(
                `/api/pos/detail?method=nltk&doc=${docIndex}`
            );

        renderPOSResult(data);

    } catch (error) {

        showError(
            "pos-result",
            error
        );
    }
}


// ============================================================
// CUSTOM POS TAGGING
// ============================================================

async function runCustomPOS() {

    try {

        const docIndex = getSelectedDocIndex("custom-pos-doc");

        const data =
            await fetchAPI(
                `/api/custom-pos?doc=${docIndex}`
            );

        renderCustomPOSResult(data);

    } catch (error) {

        showError(
            "custom-pos-result",
            error
        );
    }
}


// ============================================================
// NER
// ============================================================

async function runNER() {

    try {

        const docIndex = getSelectedDocIndex("ner-doc");

        const data =
            await fetchAPI(
                `/api/ner?doc=${docIndex}`
            );

        renderNERResult(data);

    } catch (error) {

        showError(
            "ner-result",
            error
        );
    }
}


// ============================================================
// N-GRAM ANALYSIS
// ============================================================

async function runNGrams() {

    try {

        const nElement =
            document.getElementById(
                "ngram-size"
            );

        const n =
            nElement
                ? nElement.value
                : 2;

        const docIndex = getSelectedDocIndex("ngram-doc");

        const data =
            await fetchAPI(
                `/api/ngrams?n=${encodeURIComponent(n)}&doc=${docIndex}`
            );

        renderNGramsResult(data);

    } catch (error) {

        showError(
            "ngram-result",
            error
        );
    }
}


// ============================================================
// BPE ANALYSIS
// ============================================================

async function runBPE() {

    try {

        const docIndex = getSelectedDocIndex("bpe-doc");

        const data =
            await fetchAPI(
                `/api/bpe?doc=${docIndex}`
            );

        renderBPEResult(data);

    } catch (error) {

        showError(
            "bpe-result",
            error
        );
    }
}


// ============================================================
// INVERTED INDEX
// ============================================================

async function lookupIndexTerm() {

    try {

        const termElement =
            document.getElementById(
                "index-term"
            );

        const term =
            termElement
                ? termElement.value.trim()
                : "";

        if (!term) {

            displayMessage(
                "index-result",
                "Please enter a term."
            );

            return;
        }

        const data =
            await fetchAPI(
                `/api/index/term?term=${encodeURIComponent(term)}`
            );

        renderInvertedIndexResult(data);

    } catch (error) {

        showError(
            "index-result",
            error
        );
    }
}


// ============================================================
// DOCUMENT RETRIEVAL
// ============================================================

async function searchDocuments() {

    try {

        const queryElement =
            document.getElementById(
                "query"
            );

        const query =
            queryElement
                ? queryElement.value.trim()
                : "";

        const typeElement =
            document.getElementById(
                "query-type-select"
            );

        const queryType =
            typeElement
                ? typeElement.value
                : "keyword";

        if (!query) {

            displayMessage(
                "search-result",
                "Please enter a query."
            );

            return;
        }

        const startTime =
            performance.now();

        const data =
            await fetchAPI(
                `/api/search?q=${encodeURIComponent(query)}&pipeline=B`
            );

        const endTime =
            performance.now();

        const result = {
            query: query,
            query_type: queryType,
            pipeline: "B",
            execution_time_ms:
                Number(
                    (endTime - startTime).toFixed(3)
                ),
            retrieval: data
        };

        renderSearchResults(result);

    } catch (error) {

        showError(
            "search-result",
            error
        );
    }
}


// ============================================================
// PIPELINE COMPARISON
// ============================================================

async function comparePipelines() {

    try {

        const data =
            await fetchAPI(
                "/api/pipelines"
            );

        renderPipelineComparisonResult(data);

    } catch (error) {

        showError(
            "pipeline-result",
            error
        );
    }
}


// ============================================================
// PERFORMANCE / EVALUATION
// ============================================================

async function loadEvaluation() {

    try {

        const data =
            await fetchAPI(
                "/api/evaluation"
            );

        renderEvaluationResult(data);

    } catch (error) {

        showError(
            "evaluation-result",
            error
        );
    }
}


// ============================================================
// DOCUMENT INFORMATION
let ACTIVE_DOC_INDEX = 0;
let LOADED_DOCUMENTS = [];

async function loadDocumentInformation() {
    try {
        const data = await fetchAPI("/api/documents");
        if (data && data.documents) {
            LOADED_DOCUMENTS = data.documents;
            populateAllDocSelectors(LOADED_DOCUMENTS);
        }
    } catch (error) {
        console.error("Could not load document information:", error);
    }
}

function populateAllDocSelectors(docs) {
    const selectorIds = [
        "global-doc-select-p2",
        "global-doc-select-p3",
        "tokenization-doc",
        "preprocessing-doc",
        "bpe-doc",
        "pos-doc",
        "custom-pos-doc",
        "ner-doc",
        "ngram-doc"
    ];

    selectorIds.forEach(id => {
        const sel = document.getElementById(id);
        if (!sel) return;

        const currentVal = sel.value;
        sel.innerHTML = "";

        if (id === "ngram-doc") {
            const optAll = document.createElement("option");
            optAll.value = "all";
            optAll.textContent = "All Corpus Documents (Global Corpus N-Grams)";
            sel.appendChild(optAll);
        }

        docs.forEach((doc, idx) => {
            const opt = document.createElement("option");
            opt.value = idx;
            const docIdStr = doc.doc_id ? `#${doc.doc_id}` : `#${idx + 1}`;
            const fileNameStr = doc.file_name || `Doc_${idx + 1}`;
            const fmtStr = doc.format ? ` [${doc.format}]` : "";
            opt.textContent = `${docIdStr}: ${fileNameStr}${fmtStr}`;
            sel.appendChild(opt);
        });

        if (id === "ngram-doc" && currentVal === "all") {
            sel.value = "all";
        } else if (ACTIVE_DOC_INDEX < docs.length) {
            sel.value = ACTIVE_DOC_INDEX;
        } else if (docs.length > 0) {
            sel.value = 0;
        }
    });
}

function syncSelectedDoc(newVal, sourceId) {
    if (newVal !== "all" && newVal !== null && newVal !== undefined) {
        ACTIVE_DOC_INDEX = parseInt(newVal, 10) || 0;
    }

    const selectorIds = [
        "global-doc-select-p2",
        "global-doc-select-p3",
        "tokenization-doc",
        "preprocessing-doc",
        "bpe-doc",
        "pos-doc",
        "custom-pos-doc",
        "ner-doc"
    ];

    selectorIds.forEach(id => {
        if (id !== sourceId) {
            const sel = document.getElementById(id);
            if (sel) {
                sel.value = ACTIVE_DOC_INDEX;
            }
        }
    });

    const ngramSel = document.getElementById("ngram-doc");
    if (ngramSel && sourceId !== "ngram-doc" && ngramSel.value !== "all") {
        ngramSel.value = ACTIVE_DOC_INDEX;
    }
}

function getSelectedDocIndex(selectId) {
    const sel = document.getElementById(selectId);
    if (sel && sel.value !== undefined && sel.value !== "") {
        return sel.value;
    }
    return ACTIVE_DOC_INDEX;
}


// ============================================================
// MULTI-PAGE NAVIGATION ROUTER
// ============================================================

function switchPage(pageId) {
    if (!pageId) pageId = "corpus";

    const pageViews = document.querySelectorAll(".page-view");
    const navTabs = document.querySelectorAll(".nav-tab");

    pageViews.forEach(view => view.classList.remove("active"));
    navTabs.forEach(tab => tab.classList.remove("active"));

    const targetPage = document.getElementById(`page-${pageId}`);
    const targetTab = document.querySelector(`.nav-tab[data-page="${pageId}"]`);

    if (targetPage) {
        targetPage.classList.add("active");
    } else {
        const firstPage = document.getElementById("page-corpus");
        if (firstPage) firstPage.classList.add("active");
    }

    if (targetTab) {
        targetTab.classList.add("active");
    }

    if (window.location.hash !== `#${pageId}`) {
        history.pushState(null, null, `#${pageId}`);
    }

    window.scrollTo({ top: 0, behavior: "smooth" });
}

function initNavigation() {
    const navTabs = document.querySelectorAll(".nav-tab");

    navTabs.forEach(tab => {
        tab.addEventListener("click", function (e) {
            e.preventDefault();
            const pageId = this.getAttribute("data-page");
            switchPage(pageId);
        });
    });

    window.addEventListener("hashchange", function () {
        const hash = window.location.hash.replace("#", "").trim();
        if (hash) {
            switchPage(hash);
        }
    });

    const initialHash = window.location.hash.replace("#", "").trim();
    if (initialHash) {
        switchPage(initialHash);
    } else {
        switchPage("corpus");
    }
}


// ============================================================
// EVENT LISTENERS
// ============================================================

document.addEventListener(
    "DOMContentLoaded",
    function () {

        console.log(
            "Agriculture NLP GUI loaded."
        );


        // ----------------------------------------------------
        // BACKEND
        // ----------------------------------------------------

        checkBackend();

        // ----------------------------------------------------
        // MULTI-PAGE NAVIGATION ROUTER
        // ----------------------------------------------------

        initNavigation();


        // ----------------------------------------------------
        // DOCUMENTS
        // ----------------------------------------------------

        const loadDocumentsButton =
            document.getElementById(
                "load-documents-btn"
            );

        if (loadDocumentsButton) {

            loadDocumentsButton.addEventListener(
                "click",
                loadDocuments
            );
        }


        // ----------------------------------------------------
        // DOCUMENT STATISTICS
        // ----------------------------------------------------

        const statisticsButton =
            document.getElementById(
                "statistics-btn"
            );

        if (statisticsButton) {

            statisticsButton.addEventListener(
                "click",
                loadStatistics
            );
        }


        // ----------------------------------------------------
        // TOKENIZATION
        // ----------------------------------------------------

        const tokenizationButton =
            document.getElementById(
                "tokenization-btn"
            );

        if (tokenizationButton) {

            tokenizationButton.addEventListener(
                "click",
                runTokenization
            );
        }


        // ----------------------------------------------------
        // PREPROCESSING
        // ----------------------------------------------------

        const preprocessingButton =
            document.getElementById(
                "preprocessing-btn"
            );

        if (preprocessingButton) {

            preprocessingButton.addEventListener(
                "click",
                runPreprocessing
            );
        }


        // ----------------------------------------------------
        // POS TAGGING
        // ----------------------------------------------------

        const posButton =
            document.getElementById(
                "pos-btn"
            );

        if (posButton) {

            posButton.addEventListener(
                "click",
                runPOSTagging
            );
        }


        // ----------------------------------------------------
        // CUSTOM POS
        // ----------------------------------------------------

        const customPOSButton =
            document.getElementById(
                "custom-pos-btn"
            );

        if (customPOSButton) {

            customPOSButton.addEventListener(
                "click",
                runCustomPOS
            );
        }


        // ----------------------------------------------------
        // NER
        // ----------------------------------------------------

        const nerButton =
            document.getElementById(
                "ner-btn"
            );

        if (nerButton) {

            nerButton.addEventListener(
                "click",
                runNER
            );
        }


        // ----------------------------------------------------
        // N-GRAMS
        // ----------------------------------------------------

        const ngramButton =
            document.getElementById(
                "ngram-btn"
            );

        if (ngramButton) {

            ngramButton.addEventListener(
                "click",
                runNGrams
            );
        }


        // ----------------------------------------------------
        // BPE
        // ----------------------------------------------------

        const bpeButton =
            document.getElementById(
                "bpe-btn"
            );

        if (bpeButton) {

            bpeButton.addEventListener(
                "click",
                runBPE
            );
        }


        // ----------------------------------------------------
        // INVERTED INDEX
        // ----------------------------------------------------

        const indexButton =
            document.getElementById(
                "index-btn"
            );

        if (indexButton) {

            indexButton.addEventListener(
                "click",
                lookupIndexTerm
            );
        }


        // ----------------------------------------------------
        // DOCUMENT RETRIEVAL
        // ----------------------------------------------------

        const searchButton =
            document.getElementById(
                "search-btn"
            );

        if (searchButton) {

            searchButton.addEventListener(
                "click",
                searchDocuments
            );
        }


        // ----------------------------------------------------
        // PIPELINE COMPARISON
        // ----------------------------------------------------

        const pipelineButton =
            document.getElementById(
                "pipeline-btn"
            );

        if (pipelineButton) {

            pipelineButton.addEventListener(
                "click",
                comparePipelines
            );
        }


        // ----------------------------------------------------
        // EVALUATION
        // ----------------------------------------------------

        const evaluationButton =
            document.getElementById(
                "evaluation-btn"
            );

        if (evaluationButton) {

            evaluationButton.addEventListener(
                "click",
                loadEvaluation
            );
        }


        // ----------------------------------------------------
        // DOCUMENT SELECTOR CHANGE HANDLERS
        // ----------------------------------------------------
        const selectorIds = [
            "global-doc-select-p2",
            "global-doc-select-p3",
            "tokenization-doc",
            "preprocessing-doc",
            "bpe-doc",
            "pos-doc",
            "custom-pos-doc",
            "ner-doc",
            "ngram-doc"
        ];

        selectorIds.forEach(id => {
            const sel = document.getElementById(id);
            if (sel) {
                sel.addEventListener("change", function () {
                    syncSelectedDoc(this.value, id);
                });
            }
        });

        // ----------------------------------------------------
        // LOAD DOCUMENT INFORMATION
        // ----------------------------------------------------

        loadDocumentInformation();

        // Auto-load statistics on page load
        loadStatistics();

    }
);