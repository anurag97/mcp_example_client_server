"""
Employee Leave Management MCP Server

Run:
    uv run leave_mcp_server.py
"""

from datetime import date
from typing import Dict, List, Optional
from mcp.server.fastmcp import FastMCP

# -------------------------------------------------------------------
# MCP Server initialization
# -------------------------------------------------------------------
mcp = FastMCP("Employee Leave Manager", json_response=True)

# -------------------------------------------------------------------
# In‑memory storage (demo purpose)
# -------------------------------------------------------------------
employees: Dict[str, Dict] = {
    "E001": {"name": "Alice", "balance": 20},
    "E002": {"name": "Bob", "balance": 15},
}

leave_requests: Dict[int, Dict] = {}
_leave_id_counter = 1

# Pre-populated leave history (past records)
leave_history: Dict[str, List[Dict]] = {
    "E001": [
        {
            "leave_id": "H001",
            "days": 3,
            "reason": "Family vacation",
            "status": "APPROVED",
            "applied_on": "2025-01-10",
            "approved_by": "Manager_John",
        },
        {
            "leave_id": "H002",
            "days": 1,
            "reason": "Medical appointment",
            "status": "APPROVED",
            "applied_on": "2025-03-05",
            "approved_by": "Manager_John",
        },
        {
            "leave_id": "H003",
            "days": 5,
            "reason": "Personal travel",
            "status": "REJECTED",
            "applied_on": "2025-06-20",
            "rejected_by": "Manager_John",
            "comments": "Critical project deadline",
        },
        {
            "leave_id": "H004",
            "days": 2,
            "reason": "Sick leave",
            "status": "APPROVED",
            "applied_on": "2025-09-14",
            "approved_by": "Manager_Sarah",
        },
    ],
    "E002": [
        {
            "leave_id": "H005",
            "days": 4,
            "reason": "Wedding ceremony",
            "status": "APPROVED",
            "applied_on": "2025-02-18",
            "approved_by": "Manager_Sarah",
        },
        {
            "leave_id": "H006",
            "days": 2,
            "reason": "Home renovation",
            "status": "REJECTED",
            "applied_on": "2025-05-07",
            "rejected_by": "Manager_Sarah",
            "comments": "Team understaffed that week",
        },
        {
            "leave_id": "H007",
            "days": 1,
            "reason": "Child school event",
            "status": "APPROVED",
            "applied_on": "2025-11-03",
            "approved_by": "Manager_John",
        },
    ],
}

# -------------------------------------------------------------------
# Tools
# -------------------------------------------------------------------

@mcp.tool()
def apply_leave(employee_id: str, days: int, reason: str) -> Dict:
    """Apply for leave"""

    global _leave_id_counter

    if employee_id not in employees:
        return {"error": "Employee not found"}

    if days <= 0:
        return {"error": "Leave days must be positive"}

    if employees[employee_id]["balance"] < days:
        return {"error": "Insufficient leave balance"}

    leave_id = _leave_id_counter
    _leave_id_counter += 1

    leave_requests[leave_id] = {
        "leave_id": leave_id,
        "employee_id": employee_id,
        "days": days,
        "reason": reason,
        "status": "PENDING",
        "applied_on": str(date.today()),
    }

    return {
        "message": "Leave request submitted",
        "leave_id": leave_id,
    }


@mcp.tool()
def approve_leave(leave_id: int, approver: str) -> Dict:
    """Approve a leave request"""

    if leave_id not in leave_requests:
        return {"error": "Leave request not found"}

    request = leave_requests[leave_id]

    if request["status"] != "PENDING":
        return {"error": "Leave already processed"}

    emp_id = request["employee_id"]
    employees[emp_id]["balance"] -= request["days"]

    request["status"] = "APPROVED"
    request["approved_by"] = approver

    return {
        "message": "Leave approved",
        "remaining_balance": employees[emp_id]["balance"],
    }


@mcp.tool()
def reject_leave(leave_id: int, approver: str, comments: str) -> Dict:
    """Reject a leave request"""

    if leave_id not in leave_requests:
        return {"error": "Leave request not found"}

    request = leave_requests[leave_id]

    if request["status"] != "PENDING":
        return {"error": "Leave already processed"}

    request["status"] = "REJECTED"
    request["rejected_by"] = approver
    request["comments"] = comments

    return {"message": "Leave rejected"}


@mcp.tool()
def get_leave_balance(employee_id: str) -> Dict:
    """Get remaining leave balance"""

    if employee_id not in employees:
        return {"error": "Employee not found"}

    return {
        "employee": employees[employee_id]["name"],
        "balance": employees[employee_id]["balance"],
    }


@mcp.tool()
def get_leave_history(employee_id: str, status_filter: Optional[str] = None) -> Dict:
    """Get leave history for an employee.

    Args:
        employee_id: The employee ID to look up.
        status_filter: Optional filter – one of 'APPROVED', 'REJECTED', or 'PENDING'.
                       If omitted, all records are returned.
    """

    if employee_id not in employees:
        return {"error": "Employee not found"}

    # Combine pre-populated history with any processed requests from this session
    history: List[Dict] = list(leave_history.get(employee_id, []))

    for req in leave_requests.values():
        if req["employee_id"] == employee_id and req["status"] != "PENDING":
            history.append(req)

    if status_filter:
        status_filter = status_filter.upper()
        if status_filter not in ("APPROVED", "REJECTED", "PENDING"):
            return {"error": "Invalid status_filter. Use APPROVED, REJECTED, or PENDING."}
        history = [r for r in history if r["status"] == status_filter]

    # Also include pending requests from this session if no filter or filter is PENDING
    if status_filter in (None, "PENDING"):
        for req in leave_requests.values():
            if req["employee_id"] == employee_id and req["status"] == "PENDING":
                history.append(req)

    return {
        "employee": employees[employee_id]["name"],
        "employee_id": employee_id,
        "total_records": len(history),
        "history": history,
    }

# -------------------------------------------------------------------
# Resources
# -------------------------------------------------------------------

@mcp.resource("leave://status/{leave_id}")
def leave_status(leave_id: int) -> Dict:
    """Get leave request status"""

    if leave_id not in leave_requests:
        return {"error": "Leave request not found"}

    return leave_requests[leave_id]


@mcp.resource("employee://{employee_id}")
def employee_profile(employee_id: str) -> Dict:
    """Get employee profile"""

    if employee_id not in employees:
        return {"error": "Employee not found"}

    return {
        "employee_id": employee_id,
        "name": employees[employee_id]["name"],
        "leave_balance": employees[employee_id]["balance"],
    }

# -------------------------------------------------------------------
# Prompts
# -------------------------------------------------------------------

@mcp.prompt()
def generate_leave_email(
    employee_name: str,
    days: int,
    status: str,
) -> str:
    """Generate a leave status notification email"""

    if status == "APPROVED":
        return (
            f"Write a professional email informing {employee_name} "
            f"that their leave request for {days} day(s) has been approved."
        )

    if status == "REJECTED":
        return (
            f"Write a polite email informing {employee_name} "
            f"that their leave request for {days} day(s) has been rejected."
        )

    return (
        f"Write a confirmation email to {employee_name} "
        f"acknowledging receipt of their leave request for {days} day(s)."
    )

# -------------------------------------------------------------------
# Run Server
# -------------------------------------------------------------------
if __name__ == "__main__":
    mcp.run(transport="streamable-http")