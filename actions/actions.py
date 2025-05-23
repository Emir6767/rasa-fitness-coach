# actions/actions.py
from typing import Any, Text, Dict, List
import datetime
import json
from rasa_sdk import Tracker, Action
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.forms import FormValidationAction
from rasa_sdk.events import SlotSet, AllSlotsReset
from sqlalchemy.orm import Session
from models import init_db, SessionLocal, UserProfile

# Tabellen anlegen bei Start
init_db()

def load_data(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Fehler: Datei '{filename}' nicht gefunden.")
        return None

EXERCISE_DATA = load_data('data/uebungen.json')
NUTRITION_DATA = load_data('data/ernaehrung.json')

BODY_FAT_IMAGES = {
    "männlich": "http://localhost:8000/kfa_mann.jpg",
    "weiblich": "http://localhost:8000/kfa_frau.jpg"
}

class ValidateProfileForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_profile_form"

    def validate_height(self, slot_value: Any, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict) -> Dict[Text, Any]:
        try:
            val = float(slot_value)
            if 50 <= val <= 300: return {"height": val}
        except: pass
        dispatcher.utter_message(response="utter_ask_height")
        return {"height": None}

    def validate_weight(self, slot_value, dispatcher, tracker, domain) -> Dict[Text, Any]:
        try:
            val = float(slot_value)
            if 20 <= val <= 300: return {"weight": val}
        except: pass
        dispatcher.utter_message(response="utter_ask_weight")
        return {"weight": None}

    def validate_age(self, slot_value, dispatcher, tracker, domain) -> Dict[Text, Any]:
        try:
            val = int(slot_value)
            if 5 <= val <= 120: return {"age": val}
        except: pass
        dispatcher.utter_message(response="utter_ask_age")
        return {"age": None}

    def validate_goal_type(self, slot_value, dispatcher, tracker, domain) -> Dict[Text, Any]:
        allowed_goals = ["muskelaufbau", "abnehmen", "muskelerhalt", "gewicht halten", "fettabbau"]
        if isinstance(slot_value, str) and slot_value.lower() in allowed_goals:
            return {"goal_type": slot_value}
        dispatcher.utter_message(response="utter_ask_goal")
        return {"goal_type": None}

class ActionSubmitProfile(Action):
    def name(self) -> Text:
        return "action_submit_profile"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        db: Session = SessionLocal()
        user_id = tracker.sender_id
        profile = db.query(UserProfile).filter_by(user_id=user_id).first()
        if profile:
            profile.height = tracker.get_slot("height")
            profile.weight = tracker.get_slot("weight")
            profile.age = tracker.get_slot("age")
            profile.goal_type = tracker.get_slot("goal_type")
        else:
            profile = UserProfile(user_id=user_id, height=tracker.get_slot("height"), weight=tracker.get_slot("weight"), age=tracker.get_slot("age"), goal_type=tracker.get_slot("goal_type"))
            db.add(profile)
        db.commit()
        db.close()
        dispatcher.utter_message(response="utter_profile_saved")
        return []

class ActionProvideExercises(Action):
    def name(self) -> Text:
        return "action_provide_exercises"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        musclegroup = tracker.get_slot("musclegroup")
        if not musclegroup:
            dispatcher.utter_message(response="utter_ask_musclegroup")
            return []
        if not EXERCISE_DATA:
            dispatcher.utter_message(text="Es tut mir leid, ich konnte die Übungsdaten nicht laden.")
            return []
        found_exercises = []
        for uebung in EXERCISE_DATA['uebungen']:
            if musclegroup.lower() in [mg.lower() for mg in uebung['muskelgruppen']]:
                found_exercises.append(uebung)
        if found_exercises:
            message = f"Hier sind einige Übungen für {musclegroup.capitalize()}:\n"
            for uebung in found_exercises[:3]:
                message += f"- **{uebung['name']}**: {uebung['beschreibung']} (Equipment: {', '.join(uebung['equipment'])})\n"
            dispatcher.utter_message(text=message)
        else:
            dispatcher.utter_message(response="utter_no_exercises_found")
        return []

class ActionProvideNutritionAdvice(Action):
    def name(self) -> Text:
        return "action_provide_nutrition_advice"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        nutrition_goal = tracker.get_slot("nutrition_goal")
        if not nutrition_goal:
            dispatcher.utter_message(response="utter_ask_nutrition_goal")
            return []
        if not NUTRITION_DATA:
            dispatcher.utter_message(text="Es tut mir leid, ich konnte die Ernährungsdaten nicht laden.")
            return []
        found_tips = None
        for ernaehrungsziel in NUTRITION_DATA['ernaehrungsziele']:
            if ernaehrungsziel['ziel'].lower() == nutrition_goal.lower():
                found_tips = ernaehrungsziel
                break
        if found_tips:
            message = f"Hier sind einige Prinzipien für {found_tips['ziel']}:\n"
            for prinzip in found_tips['prinzipien']:
                message += f"- {prinzip}\n"
            if 'zusatzinfo' in found_tips:
                message += f"\nZusatzinfo: {found_tips['zusatzinfo']}"
            dispatcher.utter_message(text=message)
        else:
            dispatcher.utter_message(response="utter_no_nutrition_info")
        return []

class ValidateNutritionPlanForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_nutrition_plan_form"

    async def validate_gender(self, slot_value: Any, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict) -> Dict[Text, Any]:
        # Abbruch-Logik am Anfang jeder Validierung
        if tracker.latest_message.get("intent", {}).get("name") in ["stop", "goodbye"]:
            dispatcher.utter_message(response="utter_form_aborted")
            return {"gender": None, "requested_slot": None} # Setze slot und requested_slot auf None, um Formular abzubrechen

        if isinstance(slot_value, str) and slot_value.lower() in ["männlich", "weiblich", "mann", "frau"]:
            return {"gender": "männlich" if slot_value.lower() in ["männlich", "mann"] else "weiblich"}
        dispatcher.utter_message(response="utter_ask_gender")
        return {"gender": None}

    async def validate_body_fat_percentage(self, slot_value: Any, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict) -> Dict[Text, Any]:
        if tracker.latest_message.get("intent", {}).get("name") in ["stop", "goodbye"]:
            dispatcher.utter_message(response="utter_form_aborted")
            return {"body_fat_percentage": None, "requested_slot": None}

        try:
            val = float(slot_value)
            if 5 <= val <= 60:
                return {"body_fat_percentage": val}
            else:
                dispatcher.utter_message(text="Bitte gib einen realistischen Körperfettanteil zwischen 5% und 60% ein.")
        except ValueError:
            pass
        
        gender = tracker.get_slot("gender")
        if gender and gender.lower() == "männlich" and BODY_FAT_IMAGES.get("männlich"):
            dispatcher.utter_message(response="utter_body_fat_male_example")
        elif gender and gender.lower() == "weiblich" and BODY_FAT_IMAGES.get("weiblich"):
            dispatcher.utter_message(response="utter_body_fat_female_example")
        
        dispatcher.utter_message(response="utter_ask_body_fat_percentage")
        return {"body_fat_percentage": None}

    async def validate_activity_level_sport(self, slot_value: Any, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict) -> Dict[Text, Any]:
        if tracker.latest_message.get("intent", {}).get("name") in ["stop", "goodbye"]:
            dispatcher.utter_message(response="utter_form_aborted")
            return {"activity_level_sport": None, "requested_slot": None}

        allowed_levels = ["kein sport", "wenig sport", "mäßig sport", "viel sport", "1-2 mal pro woche", "3-4 mal pro woche", "5-7 mal pro woche", "nie sport", "selten", "oft"]
        if isinstance(slot_value, str) and slot_value.lower() in allowed_levels:
            if "1-2" in slot_value.lower() or "wenig" in slot_value.lower() or "selten" in slot_value.lower():
                return {"activity_level_sport": "wenig sport"}
            elif "3-4" in slot_value.lower() or "mäßig" in slot_value.lower():
                return {"activity_level_sport": "mäßig sport"}
            elif "5-7" in slot_value.lower() or "viel" in slot_value.lower() or "oft" in slot_value.lower():
                return {"activity_level_sport": "viel sport"}
            elif "kein" in slot_value.lower() or "nie" in slot_value.lower():
                return {"activity_level_sport": "kein sport"}
            else: # Fallback, falls doch ein nicht standardisierter, aber erlaubter Begriff durchrutscht
                return {"activity_level_sport": slot_value.lower()} # Sollte durch NLU standardisiert werden
        dispatcher.utter_message(response="utter_ask_activity_level_sport")
        return {"activity_level_sport": None}

    async def validate_activity_level_daily(self, slot_value: Any, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict) -> Dict[Text, Any]:
        if tracker.latest_message.get("intent", {}).get("name") in ["stop", "goodbye"]:
            dispatcher.utter_message(response="utter_form_aborted")
            return {"activity_level_daily": None, "requested_slot": None}

        allowed_levels = ["sitzend", "leicht aktiv", "mäßig aktiv", "sehr aktiv", "bürolastig", "viel zu fuß"]
        if isinstance(slot_value, str) and slot_value.lower() in allowed_levels:
            if "bürolastig" in slot_value.lower() or "sitzend" in slot_value.lower():
                return {"activity_level_daily": "sitzend"}
            elif "viel zu fuß" in slot_value.lower() or "leicht aktiv" in slot_value.lower():
                return {"activity_level_daily": "leicht aktiv"}
            # Weitere Standardisierungen, falls nötig
            return {"activity_level_daily": slot_value.lower()}
        dispatcher.utter_message(response="utter_ask_activity_level_daily")
        return {"activity_level_daily": None}

    async def validate_diet_goal(self, slot_value: Any, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict) -> Dict[Text, Any]:
        if tracker.latest_message.get("intent", {}).get("name") in ["stop", "goodbye"]:
            dispatcher.utter_message(response="utter_form_aborted")
            return {"diet_goal": None, "requested_slot": None}

        allowed_goals = ["abnehmen", "zunehmen", "gleichbleiben", "muskelaufbau", "fett verlieren", "muskeln aufbauen"]
        if isinstance(slot_value, str) and slot_value.lower() in allowed_goals:
            if "muskelaufbau" in slot_value.lower() or "muskeln aufbauen" in slot_value.lower() or "zunehmen" in slot_value.lower():
                return {"diet_goal": "zunehmen"}
            elif "fett verlieren" in slot_value.lower() or "abnehmen" in slot_value.lower():
                return {"diet_goal": "abnehmen"}
            return {"diet_goal": slot_value.lower()}
        dispatcher.utter_message(response="utter_ask_diet_goal")
        return {"diet_goal": None}


class ActionCalculateNutritionPlan(Action):
    def name(self) -> Text:
        return "action_calculate_nutrition_plan"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        dispatcher.utter_message(response="utter_nutrition_plan_calculated")

        # Es ist wichtig, die Slots auch dann abzurufen, wenn sie aus einem *anderen* Formular
        # (wie dem initialen Profilformular) stammen, da sie im Tracker persistieren.
        gender = tracker.get_slot("gender")
        age = tracker.get_slot("age")
        weight = tracker.get_slot("weight")
        height = tracker.get_slot("height")
        
        # ACHTUNG: Hier waren die Slot-Namen falsch. Korrigiert zu activity_level_sport und activity_level_daily
        sport_activity = tracker.get_slot("activity_level_sport")
        daily_activity = tracker.get_slot("activity_level_daily")
        diet_goal = tracker.get_slot("diet_goal")

        if not all([gender, age, weight, height, sport_activity, daily_activity, diet_goal]):
            dispatcher.utter_message(text="Es tut mir leid, es fehlen einige Daten, um deinen Ernährungsplan zu berechnen. Bitte starte die Anfrage erneut.")
            return [AllSlotsReset()]

        bmr = 0
        if gender.lower() == "männlich":
            bmr = (10 * weight) + (6.25 * height) - (5 * age) + 5
        elif gender.lower() == "weiblich":
            bmr = (10 * weight) + (6.25 * height) - (5 * age) - 161
        else:
            dispatcher.utter_message(text="Interner Fehler: Ungültiges Geschlecht für Berechnung.")
            return [AllSlotsReset()]

        activity_factor = 1.2

        if daily_activity.lower() == "sitzend":
            if sport_activity.lower() == "kein sport": activity_factor = 1.2
            elif sport_activity.lower() == "wenig sport": activity_factor = 1.375
            elif sport_activity.lower() == "mäßig sport": activity_factor = 1.45
            elif sport_activity.lower() == "viel sport": activity_factor = 1.55
        elif daily_activity.lower() == "leicht aktiv":
            if sport_activity.lower() == "kein sport": activity_factor = 1.375
            elif sport_activity.lower() == "wenig sport": activity_factor = 1.55
            elif sport_activity.lower() == "mäßig sport": activity_factor = 1.6
            elif sport_activity.lower() == "viel sport": activity_factor = 1.725
        elif daily_activity.lower() == "mäßig aktiv":
            if sport_activity.lower() == "kein sport": activity_factor = 1.55
            elif sport_activity.lower() == "wenig sport": activity_factor = 1.725
            elif sport_activity.lower() == "mäßig sport": activity_factor = 1.8
            elif sport_activity.lower() == "viel sport": activity_factor = 1.9
        elif daily_activity.lower() == "sehr aktiv":
            if sport_activity.lower() == "kein sport": activity_factor = 1.725
            elif sport_activity.lower() == "wenig sport": activity_factor = 1.8
            elif sport_activity.lower() == "mäßig sport": activity_factor = 1.9
            elif sport_activity.lower() == "viel sport": activity_factor = 2.0

        tdee = bmr * activity_factor

        target_calories = tdee
        if diet_goal.lower() == "abnehmen":
            target_calories = tdee - 400
        elif diet_goal.lower() == "zunehmen":
            target_calories = tdee + 400

        protein_g = weight * 1.8
        fat_g = target_calories * 0.25 / 9
        carb_g = (target_calories - (protein_g * 4) - (fat_g * 9)) / 4

        target_calories = int(round(target_calories, -1))
        protein_g = int(round(protein_g))
        fat_g = int(round(fat_g))
        carb_g = int(round(carb_g))

        response_text = (
            f"Basierend auf deinen Angaben empfehle ich dir für dein Ziel '{diet_goal}' eine tägliche Kalorienzufuhr von etwa "
            f"**{target_calories} kcal**.\n\n"
            f"Die ungefähre Makronährstoffverteilung könnte sein:\n"
            f"- **Protein:** {protein_g} g\n"
            f"- **Fett:** {fat_g} g\n"
            f"- **Kohlenhydrate:** {carb_g} g\n\n"
            f"Denke daran, dies sind Schätzwerte. Für eine individuelle, detaillierte Ernährungsberatung wende dich bitte an einen Fachmann."
        )

        dispatcher.utter_message(text=response_text)

        return [AllSlotsReset()]