let language = "en";
let category = "";
let translations = {};

let questions = [];
let currentIndex = 0;
let score = 0;
let answered = false;
let hintUsed = false;


const interfaceText = {
    en: {
        category: "Choose a category",
        question: "Question",
        score: "Score",
        hint: "Hint",
        next: "Next",
        correct: "Correct!",
        wrong: "Wrong!",
        correctAnswer: "Correct answer:",
        completed: "Game completed!",
        finalScore: "Your final score is",
        playAgain: "Play again",
        created: "Created",
        culture: "Culture",
        unavailableHint: "No hint is available."
    },

    ar: {
        category: "اختر الفئة",
        question: "السؤال",
        score: "النتيجة",
        hint: "تلميح",
        next: "التالي",
        correct: "إجابة صحيحة!",
        wrong: "إجابة غير صحيحة",
        correctAnswer: "الإجابة الصحيحة:",
        completed: "انتهت اللعبة!",
        finalScore: "نتيجتك النهائية هي",
        playAgain: "العب مرة أخرى",
        created: "تاريخ الإنشاء",
        culture: "الثقافة",
        unavailableHint: "لا يوجد تلميح متاح."
    }
};


function showScreen(screenId) {
    document.querySelectorAll(".screen").forEach((screen) => {
        screen.classList.remove("active");
    });

    const selectedScreen =
        document.getElementById(screenId);

    if (selectedScreen) {
        selectedScreen.classList.add("active");
    }
}


async function chooseLanguage(selectedLanguage) {
    language = selectedLanguage;

    document.documentElement.lang = language;
    document.documentElement.dir =
        language === "ar" ? "rtl" : "ltr";

    document.querySelectorAll("[data-en]").forEach((element) => {
        const value = element.dataset[language];

        if (value) {
            element.textContent = value;
        }
    });

    document.getElementById("category-heading").textContent =
        interfaceText[language].category;

    document.getElementById("hint-button").textContent =
        interfaceText[language].hint;

    document.getElementById("next-button").textContent =
        interfaceText[language].next;

    document.getElementById("play-again-button").textContent =
        interfaceText[language].playAgain;

    await loadTranslations(language);

    showScreen("category-screen");
}


async function loadTranslations(selectedLanguage) {
    try {
        const response = await fetch(
            `/api/translations/${selectedLanguage}`
        );

        if (!response.ok) {
            throw new Error(
                `Translation unavailable: ${selectedLanguage}`
            );
        }

        translations = await response.json();

    } catch (error) {
        console.warn(error);

        const response = await fetch(
            "/api/translations/en"
        );

        if (!response.ok) {
            throw new Error(
                "English translation file is unavailable."
            );
        }

        translations = await response.json();
    }
}


async function startGame(selectedCategory) {
    category = selectedCategory;
    currentIndex = 0;
    score = 0;
    answered = false;
    hintUsed = false;

    try {
        const response = await fetch(
            `/api/questions/${category}`
        );

        const data = await response.json();

        if (!response.ok) {
            throw new Error(
                data.error ||
                "Questions could not be loaded."
            );
        }

        questions = data.questions;

        if (
            !Array.isArray(questions) ||
            questions.length === 0
        ) {
            throw new Error(
                "No questions are available."
            );
        }

        showScreen("question-screen");
        displayQuestion();

    } catch (error) {
        console.error(error);
        alert(error.message);
    }
}


function displayQuestion() {
    answered = false;
    hintUsed = false;

    const question = questions[currentIndex];

    if (!question) {
        console.error(
            "The current question could not be found."
        );

        return;
    }

    document.getElementById("feedback").textContent = "";
    document.getElementById("context-text").textContent = "";
    document.getElementById("context-text").hidden = true;
    document.getElementById("hint-text").textContent = "";
    document.getElementById("hint-text").hidden = true;
    document.getElementById("next-button").hidden = true;
    document.getElementById("hint-button").disabled = false;

    document.getElementById("question-progress").textContent =
        `${interfaceText[language].question} ` +
        `${currentIndex + 1} / ${questions.length}`;

    document.getElementById("score-display").textContent =
        `${interfaceText[language].score}: ${score}`;

    let questionText =
        translations[question.question_key] ||
        question.question_key ||
        "";

    const continent =
        getLocalizedValue(question.continent);

    questionText = questionText.replace(
        "{continent}",
        continent
    );

    document.getElementById("question-text").textContent =
        questionText;

    const imageFilename = String(
        question.image || ""
    ).replace(
        /^images\//,
        ""
    );

    const artworkImage =
        document.getElementById("artwork-image");

    artworkImage.src =
        `/quiz-images/${imageFilename}`;

    artworkImage.alt =
        language === "ar"
            ? "صورة العمل الفني"
            : "Artwork image";

    const localizedOptions =
        getLocalizedOptions(question.options);

    const correctAnswer =
        getLocalizedValue(question.answer);

    const shuffledOptions =
        shuffleArray([...localizedOptions]);

    displayAnswers(
        shuffledOptions,
        correctAnswer
    );
}


function displayAnswers(options, correctAnswer) {
    const container =
        document.getElementById("answer-container");

    container.innerHTML = "";

    options.forEach((option) => {
        const button =
            document.createElement("button");

        button.type = "button";
        button.className = "answer-button";
        button.textContent = displayText(option);
        button.dataset.rawAnswer = option;

        button.addEventListener("click", () => {
            checkAnswer(
                option,
                correctAnswer,
                button
            );
        });

        container.appendChild(button);
    });
}


