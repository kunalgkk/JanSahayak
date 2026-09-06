const API_URL = "http://127.0.0.1:8000";

export async function askQuestion(question) {
    const response = await fetch(`${API_URL}/ask`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({
            question: question,
        }),
    });

    return await response.json();
}


export async function checkEligibility(data) {
    const response = await fetch(
        `${API_URL}/eligibility`,
        {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify(data),
        }
    );

    return await response.json();
}


export async function summarizeDocument(text) {
    const response = await fetch(
        `${API_URL}/summarize`,
        {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                text: text,
            }),
        }
    );

    return await response.json();
}


export async function uploadDocument(file) {

    const formData = new FormData();

    formData.append("file", file);

    const response = await fetch(
        `${API_URL}/upload`,
        {
            method: "POST",
            body: formData,
        }
    );

    return await response.json();
}
