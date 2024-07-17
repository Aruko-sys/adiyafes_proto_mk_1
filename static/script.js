const video = document.getElementById('camera');
const gazeDirectionElem = document.getElementById('gazeDirection');
const numFacesElem = document.getElementById('numFaces');

navigator.mediaDevices.getUserMedia({ video: true })
    .then(stream => {
        video.srcObject = stream;
    })
    .catch(err => {
        console.error("Error accessing the camera: ", err);
    });

function sendFrame() {
    const canvas = document.createElement('canvas');
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const context = canvas.getContext('2d');
    context.drawImage(video, 0, 0, canvas.width, canvas.height);
    canvas.toBlob(blob => {
        const xhr = new XMLHttpRequest();
        xhr.open('POST', '/process_frame', true);
        xhr.onload = function() {
            if (xhr.status === 200) {
                const response = JSON.parse(xhr.responseText);
                gazeDirectionElem.textContent = response.gaze_direction;
                numFacesElem.textContent = response.num_faces;
            } else {
                console.error('Error processing frame:', xhr.responseText);
            }
        };
        const formData = new FormData();
        formData.append('file', blob);
        xhr.send(formData);
    }, 'image/jpeg');
}

setInterval(sendFrame, 1000);  // Send frame every second

function submitExam() {
    const answer1 = document.getElementById('answer1').value;
    const answer2 = document.getElementById('answer2').value;

    const data = {
        answers: [
            { question: 1, answer: answer1 },
            { question: 2, answer: answer2 }
        ]
    };

    const xhr = new XMLHttpRequest();
    xhr.open('POST', '/submit_exam', true);
    xhr.setRequestHeader('Content-Type', 'application/json;charset=UTF-8');
    xhr.onload = function() {
        if (xhr.status === 200) {
            alert('Exam submitted successfully!');
        } else {
            console.error('Error submitting exam:', xhr.responseText);
        }
    };
    xhr.send(JSON.stringify(data));
}
