function SourceCard({ source }) {

    return (
        <div className="source-card">

            <div className="source-icon">
                📄
            </div>

            <div>

                <h4>
                    {source.document}
                </h4>

                <p>
                    Relevance Score: {source.score}
                </p>

            </div>

        </div>
    );
}

export default SourceCard;
