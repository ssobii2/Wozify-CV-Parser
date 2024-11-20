let currentCVId = null;

document.addEventListener("DOMContentLoaded", function () {
  const uploadForm = document.getElementById("upload-form");
  const previewIframe = document.getElementById("cv-preview");

  const formFields = document.querySelectorAll(
    "#upload-form input, #upload-form textarea"
  );

  function fetchHtmlTemplate(callback) {
    fetch(`/static/live_preview.html`)
      .then((response) => response.text())
      .then((html) => callback(html))
      .catch((error) => console.error("Error loading template:", error));
  }

  function generateCvId() {
    return `#${Math.floor(1000 + Math.random() * 9000)}`;
  }

  window.updatePreview = function () {
    fetchHtmlTemplate((html) => {
      const data = {
        skills: document.getElementById("skills").value,
        current_position: document.getElementById("current-position").value,
        summary: document.getElementById("summary").value,
        education: Array.from(
          document.querySelectorAll(".education-entry")
        ).map((entry) => ({
          date:
            entry.querySelector('input[name="education-date[]"]').value || "",
          degree: entry.querySelector('input[name="degree[]"]').value || "",
          school: entry.querySelector('input[name="school[]"]').value || "",
        })),
        languages: Array.from(document.querySelectorAll(".language-entry")).map(
          (entry) => ({
            language:
              entry.querySelector('input[name="language[]"]').value || "",
            proficiency:
              entry.querySelector('input[name="proficiency[]"]').value || "",
          })
        ),
        experience: Array.from(
          document.querySelectorAll(".experience-entry")
        ).map((entry) => ({
          date:
            entry.querySelector('input[name="experience-date[]"]').value || "",
          job_title:
            entry.querySelector('input[name="job-title[]"]').value || "",
          company: entry.querySelector('input[name="company[]"]').value || "",
          descriptions: entry
            .querySelector('textarea[name="experience-descriptions[]"]')
            .value.split("\n")
            .map((desc) => desc.trim()),
        })),
      };

      previewIframe.onload = () => {
        const iframeDocument =
          previewIframe.contentDocument || previewIframe.contentWindow.document;

        // Update content in iframe using IDs
        iframeDocument.getElementById("skills-list").innerHTML = (
          data.skills || ""
        )
          .split(",")
          .map((skill) => `<li>${skill.trim()}</li>`)
          .join("");
        iframeDocument.getElementById("job-title").textContent =
          data.current_position || "";
        iframeDocument.getElementById("personal-summary").textContent =
          data.summary || "";

        iframeDocument.querySelector(".cv-id").textContent = currentCVId;

        // Education
        const educationEntries =
          iframeDocument.getElementById("education-entries");
        educationEntries.innerHTML = "";
        data.education.forEach((edu) => {
          const entry = document.createElement("div");
          entry.classList.add("education-entry");
          entry.innerHTML = `
                        <div class="education-date">${edu.date || ""}</div>
                        <div class="education-degree">${edu.degree || ""}</div>
                        <div class="education-school">${edu.school || ""}</div>
                    `;
          educationEntries.appendChild(entry);
        });

        // Languages
        const languagesList = iframeDocument.getElementById("languages-list");
        languagesList.innerHTML = "";
        data.languages.forEach((lang) => {
          if (lang.language && lang.proficiency) {
            const listItem = document.createElement("li");
            listItem.textContent = `${lang.language} - ${lang.proficiency}`;
            languagesList.appendChild(listItem);
          }
        });

        // Work History
        const workEntries = iframeDocument.getElementById("work-entries");
        workEntries.innerHTML = "";
        data.experience.forEach((exp) => {
          const entry = document.createElement("div");
          entry.classList.add("experience-entry");
          entry.innerHTML = `
                        <div class="experience-date">${exp.date || ""}</div>
                        <div class="experience-job-title">${
                          exp.job_title || ""
                        } - ${exp.company || ""}</div>
                        <ul class="experience-descriptions">
                            ${exp.descriptions
                              .map((desc) => `<li>${desc}</li>`)
                              .join("")}
                        </ul>
                    `;
          workEntries.appendChild(entry);
        });
      };

      previewIframe.srcdoc = html;
    });
    localStorage.setItem("formData", JSON.stringify(getFormData()));
  };

  currentCVId = generateCvId();

  formFields.forEach((field) => {
    field.addEventListener("input", updatePreview);
  });

  document.getElementById("save-cv").addEventListener("click", function () {
    const element = document.getElementById("cv-preview").contentDocument.body;

    // Fetch the CSS file
    fetch("/static/live_preview.css")
      .then((response) => response.text())
      .then((css) => {
        // Create a style element and append the CSS
        const styleElement = document.createElement("style");
        styleElement.textContent = css;
        element.prepend(styleElement);

        // Use html2pdf to generate PDF
        html2pdf()
          .from(element)
          .set({
            margin: 0,
            filename: "Generated-CV.pdf",
            html2canvas: { scale: 2, useCORS: true },
            jsPDF: {
              unit: "in",
              format: [8.5, element.scrollHeight / 105],
              // format: "a4",
              orientation: "portrait"
            },
          })
          .save();
      })
      .catch((error) => console.error("Error fetching CSS:", error));
  });

  // Export populateFields function to make it available globally
  window.populateFields = function (storedData) {
    const data = storedData || {};
    data.profile = data.profile || {};
    data.skills = data.skills || [];
    data.education = data.education || [];
    data.experience = data.experience || [];
    data.languages = data.languages || [];
    document.getElementById("name").value = data.profile.name || "";
    document.getElementById("email").value = data.profile.email || "";
    document.getElementById("phone").value = data.profile.phone || "";
    document.getElementById("location").value = data.profile.location || "";
    document.getElementById("url").value = data.profile.url || "";
    document.getElementById("summary").value = data.profile.summary || "";
    document.getElementById("skills").value = data.skills.join(", ") || "";
    document.getElementById("current-position").value = data.current_position || "";

    // Handle local storage data
    const educationContainer = document.getElementById("education-container");
    educationContainer.innerHTML = "";
    data.education.forEach((edu, index) => {
      const newEducationEntry = createEducationEntry(edu, index === 0);
      educationContainer.appendChild(newEducationEntry);
      // Attach event listeners to dynamically created inputs
      newEducationEntry.querySelectorAll("input, textarea").forEach((input) => {
        input.addEventListener("input", updatePreview);
      });
    });

    const experienceContainer = document.getElementById("experience-container");
    experienceContainer.innerHTML = "";
    data.experience.forEach((exp, index) => {
      const newExperienceEntry = createExperienceEntry(exp, index === 0);
      experienceContainer.appendChild(newExperienceEntry);
      // Attach event listeners to dynamically created inputs
      newExperienceEntry
        .querySelectorAll("input, textarea")
        .forEach((input) => {
          input.addEventListener("input", updatePreview);
        });
    });

    const languagesContainer = document.getElementById("languages-container");
    languagesContainer.innerHTML = "";
    data.languages.forEach((lang, index) => {
      const newLanguageEntry = createLanguageEntry(lang, index === 0);
      languagesContainer.appendChild(newLanguageEntry);
      // Attach event listeners to dynamically created inputs
      newLanguageEntry.querySelectorAll("input, textarea").forEach((input) => {
        input.addEventListener("input", updatePreview);
      });
    });
  };

  function createEducationEntry(edu, isFirst) {
    const entry = document.createElement("div");
    entry.classList.add("education-entry");
    entry.innerHTML = `
            <div class="form-row">
                <label for="school">School:</label>
                <input type="text" name="school[]" value="${edu.school || ""}">
            </div>
            <div class="form-row">
                <label for="degree">Degree:</label>
                <input type="text" name="degree[]" value="${edu.degree || ""}">
            </div>
            <div class="form-row">
                <label for="gpa">GPA:</label>
                <input type="text" name="gpa[]" value="${edu.gpa || ""}">
            </div>
            <div class="form-row">
                <label for="education-date">Date:</label>
                <input type="text" name="education-date[]" value="${
                  edu.date || ""
                }">
            </div>
            <div class="form-row">
                <label for="education-descriptions">Descriptions:</label>
                <textarea name="education-descriptions[]" placeholder="Your description here...">${
                  edu.descriptions.join("\n") || ""
                }</textarea>
            </div>
            ${
              isFirst
                ? ""
                : '<button type="button" class="remove-education">Remove</button>'
            }
        `;
    // Attach auto-updating event listeners
    entry.querySelectorAll("input, textarea").forEach((input) => {
      input.addEventListener("input", updatePreview);
    });
    return entry;
  }

  function createExperienceEntry(exp, isFirst) {
    const entry = document.createElement("div");
    entry.classList.add("experience-entry");
    entry.innerHTML = `
            <div class="form-row">
                <label for="company">Company:</label>
                <input type="text" name="company[]" value="${
                  exp.company || ""
                }">
            </div>
            <div class="form-row">
                <label for="job-title">Job Title:</label>
                <input type="text" name="job-title[]" value="${
                  exp.job_title || ""
                }">
            </div>
            <div class="form-row">
                <label for="experience-date">Date:</label>
                <input type="text" name="experience-date[]" value="${
                  exp.date || ""
                }">
            </div>
            <div class="form-row">
                <label for="experience-descriptions">Descriptions:</label>
                <textarea name="experience-descriptions[]" placeholder="Your description here...">${
                  exp.descriptions.join("\n") || ""
                }</textarea>
            </div>
            ${
              isFirst
                ? ""
                : '<button type="button" class="remove-experience">Remove</button>'
            }
        `;
    // Attach auto-updating event listeners
    entry.querySelectorAll("input, textarea").forEach((input) => {
      input.addEventListener("input", updatePreview);
    });
    return entry;
  }

  function createLanguageEntry(lang, isFirst) {
    const entry = document.createElement("div");
    entry.classList.add("language-entry");
    entry.innerHTML = `
              <div class="form-row">
                  <label for="language">Language:</label>
                  <input type="text" name="language[]" value="${
                    lang.language || ""
                  }">
              </div>
              <div class="form-row">
                  <label for="proficiency">Proficiency:</label>
                  <input type="text" name="proficiency[]" value="${
                    lang.proficiency || ""
                  }">
              </div>
              ${
                isFirst
                  ? ""
                  : '<button type="button" class="remove-language">Remove</button>'
              }
          `;
    // Attach auto-updating event listeners
    entry.querySelectorAll("input, textarea").forEach((input) => {
      input.addEventListener("input", updatePreview);
    });
    return entry;
  }

  // Load data from local storage on page load
  window.addEventListener("load", function () {
    const storedData = JSON.parse(localStorage.getItem("formData")) || {};
    populateFields(storedData);
    updatePreview();
  });

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
          date: entry.querySelector('input[name="experience-date[]"]').value ||
            "",
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
          date: entry.querySelector('input[name="education-date[]"]').value ||
            "",
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
          proficiency:
            entry.querySelector('input[name="proficiency[]"]').value || "",
        })
      ),
      current_position: document.getElementById("current-position").value || "",
    };
    return data;
  }

  // Update local storage whenever the form data changes
  formFields.forEach((field) => {
    field.addEventListener("input", () => {
      localStorage.setItem("formData", JSON.stringify(getFormData()));
    });
  });

  function clearLocalStorage() {
    localStorage.removeItem("uploadedFile");
    localStorage.removeItem("formData");
    // Reset form fields
    document.getElementById("name").value = "";
    document.getElementById("email").value = "";
    document.getElementById("phone").value = "";
    document.getElementById("location").value = "";
    document.getElementById("url").value = "";
    document.getElementById("summary").value = "";
    document.getElementById("skills").value = "";
    document.getElementById("current-position").value = "";

    // Reset education entries
    const educationContainer = document.getElementById("education-container");
    educationContainer.innerHTML = "";
    addEducationEntry();

    // Reset experience entries
    const experienceContainer = document.getElementById("experience-container");
    experienceContainer.innerHTML = "";
    addExperienceEntry();

    // Reset language entries
    const languagesContainer = document.getElementById("languages-container");
    languagesContainer.innerHTML = "";
    addLanguageEntry();

    // Clear file input
    document.getElementById("file-input").value = "";

    updatePreview();
  }

  document
    .getElementById("clear-button")
    .addEventListener("click", clearLocalStorage);
});
