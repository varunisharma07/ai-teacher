const API = "http://localhost:8001";

let currentUser = null;


/* =========================================================
   PAGE CONTROL
========================================================= */

function showPage(pageId) {
    document.querySelectorAll(".page").forEach(page => {
        page.classList.remove("active");
    });

    const page = document.getElementById(pageId);

    if (page) {
        page.classList.add("active");
    }
}


function showAuth(type) {
    showPage("authPage");
    toggleAuth(type);
}


function toggleAuth(type) {
    const login = document.getElementById("loginForm");
    const signup = document.getElementById("signupForm");

    if (!login || !signup) return;

    if (type === "signup") {
        login.classList.add("hidden");
        signup.classList.remove("hidden");
    } else {
        signup.classList.add("hidden");
        login.classList.remove("hidden");
    }
}


/* =========================================================
   AUTH
========================================================= */

async function signup() {

    const name =
        document.getElementById("signupName").value.trim();

    const email =
        document.getElementById("signupEmail").value.trim();

    const password =
        document.getElementById("signupPassword").value;

    if (!name || !email || !password) {
        showToast("Please fill all fields.");
        return;
    }

    try {

        const response = await fetch(`${API}/signup`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                name: name,
                email: email,
                password: password
            })
        });

        const data = await response.json();

        if (!response.ok) {
            showToast(data.detail || "Signup failed ❌");
            return;
        }

        currentUser = {
            ...data,
            isNew: true
        };

        localStorage.setItem(
            "aiTeacherUser",
            JSON.stringify(currentUser)
        );

        showToast("Account created! 🎉");

        showPage("onboardingPage");

    } catch (error) {

        console.error("SIGNUP ERROR:", error);

        showToast("Cannot connect to server ❌");
    }
}


async function login() {

    const email =
        document.getElementById("loginEmail").value.trim();

    const password =
        document.getElementById("loginPassword").value;

    if (!email || !password) {
        showToast("Please enter email and password.");
        return;
    }

    try {

        const response = await fetch(`${API}/login`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                name: "User",
                email: email,
                password: password
            })
        });

        const data = await response.json();

        if (!response.ok) {
            showToast(
                data.detail || "Invalid email or password ❌"
            );
            return;
        }

        currentUser = {
            ...data,
            isNew: false
        };

        localStorage.setItem(
            "aiTeacherUser",
            JSON.stringify(currentUser)
        );

        showToast("Welcome back! 👋");

        openDashboard();

    } catch (error) {

        console.error("LOGIN ERROR:", error);

        showToast("Cannot connect to server ❌");
    }
}


function logout() {

    localStorage.removeItem("aiTeacherUser");

    currentUser = null;

    stopTeacherSpeaking();

    showPage("landingPage");
}


/* =========================================================
   ONBOARDING
========================================================= */

function selectChoice(element) {
    element.classList.toggle("selected");
}


function finishOnboarding() {

    if (!currentUser) return;

    currentUser.isNew = false;

    localStorage.setItem(
        "aiTeacherUser",
        JSON.stringify(currentUser)
    );

    openDashboard();
}


/* =========================================================
   DASHBOARD
========================================================= */

function openDashboard() {

    if (!currentUser) {
        showPage("landingPage");
        return;
    }

    updateUserUI();

    showPage("appPage");

    showSection("dashboard");

    loadDocuments();
}


function updateUserUI() {

    const name =
        currentUser.name || "Student";

    const initial =
        name.charAt(0).toUpperCase();

    const welcomeName =
        document.getElementById("welcomeName");

    const sidebarName =
        document.getElementById("sidebarName");

    const sidebarAvatar =
        document.getElementById("sidebarAvatar");

    const profileAvatar =
        document.querySelector(".profile-avatar");

    const profileAvatar2 =
        document.getElementById("profileAvatar");

    const profileName =
        document.getElementById("profileName");

    const profileEmail =
        document.getElementById("profileEmail");

    if (welcomeName)
        welcomeName.textContent = name;

    if (sidebarName)
        sidebarName.textContent = name;

    if (sidebarAvatar)
        sidebarAvatar.textContent = initial;

    if (profileAvatar)
        profileAvatar.textContent = initial;

    if (profileAvatar2)
        profileAvatar2.textContent = initial;

    if (profileName)
        profileName.textContent = name;

    if (profileEmail)
        profileEmail.textContent =
            currentUser.email || "student@example.com";
}


/* =========================================================
   NAVIGATION
========================================================= */

