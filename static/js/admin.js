const jobsGrid = document.getElementById("jobsGrid");
const jobModal = document.getElementById("jobModal");
const jobForm = document.getElementById("jobForm");
const modalTitle = document.getElementById("modalTitle");
const closeBtn = document.querySelector(".close");
const addJobBtn = document.getElementById("addJobBtn");
const jobIdInput = document.getElementById("jobId");

addJobBtn.onclick = () => {
  jobForm.reset();
  jobIdInput.value = "";
  modalTitle.textContent = "Add Job";
  jobModal.style.display = "flex";
};


closeBtn.onclick = () => {
  jobModal.style.display = "none";
};


window.onclick = (e) => {
  if (e.target === jobModal) {
    jobModal.style.display = "none";
  }
};


async function loadJobs() {
  const res = await fetch("/admin/jobs_json");
  const jobs = await res.json();

  jobsGrid.innerHTML = jobs.map(job => `
    <div class="card">
      <h3>${job.title}</h3>
      <p><b>Company:</b> ${job.company}</p>
      <p><b>Location:</b> ${job.location}</p>
      <p><b>Salary:</b> ${job.salary}</p>
      <p><b>Status:</b> ${job.status}</p>
      <p><b>Description:</b> ${job.description}</p>
      <p><b>Experience:</b> ${job.experience}</p>
      <div class="actions">
        <button onclick="editJob(${job.id})">Edit</button>
        <button onclick="deleteJob(${job.id})">Delete</button>
      </div>
    </div>
  `).join("");
}

// Submit form (Add/Edit job)
jobForm.onsubmit = async (e) => {
  e.preventDefault();
  const jobId = jobIdInput.value;
  const method = jobId ? "PUT" : "POST";
  const url = jobId ? `/admin/edit_job/${jobId}` : "/admin/add_job";

  const jobData = {
    company: document.getElementById("company").value,
    title: document.getElementById("jobTitle").value,
    description: document.getElementById("jobDescription").value,
    salary: document.getElementById("jobSalary").value,
    location: document.getElementById("jobLocation").value,
    experience: document.getElementById("jobExperience").value,
    status: document.getElementById("jobStatus").value
  };

  await fetch(url, {
    method,
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(jobData)
  });

  jobModal.style.display = "none";
  loadJobs();
};

// Edit job
async function editJob(id) {
  const res = await fetch("/admin/jobs_json");
  const jobs = await res.json();
  const job = jobs.find(j => j.id === id);

  if (!job) return;

  jobIdInput.value = job.id;
  document.getElementById("company").value = job.company;
  document.getElementById("jobTitle").value = job.title;
  document.getElementById("jobDescription").value = job.description;
  document.getElementById("jobSalary").value = job.salary;
  document.getElementById("jobLocation").value = job.location;
  document.getElementById("jobExperience").value = job.experience;
  document.getElementById("jobStatus").value = job.status;

  modalTitle.textContent = "Edit Job";
  jobModal.style.display = "flex";
}

//Delete job
async function deleteJob(id) {
  if (!confirm("Delete this job?")) return;
  await fetch(`/admin/delete_job/${id}`, { method: "DELETE" });
  loadJobs();
}

window.editJob = editJob;
window.deleteJob = deleteJob;

loadJobs();