document.addEventListener('DOMContentLoaded', () => {
    // Left side / Detection elements
    const textInput = document.getElementById('text-input');
    const analyzeBtn = document.getElementById('analyze-btn');
    const sampleSelect = document.getElementById('sample-select');
    const resultsContainer = document.getElementById('results-container');
    const resultsList = document.getElementById('results-list');
    const btnText = analyzeBtn.querySelector('.btn-text');
    const btnLoader = analyzeBtn.querySelector('.btn-loader');

    // Right side / Enhancement elements
    const enhanceTextInput = document.getElementById('enhance-text-input');
    const enhanceBtn = document.getElementById('enhance-btn');
    const enhanceSampleSelect = document.getElementById('enhance-sample-select');
    const enhanceResultsContainer = document.getElementById('enhance-results-container');
    const enhanceOutputText = document.getElementById('enhance-output-text');
    const enhanceDevicesList = document.getElementById('enhance-devices-list');
    const enhanceBtnText = enhanceBtn.querySelector('.btn-text');
    const enhanceBtnLoader = enhanceBtn.querySelector('.btn-loader');

    // Toggle View Elements
    const modeSwitch = document.getElementById('mode-switch');
    const detectionView = document.getElementById('detection-view');
    const enhancementView = document.getElementById('enhancement-view');
    const detectLabel = document.querySelector('.toggle-label:first-child');
    const poeticLabel = document.querySelector('.poetic-label');
    const titleHighlight = document.getElementById('app-title-highlight');

    // View Toggle Logic
    modeSwitch.addEventListener('change', (e) => {
        const isGeneratorMode = e.target.checked;
        
        // Update Labels
        if (isGeneratorMode) {
            poeticLabel.classList.add('active');
            detectLabel.classList.remove('active');
            titleHighlight.innerText = 'Generator';
            titleHighlight.style.color = 'var(--alliteration)';
            titleHighlight.style.textShadow = '0 0 20px rgba(20, 184, 166, 0.4)';
            
            // Fade out detector, fade in generator
            detectionView.classList.add('fade-out');
            setTimeout(() => {
                detectionView.style.display = 'none';
                enhancementView.style.display = 'flex';
                // trigger reflow
                void enhancementView.offsetWidth;
                enhancementView.classList.remove('fade-out');
                enhancementView.classList.add('fade-in');
            }, 300);
            
        } else {
            detectLabel.classList.add('active');
            poeticLabel.classList.remove('active');
            titleHighlight.innerText = 'Detector';
            titleHighlight.style.color = ''; // reset to css default
            titleHighlight.style.textShadow = ''; // reset to css default
            
            // Fade out generator, fade in detector
            enhancementView.classList.remove('fade-in');
            enhancementView.classList.add('fade-out');
            setTimeout(() => {
                enhancementView.style.display = 'none';
                detectionView.style.display = 'flex';
                // trigger reflow
                void detectionView.offsetWidth;
                detectionView.classList.remove('fade-out');
                detectionView.classList.add('fade-in');
            }, 300);
        }
    });

    // Initialize labels
    detectLabel.classList.add('active');
    detectionView.classList.add('fade-in');
    enhancementView.classList.add('fade-out');

    // Handle sample selections
    sampleSelect.addEventListener('change', (e) => {
        if (e.target.value) {
            textInput.value = e.target.value;
        }
    });
    
    enhanceSampleSelect.addEventListener('change', (e) => {
        if (e.target.value) {
            enhanceTextInput.value = e.target.value;
        }
    });

    // Handle button clicks
    analyzeBtn.addEventListener('click', analyze);
    enhanceBtn.addEventListener('click', enhanceText);

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

    async function enhanceText() {
        const text = enhanceTextInput.value.trim();
        const lines = text.split('\n').filter(line => line.trim().length > 0);
        
        if (lines.length < 6) {
            alert('The Poetic Enhancement feature requires at least 6 lines of text.');
            return;
        }

        // Set Loading State
        enhanceBtn.disabled = true;
        enhanceBtnText.classList.add('hidden');
        enhanceBtnLoader.classList.remove('hidden');
        
        // Prevent previous results
        enhanceResultsContainer.classList.add('hidden');
        enhanceOutputText.innerHTML = '';
        enhanceDevicesList.innerHTML = '';
        
        const enhanceExplanationList = document.getElementById('enhance-explanation-list');
        if (enhanceExplanationList) {
            enhanceExplanationList.innerHTML = '';
        }

        try {
            const response = await fetch('/enhance', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ text })
            });

            if (!response.ok) {
                const errData = await response.json().catch(() => ({}));
                throw new Error(errData.error || 'Failed to enhance text.');
            }

            const data = await response.json();
            
            if (data.error) {
                 alert(data.error);
                 return;
            }

            // Render enhanced output
            enhanceOutputText.innerText = data.enhanced;
            
            // Render devices tags
            if (data.devices_added && data.devices_added.length > 0) {
                data.devices_added.forEach(device => {
                    const span = document.createElement('span');
                    span.className = 'device-badge';
                    span.innerText = device;
                    enhanceDevicesList.appendChild(span);
                });
            } else {
                enhanceDevicesList.innerHTML = `<span style="color: #94a3b8; font-style: italic;">No specific devices added</span>`;
            }
            
            // Render algorithm explanation breakdown if available
            if (enhanceExplanationList && data.modifications && data.modifications.length > 0) {
                data.modifications.forEach((mod, index) => {
                    const standardizedName = mod.device.toLowerCase().replace(/ & /g, '-').replace(/\s+/g, '-');
                    
                    const card = document.createElement('div');
                    card.className = `result-card color-${standardizedName}`;
                    card.style.animationDelay = `${index * 0.1}s`;
                    
                    card.innerHTML = `
                        <div class="result-header">
                            <span class="result-name">${mod.device}</span>
                        </div>
                        <div class="result-context" style="margin-bottom: 0.5rem; text-decoration: line-through; opacity: 0.7;">"${mod.original_sentence}"</div>
                        <div class="result-context">"${mod.enhanced_sentence}"</div>
                        <div class="algorithm-box">
                            <strong>Algorithm Logic:</strong> ${mod.algorithm}
                        </div>
                    `;
                    enhanceExplanationList.appendChild(card);
                });
            } else if (enhanceExplanationList) {
                enhanceExplanationList.innerHTML = `<div class="no-results" style="padding: 1.5rem;">No identifiable adjustments were successfully triggered this time.</div>`;
            }

            enhanceResultsContainer.classList.remove('hidden');

        } catch (error) {
            console.error(error);
            alert('Enhancement Error: ' + error.message);
        } finally {
            // Restore btn state
            enhanceBtn.disabled = false;
            enhanceBtnText.classList.remove('hidden');
            enhanceBtnLoader.classList.add('hidden');
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
