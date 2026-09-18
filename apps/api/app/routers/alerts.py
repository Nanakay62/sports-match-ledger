from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from packages.database.notifications_repository import NotificationsRepository
from packages.database.session import get_db

router = APIRouter(prefix="/alerts", tags=["alerts"])


class SubscribeRequest(BaseModel):
    email: str
    event_id: str


class SubscribeResponse(BaseModel):
    subscribed: bool


class UnsubscribeResponse(BaseModel):
    unsubscribed: bool


class SubscriptionsResponse(BaseModel):
    event_ids: list[str]


@router.post("/subscribe", response_model=SubscribeResponse)
def subscribe(req: SubscribeRequest, db: Session = Depends(get_db)) -> SubscribeResponse:
    """Subscribes an email to status-change alerts for one event (Handbook §18.1).

    Delivery timing (real-time vs. daily digest) is decided later, per subscriber,
    by NotificationDispatcher against their persisted entitlement — never here.
    """
    NotificationsRepository.subscribe(db, email=req.email, event_id=req.event_id)
    return SubscribeResponse(subscribed=True)


@router.post("/unsubscribe", response_model=UnsubscribeResponse)
def unsubscribe(req: SubscribeRequest, db: Session = Depends(get_db)) -> UnsubscribeResponse:
    removed = NotificationsRepository.unsubscribe(db, email=req.email, event_id=req.event_id)
    return UnsubscribeResponse(unsubscribed=removed)


@router.get("/subscriptions/{email}", response_model=SubscriptionsResponse)
def get_subscriptions(email: str, db: Session = Depends(get_db)) -> SubscriptionsResponse:
    event_ids = NotificationsRepository.get_subscribed_event_ids(db, email)
    return SubscriptionsResponse(event_ids=event_ids)
