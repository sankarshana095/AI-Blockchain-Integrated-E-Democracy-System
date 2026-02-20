from supabase_db.db import fetch_all,fetch_one


CONSTITUENCIES_TABLE = "constituencies"


from supabase_db.db import fetch_all

CONSTITUENCIES_TABLE = "constituencies"
DISTRICTS_TABLE = "districts"


def get_constituencies_by_state(state_id: str):
    """
    Fetch constituencies via districts → state
    """
    # 1️⃣ Get districts in the state
    districts = fetch_all(
        DISTRICTS_TABLE,
        {"state_id": state_id}
    )

    if not districts:
        return []

    district_ids = [d["id"] for d in districts]

    # 2️⃣ Fetch constituencies in those districts
    constituencies = []

    for did in district_ids:
        rows = fetch_all(
            CONSTITUENCIES_TABLE,
            {"district_id": did}
        )
        constituencies.extend(rows)

    return constituencies



def get_constituency_by_id(constituency_id: str):
    """
    Fetch single constituency
    """
    return fetch_one(
        CONSTITUENCIES_TABLE,
        {"id": constituency_id}
    )

def get_all_constituencies():
    """
    Fetch all constituencies
    """
    return fetch_all(CONSTITUENCIES_TABLE)