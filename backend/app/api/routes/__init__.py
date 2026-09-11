from fastapi import APIRouter

router = APIRouter()

# classic routes
from . import auth, findings, remediation, monitoring, tools, tasks, ai, reports, assessments, retests, scopes

# versioned/api-style routes
from . import findings_api
from . import events

# include routers (import side-effect: modules register routers in application)
