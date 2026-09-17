from flask import Flask, render_template, request, jsonify
import database
from genetic_algorithm import GeneticTimetable

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import os
from datetime import datetime, timedelta


app = Flask(__name__)


# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():
    return render_template("index.html")


# =========================================================
# SETUP PAGE
# =========================================================

@app.route("/setup")
def setup():
    return render_template("setup.html")


# =========================================================
# DATABASE TEST
# =========================================================

@app.route("/test-db")
def test_db():

    return jsonify({

        "status": "success",

        "message":
            "Database connected successfully!"

    })


# =========================================================
# FITNESS GRAPH
# =========================================================

def create_fitness_graph(fitness_history):

    os.makedirs(
        "static",
        exist_ok=True
    )

    graph_path = os.path.join(
        "static",
        "fitness_graph.png"
    )

    plt.close("all")

    plt.figure(
        figsize=(10, 5)
    )

    generations = list(
        range(
            1,
            len(fitness_history) + 1
        )
    )

    plt.plot(
        generations,
        fitness_history,
        marker="o",
        linewidth=2,
        markersize=3
    )

    plt.title(
        "Genetic Algorithm Fitness Improvement"
    )

    plt.xlabel(
        "Generation"
    )

    plt.ylabel(
        "Fitness Score"
    )

    plt.grid(
        True,
        alpha=0.3
    )

    plt.tight_layout()

    plt.savefig(
        graph_path,
        dpi=150
    )

    plt.close()

    return graph_path


# =========================================================
# GENERATE TIME SLOTS
# =========================================================

def generate_time_slots(
    start_time,
    end_time,
    lunch_enabled=False,
    lunch_start="12:00",
    lunch_end="13:00"
):

    try:

        start = datetime.strptime(
            start_time,
            "%H:%M"
        )

        end = datetime.strptime(
            end_time,
            "%H:%M"
        )

        lunch_start_dt = datetime.strptime(
            lunch_start,
            "%H:%M"
        )

        lunch_end_dt = datetime.strptime(
            lunch_end,
            "%H:%M"
        )


        slots = []

        current = start


        while (
            current + timedelta(hours=1)
            <= end
        ):

            slot_start = current

            slot_end = (
                current +
                timedelta(hours=1)
            )


            # Skip lunch slot
            if lunch_enabled:

                if (
                    slot_start >= lunch_start_dt
                    and
                    slot_end <= lunch_end_dt
                ):

                    current = slot_end

                    continue


            slot = (
                f"{slot_start.strftime('%H:%M')}"
                "-"
                f"{slot_end.strftime('%H:%M')}"
            )


            slots.append(slot)

            current = slot_end


        return slots


    except ValueError:

        return []


# =========================================================
# GENERATE TIMETABLE
# =========================================================

