
const API_URL = "http://127.0.0.1:5000";

function openLogin() {
  document.getElementById("loginModal").style.display = "flex";
}
function closeLogin() {
  document.getElementById("loginModal").style.display = "none";
}


function openRegister() {
  document.getElementById("registerModal").style.display = "flex";
}
function closeRegister() {
  document.getElementById("registerModal").style.display = "none";
}
function openResumeModal(){
   document.getElementById("resumeModal").style.display="flex"; 
  }
function closeResumeModal(){ 
  document.getElementById("resumeModal").style.display="none"; 
}

function openProfilePanel() {
  document.getElementById('profileOverlay').style.display = 'block';
  document.getElementById('profilePanel').classList.add('show');
}

function closeProfilePanel() {
  document.getElementById('profilePanel').classList.remove('show');
  setTimeout(() => {
    document.getElementById('profileOverlay').style.display = 'none';
  }, 300);
}


async function fetchWithAuth(url, options = {}) {
  const token = localStorage.getItem("jwt");
  if (!options.headers) options.headers = {};
  if (token) {
    options.headers["Authorization"] = "Bearer " + token;
  }

  const res = await fetch(API_URL + url, options);

  if (res.status === 401) {
    alert("Session expired. Please login again.");
    window.location.href = "/";
    return;
  }

  return res;
}



async function apiLogin(email, password) {
  const res = await fetch(API_URL + "/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password })
  });
  const data = await res.json();
  if (data.token) {
    localStorage.setItem("jwt", data.token);
    localStorage.setItem("role", data.role);
  }
  return data;
}

async function apiRegister(username, email, password) {
  const res = await fetch(API_URL + "/register", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, email, password })
  });
  return res.json();
}

async function apiGetJobs() {
  try {
    const res = await fetchWithAuth("/jobs", { method: "GET" });
    return res.json();
  } catch (err) {
    console.error(err);
    return [];
  }
}

async function apiApplyJob(jobId, coverLetter) {
  try {
    const res = await fetchWithAuth(`/apply/${jobId}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ cover_letter: coverLetter })
    });
    return res.json();
  } catch (err) {
    return { error: "Please login" };
  }
}


// Login - Register
document.getElementById('loginForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  const email = document.getElementById('email').value;
  const password = document.getElementById('password').value;
  const msg = document.getElementById('msg');

  try {
    const data = await apiLogin(email, password);
    if (data.token) {
      msg.style.color = "green";
      msg.innerText = "Login success! Redirecting...";

      setTimeout(() => {
        if (data.role === "admin") {
          location.href = "/admin_dashboard";
        } else {
          location.href = "/jobs_page";
        }
      }, 800);
    } else {
      msg.style.color = "red";
      msg.innerText = data.error || "Login failed";
      if (data.redirect === "register") {
    setTimeout(() => {
      closeLogin();
      openRegister();
    }, 1000);
  }
    }
  } catch (err) {
    msg.style.color = "red";
    msg.innerText = "Server error";
  }
});


const registerForm = document.getElementById('registerForm');
if (registerForm) {
  registerForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const username = document.getElementById('username').value.trim();
    const email = document.getElementById('emailReg').value.trim();
    const password = document.getElementById('passwordReg').value;
    const msg = document.getElementById('msgModal');

    const res = await apiRegister(username, email, password);

    if (res && res.message === "registered") {
      msg.style.color = "green";
      msg.innerText = "Registered successfully! Please login.";
      setTimeout(() => { 
        closeRegister(); 
        openLogin(); 
      }, 800);
    } else {
      msg.style.color = "red";
      msg.innerText = res.error || "Registration failed";
    }
  });
}


function searchJobs() {
    const role = document.getElementById("searchRole").value;
    const location = document.getElementById("searchLocation").value;
    window.location.href = `/jobs_page?role=${encodeURIComponent(role)}&location=${encodeURIComponent(location)}`;
}


    const resumeForm = document.getElementById("resumeForm");
    resumeForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const file = document.getElementById("resumeFile").files[0];

      if (!file) return alert("Please select a file.");
      if (file.size > 1024 * 1024) return alert("File too large. Must be < 1MB.");

      const formData = new FormData();
      formData.append("resume", file);

      const res = await fetchWithAuth("/upload_resume", {
        method: "POST",
        body: formData
      });

      const data = await res.json();
      alert(data.message || data.error);
      if (res.ok) closeResumeModal();
    });

async function checkSession() {
  const res = await fetch(API_URL + "/session-info");
  const data = await res.json();

  if (data.user_id) {
    document.getElementById("uploadBtn").style.display = "inline-block"; 
  } else {
    document.getElementById("uploadBtn").style.display = "none";
  }
  }
checkSession();



