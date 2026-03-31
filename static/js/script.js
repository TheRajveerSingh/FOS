document.addEventListener('DOMContentLoaded', () => {
    const textInput = document.getElementById('text-input');
    const analyzeBtn = document.getElementById('analyze-btn');
    const sampleSelect = document.getElementById('sample-select');
    const resultsContainer = document.getElementById('results-container');
    const resultsList = document.getElementById('results-list');
    const btnText = document.querySelector('.btn-text');
    const btnLoader = document.querySelector('.btn-loader');

    // Handle sample selection
    sampleSelect.addEventListener('change', (e) => {
        if (e.target.value) {
            textInput.value = e.target.value;
            // Optionally auto trigger analyze
            // analyze();
        }
    });

    // Handle button click
    analyzeBtn.addEventListener('click', analyze);

    async function analyze() {
        const text = textInput.value.trim();
        if (!text) {
            alert('Please enter some text to analyze.');
            return;
        }

        // Set Loading State
        analyzeBtn.disabled = true;
        btnText.classList.add('hidden');
        btnLoader.classList.remove('hidden');
        
        // Hide previous results
        resultsContainer.classList.add('hidden');
        resultsList.innerHTML = '';

        try {
            const response = await fetch('/analyze', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ text })
            });

            if (!response.ok) {
                const errData = await response.json().catch(() => ({}));
                throw new Error(errData.error || 'Failed to analyze text.');
            }

            const data = await response.json();
            renderResults(data.results);
        } catch (error) {
            console.error(error);
            alert('Analysis Error: ' + error.message);
        } finally {
            // Restore btn state
            analyzeBtn.disabled = false;
            btnText.classList.remove('hidden');
            btnLoader.classList.add('hidden');
        }
    }

    function initFloatingPhrases() {
        const container = document.getElementById('floating-text-container');
        if (!container) return;
        
        const phrases = [
            "No Waaaayyy!", "Hell Naah!", "As bright as the sun", "Jumbo Shrimp", 
            "A million times", "The wind whispered", "Bite the bullet", 
            "Deafening silence", "Clear as mud", "Piece of cake", 
            "Living dead", "Break a leg", "As cold as ice"
        ];
        
        for(let i=0; i<20; i++) {
            const span = document.createElement('span');
            span.className = 'floating-phrase';
            span.innerText = phrases[Math.floor(Math.random() * phrases.length)];
            
            // Random positioning horizontally, animate vertically
            span.style.left = `${Math.random() * 100}vw`;
            
            // Random styling (size, opacity, animation duration)
            const size = 1 + Math.random() * 2; // 1rem to 3rem
            span.style.fontSize = `${size}rem`;
            // Larger text is blurrier to simulate depth
            span.style.filter = `blur(${size/1.5}px)`; 
            span.style.animationDuration = `${15 + Math.random() * 25}s`;
            span.style.animationDelay = `${Math.random() * -30}s`;
            
            container.appendChild(span);
        }
    }

    // Initialize floating background text
    initFloatingPhrases();

    function renderResults(results) {
        if (results.length === 0) {
            resultsList.innerHTML = `<div class="no-results">No figures of speech detected. Try another sentence!</div>`;
        } else {
            results.forEach((result, index) => {
                const standardizedName = result.name.toLowerCase().replace(/ & /g, '-').replace(/\s+/g, '-');
                
                const card = document.createElement('div');
                card.className = `result-card color-${standardizedName}`;
                card.style.animationDelay = `${index * 0.1}s`;
                
                card.innerHTML = `
                    <div class="result-header">
                        <span class="result-name">${result.name}</span>
                    </div>
                    <div class="result-context">"${result.context}"</div>
                    <div class="result-explanation">${result.explanation}</div>
                    <div class="algorithm-box">
                        <strong>Algorithm Logic:</strong> ${result.algorithm_explanation}
                    </div>
                `;
                resultsList.appendChild(card);
            });
        }
        
        resultsContainer.classList.remove('hidden');
    }
});
