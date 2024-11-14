document.getElementById("upload-form").addEventListener("submit", function (e) {
  e.preventDefault();
  const fileInput = document.getElementById("file-input");
  const file = fileInput.files[0];
  if (!file) {
    alert("Please select a file!");
    return;
  }

  const formData = new FormData();
  formData.append("file", file);

  // Process education entries
  const educationEntries = document.querySelectorAll(".education-entry");
  educationEntries.forEach((entry) => {
    formData.append(
      "school[]",
      entry.querySelector('input[name="school[]"]').value
    );
    formData.append(
      "degree[]",
      entry.querySelector('input[name="degree[]"]').value
    );
    formData.append("gpa[]", entry.querySelector('input[name="gpa[]"]').value);
    formData.append(
      "education-date[]",
      entry.querySelector('input[name="education-date[]"]').value
    );
    formData.append(
      "education-descriptions[]",
      entry.querySelector('textarea[name="education-descriptions[]"]').value
    );
  });

  // Process experience entries
  const experienceEntries = document.querySelectorAll(".experience-entry");
  experienceEntries.forEach((entry) => {
    formData.append(
      "company[]",
      entry.querySelector('input[name="company[]"]').value
    );
    formData.append(
      "job-title[]",
      entry.querySelector('input[name="job-title[]"]').value
    );
    formData.append(
      "experience-date[]",
      entry.querySelector('input[name="experience-date[]"]').value
    );
    formData.append(
      "experience-descriptions[]",
      entry.querySelector('textarea[name="experience-descriptions[]"]').value
    );
  });

  // Process language entries
  const languageEntries = document.querySelectorAll(".language-entry");
  languageEntries.forEach((entry) => {
    formData.append(
      "language[]",
      entry.querySelector('input[name="language[]"]').value
    );
    formData.append(
      "proficiency[]",
      entry.querySelector('input[name="proficiency[]"]').value
    );
  });

  console.log("File selected:", file.name);
});

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
  // Update local storage after adding a new entry
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
  // Update local storage after adding a new entry
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

document
  .getElementById("add-education")
  .addEventListener("click", addEducationEntry);
document
  .getElementById("add-experience")
  .addEventListener("click", addExperienceEntry);
document
  .getElementById("add-language")
  .addEventListener("click", addLanguageEntry);

document
  .getElementById("education-container")
  .addEventListener("click", function (e) {
    if (e.target.classList.contains("remove-education")) {
      e.target.closest(".education-entry").remove();
      updatePreview(); // Update preview after removal
      // Update local storage after removing an entry
      localStorage.setItem("formData", JSON.stringify(getFormData()));
    }
  });

document
  .getElementById("experience-container")
  .addEventListener("click", function (e) {
    if (e.target.classList.contains("remove-experience")) {
      e.target.closest(".experience-entry").remove();
      updatePreview(); // Update preview after removal
      // Update local storage after removing an entry
      localStorage.setItem("formData", JSON.stringify(getFormData()));
    }
  });

document
  .getElementById("languages-container")
  .addEventListener("click", function (e) {
    if (e.target.classList.contains("remove-language")) {
      e.target.closest(".language-entry").remove();
      updatePreview(); // Update preview after removal
      // Update local storage after removing an entry
      localStorage.setItem("formData", JSON.stringify(getFormData()));
    }
  });

// Function to get the current form data
function getFormData() {
  const data = {
    profile: {
      name: document.getElementById("name").value,
      email: document.getElementById("email").value,
      phone: document.getElementById("phone").value,
      location: document.getElementById("location").value,
      url: document.getElementById("url").value,
      summary: document.getElementById("summary").value,
    },
    skills: document
      .getElementById("skills")
      .value.split(",")
      .map((skill) => skill.trim()),
    current_position: document.getElementById("current-position").value,
    education: Array.from(document.querySelectorAll(".education-entry")).map(
      (entry) => ({
        date: entry.querySelector('input[name="education-date[]"]').value || "",
        degree: entry.querySelector('input[name="degree[]"]').value || "",
        school: entry.querySelector('input[name="school[]"]').value || "",
        gpa: entry.querySelector('input[name="gpa[]"]').value || "",
        descriptions: entry
          .querySelector('textarea[name="education-descriptions[]"]')
          .value.split("\n")
          .map((desc) => desc.trim()),
      })
    ),
    languages: Array.from(document.querySelectorAll(".language-entry")).map(
      (entry) => ({
        language: entry.querySelector('input[name="language[]"]').value || "",
        proficiency:
          entry.querySelector('input[name="proficiency[]"]').value || "",
      })
    ),
    experience: Array.from(document.querySelectorAll(".experience-entry")).map(
      (entry) => ({
        date:
          entry.querySelector('input[name="experience-date[]"]').value || "",
        job_title: entry.querySelector('input[name="job-title[]"]').value || "",
        company: entry.querySelector('input[name="company[]"]').value || "",
        descriptions: entry
          .querySelector('textarea[name="experience-descriptions[]"]')
          .value.split("\n")
          .map((desc) => desc.trim()),
      })
    ),
  };
  return data;
}

// Update local storage whenever the form data changes
document.querySelectorAll("input, textarea").forEach((field) => {
  field.addEventListener("input", () => {
    localStorage.setItem("formData", JSON.stringify(getFormData()));
  });
});