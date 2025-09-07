const form = document.getElementById('automationForm');
const mainForm = document.getElementById('mainForm');
const loadingState = document.getElementById('loadingState');
const thankYouPage = document.getElementById('thankYouPage');
const resultContainer = document.getElementById('resultContainer');

form.addEventListener('submit', function(e) {
    e.preventDefault();
    
    const formData = new FormData(form);
    const data = {
        calendarUrl: formData.get('calendarUrl'),
        linkedinToken: formData.get('linkedinToken'),
        authorUrn: formData.get('authorUrn'),
        openaiKey: formData.get('openaiKey'),
        brandName: formData.get('brandName'),
        brandTone: formData.get('brandTone'),
        hashtags: formData.get('hashtags'),
        schedulerTime: formData.get('schedulerTime'),
    };

    mainForm.style.display = 'none';
    loadingState.style.display = 'block';

    fetch('http://127.0.0.1:5000/api/generate-post', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
    })
    .then(response => response.json())
    .then(data => {
        loadingState.style.display = 'none';
        if (data.error) {
            alert('Error: ' + data.error);
            resetForm();
        } else {
            displayResults(data);
        }
    })
    .catch(error => {
        loadingState.style.display = 'none';
        alert('An error occurred: ' + error);
        resetForm();
    });
});

function displayResults(data) {
    thankYouPage.style.display = 'block';
    const resultHtml = `
        <h2>${data.post_title}</h2>
        <p>${data.post_body}</p>
        <img src="${data.banner_url}" alt="Generated Banner" style="max-width: 100%; border-radius: 12px; margin-top: 20px;">
        <p style="margin-top: 20px;">Posted to LinkedIn with URN: ${data.linkedin_post_urn}</p>
    `;
    resultContainer.innerHTML = resultHtml;
}

function resetForm() {
    form.reset();
    thankYouPage.style.display = 'none';
    mainForm.style.display = 'block';
    resultContainer.innerHTML = '';
}