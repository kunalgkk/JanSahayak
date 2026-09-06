import { Link } from "react-router-dom";

function Navbar() {

    return (
        <nav className="navbar">

            <div className="logo">
                JanSahayak AI
            </div>

            <div className="nav-links">

                <Link to="/">
                    Home
                </Link>

                <Link to="/chat">
                    Ask AI
                </Link>

                <Link to="/eligibility">
                    Eligibility
                </Link>

                <Link to="/summarizer">
                    Summarizer
                </Link>

                <Link to="/admin">
                    Admin
                </Link>

            </div>

        </nav>
    );
}

export default Navbar;
