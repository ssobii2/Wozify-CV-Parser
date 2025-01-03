// Global variables
let formData = new FormData();

// Utility functions
function showLoading() {
  document.querySelector('.spinner-overlay').classList.add('show');
  const submitButton = document.querySelector('button[type="submit"]');
  submitButton.disabled = true;
}

function hideLoading() {
  document.querySelector('.spinner-overlay').classList.remove('show');
  const submitButton = document.querySelector('button[type="submit"]');
  submitButton.disabled = false;
}

async function checkJsonExists(filename) {
  try {
    const response = await fetch(`/check_json/${encodeURIComponent(filename)}`);
    if (response.status === 404) {
      return { exists: false };
    }
    if (!response.ok) {
      console.error('Error checking JSON:', await response.text());
      return { exists: false };
    }
    const data = await response.json();
    return { exists: true, data };
  } catch (error) {
    console.error('Error checking JSON:', error);
    return { exists: false };
  }
}

function getFormData() {
  const detectedLanguage = document.querySelector('input[name="detected-language"]')?.value || 'en';
  
  return {
    language: detectedLanguage,
    profile: {
      cv_id: document.getElementById("cv-id").value || "",
      name: document.getElementById("name").value || "",
      email: document.getElementById("email").value || "",
      phone: document.getElementById("phone").value || "",
      location: document.getElementById("location").value || "",
      url: document.getElementById("url").value || "",
      summary: document.getElementById("summary").value || "",
    },
    experience: Array.from(document.querySelectorAll(".experience-entry")).map(
      (entry) => ({
        company: entry.querySelector('input[name="company[]"]').value || "",
        job_title: entry.querySelector('input[name="job-title[]"]').value || "",
        date: entry.querySelector('input[name="experience-date[]"]').value || "",
        descriptions: entry
          .querySelector('textarea[name="experience-descriptions[]"]')
          .value.split("\n")
          .filter((desc) => desc.trim() !== "")
          .map((desc) => desc.trim()),
      })
    ),
    education: Array.from(document.querySelectorAll(".education-entry")).map(
      (entry) => ({
        school: entry.querySelector('input[name="school[]"]').value || "",
        degree: entry.querySelector('input[name="degree[]"]').value || "",
        gpa: entry.querySelector('input[name="gpa[]"]').value || "",
        date: entry.querySelector('input[name="education-date[]"]').value || "",
        descriptions: entry
          .querySelector('textarea[name="education-descriptions[]"]')
          .value.split("\n")
          .filter((desc) => desc.trim() !== "")
          .map((desc) => desc.trim()),
      })
    ),
    skills: document
      .getElementById("skills")
      .value.split(",")
      .map((skill) => skill.trim())
      .filter((skill) => skill !== ""),
    languages: Array.from(document.querySelectorAll(".language-entry")).map(
      (entry) => ({
        language: entry.querySelector('input[name="language[]"]').value || "",
        proficiency: entry.querySelector('input[name="proficiency[]"]').value || "",
      })
    ),
    current_position: document.getElementById("current-position").value || "",
  };
}

// Form submission and data handling
async function saveFormData() {
  const uploadedFile = localStorage.getItem("uploadedFile");
  
  if (!uploadedFile) {
    alert('Please upload a CV file first');
    return;
  }

  try {
    const formData = getFormData();
    const cvId = document.getElementById("cv-id").value || currentCVId;
    const detectedLanguage = document.querySelector('input[name="detected-language"]')?.value || 'en';
    
    if (!formData.profile) {
      formData.profile = {};
    }
    formData.profile.cv_id = cvId;
    formData.language = detectedLanguage;

    const response = await fetch('/save_form', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        filename: uploadedFile,
        formData: formData
      })
    });

    if (!response.ok) {
      throw new Error('Failed to save form data');
    }

    const result = await response.json();
  } catch (error) {
    console.error('Error saving form data:', error);
    alert('Error saving form data');
  }
}

// Entry management functions
function addEducationEntry() {
  const educationContainer = document.getElementById("education-container");
  const newEducationEntry = document.createElement("div");
  newEducationEntry.classList.add("education-entry");
  newEducationEntry.innerHTML = `
        <div class="form-row">
            <label for="school">School:</label>
            <input type="text" name="school[]">
        </div>
        <div class="form-row">
            <label for="degree">Degree:</label>
            <input type="text" name="degree[]">
        </div>
        <div class="form-row">
            <label for="gpa">GPA:</label>
            <input type="text" name="gpa[]">
        </div>
        <div class="form-row">
            <label for="education-date">Date:</label>
            <input type="text" name="education-date[]">
        </div>
        <div class="form-row">
            <label for="education-descriptions">Descriptions:</label>
            <textarea name="education-descriptions[]" placeholder="Your description here..."></textarea>
        </div>
        <button type="button" class="remove-education">Remove</button>
    `;
  newEducationEntry.querySelectorAll("input, textarea").forEach((input) => {
    input.addEventListener("input", updatePreview);
  });
  educationContainer.appendChild(newEducationEntry);
  localStorage.setItem("formData", JSON.stringify(getFormData()));
}

