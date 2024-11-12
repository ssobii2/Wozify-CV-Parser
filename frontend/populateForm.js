document.addEventListener('DOMContentLoaded', function() {
    const resultDiv = document.getElementById('result');
    const uploadForm = document.getElementById('upload-form');
    const pdfViewer = document.getElementById('pdf-viewer');

    uploadForm.addEventListener('submit', function(e) {
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
            const descriptions = entry.querySelector('textarea[name="education-descriptions[]"]').value;
            const listItems = descriptions.split('\n').map(item => `<li>${item}</li>`).join('');
            formData.append('education-descriptions[]', `<ul>${listItems}</ul>`);
        });

        const experienceEntries = document.querySelectorAll('.experience-entry');
        experienceEntries.forEach((entry) => {
            const descriptions = entry.querySelector('textarea[name="experience-descriptions[]"]').value;
            const listItems = descriptions.split('\n').map(item => `<li>${item}</li>`).join('');
            formData.append('experience-descriptions[]', `<ul>${listItems}</ul>`);
        });

        fetch('http://127.0.0.1:8000/process', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                resultDiv.innerText = `Error: ${data.error}`;
            } else {
                populateFields(data.data);

                // Send the same file to generate PDF
                fetch('http://127.0.0.1:8000/generate', {
                    method: 'POST',
                    body: formData
                })
                .then(res => res.blob())
                .then(blob => {
                    const url = URL.createObjectURL(blob);
                    pdfViewer.src = url;
                })
                .catch(error => console.error('Error generating PDF:', error));
            }
        })
        .catch(error => {
            console.error('Error:', error);
        });
    });

    function populateFields(data) {
        document.getElementById('name').value = data.profile.name || '';
        document.getElementById('email').value = data.profile.email || '';
        document.getElementById('phone').value = data.profile.phone || '';
        document.getElementById('location').value = data.profile.location || '';
        document.getElementById('url').value = data.profile.url || '';
        document.getElementById('summary').value = data.profile.summary || '';

        document.getElementById('skills').value = data.skills.join(', ') || '';

        document.getElementById('current-position').value = data.current_position || '';

        const educationContainer = document.getElementById('education-container');
        educationContainer.innerHTML = '';
        data.education.forEach((edu, index) => {
            const newEducationEntry = createEducationEntry(edu, index === 0); // Pass whether it's the first entry
            educationContainer.appendChild(newEducationEntry);
        });

        const experienceContainer = document.getElementById('experience-container');
        experienceContainer.innerHTML = '';
        data.experience.forEach((exp, index) => {
            const newExperienceEntry = createExperienceEntry(exp, index === 0); // Pass whether it's the first entry
            experienceContainer.appendChild(newExperienceEntry);
        });

        // Populate language entries
        const languagesContainer = document.getElementById('languages-container');
        languagesContainer.innerHTML = '';
        data.languages.forEach((lang, index) => {
            const newLanguageEntry = createLanguageEntry(lang, index === 0); // Pass whether it's the first entry
            languagesContainer.appendChild(newLanguageEntry);
        });
    }

    function createEducationEntry(edu, isFirst) {
        const entry = document.createElement('div');
        entry.classList.add('education-entry');
        entry.innerHTML = `
            <div class="form-row">
                <label for="school">School:</label>
                <input type="text" name="school[]" value="${edu.school || ''}">
            </div>
            <div class="form-row">
                <label for="degree">Degree:</label>
                <input type="text" name="degree[]" value="${edu.degree || ''}">
            </div>
            <div class="form-row">
                <label for="gpa">GPA:</label>
                <input type="text" name="gpa[]" value="${edu.gpa || ''}">
            </div>
            <div class="form-row">
                <label for="education-date">Date:</label>
                <input type="text" name="education-date[]" value="${edu.date || ''}">
            </div>
            <div class="form-row">
                <label for="education-descriptions">Descriptions:</label>
                <textarea name="education-descriptions[]" placeholder="Your description here...">${edu.descriptions.join('\n') || ''}</textarea>
            </div>
            ${isFirst ? '' : '<button type="button" class="remove-education">Remove</button>'}
        `;
        return entry;
    }

    function createExperienceEntry(exp, isFirst) {
        const entry = document.createElement('div');
        entry.classList.add('experience-entry');
        entry.innerHTML = `
            <div class="form-row">
                <label for="company">Company:</label>
                <input type="text" name="company[]" value="${exp.company || ''}">
            </div>
            <div class="form-row">
                <label for="job-title">Job Title:</label>
                <input type="text" name="job-title[]" value="${exp.job_title || ''}">
            </div>
            <div class="form-row">
                <label for="experience-date">Date:</label>
                <input type="text" name="experience-date[]" value="${exp.date || ''}">
            </div>
            <div class="form-row">
                <label for="experience-descriptions">Descriptions:</label>
                <textarea name="experience-descriptions[]" placeholder="Your description here...">${exp.descriptions.join('\n') || ''}</textarea>
            </div>
            ${isFirst ? '' : '<button type="button" class="remove-experience">Remove</button>'}
        `;
        return entry;
    }

    function createLanguageEntry(lang, isFirst) {
        const entry = document.createElement('div');
        entry.classList.add('language-entry');
        entry.innerHTML = `
            <div class="form-row">
                <label for="language">Language:</label>
                <input type="text" name="language[]" value="${lang.language || ''}">
            </div>
            <div class="form-row">
                <label for="proficiency">Proficiency:</label>
                <input type="text" name="proficiency[]" value="${lang.proficiency || ''}">
            </div>
            ${isFirst ? '' : '<button type="button" class="remove-language">Remove</button>'}
        `;
        return entry;
    }

    document.getElementById('education-container').addEventListener('click', function(e) {
        if (e.target.classList.contains('remove-education')) {
            e.target.closest('.education-entry').remove(); // Use closest to remove the specific entry
        }
    });

    document.getElementById('experience-container').addEventListener('click', function(e) {
        if (e.target.classList.contains('remove-experience')) {
            e.target.closest('.experience-entry').remove(); // Use closest to remove the specific entry
        }
    });

    document.getElementById('languages-container').addEventListener('click', function(e) {
        if (e.target.classList.contains('remove-language')) {
            e.target.closest('.language-entry').remove(); // Use closest to remove the specific entry
        }
    });
}); 