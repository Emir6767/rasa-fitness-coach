# actions.py
from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet
from models import SessionLocal, UserProfile

class ActionSetProfile(Action):
    def name(self) -> Text:
        return "action_set_profile"

    def run(
        self, dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> List:

        # Slots aus dem Tracker
        height = tracker.get_slot("height")
        weight = tracker.get_slot("weight")
        age    = tracker.get_slot("age")
        goal   = tracker.get_slot("goal_type")

        # 1) Falls Höhe noch fehlt
        if height is None:
            dispatcher.utter_message(response="utter_ask_height")
            return []

        # 2) Falls Gewicht noch fehlt
        if weight is None:
            dispatcher.utter_message(response="utter_ask_weight")
            return []

        # 3) Falls Alter fehlt
        if age is None:
            dispatcher.utter_message(response="utter_ask_age")
            return []

        # 4) Falls Ziel fehlt
        if goal is None:
            dispatcher.utter_message(response="utter_ask_goal")
            return []

        # 5) Alle Daten vollständig: in DB speichern
        session = SessionLocal()
        profile = UserProfile(
            user_id   = tracker.sender_id,
            height    = float(height),
            weight    = float(weight),
            age       = int(age),
            goal_type = goal
        )
        session.add(profile)
        session.commit()
        session.close()

        dispatcher.utter_message(response="utter_profile_saved")
        return []
