// Ace Editor Configuration
function initializeAceEditor(elementId) {
    const editor = ace.edit(elementId);
    
    // Set theme based on current site theme
    const isDark = document.body.classList.contains('dark-theme');
    editor.setTheme(isDark ? "ace/theme/monokai" : "ace/theme/chrome");
    
    // Set mode to HTML
    editor.session.setMode("ace/mode/html");
    
    // Editor options
    editor.setOptions({
        fontSize: "14px",
        showPrintMargin: false,
        showGutter: true,
        highlightActiveLine: true,
        enableBasicAutocomplete: true,
        enableSnippets: true,
        enableLiveAutocompletion: true,
        useSoftTabs: true,
        tabSize: 2,
        wrap: true
    });

    // Disable web worker to avoid CSP issues
    editor.session.setUseWorker(false);
    
    return editor;
}

// Export the initialization function
window.initializeAceEditor = initializeAceEditor; 