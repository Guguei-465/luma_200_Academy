def calculate_cbc_grade(score):
    """
    Calculate CBC Assessment Rubric.
    """

    if score >= 90:
        return "EE1", "Exceeding Expectation"

    elif score >= 75:
        return "EE2", "Exceeding Expectation"

    elif score >= 58:
        return "ME1", "Meeting Expectation"

    elif score >= 41:
        return "ME2", "Meeting Expectation"

    elif score >= 31:
        return "AE1", "Approaching Expectation"

    elif score >= 21:
        return "AE2", "Approaching Expectation"

    elif score >= 11:
        return "BE1", "Below Expectation"

    elif score >= 1:
        return "BE2", "Below Expectation"

    return "N/A", "Not Assessed"