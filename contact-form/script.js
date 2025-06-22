

const API_BASE_URL = 'http://localhost:7705';
let currentUser = null;

// Page navigation functions
function showPage(pageId) {
    document.querySelectorAll('.page').forEach(page => page.classList.remove('active'));
    document.getElementById(pageId).classList.add('active');
}

function showLogin() { showPage('loginPage'); }
function showRegister() { showPage('registerPage'); }
function showDashboard() { 
    showPage('dashboardPage');
    loadTopics();
}

function showAddTopic() { showPage('addTopicPage'); }
// API helper function
async function apiCall(endpoint, method = 'GET', data = null) {
    const options = {
        method,
        headers: {
            'Content-Type': 'application/json',
        }
    };
    
    if (data) {
        options.body = JSON.stringify(data);
    }
    
    const response = await fetch(`${API_BASE_URL}${endpoint}`, options);
    return response;
}

// Authentication functions
document.getElementById('registerForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const email = document.getElementById('registerEmail').value;
    const password = document.getElementById('registerPassword').value;
    
    try {
        const response = await apiCall('/register', 'POST', { email, password });
        const result = await response.json();
        
        if (response.ok) {
            document.getElementById('registerSuccess').style.display = 'block';
            document.getElementById('registerSuccess').textContent = 'Registration successful! You can now login.';
            document.getElementById('registerError').style.display = 'none';
            document.getElementById('registerForm').reset();
        } else {
            document.getElementById('registerError').style.display = 'block';
            document.getElementById('registerError').textContent = result.detail || 'Registration failed';
            document.getElementById('registerSuccess').style.display = 'none';
        }
    } catch (error) {
        document.getElementById('registerError').style.display = 'block';
        document.getElementById('registerError').textContent = 'Network error. Please try again.';
    }
});

document.getElementById('loginForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const email = document.getElementById('loginEmail').value;
    const password = document.getElementById('loginPassword').value;
    
    try {
        const response = await apiCall('/login', 'POST', { email, password });
        const result = await response.json();
        
        if (response.ok) {
            currentUser = email;
            document.getElementById('userEmail').textContent = email;
            showDashboard();
            document.getElementById('loginError').style.display = 'none';
        } else {
            document.getElementById('loginError').style.display = 'block';
            document.getElementById('loginError').textContent = result.detail || 'Login failed';
        }
    } catch (error) {
        document.getElementById('loginError').style.display = 'block';
        document.getElementById('loginError').textContent = 'Network error. Please try again.';
    }
});

function logout() {
    currentUser = null;
    showLogin();
    document.getElementById('loginForm').reset();
    document.getElementById('topicsList').innerHTML = '';
}

// Topic management functions
async function loadTopics() {
    if (!currentUser) return;
    
    document.getElementById('loading').style.display = 'block';
    
    try {
        const response = await apiCall(`/topics/${currentUser}`);
        const topics = await response.json();
        
        const topicsList = document.getElementById('topicsList');
        
        if (topics.length === 0) {
            topicsList.innerHTML = '<div class="no-topics">No topics found. Add your first topic!</div>';
        } else {
            topicsList.innerHTML = topics.map((topic, index) => `
                <div class="topic-item">
                    <div class="topic-content">${topic}</div>
                    <div class="topic-actions">
                        <button class="btn btn-danger" onclick="deleteTopic('${topic}')">Delete</button>
                    </div>
                </div>
            `).join('');
        }
    } catch (error) {
        document.getElementById('topicsList').innerHTML = '<div class="error">Failed to load topics</div>';
    } finally {
        document.getElementById('loading').style.display = 'none';
    }
}

document.getElementById('addTopicForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const topic = document.getElementById('newTopic').value;
    
    try {
        const response = await apiCall('/topics', 'POST', { 
            email: currentUser, 
            topic 
        });
        const result = await response.json();
        
        if (response.ok) {
            document.getElementById('addTopicSuccess').style.display = 'block';
            document.getElementById('addTopicSuccess').textContent = 'Topic added successfully!';
            document.getElementById('addTopicError').style.display = 'none';
            document.getElementById('addTopicForm').reset();
            
            setTimeout(() => {
                showDashboard();
                document.getElementById('addTopicSuccess').style.display = 'none';
            }, 1500);
        } else {
            document.getElementById('addTopicError').style.display = 'block';
            document.getElementById('addTopicError').textContent = result.detail || 'Failed to add topic';
            document.getElementById('addTopicSuccess').style.display = 'none';
        }
    } catch (error) {
        document.getElementById('addTopicError').style.display = 'block';
        document.getElementById('addTopicError').textContent = 'Network error. Please try again.';
    }
});

async function deleteTopic(topic) {
    if (!confirm('Are you sure you want to delete this topic?')) return;
    
    try {
        const response = await apiCall('/topics', 'DELETE', { 
            email: currentUser, 
            topic 
        });
        
        if (response.ok) {
            loadTopics(); // Reload topics list
        } else {
            alert('Failed to delete topic');
        }
    } catch (error) {
        alert('Network error. Please try again.');
    }
};
// Initialize app
showLogin();