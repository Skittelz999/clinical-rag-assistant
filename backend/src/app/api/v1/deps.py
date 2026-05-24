from typing import Annotated

from fastapi import Depends


def get_current_demo_user() -> dict[str, str]:
    # Replace with real JWT validation after MVP auth is implemented.
    return {"id": "demo-user", "role": "clinician", "organization_id": "demo-org"}


CurrentUser = Annotated[dict[str, str], Depends(get_current_demo_user)]
