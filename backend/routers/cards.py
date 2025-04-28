from fastapi import APIRouter, Request, Depends, HTTPException
from dependencies import get_query_token
from pydantic import BaseModel
from typing import List
import time
from db import get_user_db_connection
from routers.auth import get_current_active_user

router = APIRouter(
    prefix="/cards",
    tags=["cards"],
    # Remove the dependency on get_query_token as we're using JWT authentication
    # dependencies=[Depends(get_query_token)],
    responses={404: {"description": "Not found"}},
)

class CardBase(BaseModel):
    code1: str
    code2: str = None
    redeemed: bool = False
    failed: str = ""
    lock: bool = False
    perm_lock: bool = False

class CardResponse(CardBase):
    id: int

@router.get('/available')
async def get_available(current_user = Depends(get_current_active_user)):
    """Get an available card that hasn't been redeemed yet"""
    # Use user-specific database connection with RLS
    with get_user_db_connection(user_id=current_user["id"], user_role=current_user["role"]) as user_conn:
        cursor = user_conn.cursor()

        try:
            cursor.execute("SELECT id, code1, code2 FROM cards WHERE redeemed = false LIMIT 1")
            result = cursor.fetchone()

            if not result:
                raise HTTPException(status_code=404, detail="No available cards found")

            card = {'id': result[0], 'code1': result[1], 'code2': result[2] or None}
            return card

        except Exception as e:
            print(f"Error retrieving available card: {e}")
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(status_code=500, detail="Error retrieving available card")
        finally:
            cursor.close()

@router.post('/', response_model=List[CardResponse])
async def new_cards(cardList: List[List[str]], current_user = Depends(get_current_active_user)):
    """Add new cards to the database"""
    # Use user-specific database connection with RLS
    with get_user_db_connection(user_id=current_user["id"], user_role=current_user["role"]) as user_conn:
        cursor = user_conn.cursor()

        try:
            created_cards = []

            for cardPack in cardList:
                if len(cardPack) > 1:
                    cursor.execute(
                        "INSERT INTO cards(code1, code2, owner_id) VALUES(%s, %s, %s) RETURNING id, code1, code2, redeemed, failed, lock, perm_lock",
                        (cardPack[0], cardPack[1], current_user["id"])
                    )
                else:
                    cursor.execute(
                        "INSERT INTO cards(code1, owner_id) VALUES(%s, %s) RETURNING id, code1, code2, redeemed, failed, lock, perm_lock",
                        (cardPack[0], current_user["id"])
                    )

                result = cursor.fetchone()
                card = {
                    "id": result[0],
                    "code1": result[1],
                    "code2": result[2],
                    "redeemed": result[3],
                    "failed": result[4],
                    "lock": result[5],
                    "perm_lock": result[6]
                }
                created_cards.append(card)

            user_conn.commit()
            return created_cards

        except Exception as e:
            user_conn.rollback()
            print(f"Error creating cards: {e}")
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(status_code=500, detail="Error creating cards")
        finally:
            cursor.close()

@router.post('/redeem')
async def redeem_card(id: int = 0, codeSearch: str = "", current_user = Depends(get_current_active_user)):
    """Mark a card as redeemed"""
    if id == 0 and codeSearch == "":
        raise HTTPException(status_code=400, detail="No card_id or code_search supplied")

    # Use user-specific database connection with RLS
    with get_user_db_connection(user_id=current_user["id"], user_role=current_user["role"]) as user_conn:
        cursor = user_conn.cursor()

        try:
            affected_rows = 0

            if id != 0:
                cursor.execute("UPDATE cards SET redeemed=true WHERE id = %s RETURNING id", (id,))
                result = cursor.fetchone()
                if result:
                    affected_rows += 1

            if codeSearch != "":
                cursor.execute("UPDATE cards SET redeemed=true WHERE code1 = %s OR code2 = %s RETURNING id", (codeSearch, codeSearch))
                results = cursor.fetchall()
                affected_rows += len(results)

            user_conn.commit()

            if affected_rows == 0:
                return {"message": "No cards found to redeem"}

            return {"message": f"Successfully redeemed {affected_rows} card(s)"}

        except Exception as e:
            user_conn.rollback()
            print(f"Error redeeming card: {e}")
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(status_code=500, detail="Error redeeming card")
        finally:
            cursor.close()

@router.get('/', response_model=List[CardResponse])
async def list_cards(current_user = Depends(get_current_active_user)):
    """List all cards accessible to the current user"""
    # Use user-specific database connection with RLS
    with get_user_db_connection(user_id=current_user["id"], user_role=current_user["role"]) as user_conn:
        cursor = user_conn.cursor()

        try:
            cursor.execute("""
                SELECT id, code1, code2, redeemed, failed, lock, perm_lock
                FROM cards
                ORDER BY id
            """)

            results = cursor.fetchall()
            cards = []

            for row in results:
                card = {
                    "id": row[0],
                    "code1": row[1],
                    "code2": row[2],
                    "redeemed": row[3],
                    "failed": row[4],
                    "lock": row[5],
                    "perm_lock": row[6]
                }
                cards.append(card)

            return cards

        except Exception as e:
            print(f"Error listing cards: {e}")
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(status_code=500, detail="Error listing cards")
        finally:
            cursor.close()

@router.delete('/{card_id}')
async def delete_card(card_id: int, current_user = Depends(get_current_active_user)):
    """Delete a card"""
    # Use user-specific database connection with RLS
    with get_user_db_connection(user_id=current_user["id"], user_role=current_user["role"]) as user_conn:
        cursor = user_conn.cursor()

        try:
            cursor.execute("SELECT id FROM cards WHERE id = %s", (card_id,))
            result = cursor.fetchone()

            if not result:
                raise HTTPException(status_code=404, detail="Card not found or you don't have permission to delete it")

            cursor.execute("DELETE FROM cards WHERE id = %s", (card_id,))
            user_conn.commit()

            return {"message": "Card deleted successfully"}

        except Exception as e:
            user_conn.rollback()
            print(f"Error deleting card: {e}")
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(status_code=500, detail="Error deleting card")
        finally:
            cursor.close()