@app.route(
    "/generate",
    methods=["POST"]
)
def generate():

    try:

        data = request.get_json()


        if not data:

            return jsonify({

                "success": False,

                "message":
                    "No data received."

            })


        # -------------------------------------------------
        # BASIC DATA
        # -------------------------------------------------

        class_name = (
            data
            .get("class_name", "")
            .strip()
        )

        semester = (
            data
            .get("semester", "")
            .strip()
        )

        start_time = (
            data
            .get(
                "start_time",
                "09:00"
            )
        )

        end_time = (
            data
            .get(
                "end_time",
                "16:00"
            )
        )

        working_days = (
            data
            .get(
                "working_days",
                []
            )
        )

        subjects_data = (
            data
            .get(
                "subjects",
                []
            )
        )

        classrooms = (
            data
            .get(
                "classrooms",
                []
            )
        )

        labs = (
            data
            .get(
                "labs",
                []
            )
        )


        # -------------------------------------------------
        # LUNCH
        # -------------------------------------------------

        lunch_enabled = bool(
            data.get(
                "lunch_enabled",
                False
            )
        )

        lunch_start = (
            data.get(
                "lunch_start",
                "12:00"
            )
        )

        lunch_end = (
            data.get(
                "lunch_end",
                "13:00"
            )
        )


        # -------------------------------------------------
        # VALIDATION
        # -------------------------------------------------

        if not class_name:

            return jsonify({

                "success": False,

                "message":
                    "Please enter Class / Division."

            })


        if not semester:

            return jsonify({

                "success": False,

                "message":
                    "Please select Semester."

            })


        if not working_days:

            return jsonify({

                "success": False,

                "message":
                    "Please select at least one working day."

            })


        if not subjects_data:

            return jsonify({

                "success": False,

                "message":
                    "Please add at least one subject."

            })


        if (
            not classrooms
            and
            not labs
        ):

            return jsonify({

                "success": False,

                "message":
                    "Please add at least one classroom or lab."

            })


        # -------------------------------------------------
        # LUNCH VALIDATION
        # -------------------------------------------------

        if lunch_enabled:

            if (
                not lunch_start
                or
                not lunch_end
            ):

                return jsonify({

                    "success": False,

                    "message":
                        "Please provide lunch timing."

                })


            if lunch_start >= lunch_end:

                return jsonify({

                    "success": False,

                    "message":
                        "Lunch end time must be after lunch start time."

                })


        # -------------------------------------------------
        # CLEAR OLD DATABASE
        # -------------------------------------------------

        database.clear_old_data()


        database.save_setup(

            class_name,

            semester,

            start_time,

            end_time,

            working_days

        )


        # -------------------------------------------------
        # PREPARE SUBJECTS
        # -------------------------------------------------

        subjects = []

        teachers = []


        for item in subjects_data:


            subject_name = (
                item
                .get(
                    "subject_name",
                    ""
                )
                .strip()
            )


            teacher_name = (
                item
                .get(
                    "teacher_name",
                    ""
                )
                .strip()
            )


            subject_type = (
                item
                .get(
                    "subject_type",
                    "Theory"
                )
            )


            try:

                lectures = int(
                    item.get(
                        "lectures",
                        1
                    )
                )

            except:

                lectures = 1


            if not subject_name:

                continue


            if not teacher_name:

                continue


            if lectures < 1:

                lectures = 1


            subject = {
                "subject_name": subject_name,
                "teacher_name": teacher_name,
                "lectures": lectures,
                "subject_type": subject_type
            }


            subjects.append(
                subject
            )


            if (
                teacher_name
                not in teachers
            ):

                teachers.append(
                    teacher_name
                )


            database.save_subject(

                subject_name,

                teacher_name,

                lectures,

                subject_type

            )


        if not subjects:

            return jsonify({

                "success": False,

                "message":
                    "Please enter valid subject and teacher details."

            })


        # -------------------------------------------------
        # ROOMS
        # -------------------------------------------------

        valid_classrooms = [

            room.strip()

            for room in classrooms

            if room.strip()

        ]


        valid_labs = [

            room.strip()

            for room in labs

            if room.strip()

        ]


        for room in valid_classrooms:

            database.save_room(
                room,
                "Classroom"
            )


        for room in valid_labs:

            database.save_room(
                room,
                "Lab"
            )


        all_rooms = (
            valid_classrooms
            +
            valid_labs
        )


        # -------------------------------------------------
        # TIME SLOTS
        # -------------------------------------------------

        time_slots = generate_time_slots(

            start_time,

            end_time,

            lunch_enabled,

            lunch_start,

            lunch_end

        )


        if not time_slots:

            return jsonify({

                "success": False,

                "message":
                    "Could not create valid time slots."

            })


        # -------------------------------------------------
        # CHECK TOTAL LECTURES
        # -------------------------------------------------

        total_lectures = sum(

            int(
                subject["lectures"]
            )

            for subject
            in subjects

        )


        available_slots = (
            len(time_slots)
            *
            len(working_days)
        )


        if total_lectures > available_slots:

            return jsonify({

                "success": False,

                "message":
                    f"Too many lectures. "
                    f"You entered {total_lectures} lectures, "
                    f"but only {available_slots} lecture slots are available."

            })


        # -------------------------------------------------
        # AI INFORMATION
        # -------------------------------------------------

        print()
        print("=" * 65)
        print("🧬 AI SMART TIMETABLE GENERATOR")
        print("=" * 65)

        print(
            "Class:",
            class_name
        )

        print(
            "Semester:",
            semester
        )

        print(
            "Subjects:",
            len(subjects)
        )

        print(
            "Teachers:",
            len(teachers)
        )

        print(
            "Working Days:",
            len(working_days)
        )

        print(
            "Available Lecture Slots:",
            available_slots
        )

        print(
            "Required Lectures:",
            total_lectures
        )

        print(
            "Population Size:",
            80
        )

        print(
            "Generations:",
            100
        )

        print(
            "Mutation Rate:",
            "10%"
        )

        print("=" * 65)
        print("🧬 RUNNING GENETIC ALGORITHM")
        print("=" * 65)


        # -------------------------------------------------
        # GENETIC ALGORITHM
        # -------------------------------------------------

        ga = GeneticTimetable(
            subjects=subjects,
            working_days=working_days,
            time_slots=time_slots,
            classrooms=valid_classrooms,
            labs=valid_labs,
            population_size=80,
            generations=100,
            mutation_rate=0.10
        )

        result = ga.run()


        if not result:

            return jsonify({

                "success": False,

                "message":
                    "Genetic Algorithm returned no result."

            })


        # -------------------------------------------------
        # RESULT
        # -------------------------------------------------

        best_timetable = (
            result.get(
                "timetable"
            )
        )


        best_fitness = (
            result.get(
                "fitness",
                0
            )
        )


        generations = (
            result.get(
                "generations",
                0
            )
        )


        fitness_history = (
            result.get(
                "fitness_history",
                []
            )
        )


        if not best_timetable:

            return jsonify({

                "success": False,

                "message":
                    "Could not generate timetable."

            })


        # -------------------------------------------------
        # ADD LUNCH BREAK
        # -------------------------------------------------

        if lunch_enabled:

            combined_timetable = []


            for day in working_days:

                day_rows = [

                    row

                    for row
                    in best_timetable

                    if row["day"] == day

                ]


                inserted_lunch = False


                for row in day_rows:

                    if (
                        not inserted_lunch
                        and
                        row["time"].split("-")[0]
                        >= lunch_start
                    ):

                        combined_timetable.append({

                            "day":
                                day,

                            "time":
                                f"{lunch_start}-{lunch_end}",

                            "subject":
                                "LUNCH BREAK",

                            "teacher":
                                "-",

                            "room":
                                "-",

                            "type":
                                "Break",

                            "lecture":
                                0

                        })

                        inserted_lunch = True


                    combined_timetable.append(
                        row
                    )


                if not inserted_lunch:

                    combined_timetable.append({

                        "day":
                            day,

                        "time":
                            f"{lunch_start}-{lunch_end}",

                        "subject":
                            "LUNCH BREAK",

                        "teacher":
                            "-",

                        "room":
                            "-",

                        "type":
                            "Break",

                        "lecture":
                            0

                    })


            best_timetable = (
                combined_timetable
            )


        # -------------------------------------------------
        # FITNESS GRAPH
        # -------------------------------------------------

        if fitness_history:

            create_fitness_graph(
                fitness_history
            )


        # -------------------------------------------------
        # SAVE
        # -------------------------------------------------

        database.save_generated_timetable(
            best_timetable
        )


        # -------------------------------------------------
        # SAVE AI STATS
        # -------------------------------------------------

        app.config[
            "fitness_history"
        ] = fitness_history


        app.config[
            "best_fitness"
        ] = best_fitness


        app.config[
            "generations"
        ] = generations


        app.config[
            "population_size"
        ] = 80


        app.config[
            "mutation_rate"
        ] = 10


        app.config[
            "total_lectures"
        ] = total_lectures


        app.config[
            "total_subjects"
        ] = len(subjects)


        app.config[
            "class_name"
        ] = class_name


        app.config[
            "semester"
        ] = semester


        app.config[
            "working_days"
        ] = working_days


        print()
        print("=" * 65)
        print("✅ AI OPTIMIZATION COMPLETED")
        print("=" * 65)

        print(
            "🏆 Best Fitness:",
            best_fitness
        )

        print(
            "🔄 Generations:",
            generations
        )

        print(
            "📚 Total Lectures:",
            total_lectures
        )

        print("=" * 65)


        return jsonify({

            "success":
                True,

            "message":
                "AI timetable generated successfully!",

            "fitness":
                best_fitness,

            "generations":
                generations,

            "lectures":
                total_lectures

        })


    except Exception as e:

        print()
        print(
            "❌ ERROR:",
            str(e)
        )

        return jsonify({

            "success":
                False,

            "message":
                str(e)

        })


# =========================================================
# TIMETABLE PAGE
# =========================================================

@app.route("/timetable")
def timetable():

    timetable_data = (
        database
        .get_generated_timetable()
    )


    fitness = app.config.get(
        "best_fitness",
        0
    )


    generations = app.config.get(
        "generations",
        0
    )


    population_size = app.config.get(
        "population_size",
        80
    )


    mutation_rate = app.config.get(
        "mutation_rate",
        10
    )


    total_lectures = app.config.get(
        "total_lectures",
        0
    )


    total_subjects = app.config.get(
        "total_subjects",
        0
    )


    class_name = app.config.get(
        "class_name",
        ""
    )


    semester = app.config.get(
        "semester",
        ""
    )


    return render_template(

        "timetable.html",

        timetable=timetable_data,

        fitness=fitness,

        generations=generations,

        population_size=population_size,

        mutation_rate=mutation_rate,

        total_lectures=total_lectures,

        total_subjects=total_subjects,

        class_name=class_name,

        semester=semester

    )


# =========================================================
# START FLASK
# =========================================================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)