function showSection(sectionId, button = null) {

    document.querySelectorAll(".app-section")
        .forEach(section => {
            section.classList.remove("active-section");
        });

    const section =
        document.getElementById(sectionId);

    if (section) {
        section.classList.add("active-section");
    }

    document.querySelectorAll(".side-link")
        .forEach(link => {
            link.classList.remove("active");
        });

    if (button) {
        button.classList.add("active");
    }

    document.querySelector(".sidebar")
        ?.classList.remove("mobile-open");

    window.scrollTo({
        top: 0,
        behavior: "smooth"
    });
}


function toggleSidebar() {

    document.querySelector(".sidebar")
        ?.classList.toggle("mobile-open");
}


/* =========================================================
   FILE UPLOAD
========================================================= */

const documentInput =
    document.getElementById("documentInput");

if (documentInput) {
    documentInput.addEventListener(
        "change",
        uploadDocument
    );
}


async function uploadDocument() {

    const file =
        documentInput.files[0];

    if (!file) return;

    const documentId =
        crypto.randomUUID();

    const formData =
        new FormData();

    formData.append("file", file);

    formData.append(
        "document_id",
        documentId
    );

    const status =
        document.getElementById("uploadStatus");

    if (status) {
        status.classList.remove("hidden");

        status.textContent =
            `Processing "${file.name}"...`;
    }

    try {

        const response =
            await fetch(
                `${API}/upload-document`,
                {
                    method: "POST",
                    body: formData
                }
            );

        const data =
            await response.json();

        if (!response.ok) {
            throw new Error(
                data.detail || "Upload failed"
            );
        }

        if (status) {
            status.textContent =
                "✓ Study material processed successfully!";
        }

        showToast(
            "Study material added 📚"
        );

        loadDocuments();

    } catch (error) {

        console.error(
            "UPLOAD ERROR:",
            error
        );

        if (status) {
            status.textContent =
                "Could not connect to AI Teacher backend.";
        }

        showToast(
            "Backend connection failed ❌"
        );
    }

    documentInput.value = "";
}


/* =========================================================
   DOCUMENTS
========================================================= */

async function loadDocuments() {

    try {

        const response =
            await fetch(
                `${API}/list-documents`
            );

        if (!response.ok) return;

        const data =
            await response.json();

        const documents =
            data.document_ids ||
            data.documents ||
            data;

        if (!Array.isArray(documents)) {
            return;
        }

        const list =
            document.getElementById(
                "documentsList"
            );

        const subjects =
            document.getElementById(
                "subjectGrid"
            );

        const lessonCount =
            document.getElementById(
                "lessonCount"
            );

        if (lessonCount) {
            lessonCount.textContent =
                documents.length;
        }

        if (!list || !subjects) return;

        if (documents.length === 0) {
            list.innerHTML =
                "<p>No study material yet.</p>";

            subjects.innerHTML =
                "<p>Upload your first document.</p>";

            return;
        }

        list.innerHTML =
            documents.map(doc => {

                const id =
                    typeof doc === "string"
                        ? doc
                        : doc.document_id;

                return `
                    <div
                        class="quick-action"
                        onclick="openLesson('${id}')"
                    >
                        <span>📘</span>

                        <div>
                            <strong>${id}</strong>

                            <small>
                                Ready to learn
                            </small>
                        </div>

                        <b>→</b>
                    </div>
                `;

            }).join("");

        subjects.innerHTML =
            documents.map(doc => {

                const id =
                    typeof doc === "string"
                        ? doc
                        : doc.document_id;

                return `
                    <div class="subject-card">

                        <div class="subject-icon">
                            📚
                        </div>

                        <h3>${id}</h3>

                        <p>
                            Your AI Teacher can explain
                            this material.
                        </p>

                        <button
                            class="primary-btn"
                            onclick="openLesson('${id}')"
                        >
                            Start Learning →
                        </button>

                    </div>
                `;

            }).join("");

    } catch (error) {

        console.error(
            "DOCUMENT ERROR:",
            error
        );
    }
}


/* =========================================================
   AI TEACHER LESSON
========================================================= */

