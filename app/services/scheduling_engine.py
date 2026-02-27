import random
from datetime import datetime, time, timedelta
from typing import List, Dict, Any, Optional, Set
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.timetable import (
    TimetableConfig,
    TimetableVersion,
    TimetableSlot,
    Room,
    TeacherConstraint,
    SubjectConstraint,
)
from app.models.lms import Class, Section, ClassSubject, TeacherSubject, Subject
from app.models.users import EnrolledEmployee


class SchedulingEngine:
    def __init__(self, db: Session, academic_year_id: UUID):
        self.db = db
        self.academic_year_id = academic_year_id
        self.config = self._get_config()
        self.rooms = self.db.query(Room).filter(Room.is_active == True).all()
        self.teachers = self.db.query(EnrolledEmployee).filter(EnrolledEmployee.is_active == True).all()
        
        # Cache constraints
        self.teacher_constraints = {
            c.teacher_id: c for c in self.db.query(TeacherConstraint)
            .filter(TeacherConstraint.academic_year_id == academic_year_id).all()
        }
        self.subject_constraints = {
            c.class_subject_id: c for c in self.db.query(SubjectConstraint).all()
        }

    def _get_config(self) -> TimetableConfig:
        config = self.db.query(TimetableConfig).filter(
            TimetableConfig.academic_year_id == self.academic_year_id
        ).first()
        if not config:
            raise ValueError("Timetable configuration not found for this academic year")
        return config

    def generate(self, version_name: str, class_ids: Optional[List[UUID]] = None) -> TimetableVersion:
        """Main entry point for generation"""
        # 1. Create new version
        version = TimetableVersion(
            name=version_name,
            academic_year_id=self.academic_year_id,
            is_active=False
        )
        self.db.add(version)
        self.db.flush()

        # 2. Get classes to process
        query = self.db.query(Class).filter(Class.academic_year_id == self.academic_year_id)
        if class_ids:
            query = query.filter(Class.id.in_(class_ids))
        classes = query.all()

        print(f"[ENGINE] Found {len(classes)} classes for academic year {self.academic_year_id}")

        # 3. Initialize global teacher load tracking
        working_days = self.config.working_days
        periods_per_day = self.config.periods_per_day
        self.teacher_busy = {day: [set() for _ in range(periods_per_day)] for day in working_days}
        self.room_busy = {day: [set() for _ in range(periods_per_day)] for day in working_days}
        self.result_slots = []
        self.teacher_day_load = {t.id: {day: 0 for day in working_days} for t in self.teachers}
        self.teacher_week_load = {t.id: 0 for t in self.teachers}

        # 4. Build teacher-subject specialization map for auto-assignment
        self._build_teacher_subject_map()

        # 5. Process each class/section
        generated_count = 0
        print(f"[ENGINE] Starting generation loop for {len(classes)} classes...")
        for cls in classes:
            sections = cls.sections if cls.sections else [None]
            print(f"  [CLASS] Processing {cls.name} with {len(sections)} sections")
            for section in sections:
                if self._generate_for_section(version.id, cls, section):
                    generated_count += 1
                else:
                    print(f"    [FAILED] {cls.name} Section {section.name if section else 'N/A'}")

        if generated_count == 0:
            self.db.rollback()
            return None
            
        self.db.commit()
        return version

    def _build_teacher_subject_map(self):
        """
        Build a lookup: subject_id -> [(teacher, priority)].
        Uses fuzzy matching between teacher specialization and subject names.
        """
        self.teacher_subject_map: Dict[str, List] = {}
        
        subjects = self.db.query(Subject).all()
        # Pre-alias map for common variations
        alias_map = {
            "math": "mathematics",
            "stat": "statistics",
            "bio": "biology",
            "chem": "chemistry",
            "phy": "physics",
            "cs": "computer science",
            "it": "information technology",
            "eng": "english",
            "isl": "islamiat",
        }

        def normalize(text):
            if not text: return set()
            # Remove punctuation and split into words
            words = "".join(c if c.isalnum() else " " for c in text.lower()).split()
            # Apply aliases
            normalized = {alias_map.get(w, w) for w in words}
            return normalized

        subject_tokens = {s.id: normalize(s.name) for s in subjects}
        
        print(f"[ENGINE] Building teacher-subject map for {len(subjects)} subjects...")

        for teacher in self.teachers:
            if not teacher.subject:
                continue
            
            teacher_tokens = normalize(teacher.subject.replace(";", ","))
            
            for subject_id, tokens in subject_tokens.items():
                if not tokens: continue
                
                # Check for word overlap
                # If any word from the subject is in the teacher's specialties
                # OR if any specialty is in the subject name
                match = False
                if tokens.intersection(teacher_tokens):
                    match = True
                
                if match:
                    if subject_id not in self.teacher_subject_map:
                        self.teacher_subject_map[subject_id] = []
                    
                    if teacher.id not in [t.id for t, _ in self.teacher_subject_map[subject_id]]:
                        name = f"{teacher.first_name} {teacher.last_name}"
                        subj_name = next((s.name for s in subjects if s.id == subject_id), "Unknown")
                        print(f"  [MATCH] Teacher {name} ({teacher.subject}) -> {subj_name}")
                        self.teacher_subject_map[subject_id].append((teacher, 1))  # 1 = specialist

    def _pick_teacher_for_subject(self, subject_id: UUID, subject_name: str = "") -> Optional[EnrolledEmployee]:
        """
        Pick the best available teacher for a subject.
        Priority: 1) specialist with lowest week load, 2) any teacher with lowest week load.
        """
        candidates = self.teacher_subject_map.get(subject_id, [])
        
        if candidates:
            # Sort specialists by current week load (ascending = least loaded first)
            specialists = sorted(
                [t for t, _ in candidates],
                key=lambda t: self.teacher_week_load.get(t.id, 0)
            )
            top = specialists[0]
            print(f"  [PICK] Specialist: {top.first_name} {top.last_name} for {subject_name} (Load: {self.teacher_week_load.get(top.id, 0)})")
            return top
        
        # Fallback: pick any active teacher with lowest load
        active_teachers = [t for t in self.teachers if t.system_role == "teacher"]
        if not active_teachers:
            active_teachers = self.teachers  # All employees as last resort
        
        if not active_teachers:
            print(f"  [PICK] FAILED: No teachers available at all for {subject_name}")
            return None
        
        top = min(active_teachers, key=lambda t: self.teacher_week_load.get(t.id, 0))
        print(f"  [PICK] Fallback: {top.first_name} {top.last_name} for {subject_name} (No specialist found, Load: {self.teacher_week_load.get(top.id, 0)})")
        return top

    def _get_section_requirements(self, cls: Class, section: Optional[Section]) -> List[Dict]:
        """
        Build subject requirements for a class/section, auto-assigning teachers by specialization.
        Falls back to pre-existing TeacherSubject records if available, otherwise auto-assigns.
        """
        class_subjects = (
            self.db.query(ClassSubject, Subject.name)
            .join(Subject, ClassSubject.subject_id == Subject.id)
            .filter(ClassSubject.class_id == cls.id)
            .all()
        )
        
        if not class_subjects:
            print(f"No subjects found for class {cls.name}. Assign subjects to this class first.")
            return []

        print(f"[ENGINE] Fetching requirements for {cls.name} (Section: {section.name if section else 'N/A'})...")
        requirements = []
        for cs, subj_name in class_subjects:
            # 1. Try existing manual TeacherSubject assignment first
            ts_query = self.db.query(TeacherSubject).filter(
                TeacherSubject.class_subject_id == cs.id
            )
            if section:
                ts_query = ts_query.filter(TeacherSubject.section_id == section.id)
            ts = ts_query.first()
            
            if ts:
                teacher_id = ts.teacher_id
                print(f"  [MANUAL] Using pre-assigned teacher for {subj_name}")
            else:
                # 2. Auto-assign by specialization
                teacher = self._pick_teacher_for_subject(cs.subject_id, subj_name)
                if not teacher:
                    continue
                teacher_id = teacher.id
            
            constraints = self.subject_constraints.get(cs.id)
            
            requirements.append({
                "class_subject_id": cs.id,
                "subject_id": cs.subject_id,
                "teacher_id": teacher_id,
                "quota": cs.periods_per_week or 1,
                "is_lab": constraints.is_lab if constraints else False,
                "requires_double_period": constraints.requires_double_period if constraints else False,
                "difficulty": constraints.difficulty_level if constraints else 1,
                "is_core": constraints.is_core if constraints else False
            })
        
        return requirements

    def _generate_for_section(self, version_id: UUID, cls: Class, section: Optional[Section]) -> bool:
        requirements = self._get_section_requirements(cls, section)
        if not requirements:
            print(f"[ENGINE] No requirements for {cls.name} / Section {section.name if section else 'N/A'}")
            return False

        # Heuristic: Most Constrained Variable (MCV)
        requirements.sort(key=lambda x: (x['is_lab'], x['requires_double_period'], x['quota']), reverse=True)

        working_days = self.config.working_days
        periods_per_day = self.config.periods_per_day

        print(f"[ENGINE] Generating for {cls.name} | {len(requirements)} subjects | {len(working_days)} days | {periods_per_day} periods/day")
        print(f"[ENGINE] Rooms available: {len(self.rooms)}")
        
        # Initialize timetable grid
        timetable = {day: [None for _ in range(periods_per_day)] for day in working_days}
        
        # Pre-fill Breaks
        if self.config.break_details:
            for brk in self.config.break_details:
                after_p = brk.get('after_period')
                if after_p is not None and after_p < periods_per_day:
                    for day in working_days:
                        timetable[day][after_p] = "BREAK"

        # Flatten requirements into a pool
        period_pool = []
        for req in requirements:
            q = req['quota']
            if req['requires_double_period']:
                while q >= 2:
                    period_pool.append({**req, "type": "double"})
                    q -= 2
            for _ in range(q):
                period_pool.append({**req, "type": "single"})

        total_slots = len(working_days) * periods_per_day
        break_slots = sum(1 for d in working_days for s in timetable[d] if s == "BREAK")
        available_slots = total_slots - break_slots
        print(f"[ENGINE] Period pool size: {len(period_pool)} | Available slots: {available_slots}")

        if len(period_pool) > available_slots:
            print(f"[ENGINE] WARNING: More periods required ({len(period_pool)}) than available slots ({available_slots})!")
            # Truncate pool to fit
            period_pool = period_pool[:available_slots]

        if self._backtrack(timetable, period_pool, 0):
            self._save_timetable(version_id, cls, section, timetable)
            print(f"[ENGINE] SUCCESS: Generated timetable for {cls.name}")
            return True
        print(f"[ENGINE] FAILED: Backtracking exhausted all possibilities for {cls.name}")
        return False

    def _backtrack(self, timetable, period_pool, pool_index) -> bool:
        if pool_index >= len(period_pool):
            return True

        item = period_pool[pool_index]
        days = list(timetable.keys())
        random.shuffle(days) # Stochastic for variety

        for day in days:
            periods_per_day = len(timetable[day])
            slots_to_check = range(periods_per_day)
            
            for p_idx in slots_to_check:
                if item['type'] == "double":
                    if p_idx + 1 >= periods_per_day: continue # Need two slots
                    if timetable[day][p_idx] is not None or timetable[day][p_idx+1] is not None: continue
                    
                    # Check constraints for both slots
                    if self._is_valid(item, day, p_idx, timetable) and self._is_valid(item, day, p_idx+1, timetable):
                        # Assign
                        self._assign(timetable, day, p_idx, item)
                        self._assign(timetable, day, p_idx+1, item)
                        
                        if self._backtrack(timetable, period_pool, pool_index + 1):
                            return True
                        
                        # Unassign
                        self._unassign(timetable, day, p_idx, item)
                        self._unassign(timetable, day, p_idx+1, item)
                else:
                    if timetable[day][p_idx] is not None: continue
                    
                    if self._is_valid(item, day, p_idx, timetable):
                        self._assign(timetable, day, p_idx, item)
                        if self._backtrack(timetable, period_pool, pool_index + 1):
                            return True
                        self._unassign(timetable, day, p_idx, item)
        
        return False

    def _is_valid(self, item, day, p_idx, timetable) -> bool:
        teacher_id = item['teacher_id']

        # 1. Teacher Clash
        if teacher_id in self.teacher_busy[day][p_idx]:
            return False
        
        # 2. Teacher Unavailable
        t_const = self.teacher_constraints.get(teacher_id)
        if t_const and t_const.unavailable_slots:
            for slot in t_const.unavailable_slots:
                if slot.get('day') == day and slot.get('period_index') == p_idx:
                    return False

        # 3. Teacher Load Limits
        max_day = (t_const.max_periods_per_day if t_const and t_const.max_periods_per_day
                   else self.config.max_periods_per_teacher_day)
        max_week = (t_const.max_periods_per_week if t_const and t_const.max_periods_per_week
                    else self.config.max_periods_per_teacher_week)

        day_load = self.teacher_day_load.get(teacher_id, {}).get(day, 0)
        week_load = self.teacher_week_load.get(teacher_id, 0)

        if max_day and day_load >= max_day:
            return False
        if max_week and week_load >= max_week:
            return False

        # 4. Room Availability (optional — room_id is nullable in DB)
        if self.rooms:
            room = self._find_available_room(item, day, p_idx)
            if not room:
                return False
            
        return True

    def _find_available_room(self, item, day, p_idx) -> Optional[Room]:
        possible_rooms = [r for r in self.rooms if r.id not in self.room_busy[day][p_idx]]
        
        if item.get('is_lab'):
            possible_rooms = [r for r in possible_rooms if r.is_lab]
        else:
            # Prefer non-lab for normal subjects
            non_labs = [r for r in possible_rooms if not r.is_lab]
            if non_labs: possible_rooms = non_labs
            
        if not possible_rooms:
            return None
        return possible_rooms[0]

    def _assign(self, timetable, day, p_idx, item):
        teacher_id = item['teacher_id']
        room_id = None
        if self.rooms:
            room = self._find_available_room(item, day, p_idx)
            if room:
                room_id = room.id
                self.room_busy[day][p_idx].add(room_id)
        assignment = {**item, "room_id": room_id}
        timetable[day][p_idx] = assignment
        self.teacher_busy[day][p_idx].add(teacher_id)
        # Track load (safe get in case teacher was auto-assigned and not in initial dict)
        if teacher_id not in self.teacher_day_load:
            self.teacher_day_load[teacher_id] = {d: 0 for d in self.config.working_days}
        if teacher_id not in self.teacher_week_load:
            self.teacher_week_load[teacher_id] = 0
        self.teacher_day_load[teacher_id][day] += 1
        self.teacher_week_load[teacher_id] += 1

    def _unassign(self, timetable, day, p_idx, item):
        teacher_id = item['teacher_id']
        assignment = timetable[day][p_idx]
        if assignment and isinstance(assignment, dict):
            room_id = assignment.get('room_id')
            self.teacher_busy[day][p_idx].discard(teacher_id)
            if room_id:
                self.room_busy[day][p_idx].discard(room_id)
            if teacher_id in self.teacher_day_load:
                self.teacher_day_load[teacher_id][day] = max(0, self.teacher_day_load[teacher_id].get(day, 0) - 1)
            if teacher_id in self.teacher_week_load:
                self.teacher_week_load[teacher_id] = max(0, self.teacher_week_load.get(teacher_id, 0) - 1)
            timetable[day][p_idx] = None

    def _save_timetable(self, version_id: UUID, cls: Class, section: Optional[Section], timetable: Dict):
        start_time_base = self.config.start_time
        duration = self.config.slot_duration
        
        for day, slots in timetable.items():
            for i, slot_data in enumerate(slots):
                if slot_data is None or slot_data == "BREAK":
                    continue # Empty slot / Break
                
                # Calculate times
                # Note: This doesn't account for breaks properly yet, 
                # but following the requirements architecture.
                current_time = datetime.combine(datetime.today(), start_time_base) + timedelta(minutes=i * duration)
                end_time = current_time + timedelta(minutes=duration)
                
                slot = TimetableSlot(
                    version_id=version_id,
                    class_id=cls.id,
                    section_id=section.id if section else None,
                    subject_id=slot_data['subject_id'],
                    teacher_id=slot_data['teacher_id'],
                    room_id=slot_data['room_id'],
                    day=day,
                    period_index=i,
                    start_time=current_time.time(),
                    end_time=end_time.time(),
                    is_double_period=slot_data['type'] == 'double'
                )
                self.db.add(slot)
