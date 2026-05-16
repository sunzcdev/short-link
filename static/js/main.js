document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('shorten-form');
    const urlInput = document.getElementById('url-input');
    const resultDiv = document.getElementById('result');
    const errorDiv = document.getElementById('error');
    const shortUrlSpan = document.getElementById('short-url');
    const originalUrlSpan = document.getElementById('original-url');
    const copyBtn = document.getElementById('copy-btn');

    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const url = urlInput.value.trim();
        if (!url) return;

        errorDiv.classList.add('hidden');
        resultDiv.classList.add('hidden');

        try {
            const response = await fetch('/api/shorten', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ url: url })
            });

            const data = await response.json();

            if (response.ok) {
                shortUrlSpan.textContent = data.short_url;
                originalUrlSpan.textContent = data.original_url;
                resultDiv.classList.remove('hidden');
            } else {
                showError(data.error || '生成失败，请重试');
            }
        } catch (err) {
            showError('网络错误，请稍后重试');
        }
    });

    copyBtn.addEventListener('click', async function() {
        const url = shortUrlSpan.textContent;
        try {
            await navigator.clipboard.writeText(url);
            copyBtn.textContent = '已复制';
            copyBtn.classList.add('copied');
            setTimeout(() => {
                copyBtn.textContent = '复制';
                copyBtn.classList.remove('copied');
            }, 2000);
        } catch (err) {
            const textArea = document.createElement('textarea');
            textArea.value = url;
            document.body.appendChild(textArea);
            textArea.select();
            document.execCommand('copy');
            document.body.removeChild(textArea);
            copyBtn.textContent = '已复制';
            copyBtn.classList.add('copied');
            setTimeout(() => {
                copyBtn.textContent = '复制';
                copyBtn.classList.remove('copied');
            }, 2000);
        }
    });

    function showError(message) {
        errorDiv.textContent = message;
        errorDiv.classList.remove('hidden');
    }
});
