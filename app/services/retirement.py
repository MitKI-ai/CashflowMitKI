"""RetirementService — calculates retirement gap and required savings."""


class RetirementService:
    @staticmethod
    def calculate(
        *,
        current_age: int,
        retirement_age: int,
        life_expectancy: int,
        desired_monthly_income: float,
        expected_pension: float,
        current_savings: float,
        expected_return_pct: float,
    ) -> dict:
        monthly_gap = max(0.0, desired_monthly_income - expected_pension)
        years_to_retirement = max(0, retirement_age - current_age)
        retirement_years = max(0, life_expectancy - retirement_age)

        # Total capital needed at retirement (simple: gap * months in retirement)
        total_needed = monthly_gap * 12 * retirement_years

        # Future value of current savings at retirement
        if expected_return_pct > 0 and years_to_retirement > 0:
            annual_rate = expected_return_pct / 100
            future_value_savings = current_savings * ((1 + annual_rate) ** years_to_retirement)
        else:
            future_value_savings = current_savings

        # Remaining gap after savings grow
        remaining = max(0.0, total_needed - future_value_savings)

        # Monthly savings required to fill the gap
        if years_to_retirement > 0 and remaining > 0:
            months = years_to_retirement * 12
            if expected_return_pct > 0:
                monthly_rate = expected_return_pct / 100 / 12
                # PMT formula: remaining / ((((1+r)^n) - 1) / r)
                factor = ((1 + monthly_rate) ** months - 1) / monthly_rate
                monthly_savings_required = remaining / factor
            else:
                monthly_savings_required = remaining / months
        else:
            monthly_savings_required = 0.0

        return {
            "monthly_gap": round(monthly_gap, 2),
            "years_to_retirement": years_to_retirement,
            "retirement_years": retirement_years,
            "total_needed": round(total_needed, 2),
            "current_savings": round(current_savings, 2),
            "future_value_savings": round(future_value_savings, 2),
            "monthly_savings_required": round(monthly_savings_required, 2),
        }
