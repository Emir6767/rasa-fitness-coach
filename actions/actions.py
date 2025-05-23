# actions/actions.py
from typing import Any, Text, Dict, List
import datetime
from rasa_sdk import Tracker, Action
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.forms import FormValidationAction
from sqlalchemy.orm import Session
from models import init_db, SessionLocal, UserProfile

# Tabellen anlegen bei Start
init_db()

class ValidateProfileForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_profile_form"

    def validate_height(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict,
    ) -> Dict[Text, Any]:
        try:
            val = float(slot_value)
            if 50 <= val <= 300:
                return {"height": val}
        except:
            pass
        dispatcher.utter_message(response="utter_ask_height")
        return {"height": None}

    def validate_weight(
        self, slot_value, dispatcher, tracker, domain
    ) -> Dict[Text, Any]:
        try:
            val = float(slot_value)
            if 20 <= val <= 300:
                return {"weight": val}
        except:
            pass
        dispatcher.utter_message(response="utter_ask_weight")
        return {"weight": None}

    def validate_age(
        self, slot_value, dispatcher, tracker, domain
    ) -> Dict[Text, Any]:
        try:
            val = int(slot_value)
            if 5 <= val <= 120:
                return {"age": val}
        except:
            pass
        dispatcher.utter_message(response="utter_ask_age")
        return {"age": None}

    def validate_goal_type(
        self, slot_value, dispatcher, tracker, domain
    ) -> Dict[Text, Any]:
        if isinstance(slot_value, str) and slot_value.strip():
            return {"goal_type": slot_value}
        dispatcher.utter_message(response="utter_ask_goal")
        return {"goal_type": None}


class ActionSubmitProfile(Action):
    def name(self) -> Text:
        return "action_submit_profile"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        # DB-Session öffnen
        db: Session = SessionLocal()
        user_id = tracker.sender_id
        profile = UserProfile(
            user_id=user_id,
            height=tracker.get_slot("height"),
            weight=tracker.get_slot("weight"),
            age=tracker.get_slot("age"),
            goal_type=tracker.get_slot("goal_type"),
        )
        db.add(profile)
        db.commit()
        db.close()
        dispatcher.utter_message(response="utter_profile_saved")
        return []
