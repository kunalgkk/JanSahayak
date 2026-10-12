import { useState } from "react";

function App() {

  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [sources, setSources] = useState([]);
  const [loading, setLoading] = useState(false);

  async function askQuestion() {

    if (!question.trim()) {
      return;
    }

    setLoading(true);
    setAnswer("");
    setSources([]);

    try {

      const response = await fetch(
        "http://127.0.0.1:8000/ask",
        {
          method: "POST",

          headers: {
            "Content-Type": "application/json"
          },

          body: JSON.stringify({
            question: question
          })
        }
      );

      const data = await response.json();

      setAnswer(data.answer || "No answer found.");
      setSources(data.sources || []);

    } catch (error) {

      setAnswer(
        "Could not connect to JanSahayak backend."
      );
    }

    setLoading(false);
  }


  return (

    <div style={styles.container}>

      <div style={styles.card}>

        <h1>JanSahayak AI</h1>

        <p style={styles.subtitle}>
          Government Scheme Assistant
        </p>

        <textarea
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Ask a question about a government scheme..."
          style={styles.textarea}
        />

        <button
          onClick={askQuestion}
          style={styles.button}
        >
          {loading ? "Searching..." : "Ask JanSahayak"}
        </button>


        {answer && (

          <div style={styles.answerBox}>

            <h2>Answer</h2>

            <p>{answer}</p>

            {sources.length > 0 && (

              <div>

                <h3>Sources</h3>

                {sources.map((source, index) => (

                  <p key={index}>
                    📄 {source.document}
                  </p>

                ))}

              </div>

            )}

          </div>

        )}

      </div>

    </div>

  );
}


const styles = {

  container: {

    minHeight: "100vh",

    display: "flex",

    justifyContent: "center",

    alignItems: "center",

    background: "#f3f4f6",

    padding: "20px"

  },

  card: {

    width: "700px",

    background: "white",

    padding: "40px",

    borderRadius: "15px",

    boxShadow: "0 5px 20px rgba(0,0,0,0.1)"

  },

  subtitle: {

    color: "#666"

  },

  textarea: {

    width: "100%",

    height: "120px",

    padding: "15px",

    marginTop: "20px",

    borderRadius: "8px",

    border: "1px solid #ccc",

    fontSize: "16px",

    boxSizing: "border-box"

  },

  button: {

    marginTop: "15px",

    padding: "12px 20px",

    border: "none",

    borderRadius: "8px",

    background: "#2563eb",

    color: "white",

    fontSize: "16px",

    cursor: "pointer"

  },

  answerBox: {

    marginTop: "30px",

    padding: "20px",

    background: "#f9fafb",

    borderRadius: "10px"

  }

};


export default App;
