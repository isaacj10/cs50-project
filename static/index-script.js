document.addEventListener('DOMContentLoaded', function () {
    var inputElementsText = document.querySelectorAll('input[type="text"]');
    inputElementsText.forEach(function (input) {
        input.addEventListener('input', handleInput);
    });
    var inputElementsRadio = document.querySelectorAll('input[type="radio"]');
    inputElementsRadio.forEach(function (input) {
        input.addEventListener('input', handleInput);
    });
});

function handleInput(event) {

    var temperature = document.getElementById('temperature').value;

    var oxygen_saturation = document.getElementById('oxygen_saturation').value;

    var lung_auscultation_button = document.querySelector('input[name="lung_auscultation"]:checked');
    var lung_auscultation = lung_auscultation_button ? lung_auscultation_button.value : '';

    var crp = document.getElementById('CRP').value;

    var white_cell_count = document.getElementById('white_cell_count').value;

    var age = document.getElementById('age').value;

    var news_2_score = document.getElementById('news_2_score').value;

    var heart_disease_button = document.querySelector('input[name="heart_disease"]:checked');
    var heart_disease = heart_disease_button ? heart_disease_button.value : '';

    var copd_button = document.querySelector('input[name="copd"]:checked');
    var copd = copd_button ? copd_button.value : '';

    var renal_failure_button = document.querySelector('input[name="renal_failure"]:checked');
    var renal_failure = renal_failure_button ? renal_failure_button.value : '';

    var charlson_index = document.getElementById('charlson_index').value;

    var sex_button = document.querySelector('input[name="sex"]:checked');
    var sex = sex_button ? sex_button.value : '';

    var obesity_button = document.querySelector('input[name="obesity"]:checked');
    var obesity = obesity_button ? obesity_button.value : '';

    var immunosuppression_button = document.querySelector('input[name="immunosuppression"]:checked');
    var immunosuppression = immunosuppression_button ? immunosuppression_button.value : '';

    var diabetes_button = document.querySelector('input[name="diabetes"]:checked');
    var diabetes = diabetes_button ? diabetes_button.value : '';

    var neurological_disorder_button = document.querySelector('input[name="neurological_disorder"]:checked');
    var neurological_disorder = neurological_disorder_button ? neurological_disorder_button.value : '';

    var new_example = [temperature, oxygen_saturation, lung_auscultation, crp,white_cell_count, age, news_2_score, heart_disease, copd, renal_failure, charlson_index, sex, obesity, immunosuppression, diabetes, neurological_disorder
    ];

    fetch('/process_array', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ new_example: new_example }),
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Error retrieving prediction values');
        }
        return response.json();
    })
    .then(data => {
        console.log('Response from server:', data);

        var binaryPredictionElement = document.getElementById('binary_predict');
        binaryPredictionElement.innerHTML = `${data.binary_prediction}`;
        console.log('Binary Prediction:', data.binary_prediction);

        var probabilityElement = document.getElementById('probability');
        probabilityElement.innerHTML = `${parseFloat(data.float_probability)}`;
        console.log('Float Probability:', parseFloat(data.float_probability));
    })
    .catch(error => {
        console.error('Error during fetch operation:', error);
    });
}