async function openLesson(documentId) {

    const topic =
        prompt(
            "What topic do you want to learn from this material?"
        );

    if (!topic) return;

    stopTeacherSpeaking();

    const currentLesson =
        document.getElementById(
            "currentLesson"
        );

    if (currentLesson) {
        currentLesson.textContent =
            topic;
    }

    showSection("teacher");

    showToast(
        "Creating your lesson 🤖..."
    );

    const lessonContent =
        document.getElementById(
            "lessonContent"
        );

    if (lessonContent) {

        lessonContent.innerHTML = `
            <div class="lesson-scene">

                <h3>
                    Preparing your AI lesson...
                </h3>

                <p class="scene-narration">
                    Your teacher is reading your
                    study material and creating
                    a personalized explanation.
                </p>

            </div>
        `;
    }

    try {

        const response =
            await fetch(
                `${API}/plan-lesson`,
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({

                        topic: topic,

                        level: "beginner",

                        time_minutes: 20,

                        language: "English",

                        document_id:
                            documentId
                    })
                }
            );

        const data =
            await response.json();

        if (!response.ok) {

            throw new Error(
                data.detail ||
                "Failed to create lesson"
            );
        }

        console.log(
            "LESSON PLAN:",
            data
        );


        /* ============================
           SHOW EXPLANATION
        ============================ */

        if (
            lessonContent &&
            data.scenes
        ) {

            lessonContent.innerHTML =
                data.scenes.map(scene => {

                    return `
                        <div
                            class="lesson-scene"
                        >

                            <h3>
                                Scene
                                ${scene.scene_number}
                            </h3>

                            <p
                                class="scene-narration"
                            >
                                ${scene.narration}
                            </p>

                            <div
                                class="scene-visual"
                            >
                                <strong>
                                    Visual:
                                </strong>

                                ${scene.visual_description}
                            </div>

                            ${
                                scene.checkpoint_question
                                ? `
                                    <div
                                        class="checkpoint"
                                    >
                                        <strong>
                                            Quick Check:
                                        </strong>

                                        ${scene.checkpoint_question}
                                    </div>
                                `
                                : ""
                            }

                        </div>
                    `;

                }).join("");
        }


        /* ============================
           MAKE TEACHER SPEAK
        ============================ */

        if (
            data.scenes &&
            data.scenes.length > 0
        ) {

            const fullExplanation =
                data.scenes
                    .map(scene =>
                        scene.narration
                    )
                    .join(" ");

            startTeacherSpeaking(
                fullExplanation
            );
        }

        showToast(
            "Lesson ready! 🎓"
        );

    } catch (error) {

        console.error(
            "LESSON ERROR:",
            error
        );

        if (lessonContent) {

            lessonContent.innerHTML = `
                <div class="lesson-scene">

                    <h3>
                        Couldn't create lesson
                    </h3>

                    <p class="scene-narration">
                        ${error.message}
                    </p>

                </div>
            `;
        }

        showToast(
            "Could not create lesson ❌"
        );
    }
}


/* =========================================================
   ANIMATED AI TEACHER SPEECH
========================================================= */

let teacherSpeaking = false;
let teacherSpeech = null;


function startTeacherSpeaking(text) {

    const avatar =
        document.querySelector(
            ".ai-teacher-avatar"
        );

    const status =
        document.getElementById(
            "teacherStatus"
        );

    if (!avatar || !text) {
        return;
    }

    if (
        !("speechSynthesis" in window)
    ) {
        if (status) {
            status.textContent =
                "Your AI Teacher is ready";
        }

        return;
    }

    window.speechSynthesis.cancel();

    teacherSpeech =
        new SpeechSynthesisUtterance(
            text
        );

    teacherSpeech.rate = 0.95;
    teacherSpeech.pitch = 1.05;
    teacherSpeech.volume = 1;

    teacherSpeech.onstart = () => {

        teacherSpeaking = true;

        avatar.classList.add(
            "speaking"
        );

        if (status) {
            status.textContent =
                "AI Teacher is explaining...";
        }
    };


    teacherSpeech.onend = () => {

        teacherSpeaking = false;

        avatar.classList.remove(
            "speaking"
        );

        if (status) {
            status.textContent =
                "Explanation complete";
        }
    };


    teacherSpeech.onerror = () => {

        teacherSpeaking = false;

        avatar.classList.remove(
            "speaking"
        );

        if (status) {
            status.textContent =
                "Your AI Teacher is ready";
        }
    };


    window.speechSynthesis.speak(
        teacherSpeech
    );
}


function stopTeacherSpeaking() {

    if (
        "speechSynthesis" in window
    ) {
        window.speechSynthesis.cancel();
    }

    const avatar =
        document.querySelector(
            ".ai-teacher-avatar"
        );

    if (avatar) {
        avatar.classList.remove(
            "speaking"
        );
    }

    teacherSpeaking = false;
}


