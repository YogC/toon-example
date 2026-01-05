// TOON Playground JavaScript

// State
let currentData = null;
let currentFormats = null;
let currentExample = null;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadExamples();
});

// Load examples from API
async function loadExamples() {
    try {
        const response = await fetch('/api/examples');
        const data = await response.json();
        
        const grid = document.getElementById('examplesGrid');
        grid.innerHTML = '';
        
        Object.entries(data.examples).forEach(([key, example]) => {
            const card = document.createElement('div');
            card.className = 'example-card';
            card.innerHTML = `
                <h3>${example.name}</h3>
                <p>${example.description}</p>
            `;
            card.onclick = () => loadExample(example.data, key);
            grid.appendChild(card);
        });
    } catch (error) {
        console.error('Failed to load examples:', error);
        showError('Failed to load examples');
    }
}

// Load example data
function loadExample(data, exampleKey) {
    const jsonInput = document.getElementById('jsonInput');
    jsonInput.value = JSON.stringify(data, null, 2);
    currentExample = exampleKey;
    convertData();
    
    // Scroll to input
    jsonInput.scrollIntoView({ behavior: 'smooth', block: 'center' });
}

// Format JSON
function formatJSON() {
    const jsonInput = document.getElementById('jsonInput');
    try {
        const data = JSON.parse(jsonInput.value);
        jsonInput.value = JSON.stringify(data, null, 2);
    } catch (error) {
        showError('Invalid JSON format');
    }
}

// Convert data to all formats
async function convertData() {
    const jsonInput = document.getElementById('jsonInput').value.trim();
    
    if (!jsonInput) {
        showError('Please enter some JSON data');
        return;
    }
    
    try {
        // Validate JSON first
        JSON.parse(jsonInput);
        
        showLoading();
        
        const response = await fetch('/api/convert', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ json_data: jsonInput })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Conversion failed');
        }
        
        const data = await response.json();
        currentData = jsonInput;
        currentFormats = data.formats;
        
        displayResults(data);
        hideLoading();
        
    } catch (error) {
        hideLoading();
        showError(error.message);
    }
}

// Display conversion results
function displayResults(data) {
    const comparisonSection = document.getElementById('comparisonSection');
    const llmSection = document.getElementById('llmSection');
    
    comparisonSection.style.display = 'block';
    llmSection.style.display = 'block';
    
    // Update token counts
    const jsonTokens = data.formats.json.tokens;
    const yamlTokens = data.formats.yaml.tokens;
    const toonTokens = data.formats.toon.tokens;
    
    const maxTokens = Math.max(jsonTokens, yamlTokens, toonTokens);
    
    document.getElementById('jsonTokens').textContent = `${jsonTokens} tokens`;
    document.getElementById('yamlTokens').textContent = `${yamlTokens} tokens`;
    document.getElementById('toonTokens').textContent = `${toonTokens} tokens`;
    
    // Update token bars
    document.getElementById('jsonBar').style.width = `${(jsonTokens / maxTokens) * 100}%`;
    document.getElementById('yamlBar').style.width = `${(yamlTokens / maxTokens) * 100}%`;
    document.getElementById('toonBar').style.width = `${(toonTokens / maxTokens) * 100}%`;
    
    // Update savings badges
    const yamlSavings = data.comparison.toon_vs_yaml.savings_percent;
    const toonSavings = data.comparison.toon_vs_json.savings_percent;
    
    if (yamlSavings > 0) {
        document.getElementById('yamlSavings').textContent = `${yamlSavings}% vs JSON`;
        document.getElementById('yamlSavings').classList.add('success');
    } else {
        document.getElementById('yamlSavings').textContent = `${Math.abs(yamlSavings)}% more than JSON`;
        document.getElementById('yamlSavings').classList.remove('success');
    }
    
    document.getElementById('toonSavings').textContent = `🎉 ${toonSavings}% savings vs JSON`;
    
    // Update header stat
    document.getElementById('savingsPercent').textContent = `${toonSavings}%`;
    
    // Update format outputs
    document.getElementById('jsonOutput').textContent = data.formats.json.formatted;
    document.getElementById('yamlOutput').textContent = data.formats.yaml.formatted;
    document.getElementById('toonOutput').textContent = data.formats.toon.formatted;
    
    // Scroll to results
    comparisonSection.scrollIntoView({ behavior: 'smooth' });
}

