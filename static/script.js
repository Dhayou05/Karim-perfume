const questions = [
    {
        question: "What type of scent do you prefer?",
        answers: ["Floral", "Woody", "Fruity"]
    },
    {
        question: "What is your favorite season?",
        answers: ["Spring", "Summer", "Winter"]
    },
    {
        question: "Do you prefer strong or subtle scents?",
        answers: ["Strong", "Subtle", "Balanced"]
    },
    // Add more questions as needed
];

const questionsDiv = document.getElementById('questions');

questions.forEach((q, index) => {
    const questionElement = document.createElement('div');
    questionElement.innerHTML = `<p>${q.question}</p>`;
    q.answers.forEach(answer => {
        questionElement.innerHTML += `
            <label>
                <input type="radio" name="question${index}" value="${answer}" required>
                ${answer}
            </label><br>
        `;
    });
    questionsDiv.appendChild(questionElement);
});