function toggleTeacher() {

    if (teacherSpeaking) {

        stopTeacherSpeaking();

        const status =
            document.getElementById(
                "teacherStatus"
            );

        if (status) {
            status.textContent =
                "Your AI Teacher is ready";
        }

        return;
    }

    const topic =
        document.getElementById(
            "currentLesson"
        )?.textContent;

    if (topic) {

        const scenes =
            document.querySelectorAll(
                ".scene-narration"
            );

        const text =
            Array.from(scenes)
                .map(scene =>
                    scene.textContent
                )
                .join(" ");

        if (text) {
            startTeacherSpeaking(text);
        }
    }
}


/* =========================================================
   QUIZ
========================================================= */

let quizScore = 0;
let quizAnswered = 0;


function startQuiz() {

    quizScore = 0;
    quizAnswered = 0;
}


async function generateQuiz() {

    const topic =
        document.getElementById(
            "currentLesson"
        )?.textContent;

    if (
        !topic ||
        topic === "Select a lesson"
    ) {
        showToast(
            "Open a lesson first 📚"
        );

        return;
    }

    stopTeacherSpeaking();

    startQuiz();

    const lessonContent =
        document.getElementById(
            "lessonContent"
        );

    if (lessonContent) {

        lessonContent.innerHTML = `
            <div class="lesson-scene">

                <h3>
                    🧠 Generating Quiz...
                </h3>

                <p class="scene-narration">
                    Let's see what you remember!
                </p>

            </div>
        `;
    }

    try {

        const response =
            await fetch(
                `${API}/generate-quiz`,
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({

                        topic: topic,

                        lesson_summary: topic,

                        num_questions: 3
                    })
                }
            );

        const data =
            await response.json();

        if (!response.ok) {

            throw new Error(
                data.detail ||
                "Quiz generation failed"
            );
        }


        lessonContent.innerHTML = `

            <div class="quiz-container">

                <div class="quiz-header">

                    <span class="eyebrow">
                        QUICK QUIZ
                    </span>

                    <h2>
                        Test your understanding 🧠
                    </h2>

                </div>

                ${data.questions.map(
                    (q, index) => `

                    <div class="quiz-question">

                        <h3>
                            ${index + 1}.
                            ${q.question}
                        </h3>

                        <div class="quiz-options">

                            ${q.options.map(
                                option => {

                                    const safeOption =
                                        option
                                            .replace(
                                                /'/g,
                                                "\\'"
                                            );

                                    const safeAnswer =
                                        q.answer
                                            .replace(
                                                /'/g,
                                                "\\'"
                                            );

                                    return `

                                        <button
                                            class="quiz-option"
                                            onclick="checkAnswer(
                                                this,
                                                '${safeOption}',
                                                '${safeAnswer}'
                                            )"
                                        >
                                            ${option}
                                        </button>

                                    `;

                                }
                            ).join("")}

                        </div>

                    </div>

                `
                ).join("")}

            </div>
        `;

        showToast(
            "Quiz ready! 🧠"
        );

    } catch (error) {

        console.error(
            "QUIZ ERROR:",
            error
        );

        lessonContent.innerHTML = `

            <div class="lesson-scene">

                <h3>
                    Quiz couldn't load ❌
                </h3>

                <p>
                    ${error.message}
                </p>

            </div>
        `;
    }
}


/* =========================================================
   QUIZ ANSWERS
========================================================= */

async function checkAnswer(
    button,
    selected,
    correct
) {

    const buttons =
        button.parentElement
            .querySelectorAll(
                ".quiz-option"
            );

    buttons.forEach(btn => {
        btn.disabled = true;
    });

    quizAnswered++;


    if (selected === correct) {

        button.classList.add(
            "correct"
        );

        quizScore++;

        showToast(
            "Correct! 🎉"
        );

    } else {

        button.classList.add(
            "wrong"
        );

        showToast(
            "Not quite — keep learning! 💡"
        );

        buttons.forEach(btn => {

            if (
                btn.textContent.trim() ===
                correct
            ) {

                btn.classList.add(
                    "correct"
                );
            }
        });
    }


    const totalQuestions =
        document.querySelectorAll(
            ".quiz-question"
        ).length;


    if (
        quizAnswered ===
        totalQuestions
    ) {

        await saveQuizScore(
            quizScore,
            totalQuestions
        );
    }
}


/* =========================================================
   SAVE QUIZ SCORE
========================================================= */

