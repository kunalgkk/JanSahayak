import EligibilityForm
    from "../components/EligibilityForm";


function Eligibility() {

    return (

        <div className="page">

            <h1>
                Scheme Eligibility
            </h1>

            <p>
                Enter your details to check
                basic scheme eligibility.
            </p>

            <EligibilityForm />

        </div>
    );
}

export default Eligibility;
