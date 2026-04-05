from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_tenant_id, get_current_user
from app.models.retirement_profile import RetirementProfile
from app.models.user import User
from app.schemas.retirement import RetirementCalculation, RetirementProfileResponse, RetirementProfileUpdate
from app.services.retirement import RetirementService

router = APIRouter(prefix="/retirement", tags=["retirement"])


def _get_or_create_profile(db: Session, user: User, tenant_id: str) -> RetirementProfile:
    profile = db.query(RetirementProfile).filter(RetirementProfile.user_id == user.id).first()
    if not profile:
        profile = RetirementProfile(tenant_id=tenant_id, user_id=user.id)
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return profile


@router.get("/profile", response_model=RetirementProfileResponse)
def get_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant_id),
):
    return _get_or_create_profile(db, current_user, tenant_id)


@router.put("/profile", response_model=RetirementProfileResponse)
def update_profile(
    data: RetirementProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant_id),
):
    profile = _get_or_create_profile(db, current_user, tenant_id)
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(profile, field, value)
    db.commit()
    db.refresh(profile)
    return profile


@router.get("/calculate")
def calculate_retirement(
    inflation: float = Query(2.0, description="Annual inflation rate in %"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant_id),
):
    profile = _get_or_create_profile(db, current_user, tenant_id)
    result = RetirementService.calculate(
        current_age=profile.current_age,
        retirement_age=profile.retirement_age,
        life_expectancy=profile.life_expectancy,
        desired_monthly_income=profile.desired_monthly_income,
        expected_pension=profile.expected_pension,
        current_savings=profile.current_savings,
        expected_return_pct=profile.expected_return_pct,
    )
    # Add inflation-adjusted values
    years = max(0, profile.retirement_age - profile.current_age)
    infl = inflation / 100
    if infl > 0 and years > 0:
        factor = (1 + infl) ** years
        result["real_monthly_gap"] = round(result["monthly_gap"] * factor, 2)
        result["real_total_needed"] = round(result["total_needed"] * factor, 2)
    else:
        result["real_monthly_gap"] = result["monthly_gap"]
        result["real_total_needed"] = result["total_needed"]
    result["inflation_rate"] = inflation
    return result


@router.get("/scenarios")
def retirement_scenarios(
    pessimistic: float = Query(3.0),
    realistic: float = Query(5.0),
    optimistic: float = Query(7.0),
    inflation: float = Query(2.0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant_id),
):
    profile = _get_or_create_profile(db, current_user, tenant_id)
    years = max(0, profile.retirement_age - profile.current_age)
    infl = inflation / 100
    results = {}
    for name, rate in [("pessimistic", pessimistic), ("realistic", realistic), ("optimistic", optimistic)]:
        calc = RetirementService.calculate(
            current_age=profile.current_age,
            retirement_age=profile.retirement_age,
            life_expectancy=profile.life_expectancy,
            desired_monthly_income=profile.desired_monthly_income,
            expected_pension=profile.expected_pension,
            current_savings=profile.current_savings,
            expected_return_pct=rate,
        )
        calc["return_pct"] = rate
        if infl > 0 and years > 0:
            factor = (1 + infl) ** years
            calc["real_total_needed"] = round(calc["total_needed"] * factor, 2)
        else:
            calc["real_total_needed"] = calc["total_needed"]
        results[name] = calc
    return results
