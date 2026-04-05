"""Executes tool calls from LLM chat — maps tool names to service calls."""
from datetime import date

from sqlalchemy.orm import Session

from app.models.account import Account
from app.models.budget_alert import BudgetAlert
from app.models.direct_debit import DirectDebit
from app.models.investment import Investment
from app.models.savings_goal import SavingsGoal
from app.models.standing_order import StandingOrder
from app.models.transaction import Transaction
from app.services.cashflow import CashflowService


class ChatExecutor:
    @staticmethod
    def execute(tool_name: str, tool_input: dict, *, db: Session, tenant_id: str, user_id: str) -> dict:
        if tool_name == "create_account":
            return ChatExecutor._create_account(tool_input, db=db, tenant_id=tenant_id, user_id=user_id)
        if tool_name == "list_accounts":
            return ChatExecutor._list_accounts(db=db, tenant_id=tenant_id)
        if tool_name == "create_standing_order":
            return ChatExecutor._create_standing_order(tool_input, db=db, tenant_id=tenant_id, user_id=user_id)
        if tool_name == "create_direct_debit":
            return ChatExecutor._create_direct_debit(tool_input, db=db, tenant_id=tenant_id, user_id=user_id)
        if tool_name == "create_transaction":
            return ChatExecutor._create_transaction(tool_input, db=db, tenant_id=tenant_id, user_id=user_id)
        if tool_name == "create_investment":
            return ChatExecutor._create_investment(tool_input, db=db, tenant_id=tenant_id, user_id=user_id)
        if tool_name == "create_savings_goal":
            return ChatExecutor._create_savings_goal(tool_input, db=db, tenant_id=tenant_id, user_id=user_id)
        if tool_name == "update_savings_goal":
            return ChatExecutor._update_savings_goal(tool_input, db=db, tenant_id=tenant_id)
        if tool_name == "create_budget_alert":
            return ChatExecutor._create_budget_alert(tool_input, db=db, tenant_id=tenant_id, user_id=user_id)
        if tool_name == "get_cashflow_summary":
            return CashflowService.monthly_summary(db, tenant_id=tenant_id)
        if tool_name == "get_net_worth":
            acc = sum(a.balance for a in db.query(Account).filter(Account.tenant_id == tenant_id, Account.is_active == True).all())
            inv = sum(i.current_value for i in db.query(Investment).filter(Investment.tenant_id == tenant_id, Investment.is_active == True).all())
            return {"accounts": float(acc), "investments": float(inv), "total": float(acc + inv)}
        return {"error": f"Unknown tool: {tool_name}"}

    @staticmethod
    def _create_account(inp, *, db, tenant_id, user_id):
        # Find primary account for account_id references
        acc = Account(
            tenant_id=tenant_id, created_by_id=user_id,
            name=inp["name"], type=inp.get("type", "checking"),
            bank_name=inp.get("bank_name", ""), balance=inp.get("balance", 0.0),
        )
        db.add(acc)
        db.commit()
        return {"created": "account", "name": acc.name, "id": acc.id}

    @staticmethod
    def _list_accounts(*, db, tenant_id):
        accounts = db.query(Account).filter(Account.tenant_id == tenant_id, Account.is_active == True).all()
        return {"accounts": [{"name": a.name, "type": a.type, "balance": a.balance} for a in accounts]}

    @staticmethod
    def _create_standing_order(inp, *, db, tenant_id, user_id):
        acc = db.query(Account).filter(Account.tenant_id == tenant_id).first()
        so = StandingOrder(
            tenant_id=tenant_id, created_by_id=user_id,
            account_id=acc.id if acc else None,
            name=inp["name"], type=inp.get("type", "expense"),
            amount=inp["amount"], frequency=inp.get("frequency", "monthly"),
            execution_day=inp.get("execution_day", 1),
        )
        db.add(so)
        db.commit()
        return {"created": "standing_order", "name": so.name, "id": so.id}

    @staticmethod
    def _create_direct_debit(inp, *, db, tenant_id, user_id):
        acc = db.query(Account).filter(Account.tenant_id == tenant_id).first()
        dd = DirectDebit(
            tenant_id=tenant_id, created_by_id=user_id,
            account_id=acc.id if acc else None,
            name=inp["name"], creditor=inp.get("creditor", ""),
            amount=inp["amount"], frequency=inp.get("frequency", "monthly"),
            expected_day=inp.get("expected_day", 1),
        )
        db.add(dd)
        db.commit()
        return {"created": "direct_debit", "name": dd.name, "id": dd.id}

    @staticmethod
    def _create_transaction(inp, *, db, tenant_id, user_id):
        tx = Transaction(
            tenant_id=tenant_id, created_by_id=user_id,
            description=inp["description"], amount=inp["amount"],
            type=inp.get("type", "expense"), category=inp.get("category", ""),
            transaction_date=date.fromisoformat(inp["transaction_date"]),
        )
        db.add(tx)
        db.commit()
        return {"created": "transaction", "description": tx.description, "id": tx.id}

    @staticmethod
    def _create_investment(inp, *, db, tenant_id, user_id):
        inv = Investment(
            tenant_id=tenant_id, created_by_id=user_id,
            name=inp["name"], type=inp.get("type", "other"),
            current_value=inp.get("current_value", 0.0),
            invested_amount=inp.get("invested_amount", inp.get("current_value", 0.0)),
            broker=inp.get("broker", ""), isin=inp.get("isin"),
        )
        db.add(inv)
        db.commit()
        return {"created": "investment", "name": inv.name, "id": inv.id}

    @staticmethod
    def _create_savings_goal(inp, *, db, tenant_id, user_id):
        sg = SavingsGoal(
            tenant_id=tenant_id, created_by_id=user_id,
            name=inp["name"], type=inp.get("type", "emergency"),
            target_amount=inp["target_amount"],
            current_amount=inp.get("current_amount", 0.0),
        )
        db.add(sg)
        db.commit()
        return {"created": "savings_goal", "name": sg.name, "id": sg.id}

    @staticmethod
    def _update_savings_goal(inp, *, db, tenant_id):
        goal = db.query(SavingsGoal).filter(
            SavingsGoal.tenant_id == tenant_id, SavingsGoal.name == inp["name"],
        ).first()
        if not goal:
            return {"error": f"Sparziel '{inp['name']}' nicht gefunden"}
        if "target_amount" in inp:
            goal.target_amount = inp["target_amount"]
        if "current_amount" in inp:
            goal.current_amount = inp["current_amount"]
        db.commit()
        return {"updated": "savings_goal", "name": goal.name, "id": goal.id}

    @staticmethod
    def _create_budget_alert(inp, *, db, tenant_id, user_id):
        alert = BudgetAlert(
            tenant_id=tenant_id, created_by_id=user_id,
            name=inp["name"], category=inp["category"],
            monthly_limit=inp["monthly_limit"],
        )
        db.add(alert)
        db.commit()
        return {"created": "budget_alert", "name": alert.name, "id": alert.id}
