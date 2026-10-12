import { Link } from "react-router-dom";

function Home() {

    return (

        <div className="home">

            <section className="hero">

                <h1>
                    Welcome to JanSahayak AI
                </h1>

                <p>
                    Your AI assistant for
                    understanding government schemes
                    and official documents.
                </p>

                <Link
                    to="/chat"
                    className="primary-button"
                >
                    Ask JanSahayak
                </Link>

            </section>


            <section className="features">

                <div className="feature-card">

                    <h2>🤖 AI Q&A</h2>

                    <p>
                        Ask questions in natural language
                        and find relevant information.
                    </p>

                </div>


                <div className="feature-card">

                    <h2>✅ Eligibility</h2>

                    <p>
                        Check your eligibility based on
                        scheme criteria.
                    </p>

                </div>


                <div className="feature-card">

                    <h2>📄 Summarization</h2>

                    <p>
                        Convert long government documents
                        into easy-to-understand summaries.
                    </p>

                </div>


                <div className="feature-card">

                    <h2>🔎 Sources</h2>

                    <p>
                        View the documents used to generate
                        an answer.
                    </p>

                </div>

            </section>

        </div>
    );
}

export default Home;
