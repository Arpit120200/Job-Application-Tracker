const addBtn = document.getElementById("add-btn");
const formStatus = document.getElementById("form-status");
const jobsList = document.getElementById("jobs-list");
const modalOverlay = document.getElementById("modal-overlay");
const closeModal = document.getElementById("close-modal");
const coverLetterContent = document.getElementById("cover-letter-content");
const copyBtn = document.getElementById("copy-btn");
const generateBtn = document.getElementById("generate-btn");
const jobDescriptionInput = document.getElementById("job-description");

// Track which job the modal is currently open for
let activeJobId = null;

document.addEventListener("DOMContentLoaded", fetchJobs);

// ---- REFERRAL TOGGLE ----
function toggleReferral() {
    const checked = document.getElementById("referred").checked;
    const referralGroup = document.getElementById("referral-name-group");
    referralGroup.style.display = checked ? "block" : "none";
}

// ---- FETCH ALL JOBS ----
async function fetchJobs() {
    try {
        const response = await fetch("/jobs");
        const jobs = await response.json();

        if (jobs.length === 0) {
            jobsList.innerHTML = '<p class="empty-state">No applications yet. Add one above.</p>';
            return;
        }

        jobsList.innerHTML = "";
        jobs.forEach(job => {
            jobsList.appendChild(createJobCard(job));
        });

    } catch (error) {
        jobsList.innerHTML = '<p class="empty-state">Could not load jobs. Is your server running?</p>';
    }
}

// ---- CREATE A JOB CARD ----
function createJobCard(job) {
    const card = document.createElement("div");
    card.className = "job-card";
    card.id = `job-${job.id}`;

    // Build optional fields conditionally
    const referralHTML = job.referred
        ? `<p class="referral">Referred by ${job.referral_name || "someone"}</p>`
        : "";

    const linkHTML = job.job_link
        ? `<p class="job-link"><a href="${job.job_link}" target="_blank">View Job Posting</a></p>`
        : "";

    card.innerHTML = `
        <div class="job-info">
            <h3>${job.role}</h3>
            <p class="company">${job.company}</p>
            <p class="date">Applied: ${job.date_applied}</p>
            ${referralHTML}
            ${linkHTML}
        </div>
        <div class="job-actions">
            <span class="status-badge status-${job.status.replace(" ", "-")}">${job.status}</span>
            <select class="status-select" onchange="updateStatus(${job.id}, this.value)">
                <option value="Applied"     ${job.status === "Applied"     ? "selected" : ""}>Applied</option>
                <option value="Interview"   ${job.status === "Interview"   ? "selected" : ""}>Interview</option>
                <option value="Final Round" ${job.status === "Final Round" ? "selected" : ""}>Final Round</option>
                <option value="Offer"       ${job.status === "Offer"       ? "selected" : ""}>Offer</option>
                <option value="Rejected"    ${job.status === "Rejected"    ? "selected" : ""}>Rejected</option>
            </select>
            <div class="action-buttons">
                <button class="btn-small btn-ai" onclick="openCoverLetterModal(${job.id})">Generate Cover Letter</button>
                <button class="btn-small btn-danger" onclick="deleteJob(${job.id})">Delete</button>
            </div>
        </div>
    `;

    return card;
}

// ---- ADD A JOB ----
addBtn.addEventListener("click", async function() {
    const company = document.getElementById("company").value.trim();
    const role = document.getElementById("role").value.trim();
    const status = document.getElementById("status").value;
    const date_applied = document.getElementById("date_applied").value;
    const job_link = document.getElementById("job_link").value.trim();
    const referred = document.getElementById("referred").checked;
    const referral_name = document.getElementById("referral_name").value.trim();

    if (!company || !role || !date_applied) {
        formStatus.textContent = "Please fill in company, role and date.";
        return;
    }

    addBtn.disabled = true;
    formStatus.textContent = "Adding...";

    try {
        const response = await fetch("/jobs", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                company,
                role,
                status,
                date_applied,
                job_link,
                referred,
                referral_name
            })
        });

        const data = await response.json();

        if (data.error) {
            formStatus.textContent = "Error: " + data.error;
        } else {
            // Clear the form
            document.getElementById("company").value = "";
            document.getElementById("role").value = "";
            document.getElementById("date_applied").value = "";
            document.getElementById("job_link").value = "";
            document.getElementById("referred").checked = false;
            document.getElementById("referral_name").value = "";
            document.getElementById("referral-name-group").style.display = "none";
            formStatus.textContent = "Application added.";
            fetchJobs();
        }

    } catch (error) {
        formStatus.textContent = "Connection error.";
    }

    addBtn.disabled = false;
});

// ---- DELETE A JOB ----
async function deleteJob(jobId) {
    try {
        await fetch(`/jobs/${jobId}`, { method: "DELETE" });
        const card = document.getElementById(`job-${jobId}`);
        if (card) card.remove();

        if (jobsList.children.length === 0) {
            jobsList.innerHTML = '<p class="empty-state">No applications yet. Add one above.</p>';
        }
    } catch (error) {
        alert("Could not delete. Is your server running?");
    }
}

// ---- UPDATE STATUS ----
async function updateStatus(jobId, newStatus) {
    try {
        await fetch(`/jobs/${jobId}`, {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ status: newStatus })
        });
        fetchJobs();
    } catch (error) {
        alert("Could not update status.");
    }
}

// ---- OPEN COVER LETTER MODAL ----
function openCoverLetterModal(jobId) {
    activeJobId = jobId;

    // Reset the modal state
    jobDescriptionInput.value = "";
    coverLetterContent.textContent = "";
    coverLetterContent.classList.remove("visible");
    copyBtn.classList.remove("visible");
    generateBtn.textContent = "Generate Cover Letter";
    generateBtn.disabled = false;

    modalOverlay.classList.remove("hidden");
}

// ---- GENERATE COVER LETTER ----
generateBtn.addEventListener("click", async function() {
    if (!activeJobId) return;

    const jobDescription = jobDescriptionInput.value.trim();

    generateBtn.disabled = true;
    generateBtn.textContent = "Generating...";
    coverLetterContent.classList.remove("visible");
    copyBtn.classList.remove("visible");

    try {
        const response = await fetch(`/jobs/${activeJobId}/cover-letter`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ job_description: jobDescription })
        });

        const data = await response.json();

        if (data.error) {
            coverLetterContent.textContent = "Error: " + data.error;
        } else {
            coverLetterContent.textContent = data.cover_letter;
            copyBtn.classList.add("visible");
        }

        coverLetterContent.classList.add("visible");

    } catch (error) {
        coverLetterContent.textContent = "Connection error.";
        coverLetterContent.classList.add("visible");
    }

    generateBtn.textContent = "Regenerate";
    generateBtn.disabled = false;
});

// ---- MODAL CONTROLS ----
closeModal.addEventListener("click", function() {
    modalOverlay.classList.add("hidden");
    activeJobId = null;
});

modalOverlay.addEventListener("click", function(e) {
    if (e.target === modalOverlay) {
        modalOverlay.classList.add("hidden");
        activeJobId = null;
    }
});

// ---- COPY TO CLIPBOARD ----
copyBtn.addEventListener("click", function() {
    navigator.clipboard.writeText(coverLetterContent.textContent)
        .then(() => {
            copyBtn.textContent = "Copied!";
            setTimeout(() => {
                copyBtn.textContent = "Copy to Clipboard";
            }, 2000);
        });
});