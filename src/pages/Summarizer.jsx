import { useState } from "react";

import {
    summarizeDocument
} from "../services/api";


function Summarizer() {

    const [text, setText] =
        useState("");

    const [summary, setSummary] =
        useState("");


    async function summarize() {

        if (!text.trim()) {
            return;
        }

        const result =
            await summarizeDocument(text);

        setSummary(
            result.summary || ""
        );
    }


    return (

        <div className="page">

            <h1>
                Government Document Summarizer
            </h1>

            <textarea
                value={text}
                onChange={
                    e =>
                        setText(e.target.value)
                }
                placeholder="Paste government document text here..."
                className="large-textarea"
            />

            <button
                onClick={summarize}
            >
                Summarize
            </button>


            {summary && (

                <div className="summary-card">

                    <h2>
                        Summary
                    </h2>

                    <p>
                        {summary}
                    </p>

                </div>

            )}

        </div>
    );
}

export default Summarizer;