// Load preset prompt based on current example
function loadPresetPrompt() {
    const presetPrompts = {
        'simple_users': 'List all users and highlight which ones are active.',
        'products': 'Calculate the total value of all products in stock (price × stock). Show the breakdown and total.',
        'analytics': 'What was the best performing day? Include the date, views, clicks, and revenue.',
        'nested': 'List all hikes with their companions and tell me which hike had the highest elevation gain.'
    };
    
    // Use preset for current example, or a generic one
    let prompt = presetPrompts[currentExample] || 'Analyze this data and provide key insights.';
    
    // If no example loaded yet, suggest loading one
    if (!currentExample) {
        prompt = 'First, click an example above to load data, then try this preset again!';
        showError('Please load an example first');
    }
    
    document.getElementById('llmPrompt').value = prompt;
    
    // Show success feedback
    if (currentExample) {
        showSuccess('✨ Preset prompt loaded!');
    }
}

// Test with LLM
async function testWithLLM() {
    if (!currentFormats) {
        showError('Please convert data first');
        return;
    }
    
    const prompt = document.getElementById('llmPrompt').value.trim();
    if (!prompt) {
        showError('Please enter a prompt');
        return;
    }
    
    const selectedFormat = document.querySelector('input[name="testFormat"]:checked').value;
    
    let formatData;
    switch(selectedFormat) {
        case 'json':
            formatData = currentFormats.json.formatted;
            break;
        case 'yaml':
            formatData = currentFormats.yaml.formatted;
            break;
        case 'toon':
            formatData = currentFormats.toon.formatted;
            break;
    }
    
    try {
        showLLMLoading();
        
        const response = await fetch('/api/llm-test', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                format: selectedFormat,
                data: formatData,
                prompt: prompt
            })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'LLM request failed');
        }
        
        const data = await response.json();
        displayLLMResults(data);
        
    } catch (error) {
        hideLLMLoading();
        showError(error.message);
    }
}

// Display LLM results
function displayLLMResults(data) {
    const resultsDiv = document.getElementById('llmResults');
    const metaDiv = document.getElementById('resultMeta');
    const contentDiv = document.getElementById('resultContent');
    
    resultsDiv.style.display = 'block';
    
    metaDiv.innerHTML = `
        <div><strong>Format:</strong> ${data.format_used.toUpperCase()}</div>
        <div><strong>Input:</strong> ${data.input_tokens} tokens</div>
        <div><strong>Output:</strong> ${data.output_tokens} tokens</div>
        <div><strong>Total:</strong> ${data.total_tokens} tokens</div>
        <div><strong>Model:</strong> ${data.model}</div>
    `;
    
    contentDiv.innerHTML = formatMarkdown(data.response);
    
    hideLLMLoading();
    
    // Scroll to results
    resultsDiv.scrollIntoView({ behavior: 'smooth' });
}

// Simple markdown formatter
function formatMarkdown(text) {
    return text
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/`(.*?)`/g, '<code>$1</code>')
        .replace(/\n/g, '<br>');
}

// Copy to clipboard
function copyToClipboard(elementId) {
    const element = document.getElementById(elementId);
    const text = element.textContent;
    
    navigator.clipboard.writeText(text).then(() => {
        showSuccess('Copied to clipboard!');
    }).catch(err => {
        showError('Failed to copy');
    });
}

// Clear all
function clearAll() {
    document.getElementById('jsonInput').value = '';
    document.getElementById('comparisonSection').style.display = 'none';
    document.getElementById('llmSection').style.display = 'none';
    document.getElementById('savingsPercent').textContent = '--';
    currentExample = null;
    currentData = null;
    currentFormats = null;
}

// Show/hide loading states
function showLoading() {
    // You can add a loading spinner here
    document.body.style.cursor = 'wait';
}

function hideLoading() {
    document.body.style.cursor = 'default';
}

function showLLMLoading() {
    const resultsDiv = document.getElementById('llmResults');
    resultsDiv.style.display = 'block';
    document.getElementById('resultContent').innerHTML = '<div class="skeleton-loader" style="height: 200px;"></div>';
}

function hideLLMLoading() {
    // Loading content will be replaced by actual results
}

// Toast notifications
function showError(message) {
    showToast(message, 'error');
}

function showSuccess(message) {
    showToast(message, 'success');
}

function showToast(message, type = 'info') {
    // Create toast element
    const toast = document.createElement('div');
    toast.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 16px 24px;
        background: ${type === 'error' ? '#ef4444' : type === 'success' ? '#10b981' : '#6366f1'};
        color: white;
        border-radius: 8px;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
        z-index: 9999;
        font-family: 'Inter', sans-serif;
        font-weight: 500;
        animation: slideIn 0.3s ease;
    `;
    toast.textContent = message;
    
    document.body.appendChild(toast);
    
    // Remove after 3 seconds
    setTimeout(() => {
        toast.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => {
            document.body.removeChild(toast);
        }, 300);
    }, 3000);
}

// Add animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);
