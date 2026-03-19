/**
 * AskMyDocs — Frontend Application Logic
 * Handles query submission, response rendering, and citation highlighting.
 */

(function () {
    'use strict';

    // DOM Elements
    const queryInput = document.getElementById('query-input');
    const searchBtn = document.getElementById('search-btn');
    const ingestBtn = document.getElementById('ingest-btn');
    const resultsArea = document.getElementById('results-area');
    const emptyState = document.getElementById('empty-state');
    const loadingState = document.getElementById('loading-state');
    const answerContainer = document.getElementById('answer-container');
    const exampleQueries = document.querySelectorAll('.example-query');

    // Loading step elements
    const stepRetrieve = document.getElementById('step-retrieve');
    const stepRerank = document.getElementById('step-rerank');
    const stepGenerate = document.getElementById('step-generate');

    // =========================================
    //  QUERY HANDLING
    // =========================================

    async function submitQuery(question) {
        if (!question.trim()) return;

        showLoadingState();

        try {
            // Simulate step progression
            activateStep(stepRetrieve);
            await delay(400);
            markStepDone(stepRetrieve);
            activateStep(stepRerank);
            await delay(300);
            markStepDone(stepRerank);
            activateStep(stepGenerate);

            const response = await fetch('/api/query', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ question }),
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Query failed');
            }

            const data = await response.json();
            markStepDone(stepGenerate);
            await delay(200);

            renderAnswer(data);
        } catch (error) {
            showToast(error.message, 'error');
            showEmptyState();
        }
    }

    // =========================================
    //  RENDERING
    // =========================================

    function renderAnswer(data) {
        const isDeclined = data.is_declined;
        const statusClass = isDeclined ? 'answer-card__status--declined' : 'answer-card__status--success';
        const statusText = isDeclined ? '⚠ Insufficient Evidence' : '✓ Answer Found';
        const cardClass = isDeclined ? 'answer-card answer-card--declined' : 'answer-card';

        // Format answer text: convert [Source N] to clickable tags
        const formattedAnswer = formatAnswerWithCitations(data.answer);

        let html = `
            <div class="${cardClass}">
                <div class="answer-card__header">
                    <span class="answer-card__status ${statusClass}">${statusText}</span>
                    <span class="answer-card__meta">
                        ${data.num_chunks_retrieved} retrieved · ${data.num_chunks_reranked} re-ranked
                    </span>
                </div>
                <div class="answer-card__body">${formattedAnswer}</div>
        `;

        // Citations panel
        if (data.citations && data.citations.length > 0) {
            html += `
                <div class="citations-panel">
                    <div class="citations-panel__title">📎 Sources (${data.citations.length})</div>
            `;

            for (const citation of data.citations) {
                html += `
                    <div class="citation-item" id="citation-${citation.source_index}" data-index="${citation.source_index}">
                        <div class="citation-item__header">
                            <span class="citation-item__index">${citation.source_index}</span>
                            <span class="citation-item__source">${escapeHtml(citation.source_file)}</span>
                            <span class="citation-item__section">${escapeHtml(citation.section_heading || 'N/A')}</span>
                        </div>
                        <div class="citation-item__text">${escapeHtml(citation.text_excerpt)}</div>
                    </div>
                `;
            }

            html += `</div>`;
        }

        html += `</div>`;

        answerContainer.innerHTML = html;
        emptyState.style.display = 'none';
        loadingState.style.display = 'none';
        answerContainer.style.display = 'block';

        // Attach citation click handlers
        attachCitationHandlers();
    }

    function formatAnswerWithCitations(text) {
        // Convert markdown-style paragraphs
        let formatted = escapeHtml(text);

        // Replace [Source N] with clickable citation tags
        formatted = formatted.replace(
            /\[Source\s+(\d+)\]/g,
            '<span class="citation-tag" data-citation-index="$1" title="Click to view source">[Source $1]</span>'
        );

        // Convert newlines to paragraphs
        const paragraphs = formatted.split(/\n\n+/);
        formatted = paragraphs
            .map(p => p.trim())
            .filter(p => p)
            .map(p => `<p>${p.replace(/\n/g, '<br>')}</p>`)
            .join('');

        return formatted;
    }

    function attachCitationHandlers() {
        const tags = document.querySelectorAll('.citation-tag');
        tags.forEach(tag => {
            tag.addEventListener('click', () => {
                const index = tag.getAttribute('data-citation-index');
                const citationEl = document.getElementById(`citation-${index}`);
                if (citationEl) {
                    // Remove previous highlight
                    document.querySelectorAll('.citation-item.highlight').forEach(el => {
                        el.classList.remove('highlight');
                    });
                    // Highlight and scroll to citation
                    citationEl.classList.add('highlight');
                    citationEl.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    // Auto-remove highlight after 3s
                    setTimeout(() => citationEl.classList.remove('highlight'), 3000);
                }
            });
        });
    }

    // =========================================
    //  DOCUMENT INGESTION
    // =========================================

    async function ingestDocuments() {
        ingestBtn.disabled = true;
        ingestBtn.textContent = '⟳ Ingesting...';

        try {
            const response = await fetch('/api/ingest', {
                method: 'POST',
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Ingestion failed');
            }

            const data = await response.json();
            showToast(
                `✓ Ingested ${data.documents_loaded} docs → ${data.total_chunks} chunks (${data.new_chunks_indexed} new)`,
                'success'
            );
        } catch (error) {
            showToast(`✗ ${error.message}`, 'error');
        } finally {
            ingestBtn.disabled = false;
            ingestBtn.textContent = '⟳ Ingest Documents';
        }
    }

    // =========================================
    //  UI STATE HELPERS
    // =========================================

    function showLoadingState() {
        emptyState.style.display = 'none';
        answerContainer.style.display = 'none';
        loadingState.style.display = 'flex';

        // Reset steps
        [stepRetrieve, stepRerank, stepGenerate].forEach(step => {
            step.classList.remove('active', 'done');
        });
    }

    function showEmptyState() {
        loadingState.style.display = 'none';
        answerContainer.style.display = 'none';
        emptyState.style.display = 'block';
    }

    function activateStep(stepEl) {
        stepEl.classList.add('active');
    }

    function markStepDone(stepEl) {
        stepEl.classList.remove('active');
        stepEl.classList.add('done');
    }

    function showToast(message, type = 'success') {
        const toast = document.createElement('div');
        toast.className = `toast toast--${type}`;
        toast.textContent = message;
        document.body.appendChild(toast);
        setTimeout(() => toast.remove(), 3000);
    }

    function delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // =========================================
    //  EVENT LISTENERS
    // =========================================

    searchBtn.addEventListener('click', () => {
        submitQuery(queryInput.value);
    });

    queryInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            submitQuery(queryInput.value);
        }
    });

    ingestBtn.addEventListener('click', ingestDocuments);

    exampleQueries.forEach(example => {
        example.addEventListener('click', () => {
            const query = example.getAttribute('data-query');
            queryInput.value = query;
            submitQuery(query);
        });
    });

    // Focus input on load
    queryInput.focus();
})();