async function saveQuizScore(
    score,
    total
) {

    const user =
        currentUser ||
        JSON.parse(
            localStorage.getItem(
                "aiTeacherUser"
            )
        );

    if (!user) return;

    const topic =
        document.getElementById(
            "currentLesson"
        )?.textContent ||
        "Unknown Topic";

    if (!user.user_id) {
        console.warn(
            "No user_id available for quiz score."
        );
        return;
    }

    try {

        const response =
            await fetch(
                `${API}/quiz-score`,
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({

                        user_id:
                            user.user_id,

                        topic:
                            topic,

                        score:
                            score,

                        total:
                            total
                    })
                }
            );

        const data =
            await response.json();

        if (response.ok) {

            showToast(
                `Quiz complete! ${data.percentage}% 🎉`
            );

        } else {

            console.error(
                "QUIZ SCORE ERROR:",
                data
            );
        }

    } catch (error) {

        console.error(
            "QUIZ SCORE ERROR:",
            error
        );
    }
}


/* =========================================================
   CHAT WITH AI TEACHER
========================================================= */

async function sendTeacherMessage() {

    const input =
        document.querySelector(
            ".chat-input input"
        );

    if (!input) return;

    const message =
        input.value.trim();

    if (!message) return;

    const topic =
        document.getElementById(
            "currentLesson"
        )?.textContent ||
        "General";

    const chatBox =
        document.querySelector(
            ".teacher-chat"
        );

    if (!chatBox) return;


    /* Student message */

    chatBox.insertAdjacentHTML(
        "beforeend",
        `
        <div class="chat-message student-message">

            <div class="chat-avatar">
                👤
            </div>

            <div>

                <strong>
                    You
                </strong>

                <p>
                    ${message}
                </p>

            </div>

        </div>
        `
    );


    input.value = "";


    /* Thinking message */

    chatBox.insertAdjacentHTML(
        "beforeend",
        `
        <div
            class="chat-message teacher-message"
            id="thinkingMessage"
        >

            <div class="chat-avatar">
                ✦
            </div>

            <div>

                <strong>
                    AI Teacher
                </strong>

                <p>
                    Thinking... 🤔
                </p>

            </div>

        </div>
        `
    );


    chatBox.scrollTop =
        chatBox.scrollHeight;


    try {

        const response =
            await fetch(
                `${API}/chat`,
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({

                        topic:
                            topic,

                        message:
                            message
                    })
                }
            );

        const data =
            await response.json();


        document
            .getElementById(
                "thinkingMessage"
            )
            ?.remove();


        const reply =
            data.reply ||
            "I couldn't generate a response.";


        chatBox.insertAdjacentHTML(
            "beforeend",
            `
            <div
                class="chat-message teacher-message"
            >

                <div class="chat-avatar">
                    ✦
                </div>

                <div>

                    <strong>
                        AI Teacher
                    </strong>

                    <p>
                        ${reply}
                    </p>

                </div>

            </div>
            `
        );


        chatBox.scrollTop =
            chatBox.scrollHeight;


        /* Make teacher speak the reply */

        startTeacherSpeaking(
            reply
        );


    } catch (error) {

        document
            .getElementById(
                "thinkingMessage"
            )
            ?.remove();


        chatBox.insertAdjacentHTML(
            "beforeend",
            `
            <div
                class="chat-message teacher-message"
            >

                <div class="chat-avatar">
                    ✦
                </div>

                <div>

                    <strong>
                        AI Teacher
                    </strong>

                    <p>
                        Sorry, I couldn't connect
                        to the teacher right now. ❌
                    </p>

                </div>

            </div>
            `
        );


        console.error(
            "CHAT ERROR:",
            error
        );
    }
}


/* =========================================================
   TOAST
========================================================= */

function showToast(message) {

    const toast =
        document.getElementById(
            "toast"
        );

    if (!toast) return;

    toast.textContent =
        message;

    toast.classList.add(
        "show"
    );

    setTimeout(() => {

        toast.classList.remove(
            "show"
        );

    }, 3000);
}


/* =========================================================
   STARTUP
========================================================= */

window.addEventListener(
    "DOMContentLoaded",
    () => {

        const savedUser =
            localStorage.getItem(
                "aiTeacherUser"
            );

        if (savedUser) {

            try {

                currentUser =
                    JSON.parse(
                        savedUser
                    );

            } catch (error) {

                localStorage.removeItem(
                    "aiTeacherUser"
                );

                currentUser = null;
            }
        }
    }
);
