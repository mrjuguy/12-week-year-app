import pandas as pd
import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from datetime import date, datetime, timedelta
from typing import List
from src.models import Cycle, Goal, Tactic, BlockType

# Constants
WORKSHEET_NAME = "Tactics"
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/calendar",
]

class Storage:
    def __init__(self):
        # Initialize direct gspread connection
        try:
            if "connections" not in st.secrets or "gsheets" not in st.secrets["connections"]:
                st.error("Secrets missing! Check .streamlit/secrets.toml")
                st.stop()
                
            creds_dict = st.secrets["connections"]["gsheets"]["service_account"]
            creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
            self.client = gspread.authorize(creds)
            self.calendar_service = build('calendar', 'v3', credentials=creds)
            
            url = st.secrets["connections"]["gsheets"]["spreadsheet"]
            self.sh = self.client.open_by_url(url)
            self.worksheet = self.sh.worksheet(WORKSHEET_NAME)
            
            # Initialize Vision Worksheet
            try:
                self.vision_worksheet = self.sh.worksheet("Vision")
            except gspread.WorksheetNotFound:
                self.vision_worksheet = self.sh.add_worksheet(title="Vision", rows=20, cols=2)
                self.vision_worksheet.append_row(["Type", "Content"])
                self.vision_worksheet.append_row(["3_Year", ""])
                self.vision_worksheet.append_row(["1_Year", ""])

            # Initialize Reviews Worksheet
            try:
                self.reviews_worksheet = self.sh.worksheet("Reviews")
            except gspread.WorksheetNotFound:
                self.reviews_worksheet = self.sh.add_worksheet(title="Reviews", rows=50, cols=5)
                self.reviews_worksheet.append_row(["Week_Num", "Score", "Wins", "Lessons", "Date_Submitted"])

            # Initialize Settings Worksheet (for Strategic Blocks etc)
            try:
                self.settings_worksheet = self.sh.worksheet("Settings")
            except gspread.WorksheetNotFound:
                self.settings_worksheet = self.sh.add_worksheet(title="Settings", rows=20, cols=4)
                self.settings_worksheet.append_row(["Type", "Key", "Value", "Extra"])

            # Initialize Vision Images Worksheet
            try:
                self.vision_images_worksheet = self.sh.worksheet("Vision_Images")
            except gspread.WorksheetNotFound:
                self.vision_images_worksheet = self.sh.add_worksheet(title="Vision_Images", rows=5, cols=2)
                self.vision_images_worksheet.append_row(["Type", "Base64_Data"])

            # Initialize Metrics Worksheet
            try:
                self.metrics_worksheet = self.sh.worksheet("Metrics")
            except gspread.WorksheetNotFound:
                self.metrics_worksheet = self.sh.add_worksheet(title="Metrics", rows=50, cols=9)
                self.metrics_worksheet.append_row(["Goal_ID", "Metric_ID", "Title", "Type", "Starting_Value", "Target_Value", "Current_Value", "Unit", "Last_Updated"])
            
        except Exception as e:
            st.error(f"Database Connection Error: {e}")
            st.stop()
    
    def get_cycle(self) -> Cycle:
        """
        Loads the cycle from Google Sheets.
        """
        try:
            # 1. Load Tactics
            data = self.worksheet.get_all_records()
            if not data:
                cycle = self._create_default_cycle()
            else:
                df = pd.DataFrame(data)
                cycle = self._reconstruct_cycle(df)
            
            # 2. Load Vision
            try:
                vision_data = self.vision_worksheet.get_all_records()
                for row in vision_data:
                    if row.get('Type') == '3_Year':
                        cycle.vision_3_year = str(row.get('Content', ''))
                    elif row.get('Type') == '1_Year':
                        cycle.vision_1_year = str(row.get('Content', ''))
            except Exception as v_err:
                print(f"Vision load error: {v_err}")

            # 3. Load Reviews
            try:
                from src.models import WeeklyReview # Import here to avoid circular issues if any
                review_data = self.reviews_worksheet.get_all_records()
                for row in review_data:
                    # Basic validation
                    if row.get('Week_Num'):
                        cycle.reviews.append(WeeklyReview(
                            week_num=int(row['Week_Num']),
                            score=float(row['Score']),
                            wins=str(row.get('Wins', '')),
                            lessons=str(row.get('Lessons', '')),
                            date_submitted=date.fromisoformat(str(row['Date_Submitted'])) if row.get('Date_Submitted') else date.today()
                        ))
            except Exception as r_err:
                print(f"Reviews load error: {r_err}")

            # 4. Load Metrics
            try:
                from src.models import Metric, MetricType
                metric_data = self.metrics_worksheet.get_all_records()
                
                # Create a map of Goal_ID -> List[Metric]
                metrics_map = {}
                for row in metric_data:
                    g_id = str(row['Goal_ID'])
                    if g_id not in metrics_map:
                        metrics_map[g_id] = []
                    
                    try:
                        m = Metric(
                            id=str(row['Metric_ID']),
                            title=str(row['Title']),
                            type=MetricType(row['Type']),
                            starting_value=float(row['Starting_Value']) if row['Starting_Value'] != '' else 0.0,
                            target_value=float(row['Target_Value']),
                            current_value=float(row['Current_Value']) if row['Current_Value'] != '' else 0.0,
                            unit=str(row.get('Unit', '')),
                            last_updated=date.fromisoformat(str(row['Last_Updated'])) if row.get('Last_Updated') else date.today()
                        )
                        metrics_map[g_id].append(m)
                    except Exception as m_parse_err:
                        print(f"Error parsing metric row {row}: {m_parse_err}")

                # Attach metrics to goals
                for goal in cycle.goals:
                    if goal.id in metrics_map:
                        goal.metrics = metrics_map[goal.id]

            except Exception as m_err:
                print(f"Metrics load error: {m_err}")
                
            except Exception as m_err:
                print(f"Metrics load error: {m_err}")

            # 5. Load Strategic Blocks (Settings)
            try:
                from src.models import StrategicBlock
                settings_data = self.settings_worksheet.get_all_records()
                for row in settings_data:
                    if row.get('Type') == 'StrategicBlock':
                        cycle.strategic_blocks.append(StrategicBlock(
                            day_of_week=str(row['Key']),
                            start_time=str(row['Value']),
                            end_time=str(row['Extra'])
                        ))
            except Exception as s_err:
                print(f"Settings load error: {s_err}")
                
            return cycle
            
        except Exception as e:
            st.error(f"Error loading data: {e}")
            return self._create_default_cycle()

    def save_cycle(self, cycle: Cycle):
        """
        Flattens the cycle object and writes it to Google Sheets.
        """
        # 1. Save Tactics
        rows = []
        for goal in cycle.goals:
            for tactic in goal.tactics:
                rows.append({
                    "Goal_ID": goal.id,
                    "Goal_Title": goal.title,
                    "Tactic_ID": tactic.id,
                    "Tactic_Title": tactic.title,
                    "Due_Week": tactic.due_week,
                    "Status": tactic.status,
                    "Block_Type": tactic.block_type.value,
                    "Is_Completed": tactic.is_completed
                })
        
        try:
            if not rows:
                self.worksheet.clear()
                headers = ["Goal_ID", "Goal_Title", "Tactic_ID", "Tactic_Title", "Due_Week", "Status", "Block_Type", "Is_Completed"]
                self.worksheet.append_row(headers)
            else:
                df = pd.DataFrame(rows)
                data_to_write = [df.columns.values.tolist()] + df.values.tolist()
                self.worksheet.clear()
                self.worksheet.update(data_to_write)
            
            # 2. Save Vision
            self.vision_worksheet.clear()
            self.vision_worksheet.append_row(["Type", "Content"])
            self.vision_worksheet.append_row(["3_Year", cycle.vision_3_year])
            self.vision_worksheet.append_row(["1_Year", cycle.vision_1_year])

            # 3. Save Reviews
            self.reviews_worksheet.clear()
            self.reviews_worksheet.append_row(["Week_Num", "Score", "Wins", "Lessons", "Date_Submitted"])
            
            review_rows = []
            for r in cycle.reviews:
                review_rows.append([
                    r.week_num,
                    r.score,
                    r.wins,
                    r.lessons,
                    r.date_submitted.isoformat()
                ])
            
            if review_rows:
                self.reviews_worksheet.append_rows(review_rows)

            # 4. Save Metrics
            self.metrics_worksheet.clear()
            self.metrics_worksheet.append_row(["Goal_ID", "Metric_ID", "Title", "Type", "Starting_Value", "Target_Value", "Current_Value", "Unit", "Last_Updated"])
            
            metric_rows = []
            for goal in cycle.goals:
                for m in goal.metrics:
                    metric_rows.append([
                        goal.id,
                        m.id,
                        m.title,
                        m.type.value,
                        m.starting_value,
                        m.target_value,
                        m.current_value,
                        m.unit,
                        m.last_updated.isoformat()
                    ])
            
            if metric_rows:
                self.metrics_worksheet.append_rows(metric_rows)

            # 5. Save Strategic Blocks (Settings)
            self.settings_worksheet.clear()
            self.settings_worksheet.append_row(["Type", "Key", "Value", "Extra"])
            
            settings_rows = []
            for sb in cycle.strategic_blocks:
                settings_rows.append([
                    "StrategicBlock",
                    sb.day_of_week,
                    sb.start_time,
                    sb.end_time
                ])
            
            if settings_rows:
                self.settings_worksheet.append_rows(settings_rows)
                
            st.toast("Saved to Google Sheets!", icon="☁️")
            
        except Exception as e:
            st.error(f"Failed to save to Google Sheets: {e}")

    def _reconstruct_cycle(self, df: pd.DataFrame) -> Cycle:
        """
        Rebuilds the Cycle object hierarchy from the flat DataFrame.
        """
        # Ensure columns exist (handle potential schema drift)
        expected_cols = ["Goal_ID", "Goal_Title", "Tactic_ID", "Tactic_Title", "Due_Week", "Status", "Block_Type", "Is_Completed"]
        for col in expected_cols:
            if col not in df.columns:
                df[col] = None # Fill missing cols

        goals_map = {}
        
        for _, row in df.iterrows():
            g_id = str(row["Goal_ID"])
            
            # Create Goal if not exists
            if g_id not in goals_map:
                goals_map[g_id] = Goal(
                    id=g_id,
                    title=str(row["Goal_Title"]) if pd.notna(row["Goal_Title"]) else "Untitled Goal",
                    tactics=[]
                )
            
            # Create Tactic
            if pd.notna(row["Tactic_ID"]) and str(row["Tactic_ID"]) != "":
                # Handle boolean conversion safely
                is_comp = row["Is_Completed"]
                if isinstance(is_comp, str):
                    is_comp = is_comp.lower() == 'true'
                
                # Handle status mapping
                raw_status = str(row["Status"]) if pd.notna(row["Status"]) else "Not Started"
                if raw_status == "Pending":
                    raw_status = "Not Started"
                
                tactic = Tactic(
                    id=str(row["Tactic_ID"]),
                    title=str(row["Tactic_Title"]) if pd.notna(row["Tactic_Title"]) else "Untitled Tactic",
                    due_week=int(row["Due_Week"]) if pd.notna(row["Due_Week"]) and row["Due_Week"] != "" else 1,
                    status=raw_status,
                    block_type=row["Block_Type"] if pd.notna(row["Block_Type"]) else "None",
                    is_completed=bool(is_comp)
                )
                goals_map[g_id].tactics.append(tactic)
        
        return Cycle(
            id="c1", 
            start_date=date.today(),
            goals=list(goals_map.values())
        )

    def _create_default_cycle(self) -> Cycle:
        return Cycle(id="c1", start_date=date.today(), goals=[])

    def create_calendar_event(self, title: str, start_datetime: str, duration_minutes: int = 60):
        """
        Creates an event in the primary calendar.
        start_datetime should be ISO format string (e.g. '2023-11-21T10:00:00')
        """
        try:
            start_time = datetime.fromisoformat(start_datetime)
            end_time = start_time + timedelta(minutes=duration_minutes)
            
            event = {
                'summary': title,
                'start': {
                    'dateTime': start_time.isoformat(),
                    'timeZone': 'America/Los_Angeles', # Default to PST for now
                },
                'end': {
                    'dateTime': end_time.isoformat(),
                    'timeZone': 'America/Los_Angeles',
                },
            }

            # Get Calendar ID from secrets, default to 'primary' (which is the service account's calendar)
            calendar_id = st.secrets["connections"]["gsheets"].get("calendar_id", "primary")

            event = self.calendar_service.events().insert(calendarId=calendar_id, body=event).execute()
            return True, event.get('htmlLink')
        except Exception as e:
            return False, str(e)

    def archive_cycle(self, cycle: Cycle):
        """
        Archives the current cycle by duplicating sheets and clearing active ones.
        """
        try:
            archive_suffix = f"_{date.today().strftime('%Y-%m-%d')}"
            
            # 1. Duplicate Sheets
            self.sh.duplicate_sheet(self.worksheet.id, new_sheet_name=f"Tactics{archive_suffix}")
            self.sh.duplicate_sheet(self.reviews_worksheet.id, new_sheet_name=f"Reviews{archive_suffix}")
            self.sh.duplicate_sheet(self.metrics_worksheet.id, new_sheet_name=f"Metrics{archive_suffix}")
            
            # 2. Clear Active Sheets (Keep Headers)
            # Tactics
            self.worksheet.clear()
            self.worksheet.append_row(["Goal_ID", "Goal_Title", "Tactic_ID", "Tactic_Title", "Due_Week", "Status", "Block_Type", "Is_Completed"])
            
            # Reviews
            self.reviews_worksheet.clear()
            self.reviews_worksheet.append_row(["Week_Num", "Score", "Wins", "Lessons", "Date_Submitted"])
            
            # Metrics
            self.metrics_worksheet.clear()
            self.metrics_worksheet.append_row(["Goal_ID", "Metric_ID", "Title", "Type", "Starting_Value", "Target_Value", "Current_Value", "Unit", "Last_Updated"])
            
            # Note: We do NOT clear Vision or Settings as those persist or evolve.
            
            st.toast("Cycle Archived Successfully!", icon="📦")
            return True
        except Exception as e:
            st.error(f"Archival Failed: {e}")
            return False

    def save_vision_image(self, image_data: str):
        """
        Saves the base64 image string to the Vision_Images worksheet.
        """
        try:
            self.vision_images_worksheet.clear()
            self.vision_images_worksheet.append_row(["Type", "Base64_Data"])
            # Split data if too long? Cell limit is 50k chars. 
            # For now, assume it fits or user uploads small image.
            # We'll just save it in one cell for simplicity, but warn user if it fails.
            self.vision_images_worksheet.append_row(["Main_Vision_Board", image_data])
            return True
        except Exception as e:
            st.error(f"Failed to save image: {e}")
            return False

    def get_vision_image(self) -> str:
        """
        Retrieves the base64 image string.
        """
        try:
            records = self.vision_images_worksheet.get_all_records()
            for row in records:
                if row.get('Type') == 'Main_Vision_Board':
                    return row.get('Base64_Data', '')
            return ""
        except Exception as e:
            print(f"Image load error: {e}")
            return ""
