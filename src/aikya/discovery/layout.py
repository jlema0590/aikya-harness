"""Aikya repository topology, independent from software architecture."""
LAYOUTS = ("monorepo", "singlerepo")

def app_count(profile: dict) -> int:
    backend = profile.get("backend", "none")
    frontend = profile.get("frontend", "none")
    mobile = profile.get("mobile", "none")
    count = int(backend != "none")
    if frontend != "none" and not (backend == "next" and frontend == "react"):
        count += 1
    if mobile != "none":
        count += 2 if mobile == "both" and profile.get("mobile_framework") == "native" else 1
    return count

def layout_of(profile: dict) -> str:
    value = profile.get("repository_layout", "monorepo")
    if value not in LAYOUTS:
        raise ValueError("repository_layout debe ser monorepo o singlerepo")
    return value

def validate_layout(profile: dict) -> None:
    if profile.get('project_type','development') != 'development':
        return
    if profile.get("mode") == "new" and layout_of(profile) == "singlerepo" and app_count(profile) != 1:
        raise ValueError("singlerepo requires exactly one application. Select monorepo for separate backend/frontend apps or multiple mobile targets.")

def module_root(profile: dict, module: str) -> str:
    if layout_of(profile) == "singlerepo":
        return "."
    return {"backend": "apps/api", "web": "apps/web", "frontend": "apps/frontend", "mobile": "apps/mobile", "android": "apps/android", "ios": "apps/ios"}[module]
