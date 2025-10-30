document.addEventListener('DOMContentLoaded', () => {

    // --- Claves de LocalStorage ---
    const USERS_KEY = 'goInvestUsers';
    const SESSION_KEY = 'goInvestSession';
    const IDEAS_KEY = 'goInvestIdeas';

    // --- Elementos comunes ---
    const messageEl = document.getElementById('message');
    const welcomeUserEl = document.getElementById('welcome-user');
    const logoutBtn = document.getElementById('logout-btn');

    // --- Funciones de Ayuda (Storage) ---

    // Obtener todos los usuarios
    function getUsers() {
        return JSON.parse(localStorage.getItem(USERS_KEY)) || [];
    }

    // Guardar usuarios
    function saveUsers(users) {
        localStorage.setItem(USERS_KEY, JSON.stringify(users));
    }

    // Obtener todas las ideas
    function getIdeas() {
        return JSON.parse(localStorage.getItem(IDEAS_KEY)) || [];
    }

    // Guardar ideas
    function saveIdeas(ideas) {
        localStorage.setItem(IDEAS_KEY, JSON.stringify(ideas));
    }

    // Iniciar sesión
    function startSession(user) {
        localStorage.setItem(SESSION_KEY, JSON.stringify(user));
    }

    // Obtener sesión actual
    function getCurrentSession() {
        return JSON.parse(localStorage.getItem(SESSION_KEY));
    }

    // Cerrar sesión
    function endSession() {
        localStorage.removeItem(SESSION_KEY);
    }

    // --- Lógica de Autenticación (Login/Register) ---

    const loginForm = document.getElementById('login-form');
    const registerForm = document.getElementById('register-form');

    if (registerForm) {
        registerForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;
            const role = document.querySelector('input[name="role"]:checked').value;

            const users = getUsers();
            
            // Comprobar si el usuario ya existe
            if (users.find(user => user.username === username)) {
                messageEl.textContent = 'Error: Username already exists.';
                messageEl.className = 'message error';
                return;
            }

            // *** ADVERTENCIA DE SEGURIDAD ***
            // Nunca guardes contraseñas en texto plano en una app real.
            // Esto es solo para un prototipo local.
            const newUser = { id: Date.now().toString(), username, password, role };
            users.push(newUser);
            saveUsers(users);

            messageEl.textContent = 'Registration successful! Please login.';
            messageEl.className = 'message success';
            registerForm.reset();
            // Redirigir al login después de 2 segundos
            setTimeout(() => {
                window.location.href = 'index.html';
            }, 2000);
        });
    }

    if (loginForm) {
        loginForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;

            const users = getUsers();
            const user = users.find(u => u.username === username && u.password === password);

            if (user) {
                startSession(user);
                // Redirigir según el rol
                if (user.role === 'student') {
                    window.location.href = 'student.html';
                } else {
                    window.location.href = 'investor.html';
                }
            } else {
                messageEl.textContent = 'Error: Invalid username or password.';
                messageEl.className = 'message error';
            }
        });
    }

    // --- Lógica de Páginas Protegidas (Dashboards) ---

    if (welcomeUserEl) {
        const session = getCurrentSession();
        
        // 1. Proteger la ruta
        if (!session) {
            window.location.href = 'index.html'; // No hay sesión, fuera
            return;
        }

        // 2. Mostrar bienvenida
        welcomeUserEl.textContent = `Welcome, ${session.username}`;

        // 3. Lógica de Logout
        logoutBtn.addEventListener('click', () => {
            endSession();
            window.location.href = 'index.html';
        });

        // 4. Proteger por Rol
        const currentPage = window.location.pathname.split('/').pop();
        if (currentPage === 'student.html' && session.role !== 'student') {
            window.location.href = 'index.html'; // Inversor en pág de estudiante
        }
        if (currentPage === 'investor.html' && session.role !== 'investor') {
            window.location.href = 'index.html'; // Estudiante en pág de inversor
        }
    }

    // --- Lógica de la App: Ideas ---

    const ideaForm = document.getElementById('idea-form');
    const ideasContainer = document.getElementById('ideas-container');

    // --- Lógica del Estudiante (Publicar Idea) ---
    if (ideaForm) {
        ideaForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const ideaText = document.getElementById('idea-text').value;
            const session = getCurrentSession();

            if (ideaText.trim() === '') {
                alert('Please describe your idea.');
                return;
            }

            const ideas = getIdeas();
            const newIdea = {
                id: Date.now().toString(),
                author: session.username, // Añadimos quién la publicó
                text: ideaText,
                likes: 0
            };

            ideas.unshift(newIdea);
            saveIdeas(ideas);

            alert('Idea posted successfully! 🎉');
            ideaForm.reset();
        });
    }

    // --- Lógica del Inversor (Ver y dar Like) ---
    if (ideasContainer) {
        
        function displayIdeas() {
            ideasContainer.innerHTML = ''; 
            const ideas = getIdeas();

            if (ideas.length === 0) {
                ideasContainer.innerHTML = '<p>No ideas have been posted yet.</p>';
                return;
            }

            ideas.forEach(idea => {
                const card = document.createElement('div');
                card.className = 'card';
                
                card.innerHTML = `
                    <p>${idea.text}</p>
                    <div class="card-footer">
                        <span class="card-author">Posted by: ${idea.author}</span>
                        <button class="like-btn" data-id="${idea.id}">
                            👍 Like (${idea.likes})
                        </button>
                    </div>
                `;
                ideasContainer.appendChild(card);
            });

            addLikeButtonEvents();
        }

        function addLikeButtonEvents() {
            document.querySelectorAll('.like-btn').forEach(button => {
                button.addEventListener('click', () => {
                    const ideaId = button.dataset.id;
                    addLike(ideaId);
                });
            });
        }

        function addLike(id) {
            const ideas = getIdeas();
            const ideaToLike = ideas.find(idea => idea.id === id);

            if (ideaToLike) {
                ideaToLike.likes++;
                saveIdeas(ideas);
                displayIdeas(); // Recargar ideas para mostrar el nuevo conteo
            }
        }

        displayIdeas(); // Carga inicial
    }
    // --- COMMENTS LOGIC ---
