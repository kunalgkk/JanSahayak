import { useState } from "react";

import { askQuestion } from "../services/api";

import Message from "./Message";
import Loading from "./Loading";


function ChatBox() {

    const [question, setQuestion] = useState("");

    const [messages, setMessages] = useState([]);

    const [loading, setLoading] = useState(false);


    async function sendQuestion() {

        if (!question.trim()) {
            return;
        }

        const userMessage = {
            sender: "user",
            text: question,
        };

        setMessages(
            previous => [
                ...previous,
                userMessage
            ]
        );

        setQuestion("");

        setLoading(true);


        try {

            const result =
                await askQuestion(
                    question
                );


            const botMessage = {

                sender: "bot",

                text:
                    result.answer ||
                    "No information found.",

                sources:
                    result.sources || []

            };


            setMessages(
                previous => [
                    ...previous,
                    botMessage
                ]
            );

        } catch (error) {

            setMessages(
                previous => [
                    ...previous,
                    {
                        sender: "bot",
                        text:
                            "Unable to connect to the server."
                    }
                ]
            );

        } finally {

            setLoading(false);

        }
    }


    return (

        <div className="chat-container">

            <div className="messages">

                {messages.map(
                    (message, index) => (

                        <Message
                            key={index}
                            message={message}
                        />

                    )
                )}

                {loading && <Loading />}

            </div>


            <div className="chat-input">

                <input
                    type="text"
                    value={question}
                    placeholder="Ask about a government scheme..."
                    onChange={
                        e =>
                            setQuestion(e.target.value)
                    }
                    onKeyDown={
                        e => {
                            if (e.key === "Enter") {
                                sendQuestion();
                            }
                        }
                    }
                />

                <button
                    onClick={sendQuestion}
                    disabled={loading}
                >
                    Ask
                </button>

            </div>

        </div>
    );
}

export default ChatBox;
