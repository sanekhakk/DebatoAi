class DebateSetup {
    constructor() {
        this.currentStep = 1;
        this.selectedCategory = null;
        this.selectedTopic = null;
        this.selectedDifficulty = 'medium';
        this.selectedTime = 10;
        this.categories = [];
        this.topics = [];
        this.isLoading = false;
        
        //Ensure DOM is fully loaded
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.init());
        } else {
            this.init();
        }
    }
    
    init() {
        console.log('Initializing DebateSetup...');
        this.initializeElements();
        this.bindStaticEvents();
        this.loadCategories();
        this.checkGuestStatus();
        this.initializeDefaults();
    }
    
    initializeElements() {
        this.steps = document.querySelectorAll('.setup-step');
        this.progressFill = document.getElementById('progress-fill');
        this.progressSteps = document.querySelectorAll('.progress-step');
        
        //Navigation buttons
        this.nextToTopicsBtn = document.getElementById('next-to-topics'); 
        this.nextToSettingsBtn = document.getElementById('next-to-settings');
        this.backToCategoriesBtn = document.getElementById('back-to-categories');
        this.backToTopicsBtn = document.getElementById('back-to-topics'); // This is the button in Step 3
        this.startDebateBtn = document.getElementById('start-debate');
        
        //Containers
        this.categoriesContainer = document.getElementById('categories-container');
        this.topicsContainer = document.getElementById('topics-container');
        this.topicsGrid = document.getElementById('topics-grid');
        this.topicsLoading = document.querySelector('.topics-loading');
        
        //Modals
        this.guestWarningModal = document.getElementById('guest-warning-modal');
        this.loadingModal = document.getElementById('loading-modal');
        
        console.log('Elements initialized');
    }
    
    bindStaticEvents() {
        if (this.nextToTopicsBtn) {
            this.nextToTopicsBtn.onclick = (e) => {
                e.preventDefault();
                console.log('Next to topics clicked');
                this.goToStep(2);
            };
        }
        
        if (this.nextToSettingsBtn) {
            this.nextToSettingsBtn.onclick = (e) => {
                e.preventDefault();
                console.log('Next to settings clicked');
                this.goToStep(3);
            };
        }
        
        if (this.backToCategoriesBtn) {
            this.backToCategoriesBtn.onclick = (e) => {
                e.preventDefault();
                this.goToStep(1);
            };
        }

        if (this.backToTopicsBtn) { 
            this.backToTopicsBtn.onclick = (e) => {
                e.preventDefault();
                this.goToStep(2);
            };
        }
        
        if (this.startDebateBtn) {
            this.startDebateBtn.onclick = (e) => {
                e.preventDefault();
                this.startDebate();
            };
        }
        
        //Modal events
        const continueAsGuestBtn = document.getElementById('continue-as-guest');
        const registerInsteadBtn = document.getElementById('register-instead');
        
        if (continueAsGuestBtn) {
            continueAsGuestBtn.onclick = () => this.hideGuestWarning();
        }
        
        if (registerInsteadBtn) {
            registerInsteadBtn.onclick = () => this.redirectToRegister();
        }
        
        console.log('Static events bound');
    }
    
    initializeDefaults() {
        //Set default difficulty and time on step 3
        setTimeout(() => {
            this.setDefaultSelections();
        }, 500);
    }
    
    setDefaultSelections() {
        //Set medium difficulty as default
        const mediumCard = document.querySelector('.difficulty-card[data-difficulty="medium"]');
        if (mediumCard && !mediumCard.classList.contains('selected')) {
            mediumCard.classList.add('selected');
            this.selectedDifficulty = 'medium';
        }
        
        //Set 10 minutes as default
        const timeCard = document.querySelector('.time-card[data-time="10"]');
        if (timeCard && !timeCard.classList.contains('selected')) {
            timeCard.classList.add('selected');
            this.selectedTime = 10;
        }
        
        this.checkStartButtonState();
    }
    
    async loadCategories() {
        if (this.isLoading) return;
        this.isLoading = true;
        
        try {
            console.log('Loading categories...');
            this.showCategoriesLoading();
            
            const response = await fetch('/api/categories/', {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': window.csrfToken || ''
                }
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: Failed to load categories`);
            }
            
            this.categories = await response.json();
            console.log('Categories loaded:', this.categories.length, 'items');
            
            //Small delay to ensure DOM is ready
            setTimeout(() => {
                this.renderCategories();
                this.isLoading = false;
            }, 100);
            
        } catch (error) {
            console.error('Error loading categories:', error);
            this.showError('Failed to load debate categories. Please refresh the page.');
            this.isLoading = false;
        }
    }
    
    async loadTopics(categoryId) {
        if (this.isLoading) return;
        this.isLoading = true;
        
        try {
            console.log('Loading topics for category:', categoryId);
            this.showTopicsLoading(true);
            
            const response = await fetch(`/api/topics/?category=${categoryId}`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': window.csrfToken || ''
                }
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: Failed to load topics`);
            }
            
            this.topics = await response.json();
            console.log('Topics loaded:', this.topics.length, 'items');
            
            //Longer delay to ensure stable rendering
            setTimeout(() => {
                this.renderTopics();
                this.isLoading = false;
            }, 300);
            
        } catch (error) {
            console.error('Error loading topics:', error);
            this.showError('Failed to load topics. Please try again.');
            this.showTopicsLoading(false);
            this.isLoading = false;
        }
    }
    
    showCategoriesLoading() {
        if (this.categoriesContainer) {
            this.categoriesContainer.innerHTML = `
                <div class="category-loading">
                    <i class="fas fa-spinner fa-spin"></i>
                    <div>Loading categories...</div>
                </div>
            `;
        }
    }
    
    showTopicsLoading(show) {
        if (!this.topicsLoading) return;
        
        if (show) {
            this.topicsLoading.classList.remove('hidden');
            this.topicsLoading.style.display = 'flex';
            this.topicsLoading.style.opacity = '1';
            this.topicsLoading.style.visibility = 'visible';
        } else {
            this.topicsLoading.classList.add('hidden');
            this.topicsLoading.style.opacity = '0';
            setTimeout(() => {
                if (this.topicsLoading.classList.contains('hidden')) {
                    this.topicsLoading.style.display = 'none';
                }
            }, 300);
        }
    }
    
    renderCategories() {
        console.log('Rendering categories...');
        
        if (!this.categories || this.categories.length === 0) {
            this.categoriesContainer.innerHTML = `
                <div class="category-loading">
                    <i class="fas fa-exclamation-triangle"></i>
                    <div>No categories available</div>
                </div>
            `;
            return;
        }
        
        const categoriesHTML = this.categories.map(category => `
            <div class="category-card" data-category-id="${category.id}">
                <div class="category-topics-count">${category.topics_count} topics</div>
                <div class="category-icon">
                    <i class="fas fa-${this.getCategoryIcon(category.name)}"></i>
                </div>
                <h3 class="category-name">${category.name}</h3>
                <p class="category-desc">${category.description}</p>
            </div>
        `).join('');
        
        this.categoriesContainer.innerHTML = categoriesHTML;
        
        //Bind category selection events with proper delegation
        this.bindCategoryEvents();
        
        console.log('Categories rendered successfully');
    }
    
    bindCategoryEvents() {
        //Remove any existing listeners
        this.categoriesContainer.onclick = null;
        
        //Add single event listener with delegation
        this.categoriesContainer.onclick = (e) => {
            e.preventDefault();
            e.stopPropagation();
            
            const categoryCard = e.target.closest('.category-card');
            if (categoryCard && !this.isLoading) {
                console.log('Category selected:', categoryCard.dataset.categoryId);
                this.selectCategory(categoryCard);
            }
        };
    }
    
    renderTopics() {
        console.log('Rendering topics...');
        
        //First hide loading
        this.showTopicsLoading(false);
        
        if (!this.topics || this.topics.length === 0) {
            this.topicsGrid.innerHTML = `
                <div class="no-topics">
                    <i class="fas fa-info-circle"></i>
                    <p>No topics found for this category.</p>
                </div>
            `;
            return;
        }
        
        const topicsHTML = this.topics.map(topic => `
            <div class="topic-card" data-topic-id="${topic.id}" style="justify-content: center; align-items: center; text-align: center;">
                <h3 class="topic-title">${topic.title}</h3>
            </div>
        `).join('');
        
        //Force clear and set new content
        this.topicsGrid.innerHTML = '';
        setTimeout(() => {
            this.topicsGrid.innerHTML = topicsHTML;
            
            //Force visibility
            const topicCards = this.topicsGrid.querySelectorAll('.topic-card');
            topicCards.forEach(card => {
                card.style.opacity = '1';
                card.style.visibility = 'visible';
                card.style.display = 'flex';
            });
            
            this.bindTopicEvents();
            console.log('Topics rendered and visible:', topicCards.length, 'cards');
        }, 100);
    }
    
    bindTopicEvents() {
        //Remove any existing listeners
        this.topicsGrid.onclick = null;
        
        //Add single event listener with delegation
        this.topicsGrid.onclick = (e) => {
            e.preventDefault();
            e.stopPropagation();
            
            const topicCard = e.target.closest('.topic-card');
            if (topicCard && !this.isLoading) {
                console.log('Topic selected:', topicCard.dataset.topicId);
                this.selectTopic(topicCard);
            }
        };
    }
    
    selectCategory(categoryCard) {
        //Remove previous selection
        document.querySelectorAll('.category-card.selected').forEach(card => {
            card.classList.remove('selected');
        });
        
        //Select current category
        categoryCard.classList.add('selected');
        this.selectedCategory = parseInt(categoryCard.dataset.categoryId);
        
        //Enable next button
        this.nextToTopicsBtn.disabled = false;
        this.nextToTopicsBtn.style.opacity = '1';
        
        console.log('Category selected:', this.selectedCategory);
        
        //Load topics for selected category
        this.loadTopics(this.selectedCategory);
    }
    
    selectTopic(topicCard) {
        //Remove previous selection
        document.querySelectorAll('.topic-card.selected').forEach(card => {
            card.classList.remove('selected');
        });
        
        //Select current topic
        topicCard.classList.add('selected');
        this.selectedTopic = parseInt(topicCard.dataset.topicId);
        
        //Enable next button
        this.nextToSettingsBtn.disabled = false;
        this.nextToSettingsBtn.style.opacity = '1';
        
        console.log('Topic selected:', this.selectedTopic);
    }
    
    goToStep(stepNumber) {
        //Validate step transition
        if (stepNumber === 2 && !this.selectedCategory) {
            this.showError('Please select a category first.');
            return;
        }
        
        if (stepNumber === 3 && !this.selectedTopic) {
            this.showError('Please select a topic first.');
            return;
        }
        
        console.log('Going to step:', stepNumber);
        window.scrollTo(0, 0);
        
        //Hide current step
        this.steps[this.currentStep - 1].classList.remove('active');
        
        //Show new step
        this.currentStep = stepNumber;
        this.steps[this.currentStep - 1].classList.add('active');
        
        //Update progress
        this.updateProgress();
        
        //Setup step-specific functionality
        if (stepNumber === 3) {
            setTimeout(() => {
                this.setupStep3();
            }, 200);
        }
    }
    
    setupStep3() {
        console.log('Setting up step 3...');
        
        //Bind difficulty selection
        document.querySelectorAll('.difficulty-card').forEach(card => {
            card.onclick = (e) => {
                e.preventDefault();
                e.stopPropagation();
                this.selectDifficulty(card);
            };
        });
        
        //Bind time selection
        document.querySelectorAll('.time-card').forEach(card => {
            card.onclick = (e) => {
                e.preventDefault();
                e.stopPropagation();
                this.selectTime(card);
            };
        });
        
        //Set defaults
        this.setDefaultSelections();
    }
    
    selectDifficulty(difficultyCard) {
        //Remove previous selection
        document.querySelectorAll('.difficulty-card.selected').forEach(card => {
            card.classList.remove('selected');
        });
        
        //Select current difficulty
        difficultyCard.classList.add('selected');
        this.selectedDifficulty = difficultyCard.dataset.difficulty;
        
        console.log('Difficulty selected:', this.selectedDifficulty);
        this.checkStartButtonState();
    }
    
    selectTime(timeCard) {
        //Remove previous selection
        document.querySelectorAll('.time-card.selected').forEach(card => {
            card.classList.remove('selected');
        });
        
        //Select current time
        timeCard.classList.add('selected');
        this.selectedTime = parseInt(timeCard.dataset.time);
        
        console.log('Time selected:', this.selectedTime);
        this.checkStartButtonState();
    }
    
    checkStartButtonState() {
        if (this.selectedDifficulty && this.selectedTime && this.startDebateBtn) {
            this.startDebateBtn.disabled = false;
            this.startDebateBtn.style.opacity = '1';
            console.log('Start button enabled');
        }
    }
    
    updateProgress() {
        const progressPercent = (this.currentStep / 3) * 100;
        this.progressFill.style.width = `${progressPercent}%`;
        
        this.progressSteps.forEach((step, index) => {
            step.classList.remove('active', 'completed');
            if (index + 1 < this.currentStep) {
                step.classList.add('completed');
            } else if (index + 1 === this.currentStep) {
                step.classList.add('active');
            }
        });
    }
    
    checkGuestStatus() {
        if (window.isAuthenticated === 'false' && this.guestWarningModal) {
            this.showGuestWarning();
        }
    }
    
    showGuestWarning() {
        if (this.guestWarningModal) {
            this.guestWarningModal.classList.remove('hidden');
        }
    }
    
    hideGuestWarning() {
        if (this.guestWarningModal) {
            this.guestWarningModal.classList.add('hidden');
        }
    }
    
    redirectToRegister() {
        window.location.href = '/register/';
    }
    
    async startDebate() {
        if (!this.validateSetup()) {
            return;
        }
        
        try {
            console.log('Starting debate...');
            this.showLoadingModal();
            
            const debateData = {
                topic: this.selectedTopic,
                difficulty_level: this.selectedDifficulty,
                total_time_limit: this.selectedTime
            };
            
            console.log('Creating debate with data:', debateData);
            
            const response = await fetch('/api/debates/create/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': window.csrfToken || ''
                },
                body: JSON.stringify(debateData)
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Failed to create debate');
            }
            
            const debate = await response.json();
            console.log('Debate created successfully:', debate);
            
            //Redirect to debate room
            window.location.href = `/debate/${debate.id}/`;
            
        } catch (error) {
            console.error('Error creating debate:', error);
            this.hideLoadingModal();
            this.showError(error.message || 'Failed to start debate. Please try again.');
        }
    }
    
    validateSetup() {
        if (!this.selectedTopic) {
            this.showError('Please select a debate topic.');
            this.goToStep(2);
            return false;
        }
        
        if (!this.selectedDifficulty) {
            this.showError('Please select a difficulty level.');
            this.goToStep(3);
            return false;
        }
        
        if (!this.selectedTime) {
            this.showError('Please select a time limit.');
            this.goToStep(3);
            return false;
        }
        
        return true;
    }
    
    showLoadingModal() {
        if (this.loadingModal) {
            this.loadingModal.classList.remove('hidden');
        }
    }
    
    hideLoadingModal() {
        if (this.loadingModal) {
            this.loadingModal.classList.add('hidden');
        }
    }
    
    showError(message) {
        console.error('Error:', message);
        
        //Remove any existing toasts
        const existingToasts = document.querySelectorAll('.error-toast');
        existingToasts.forEach(toast => toast.remove());
        
        //Create toast
        const toast = document.createElement('div');
        toast.className = 'error-toast';
        toast.style.cssText = `
            position: fixed;
            top: 2rem;
            right: 2rem;
            background: #dc2626;
            color: white;
            padding: 1rem 1.5rem;
            border-radius: 0.5rem;
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
            max-width: 24rem;
            z-index: 10000;
            font-weight: 500;
            cursor: pointer;
        `;
        toast.textContent = message;
        document.body.appendChild(toast);
        
        //Auto remove after 5 seconds
        setTimeout(() => {
            if (toast.parentNode) {
                toast.style.opacity = '0';
                toast.style.transform = 'translateX(100%)';
                setTimeout(() => toast.remove(), 300);
            }
        }, 5000);
        
        //Click to dismiss
        toast.onclick = () => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateX(100%)';
            setTimeout(() => toast.remove(), 300);
        };
    }
    
    getCategoryIcon(categoryName) {
        const iconMap = {
            'Technology': 'laptop-code',
            'Politics': 'landmark',
            'Education': 'graduation-cap',
            'Environment': 'leaf',
            'Health': 'heartbeat',
            'Healthcare': 'heartbeat',
            'Economics': 'chart-line',
            'Society': 'users',
            'Ethics': 'balance-scale',
            'Science': 'microscope',
            'Sports': 'futbol',
            'Entertainment': 'film'
        };
        
        return iconMap[categoryName] || 'comments';
    }
}

//Initialize when DOM is ready or immediately if already loaded
function initializeDebateSetup() {
    console.log('Initializing debate setup...');
    window.debateSetupInstance = new DebateSetup();
}

//Auto-initialize
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeDebateSetup);
} else {
    initializeDebateSetup();
}

//Export for external use
window.DebateSetup = DebateSetup;