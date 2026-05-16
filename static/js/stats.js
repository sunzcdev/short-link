document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('stats-form');
    const codeInput = document.getElementById('code-input');
    const errorDiv = document.getElementById('error');
    const statsResultDiv = document.getElementById('stats-result');
    const totalVisitsEl = document.getElementById('total-visits');
    const uniqueVisitorsEl = document.getElementById('unique-visitors');
    const codeEl = document.getElementById('stats-code');
    const originalUrlEl = document.getElementById('stats-original-url');
    const createdAtEl = document.getElementById('stats-created-at');
    const visitsContainer = document.getElementById('visits-container');
    const noVisitsEl = document.getElementById('no-visits');

    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        let code = codeInput.value.trim();
        if (!code) return;

        if (code.includes('/')) {
            const parts = code.split('/');
            code = parts[parts.length - 1];
        }

        errorDiv.classList.add('hidden');
        statsResultDiv.classList.add('hidden');

        try {
            const response = await fetch(`/api/stats/${encodeURIComponent(code)}`);
            const data = await response.json();

            if (response.ok) {
                displayStats(data);
            } else {
                showError(data.error || '查询失败，请重试');
            }
        } catch (err) {
            showError('网络错误，请稍后重试');
        }
    });

    function displayStats(data) {
        totalVisitsEl.textContent = data.total_visits;
        uniqueVisitorsEl.textContent = data.unique_visitors;
        codeEl.textContent = data.short_code;
        originalUrlEl.textContent = data.original_url;
        originalUrlEl.href = data.original_url;
        createdAtEl.textContent = data.created_at;

        visitsContainer.innerHTML = '';
        
        if (data.recent_visits.length > 0) {
            data.recent_visits.forEach(visit => {
                const row = document.createElement('div');
                row.className = 'visit-item';
                row.innerHTML = `
                    <span>${visit.ip || '-'}</span>
                    <span>${visit.browser || '-'}</span>
                    <span>${visit.os || '-'}</span>
                    <span>${visit.device || '-'}</span>
                    <span>${visit.time}</span>
                `;
                visitsContainer.appendChild(row);
            });
            noVisitsEl.classList.add('hidden');
        } else {
            noVisitsEl.classList.remove('hidden');
        }

        statsResultDiv.classList.remove('hidden');
    }

    function showError(message) {
        errorDiv.textContent = message;
        errorDiv.classList.remove('hidden');
    }
});
