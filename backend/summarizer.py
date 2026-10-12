def summarize_text(text, sentence_count=3):

    sentences = text.replace("!", ".").replace("?", ".").split(".")

    sentences = [
        sentence.strip()
        for sentence in sentences
        if sentence.strip()
    ]

    summary = sentences[:sentence_count]

    return ". ".join(summary) + "."