const commentInput = document.getElementById("comment-input");
const publishBtn = document.getElementById("publish-btn");
const clearBtn = document.getElementById("clear-btn");
const errorMsg = document.getElementById("error-message");
const commentsList = document.getElementById("comments-list");

// Simulate "logged in investor"
const currentUser = {
  name: "Investor John",
  role: "investor",
};

// Load previous comments from localStorage
let comments = JSON.parse(localStorage.getItem("comments")) || [];

// Function to display comments
function renderComments() {
  commentsList.innerHTML = "";
  comments.forEach((c) => {
    const li = document.createElement("li");
    li.style.border = "1px solid #ccc";
    li.style.padding = "8px";
    li.style.marginBottom = "5px";
    li.innerHTML = `<strong>${c.author}</strong> 
      <span style="color:gray; font-size:12px;">(${c.time})</span><br>${c.text}`;
    commentsList.appendChild(li);
  });
}

// Save + render
function saveComments() {
  localStorage.setItem("comments", JSON.stringify(comments));
  renderComments();
}

// Publish button click
publishBtn.addEventListener("click", () => {
  const text = commentInput.value.trim();

  if (text.length === 0) {
    errorMsg.textContent = "Comment cannot be empty.";
    return;
  }
  if (text.length > 1000) {
    errorMsg.textContent = "Comment cannot exceed 1000 characters.";
    return;
  }

  errorMsg.textContent = "";

  const newComment = {
    author: currentUser.name,
    text,
    time: new Date().toLocaleString(),
  };

  // Add to top
  comments.unshift(newComment);
  saveComments();

  commentInput.value = "";
});

// Clear button click
clearBtn.addEventListener("click", () => {
  commentInput.value = "";
  errorMsg.textContent = "";
});

// Initial render
renderComments();

});