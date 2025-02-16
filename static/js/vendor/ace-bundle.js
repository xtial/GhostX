// Ace Editor Bundle
(function loadAceScripts() {
    const scripts = [
        'https://cdnjs.cloudflare.com/ajax/libs/ace/1.4.12/ace.js',
        'https://cdnjs.cloudflare.com/ajax/libs/ace/1.4.12/ext-language_tools.js',
        'https://cdnjs.cloudflare.com/ajax/libs/ace/1.4.12/theme-monokai.min.js',
        'https://cdnjs.cloudflare.com/ajax/libs/ace/1.4.12/mode-html.js'
    ];

    function loadScript(url) {
        return new Promise((resolve, reject) => {
            const script = document.createElement('script');
            script.src = url;
            script.async = false;
            script.onload = resolve;
            script.onerror = reject;
            document.head.appendChild(script);
        });
    }

    // Load scripts in sequence
    scripts.reduce((promise, script) => {
        return promise.then(() => loadScript(script));
    }, Promise.resolve());
})();