import { useState } from "react";

import {
    uploadDocument
} from "../services/api";


function Admin() {

    const [file, setFile] =
        useState(null);

    const [message, setMessage] =
        useState("");


    async function upload() {

        if (!file) {
            setMessage(
                "Please select a document."
            );
            return;
        }

        try {

            const result =
                await uploadDocument(file);

            setMessage(
                result.message
            );

        } catch {

            setMessage(
                "Upload failed."
            );

        }
    }


    return (

        <div className="page">

            <h1>
                Admin Dashboard
            </h1>

            <p>
                Upload official government documents.
            </p>

            <div className="upload-box">

                <input
                    type="file"
                    accept=".pdf,.txt"
                    onChange={
                        e =>
                            setFile(
                                e.target.files[0]
                            )
                    }
                />

                <button
                    onClick={upload}
                >
                    Upload Document
                </button>

            </div>


            {message && (

                <p className="upload-message">
                    {message}
                </p>

            )}

        </div>
    );
}

export default Admin;
