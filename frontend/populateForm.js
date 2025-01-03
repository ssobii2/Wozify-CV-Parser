// Global variables
let currentCVId = null;

// Utility functions
function generateCvId() {
  return `#${Math.floor(1000 + Math.random() * 9000)}`;
}

function fetchHtmlTemplate(callback, language = 'en') {
  const templateFile = language === 'hu' ? 'live_preview_hu.html' : 'live_preview.html';
  fetch(`/static/${templateFile}`)
    .then((response) => response.text())
    .then((html) => callback(html))
    .catch((error) => {
      console.error("Error loading template:", error);
      if (language === 'hu') {
        fetchHtmlTemplate(callback, 'en');
      }
    });
}

// Form data management functions
function getFormData() {
  const detectedLanguage = document.querySelector('input[name="detected-language"]')?.value || 'en';
  
  const formData = {
    language: detectedLanguage,
    profile: {
      cv_id: document.getElementById("cv-id").value || currentCVId,
      name: document.getElementById("name").value || "",
      email: document.getElementById("email").value || "",
      phone: document.getElementById("phone").value || "",
      location: document.getElementById("location").value || "",
      url: document.getElementById("url").value || "",
      summary: document.getElementById("summary").value || "",
    },
    skills: document.getElementById("skills").value || "",
    current_position: document.getElementById("current-position").value || "",
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
    languages: Array.from(document.querySelectorAll(".language-entry")).map(
      (entry) => ({
        language: entry.querySelector('input[name="language[]"]').value || "",
        proficiency: entry.querySelector('input[name="proficiency[]"]').value || "",
      })
    ),
  };
  return formData;
}

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

  currentCVId = null;
  document.getElementById("cv-id").value = "";

  // Reset entries
  const educationContainer = document.getElementById("education-container");
  educationContainer.innerHTML = "";
  addEducationEntry();

  const experienceContainer = document.getElementById("experience-container");
  experienceContainer.innerHTML = "";
  addExperienceEntry();

  const languagesContainer = document.getElementById("languages-container");
  languagesContainer.innerHTML = "";
  addLanguageEntry();

  document.getElementById("file-input").value = "";
  updatePreview();
}

// Entry creation functions
function createEducationEntry(edu, isFirst) {
  const entry = document.createElement("div");
  entry.classList.add("education-entry");
  entry.innerHTML = `
        <div class="form-row">
            <label for="school">School:</label>
            <input type="text" name="school[]" value="${edu?.school || ""}">
        </div>
        <div class="form-row">
            <label for="degree">Degree:</label>
            <input type="text" name="degree[]" value="${edu?.degree || ""}">
        </div>
        <div class="form-row">
            <label for="gpa">GPA:</label>
            <input type="text" name="gpa[]" value="${edu?.gpa || ""}">
        </div>
        <div class="form-row">
            <label for="education-date">Date:</label>
            <input type="text" name="education-date[]" value="${edu?.date || ""}">
        </div>
        <div class="form-row">
            <label for="education-descriptions">Descriptions:</label>
            <textarea name="education-descriptions[]" placeholder="Your description here...">${edu?.descriptions ? edu.descriptions.join("\n") : ""}</textarea>
        </div>
        ${isFirst ? "" : '<button type="button" class="remove-education">Remove</button>'}
    `;
  entry.querySelectorAll("input, textarea").forEach((input) => {
    input.addEventListener("input", updatePreview);
  });
  
  const removeButton = entry.querySelector(".remove-education");
  if (removeButton) {
    removeButton.addEventListener("click", function() {
      entry.remove();
      updatePreview();
    });
  }
  
  return entry;
}

function createExperienceEntry(exp, isFirst) {
  const entry = document.createElement("div");
  entry.classList.add("experience-entry");
  entry.innerHTML = `
        <div class="form-row">
            <label for="company">Company:</label>
            <input type="text" name="company[]" value="${exp?.company || ""}">
        </div>
        <div class="form-row">
            <label for="job-title">Job Title:</label>
            <input type="text" name="job-title[]" value="${exp?.job_title || ""}">
        </div>
        <div class="form-row">
            <label for="experience-date">Date:</label>
            <input type="text" name="experience-date[]" value="${exp?.date || ""}">
        </div>
        <div class="form-row">
            <label for="experience-descriptions">Descriptions:</label>
            <textarea name="experience-descriptions[]" placeholder="Your description here...">${exp?.descriptions ? exp.descriptions.join("\n") : ""}</textarea>
        </div>
        ${isFirst ? "" : '<button type="button" class="remove-experience">Remove</button>'}
    `;
  entry.querySelectorAll("input, textarea").forEach((input) => {
    input.addEventListener("input", updatePreview);
  });
  
  const removeButton = entry.querySelector(".remove-experience");
  if (removeButton) {
    removeButton.addEventListener("click", function() {
      entry.remove();
      updatePreview();
    });
  }
  
  return entry;
}

