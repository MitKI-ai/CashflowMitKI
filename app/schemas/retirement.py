from datetime import datetime

from pydantic import BaseModel


class RetirementProfileUpdate(BaseModel):
    current_age: int | None = None
    retirement_age: int | None = None
    life_expectancy: int | None = None
    desired_monthly_income: float | None = None
    expected_pension: float | None = None
    current_savings: float | None = None
    expected_return_pct: float | None = None


class RetirementProfileResponse(BaseModel):
    id: str
    current_age: int
    retirement_age: int
    life_expectancy: int
    desired_monthly_income: float
    expected_pension: float
    current_savings: float
    expected_return_pct: float

    model_config = {"from_attributes": True}


class RetirementCalculation(BaseModel):
    monthly_gap: float
    years_to_retirement: int
    retirement_years: int
    total_needed: float
    current_savings: float
    future_value_savings: float
    monthly_savings_required: float
