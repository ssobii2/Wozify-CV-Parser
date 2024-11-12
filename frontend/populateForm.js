document.addEventListener("DOMContentLoaded", function () {
  const uploadForm = document.getElementById("upload-form");
  const saveCvButton = document.getElementById("save-cv");
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

  function updatePreview() {
    fetchHtmlTemplate((html) => {
      const data = {
        skills: document.getElementById("skills").value,
        job_title: document.getElementById("current-position").value,
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
          data.job_title || "";
        iframeDocument.getElementById("personal-summary").textContent =
          data.summary || "";

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
  }

  formFields.forEach((field) => {
    field.addEventListener("input", updatePreview);
  });

  uploadForm.addEventListener("submit", function (e) {
    e.preventDefault();
    const fileInput = document.getElementById("file-input");
    const file = fileInput.files[0];

    if (!file) {
      alert("Please select a file!");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);

    fetch("http://127.0.0.1:8000/process", {
      method: "POST",
      body: formData,
    })
      .then((response) => response.json())
      .then((data) => {
        if (data.error) {
          resultDiv.innerText = `Error: ${data.error}`;
        } else {
          populateFields(data.data);
          updatePreview();
        }
      })
      .catch((error) => {
        console.error("Error:", error);
      });
  });

  saveCvButton.addEventListener("click", function () {
    const formData = new FormData(uploadForm);
    fetch("http://127.0.0.1:8000/generate", {
      method: "POST",
      body: formData,
    })
      .then((res) => res.blob())
      .then((blob) => {
        const link = document.createElement("a");
        link.href = URL.createObjectURL(blob);
        link.download = "CV.pdf";
        link.click();
      })
      .catch((error) => console.error("Error generating PDF:", error));
  });

  function populateFields(data) {
    document.getElementById("name").value = data.profile.name || "";
    document.getElementById("email").value = data.profile.email || "";
    document.getElementById("phone").value = data.profile.phone || "";
    document.getElementById("location").value = data.profile.location || "";
    document.getElementById("url").value = data.profile.url || "";
    document.getElementById("summary").value = data.profile.summary || "";

    document.getElementById("skills").value = data.skills.join(", ") || "";

    document.getElementById("current-position").value =
      data.current_position || "";

    const educationContainer = document.getElementById("education-container");
    educationContainer.innerHTML = "";
    data.education.forEach((edu, index) => {
      const newEducationEntry = createEducationEntry(edu, index === 0); // Pass whether it's the first entry
      educationContainer.appendChild(newEducationEntry);
    });

    const experienceContainer = document.getElementById("experience-container");
    experienceContainer.innerHTML = "";
    data.experience.forEach((exp, index) => {
      const newExperienceEntry = createExperienceEntry(exp, index === 0); // Pass whether it's the first entry
      experienceContainer.appendChild(newExperienceEntry);
    });

    // Populate language entries
    const languagesContainer = document.getElementById("languages-container");
    languagesContainer.innerHTML = "";
    data.languages.forEach((lang, index) => {
      const newLanguageEntry = createLanguageEntry(lang, index === 0); // Pass whether it's the first entry
      languagesContainer.appendChild(newLanguageEntry);
    });
  }

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
    return entry;
  }

  document
    .getElementById("education-container")
    .addEventListener("click", function (e) {
      if (e.target.classList.contains("remove-education")) {
        e.target.closest(".education-entry").remove(); // Use closest to remove the specific entry
      }
    });

  document
    .getElementById("experience-container")
    .addEventListener("click", function (e) {
      if (e.target.classList.contains("remove-experience")) {
        e.target.closest(".experience-entry").remove(); // Use closest to remove the specific entry
      }
    });

  document
    .getElementById("languages-container")
    .addEventListener("click", function (e) {
      if (e.target.classList.contains("remove-language")) {
        e.target.closest(".language-entry").remove(); // Use closest to remove the specific entry
      }
    });
});