function createLanguageEntry(lang, isFirst) {
  const entry = document.createElement("div");
  entry.classList.add("language-entry");
  entry.innerHTML = `
        <div class="form-row">
            <label for="language">Language:</label>
            <input type="text" name="language[]" value="${lang?.language || ""}">
        </div>
        <div class="form-row">
            <label for="proficiency">Proficiency:</label>
            <input type="text" name="proficiency[]" value="${lang?.proficiency || ""}">
        </div>
        ${isFirst ? "" : '<button type="button" class="remove-language">Remove</button>'}
    `;
  entry.querySelectorAll("input, textarea").forEach((input) => {
    input.addEventListener("input", updatePreview);
  });
  
  const removeButton = entry.querySelector(".remove-language");
  if (removeButton) {
    removeButton.addEventListener("click", function() {
      entry.remove();
      updatePreview();
    });
  }
  
  return entry;
}

// Preview update functions
window.updatePreview = function () {
  const detectedLanguage = document.querySelector('input[name="detected-language"]')?.value || 'en';
  fetchHtmlTemplate((html) => {
    const data = {
      profile: {
        cv_id: document.getElementById("cv-id").value || currentCVId,
        name: document.getElementById("name").value || "",
        email: document.getElementById("email").value || "",
        phone: document.getElementById("phone").value || "",
        location: document.getElementById("location").value || "",
        url: document.getElementById("url").value || "",
        summary: document.getElementById("summary").value || "",
      },
      skills: document.getElementById("skills").value,
      current_position: document.getElementById("current-position").value,
      education: Array.from(document.querySelectorAll(".education-entry")).map((entry) => ({
        date: entry.querySelector('input[name="education-date[]"]').value || "",
        degree: entry.querySelector('input[name="degree[]"]').value || "",
        school: entry.querySelector('input[name="school[]"]').value || "",
      })),
      languages: Array.from(document.querySelectorAll(".language-entry")).map((entry) => ({
        language: entry.querySelector('input[name="language[]"]').value || "",
        proficiency: entry.querySelector('input[name="proficiency[]"]').value || "",
      })),
      experience: Array.from(document.querySelectorAll(".experience-entry")).map((entry) => ({
        date: entry.querySelector('input[name="experience-date[]"]').value || "",
        job_title: entry.querySelector('input[name="job-title[]"]').value || "",
        company: entry.querySelector('input[name="company[]"]').value || "",
        descriptions: entry.querySelector('textarea[name="experience-descriptions[]"]').value.split("\n").map((desc) => desc.trim()),
      })),
    };

    const previewIframe = document.getElementById("cv-preview");
    previewIframe.onload = () => {
      const iframeDocument = previewIframe.contentDocument;

      iframeDocument.getElementById("skills-list").innerHTML = (data.skills || "")
        .split(",")
        .map((skill) => `<li>${skill.trim()}</li>`)
        .join("");
      iframeDocument.getElementById("job-title").textContent = data.current_position || "";
      iframeDocument.getElementById("personal-summary").textContent = data.profile.summary || "";
      iframeDocument.querySelector(".cv-id").textContent = data.profile.cv_id || currentCVId;

      const educationEntries = iframeDocument.getElementById("education-entries");
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

      const languagesList = iframeDocument.getElementById("languages-list");
      languagesList.innerHTML = "";
      data.languages.forEach((lang) => {
        if (lang.language && lang.proficiency) {
          const listItem = document.createElement("li");
          listItem.textContent = `${lang.language} - ${lang.proficiency}`;
          languagesList.appendChild(listItem);
        }
      });

      const workEntries = iframeDocument.getElementById("work-entries");
      workEntries.innerHTML = "";
      data.experience.forEach((exp) => {
        const entry = document.createElement("div");
        entry.classList.add("experience-entry");
        entry.innerHTML = `
          <div class="experience-date">${exp.date || ""}</div>
          <div class="experience-job-title">${exp.job_title || ""} - ${exp.company || ""}</div>
          <ul class="experience-descriptions">
            ${exp.descriptions.map((desc) => `<li>${desc}</li>`).join("")}
          </ul>
        `;
        workEntries.appendChild(entry);
      });
    };

    previewIframe.srcdoc = html;
  }, detectedLanguage);
  localStorage.setItem("formData", JSON.stringify(getFormData()));
};

