document.getElementById('upload-form').addEventListener('submit', function(e) {
    e.preventDefault();
    const fileInput = document.getElementById('file-input');
    const file = fileInput.files[0];
    if (!file) {
        alert('Please select a file!');
        return;
    }

    const formData = new FormData();
    formData.append('file', file);

    const educationEntries = document.querySelectorAll('.education-entry');
    educationEntries.forEach((entry) => {
        formData.append('school[]', entry.querySelector('input[name="school[]"]').value);
        formData.append('degree[]', entry.querySelector('input[name="degree[]"]').value);
        formData.append('gpa[]', entry.querySelector('input[name="gpa[]"]').value);
        formData.append('education-date[]', entry.querySelector('input[name="education-date[]"]').value);
        formData.append('education-descriptions[]', entry.querySelector('.editable[name="education-descriptions[]"]').innerText);
    });

    const experienceEntries = document.querySelectorAll('.experience-entry');
    experienceEntries.forEach((entry) => {
        formData.append('company[]', entry.querySelector('input[name="company[]"]').value);
        formData.append('job-title[]', entry.querySelector('input[name="job-title[]"]').value);
        formData.append('experience-date[]', entry.querySelector('input[name="experience-date[]"]').value);
        formData.append('experience-descriptions[]', entry.querySelector('.editable[name="experience-descriptions[]"]').innerText);
    });

    const languageEntries = document.querySelectorAll('.language-entry');
    languageEntries.forEach((entry) => {
        formData.append('language[]', entry.querySelector('input[name="language[]"]').value);
        formData.append('proficiency[]', entry.querySelector('input[name="proficiency[]"]').value);
    });

    console.log('File selected:', file.name);
});

function initializeEditableDivs() {
    const editableDivs = document.querySelectorAll('.editable');
    editableDivs.forEach(div => {
        div.innerHTML = '';
        placeCaretAtEnd(div);
        div.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                const currentContent = div.innerHTML;
                div.innerHTML = currentContent + '<br>• ';
                placeCaretAtEnd(div);
            }
        });
    });
}

function placeCaretAtEnd(el) {
    el.focus();
    const range = document.createRange();
    range.selectNodeContents(el);
    range.collapse(false);
    const sel = window.getSelection();
    sel.removeAllRanges();
    sel.addRange(range);
}

initializeEditableDivs();

document.getElementById('add-education').addEventListener('click', function() {
    const educationContainer = document.getElementById('education-container');
    const newEducationEntry = document.createElement('div');
    newEducationEntry.classList.add('education-entry');
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
            <div class="editable" contenteditable="true" name="education-descriptions[]"></div>
        </div>
        <button type="button" class="remove-education">Remove</button>
    `;
    educationContainer.appendChild(newEducationEntry);
    initializeEditableDivs();
});

document.getElementById('education-container').addEventListener('click', function(e) {
    if (e.target.classList.contains('remove-education')) {
        e.target.parentElement.remove();
    }
});

document.getElementById('add-experience').addEventListener('click', function() {
    const experienceContainer = document.getElementById('experience-container');
    const newExperienceEntry = document.createElement('div');
    newExperienceEntry.classList.add('experience-entry');
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
            <div class="editable" contenteditable="true" name="experience-descriptions[]"></div>
        </div>
        <button type="button" class="remove-experience">Remove</button>
    `;
    experienceContainer.appendChild(newExperienceEntry);
    initializeEditableDivs();
});

document.getElementById('experience-container').addEventListener('click', function(e) {
    if (e.target.classList.contains('remove-experience')) {
        e.target.parentElement.remove();
    }
});

document.getElementById('add-language').addEventListener('click', function() {
    const languagesContainer = document.getElementById('languages-container');
    const newLanguageEntry = document.createElement('div');
    newLanguageEntry.classList.add('language-entry');
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
    languagesContainer.appendChild(newLanguageEntry);
});

document.getElementById('languages-container').addEventListener('click', function(e) {
    if (e.target.classList.contains('remove-language')) {
        e.target.parentElement.remove();
    }
}); 