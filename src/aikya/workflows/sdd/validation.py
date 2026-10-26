"""Validate persisted SDD state independently from storage and orchestration."""
from aikya.workflows.sdd.contracts import (
    KINDS, ID_RE, TASK_RE, STAGES, require, clean, items, fields_spec, approvals_done,
)
from aikya.workflows.sdd.templates import normalize_sections

def validate_state(data):
    """Recheck persisted records, including edits and merge results, on every load."""
    errors = []
    try:
        require(isinstance(data, dict) and data.get("schema") == 1, "Unsupported SDD state schema")
        require(data.get("kind") in KINDS, "Invalid project type")
        require(bool(ID_RE.fullmatch(str(data.get("id", "")))), "Invalid specification ID")
        spec = fields_spec(data.get("spec", {}))
        require(spec["id"] == data["id"], "Specification ID mismatch")
        answers = data.get("clarifications")
        require(isinstance(answers, dict) and set(answers).issubset(spec["questions"]), "Invalid clarifications")
        for answer in answers.values(): clean(answer, "answer", 2000)
        approvals = data.get("approvals")
        require(isinstance(approvals, dict) and set(approvals).issubset(STAGES), "Invalid approvals")
        for stage, approval in approvals.items():
            require(isinstance(approval, dict) and approval.get("approved") is True, "Invalid approval: " + stage)
            clean(approval.get("actor"), "approval actor", 120)
        if approvals_done(data, "spec"):
            require(set(answers) == set(spec["questions"]), "Unanswered clarifications")
        plan = data.get("plan")
        if plan is not None:
            require(approvals_done(data, "spec") and isinstance(plan, dict), "Plan requires approved specification")
            clean(plan.get("design"), "design")
            clean(plan.get("testing"), "testing")
            normalize_sections("design",plan.get("sections"))
            for key in ("decisions", "risks"):
                for value in items(plan.get(key), key): clean(value, key)
        if approvals_done(data, "plan"):
            require(plan is not None, "Approved plan is missing")
        tasks = items(data.get("tasks"), "tasks")
        require(len(tasks) <= 120, "Too many tasks")
        valid_req = {r["id"] for r in spec["requirements"]}
        byid = {}; covered = set()
        for task in tasks:
            require(isinstance(task, dict), "Invalid task")
            key = task.get("id")
            require(isinstance(key, str) and bool(TASK_RE.fullmatch(key)) and key not in byid, "Invalid or duplicate task ID")
            clean(task.get("description"), "task description", 1500)
            normalize_sections("tasks",task.get("sections"))
            refs = items(task.get("requirements"), "task requirements")
            require(bool(refs) and all(isinstance(r, str) and r in valid_req for r in refs), "Unknown task requirement")
            covered.update(refs)
            deps = items(task.get("depends_on"), "dependencies")
            require(all(isinstance(d, str) and bool(TASK_RE.fullmatch(d)) for d in deps), "Invalid dependency")
            require(task.get("status") in ("todo", "in_progress", "done"), "Invalid task status")
            evidence = items(task.get("evidence"), "task evidence")
            require(all(isinstance(e, str) and e for e in evidence), "Invalid evidence paths")
            if task["status"] != "todo": require(approvals_done(data, "tasks"), "Task progress requires approval")
            if task["status"] == "done": require(bool(evidence), "Completed task requires evidence")
            byid[key] = task
        if tasks:
            require(approvals_done(data, "plan"), "Tasks require approved plan")
            require(covered == valid_req, "Tasks must cover all requirements")
        if approvals_done(data, "tasks"):
            require(approvals_done(data, "plan") and bool(tasks), "Task approval requires approved plan and tasks")
        visited = set()
        def visit(key, stack):
            require(key not in stack, "Cyclic task dependencies")
            require(key in byid, "Unknown task dependency")
            if key in visited: return
            for dep in byid[key]["depends_on"]: visit(dep, stack | {key})
            visited.add(key)
        for key, task in byid.items():
            visit(key, set())
            if task["status"] != "todo":
                require(all(byid[d]["status"] == "done" for d in task["depends_on"]), "Task dependencies are incomplete")
        verification = data.get("verification")
        if verification is not None:
            require(approvals_done(data, "tasks") and all(t["status"] == "done" for t in tasks), "Verification requires completed approved tasks")
            require(isinstance(verification, dict) and verification.get("independently_executed") is False, "Invalid verification record")
            normalize_sections("evidence",verification.get("sections"))
            entries = items(verification.get("requirements"), "verification requirements")
            found = set()
            for entry in entries:
                require(isinstance(entry, dict), "Invalid verification item")
                key = entry.get("id")
                require(isinstance(key, str) and key in valid_req and key not in found, "Invalid verification requirement")
                found.add(key)
                clean(entry.get("command"), "command", 800)
                clean(entry.get("evidence"), "evidence", 240)
                require(entry.get("result") in ("passed", "failed"), "Invalid verification result")
            require(found == valid_req, "Verification must cover all requirements")
            status = "EVIDENCE_RECORDED" if all(e["result"] == "passed" for e in entries) else "FAILED"
            require(verification.get("status") == status, "Inconsistent verification status")
    except (ValueError, TypeError, KeyError, AttributeError, RecursionError) as exc:
        errors.append(str(exc))
    return errors
