import SourceCard from "./SourceCard";

function Message({ message }) {

    return (

        <div
            className={
                message.sender === "user"
                    ? "message user-message"
                    : "message bot-message"
            }
        >

            <div className="message-header">

                {message.sender === "user"
                    ? "You"
                    : "JanSahayak AI"}

            </div>

            <p>
                {message.text}
            </p>


            {message.sources &&
                message.sources.length > 0 && (

                <div className="sources">

                    <h4>
                        Sources
                    </h4>

                    {message.sources.map(
                        (source, index) => (

                            <SourceCard
                                key={index}
                                source={source}
                            />

                        )
                    )}

                </div>

            )}

        </div>
    );
}

export default Message;