function addExperienceEntry() {
  const experienceContainer = document.getElementById("experience-container");
  const newExperienceEntry = document.createElement("div");
  newExperienceEntry.classList.add("experience-entry");
  newExperienceEntry.innerHTML = `
        <div class="form-row">
            <label for="company">Company:</label>
            <input type="text" name="company[]">
        </div>
        <div class="form-row">
            <label for="job-title">Job Title:</label>
            <input type="text" name="job-title[]">
        </div>
        <div class="form-row">
            <label for="experience-date">Date:</label>
            <input type="text" name="experience-date[]">
        </div>
        <div class="form-row">
            <label for="experience-descriptions">Descriptions:</label>
            <textarea name="experience-descriptions[]" placeholder="Your description here..."></textarea>
        </div>
        <button type="button" class="remove-experience">Remove</button>
    `;
  newExperienceEntry.querySelectorAll("input, textarea").forEach((input) => {
    input.addEventListener("input", updatePreview);
  });
  experienceContainer.appendChild(newExperienceEntry);
  localStorage.setItem("formData", JSON.stringify(getFormData()));
}

function addLanguageEntry() {
  const languagesContainer = document.getElementById("languages-container");
  const newLanguageEntry = document.createElement("div");
  newLanguageEntry.classList.add("language-entry");
  newLanguageEntry.innerHTML = `
        <div class="form-row">
            <label for="language">Language:</label>
            <input type="text" name="language[]">
        </div>
        <div class="form-row">
            <label for="proficiency">Proficiency:</label>
            <input type="text" name="proficiency[]">
        </div>
        <button type="button" class="remove-language">Remove</button>
    `;
  newLanguageEntry.querySelectorAll("input, textarea").forEach((input) => {
    input.addEventListener("input", updatePreview);
  });
  languagesContainer.appendChild(newLanguageEntry);
  localStorage.setItem("formData", JSON.stringify(formData));
}

// Event listeners
document.getElementById("upload-form").addEventListener("submit", async function (e) {
  e.preventDefault();
  const fileInput = document.getElementById("file-input");
  const file = fileInput.files[0];
  if (!file) {
    alert("Please select a file!");
    return;
  }

  showLoading();

  const jsonFilename = file.name.replace(/\.[^/.]+$/, "") + ".json";
  const jsonCheck = await checkJsonExists(jsonFilename);
  
  if (jsonCheck.exists && jsonCheck.data) {
    try {
      if (typeof window.populateFields === 'function') {
        window.populateFields(jsonCheck.data);
        window.updatePreview();
        hideLoading();
        return;
      } else {
        console.error('populateFields function not found');
      }
    } catch (error) {
      console.error('Error loading JSON data:', error);
    }
  }

  formData = new FormData();
  formData.append("file", file);

  const educationEntries = document.querySelectorAll(".education-entry");
  educationEntries.forEach((entry) => {
    formData.append("school[]", entry.querySelector('input[name="school[]"]').value);
    formData.append("degree[]", entry.querySelector('input[name="degree[]"]').value);
    formData.append("gpa[]", entry.querySelector('input[name="gpa[]"]').value);
    formData.append("education-date[]", entry.querySelector('input[name="education-date[]"]').value);
    formData.append("education-descriptions[]", entry.querySelector('textarea[name="education-descriptions[]"]').value);
  });

  const experienceEntries = document.querySelectorAll(".experience-entry");
  experienceEntries.forEach((entry) => {
    formData.append("company[]", entry.querySelector('input[name="company[]"]').value);
    formData.append("job-title[]", entry.querySelector('input[name="job-title[]"]').value);
    formData.append("experience-date[]", entry.querySelector('input[name="experience-date[]"]').value);
    formData.append("experience-descriptions[]", entry.querySelector('textarea[name="experience-descriptions[]"]').value);
  });

  const languageEntries = document.querySelectorAll(".language-entry");
  languageEntries.forEach((entry) => {
    formData.append("language[]", entry.querySelector('input[name="language[]"]').value);
    formData.append("proficiency[]", entry.querySelector('input[name="proficiency[]"]').value);
  });

  try {
    const response = await fetch('/process', {
      method: 'POST',
      body: formData
    });
    
    if (!response.ok) {
      throw new Error('Failed to process CV');
    }
    
    const result = await response.json();
    
    if (result.data && typeof window.populateFields === 'function') {
      window.populateFields(result.data);
      window.updatePreview();
    }
  } catch (error) {
    console.error('Error processing CV:', error);
    alert('An error occurred while processing the CV. Please try again.');
  } finally {
    hideLoading();
  }
});

// Add entry button listeners
document.getElementById("add-education").addEventListener("click", addEducationEntry);
document.getElementById("add-experience").addEventListener("click", addExperienceEntry);
document.getElementById("add-language").addEventListener("click", addLanguageEntry);

// Remove entry listeners
document.getElementById("education-container").addEventListener("click", function (e) {
  if (e.target.classList.contains("remove-education")) {
    e.target.closest(".education-entry").remove();
    updatePreview();
    localStorage.setItem("formData", JSON.stringify(getFormData()));
  }
});

document.getElementById("experience-container").addEventListener("click", function (e) {
  if (e.target.classList.contains("remove-experience")) {
    e.target.closest(".experience-entry").remove();
    updatePreview();
    localStorage.setItem("formData", JSON.stringify(getFormData()));
  }
});

document.getElementById("languages-container").addEventListener("click", function (e) {
  if (e.target.classList.contains("remove-language")) {
    e.target.closest(".language-entry").remove();
    updatePreview();
    localStorage.setItem("formData", JSON.stringify(getFormData()));
  }
});

// Form field change listeners
document.querySelectorAll("input, textarea").forEach((field) => {
  field.addEventListener("input", () => {
    localStorage.setItem("formData", JSON.stringify(getFormData()));
  });
});

// File input change listener
document.getElementById("file-input").addEventListener("change", function(e) {
  if (e.target.files.length > 0) {
    localStorage.setItem("uploadedFile", e.target.files[0].name.replace(/\.[^/.]+$/, "") + ".json");
  }
});

// Save button listener
document.getElementById("save-cv").addEventListener("click", saveFormData);