async function checkAnswer(
    selectedAnswer,
    correctAnswer,
    selectedButton
) {
    if (answered) {
        return;
    }

    answered = true;

    const isCorrect =
        selectedAnswer === correctAnswer;

    document
        .querySelectorAll(".answer-button")
        .forEach((button) => {
            button.disabled = true;

            if (
                button.dataset.rawAnswer ===
                correctAnswer
            ) {
                button.classList.add("correct");
            }
        });

    const feedback =
        document.getElementById("feedback");

    if (isCorrect) {
        score++;

        selectedButton.classList.add("correct");

        feedback.textContent =
            interfaceText[language].correct;

        await activateLED("correct");

    } else {
        selectedButton.classList.add("wrong");

        feedback.textContent =
            `${interfaceText[language].wrong} ` +
            `${interfaceText[language].correctAnswer} ` +
            `${displayText(correctAnswer)}`;

        await activateLED("wrong");
    }

    document.getElementById("score-display").textContent =
        `${interfaceText[language].score}: ${score}`;

    showContextAfterAnswer();

    document.getElementById("next-button").hidden = false;
}


function showContextAfterAnswer() {
    const question = questions[currentIndex];

    const contextElement =
        document.getElementById("context-text");

    if (
        category === "year" ||
        category === "origin"
    ) {
        const context =
            getLocalizedValue(question.context);

        if (context) {
            contextElement.textContent = context;
            contextElement.hidden = false;
        }
    }
}


function showHint() {
    if (hintUsed) {
        return;
    }

    hintUsed = true;

    const question = questions[currentIndex];

    let hint =
        getLocalizedValue(
            question.did_you_know
        );

    /*
    Temporary fallback for questions that do not
    have did_you_know in the JSON yet.
    */
    if (
        !hint &&
        (
            category === "title" ||
            category === "medium"
        )
    ) {
        const creationDate =
            getLocalizedValue(
                question.creation_date
            );

        const culture =
            getLocalizedValue(
                question.culture
            );

        const hintParts = [];

        if (creationDate) {
            hintParts.push(
                `${interfaceText[language].created}: ` +
                creationDate
            );
        }

        if (culture) {
            hintParts.push(
                `${interfaceText[language].culture}: ` +
                culture
            );
        }

        hint = hintParts.join(" | ");
    }

    if (!hint) {
        hint =
            interfaceText[language].unavailableHint;
    }

    const hintElement =
        document.getElementById("hint-text");

    hintElement.textContent = hint;
    hintElement.hidden = false;

    document.getElementById(
        "hint-button"
    ).disabled = true;
}


async function activateLED(result) {
    try {
        const response = await fetch(
            `/api/led/${result}`,
            {
                method: "POST"
            }
        );

        if (!response.ok) {
            throw new Error(
                `LED request failed: ${result}`
            );
        }

    } catch (error) {
        console.error(
            "LED request failed:",
            error
        );
    }
}


function nextQuestion() {
    if (!answered) {
        return;
    }

    currentIndex++;

    if (currentIndex >= questions.length) {
        showResults();
        return;
    }

    displayQuestion();
}


function showResults() {
    document.getElementById(
        "result-heading"
    ).textContent =
        interfaceText[language].completed;

    document.getElementById(
        "final-score"
    ).textContent =
        `${interfaceText[language].finalScore} ` +
        `${score} / ${questions.length}`;

    showScreen("result-screen");
}


function returnToCategories() {
    questions = [];
    currentIndex = 0;
    score = 0;
    answered = false;
    hintUsed = false;

    showScreen("category-screen");
}


function displayText(value) {
    const text = String(value || "");

    if (!text) {
        return "";
    }

    if (language === "ar") {
        return text;
    }

    return (
        text.charAt(0).toUpperCase() +
        text.slice(1)
    );
}


function getLocalizedValue(value) {
    if (
        value === null ||
        value === undefined
    ) {
        return "";
    }

    /*
    New bilingual format:

    {
        "en": "English value",
        "ar": "القيمة العربية"
    }
    */
    if (
        typeof value === "object" &&
        !Array.isArray(value)
    ) {
        return (
            value[language] ||
            value.en ||
            ""
        );
    }

    /*
    Old English-only format:

    "English value"
    */
    return value;
}


function getLocalizedOptions(options) {
    if (!options) {
        return [];
    }

    /*
    Old English-only format:

    [
        "Option 1",
        "Option 2"
    ]
    */
    if (Array.isArray(options)) {
        return options;
    }

    /*
    New bilingual format:

    {
        "en": ["Option 1", "Option 2"],
        "ar": ["الخيار 1", "الخيار 2"]
    }
    */
    return (
        options[language] ||
        options.en ||
        []
    );
}


function shuffleArray(array) {
    for (
        let index = array.length - 1;
        index > 0;
        index--
    ) {
        const randomIndex =
            Math.floor(
                Math.random() * (index + 1)
            );

        [
            array[index],
            array[randomIndex]
        ] = [
            array[randomIndex],
            array[index]
        ];
    }

    return array;
}