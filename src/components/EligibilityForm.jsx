import { useState } from "react";

import { checkEligibility }
    from "../services/api";


function EligibilityForm() {

    const [form, setForm] = useState({

        scheme: "",
        age: "",
        occupation: "",
        income: "",
        education: ""

    });


    const [result, setResult] =
        useState(null);


    function handleChange(event) {

        setForm({

            ...form,

            [event.target.name]:
                event.target.value

        });
    }


    async function submit(event) {

        event.preventDefault();

        const result =
            await checkEligibility({
                ...form,
                age: form.age
                    ? Number(form.age)
                    : null,
                income: form.income
                    ? Number(form.income)
                    : null
            });

        setResult(result);
    }


    return (

        <div className="eligibility-container">

            <form onSubmit={submit}>

                <label>
                    Scheme
                </label>

                <select
                    name="scheme"
                    value={form.scheme}
                    onChange={handleChange}
                    required
                >

                    <option value="">
                        Select Scheme
                    </option>

                    <option value="pm kisan">
                        PM Kisan
                    </option>

                    <option value="scholarship">
                        PM Scholarship
                    </option>

                    <option value="ayushman">
                        Ayushman Bharat
                    </option>

                </select>


                <label>
                    Age
                </label>

                <input
                    name="age"
                    type="number"
                    value={form.age}
                    onChange={handleChange}
                />


                <label>
                    Occupation
                </label>

                <input
                    name="occupation"
                    value={form.occupation}
                    placeholder="e.g. farmer"
                    onChange={handleChange}
                />


                <label>
                    Annual Income
                </label>

                <input
                    name="income"
                    type="number"
                    value={form.income}
                    onChange={handleChange}
                />


                <label>
                    Education
                </label>

                <input
                    name="education"
                    value={form.education}
                    placeholder="e.g. student"
                    onChange={handleChange}
                />


                <button type="submit">
                    Check Eligibility
                </button>

            </form>


            {result && (

                <div className="eligibility-result">

                    <h2>
                        Result
                    </h2>

                    <h3>

                        {result.eligible
                            ? "Potentially Eligible"
                            : "Not Eligible"}

                    </h3>


                    <p>
                        {Array.isArray(result.reason)
                            ? result.reason.join(", ")
                            : result.reason}
                    </p>

                </div>

            )}

        </div>
    );
}

export default EligibilityForm;