// Form population functions
window.populateFields = function (data) {
  if (!data) return;

  let detectedLanguageInput = document.querySelector('input[name="detected-language"]');
  if (!detectedLanguageInput) {
    detectedLanguageInput = document.createElement('input');
    detectedLanguageInput.type = 'hidden';
    detectedLanguageInput.name = 'detected-language';
    document.getElementById('upload-form').appendChild(detectedLanguageInput);
  }
  detectedLanguageInput.value = data.language || 'en';

  const detectedLanguage = detectedLanguageInput.value;

  if (data.profile) {
    document.getElementById("name").value = data.profile.name || "";
    document.getElementById("email").value = data.profile.email || "";
    document.getElementById("phone").value = data.profile.phone || "";
    document.getElementById("location").value = data.profile.location || "";
    document.getElementById("url").value = data.profile.url || "";
    document.getElementById("summary").value = data.profile.summary || "";

    if (data.profile.cv_id) {
      currentCVId = data.profile.cv_id;
      document.getElementById("cv-id").value = currentCVId;
    }
  }

  document.getElementById("skills").value = Array.isArray(data.skills) 
    ? data.skills.join(", ")
    : data.skills;

  document.getElementById("current-position").value = data.current_position || "";

  const educationContainer = document.getElementById("education-container");
  educationContainer.innerHTML = "";
  if (data.education && data.education.length > 0) {
    data.education.forEach((edu, index) => {
      const newEducationEntry = createEducationEntry(edu, index === 0);
      educationContainer.appendChild(newEducationEntry);
    });
  } else {
    addEducationEntry();
  }

  const experienceContainer = document.getElementById("experience-container");
  experienceContainer.innerHTML = "";
  if (data.experience && data.experience.length > 0) {
    data.experience.forEach((exp, index) => {
      const newExperienceEntry = createExperienceEntry(exp, index === 0);
      experienceContainer.appendChild(newExperienceEntry);
    });
  } else {
    addExperienceEntry();
  }

  const languagesContainer = document.getElementById("languages-container");
  languagesContainer.innerHTML = "";
  if (data.languages && data.languages.length > 0) {
    data.languages.forEach((lang, index) => {
      const newLanguageEntry = createLanguageEntry(lang, index === 0);
      languagesContainer.appendChild(newLanguageEntry);
    });
  } else {
    addLanguageEntry();
  }

  fetchHtmlTemplate((html) => {
    const previewIframe = document.getElementById("cv-preview");
    previewIframe.srcdoc = html;
    setTimeout(updatePreview, 100);
  }, detectedLanguage);
};

// Initialize form and event listeners
document.addEventListener("DOMContentLoaded", function () {
  const uploadForm = document.getElementById("upload-form");
  const previewIframe = document.getElementById("cv-preview");
  const formFields = document.querySelectorAll("#upload-form input, #upload-form textarea");

  formFields.forEach((field) => {
    field.addEventListener("input", updatePreview);
  });

  document.getElementById("save-cv").addEventListener("click", function () {
    const element = document.getElementById("cv-preview").contentDocument.body;

    fetch("/static/live_preview.css")
      .then((response) => response.text())
      .then((css) => {
        const styleElement = document.createElement("style");
        styleElement.textContent = css;
        element.prepend(styleElement);

        const a4HeightMm = 297;
        const pixelsPerMm = 3.7795275591;
        const a4HeightPx = a4HeightMm * pixelsPerMm;
        const contentHeight = Math.max(
          element.scrollHeight,
          element.offsetHeight,
          element.clientHeight,
          a4HeightPx
        );
        const numPages = Math.ceil(contentHeight / a4HeightPx);
        const totalHeight = numPages * a4HeightPx;
        
        const opt = {
          margin: 0,
          filename: "Generated-CV.pdf",
          html2canvas: { 
            scale: 2,
            useCORS: true,
            onclone: function(clonedDoc) {
              const sidebar = clonedDoc.querySelector('.left-sidebar');
              const mainContent = clonedDoc.querySelector('.main-content');
              
              const workEntries = mainContent.querySelectorAll('#work-entries > div');
              workEntries.forEach((entry, index) => {
                const entryHeight = entry.offsetHeight;
                const currentY = entry.offsetTop;
                const pageHeight = 297 * 3.779527559;
                
                if (currentY % pageHeight + entryHeight > pageHeight) {
                  entry.style.marginTop = (pageHeight - (currentY % pageHeight) + 40) + 'px';
                }
              });
              
              if (sidebar && mainContent) {
                const maxHeight = Math.max(
                  mainContent.scrollHeight,
                  sidebar.scrollHeight,
                  totalHeight
                );
                const adjustedHeight = maxHeight - 1;
                sidebar.style.minHeight = adjustedHeight + 'px';
                mainContent.style.minHeight = adjustedHeight + 'px';
                clonedDoc.querySelector('.wrapper').style.minHeight = adjustedHeight + 'px';
              }
            }
          },
          jsPDF: {
            unit: "mm",
            format: "a4",
            orientation: "portrait",
            compress: true
          },
          pagebreak: { mode: 'avoid-all' }
        };

        html2pdf().set(opt).from(element).save();
      })
      .catch((error) => console.error("Error fetching CSS:", error));
  });

  document.getElementById("clear-button").addEventListener("click", clearLocalStorage);

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

  formFields.forEach((field) => {
    field.addEventListener("input", () => {
      localStorage.setItem("formData", JSON.stringify(getFormData()));
    });
  });

  window.addEventListener("load", function () {
    const storedData = JSON.parse(localStorage.getItem("formData")) || {};
    populateFields(storedData);
    updatePreview();
  });
});
