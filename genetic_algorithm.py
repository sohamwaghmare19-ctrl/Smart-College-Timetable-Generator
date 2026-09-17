import random
import numpy as np


class GeneticTimetable:

    def __init__(
        self,
        subjects,
        working_days,
        time_slots,
        classrooms,
        labs,
        population_size=80,
        generations=100,
        mutation_rate=0.10
    ):
        self.subjects = subjects
        self.working_days = working_days
        self.time_slots = time_slots
        self.classrooms = classrooms
        self.labs = labs

        self.population_size = population_size
        self.generations = generations
        self.mutation_rate = mutation_rate

        # Create unique lecture genes
        self.lecture_pool = []

        for subject in subjects:
            for lecture_number in range(int(subject["lectures"])):
                self.lecture_pool.append({
                    "id": len(self.lecture_pool),
                    "subject": subject["subject_name"],
                    "teacher": subject["teacher_name"],
                    "type": subject["subject_type"],
                    "lecture_number": lecture_number + 1
                })

        self.total_slots = (
            len(self.working_days)
            * len(self.time_slots)
        )

        if len(self.lecture_pool) > self.total_slots:
            raise ValueError(
                "Not enough timetable slots for all lectures."
            )

        self.fitness_history = []

    # =====================================================
    # CREATE CHROMOSOME
    # =====================================================

    def create_chromosome(self):

        chromosome = list(self.lecture_pool)

        free_slots = (
            self.total_slots
            - len(self.lecture_pool)
        )

        for _ in range(free_slots):
            chromosome.append(None)

        random.shuffle(chromosome)

        return chromosome

    # =====================================================
    # CREATE POPULATION
    # =====================================================

    def create_population(self):

        population = []

        for _ in range(self.population_size):
            population.append(
                self.create_chromosome()
            )

        return population

    # =====================================================
    # FITNESS FUNCTION
    # =====================================================

    def calculate_fitness(
        self,
        chromosome,
        return_details=False
    ):

        score = 100.0

        details = {
            "same_subject_day": 0,
            "consecutive_subject": 0,
            "consecutive_teacher": 0,
            "empty_day": 0,
            "daily_imbalance": 0,
            "long_gaps": 0,
            "subject_variety": 0
        }

        # Convert chromosome into daily timetable
        days = []

        index = 0

        for day in self.working_days:

            day_lectures = []

            for slot in self.time_slots:

                if index < len(chromosome):
                    day_lectures.append(
                        chromosome[index]
                    )

                index += 1

            days.append(day_lectures)

        # Daily analysis
        daily_counts = []

        for day_lectures in days:

            valid_lectures = [
                lecture
                for lecture in day_lectures
                if lecture is not None
            ]

            daily_counts.append(
                len(valid_lectures)
            )

            # Empty day penalty
            if (
                len(valid_lectures) == 0
                and len(self.lecture_pool) > 0
            ):
                score -= 5
                details["empty_day"] += 1

            # Same subject multiple times in a day
            subject_counts = {}

            for lecture in valid_lectures:

                subject = lecture["subject"]

                subject_counts[subject] = (
                    subject_counts.get(
                        subject,
                        0
                    ) + 1
                )

            for subject, count in subject_counts.items():

                if count > 1:

                    penalty = (
                        count - 1
                    ) * 2

                    score -= penalty

                    details[
                        "same_subject_day"
                    ] += penalty

            # Consecutive subjects / teachers
            for i in range(
                len(day_lectures) - 1
            ):

                current = day_lectures[i]

                next_lecture = day_lectures[i + 1]

                if (
                    current is not None
                    and next_lecture is not None
                ):

                    # Same subject consecutively
                    if (
                        current["subject"]
                        ==
                        next_lecture["subject"]
                    ):

                        score -= 10

                        details[
                            "consecutive_subject"
                        ] += 10

                    # Same teacher consecutively
                    if (
                        current["teacher"]
                        ==
                        next_lecture["teacher"]
                    ):

                        score -= 5

                        details[
                            "consecutive_teacher"
                        ] += 5

            # Long gaps
            lecture_positions = [
                i
                for i, lecture
                in enumerate(day_lectures)
                if lecture is not None
            ]

            if len(lecture_positions) >= 2:

                first = min(
                    lecture_positions
                )

                last = max(
                    lecture_positions
                )

                for position in range(
                    first,
                    last + 1
                ):

                    if (
                        day_lectures[position]
                        is None
                    ):

                        score -= 2

                        details[
                            "long_gaps"
                        ] += 2

            # Subject variety reward
            unique_subjects = len(
                set(
                    lecture["subject"]
                    for lecture in valid_lectures
                )
            )

            if unique_subjects >= 3:

                score += 4

                details[
                    "subject_variety"
                ] += 4

            elif unique_subjects == 2:

                score += 2

                details[
                    "subject_variety"
                ] += 2

        # Daily load balancing
        if daily_counts:

            average_load = np.mean(
                daily_counts
            )

            imbalance = sum(
                abs(
                    count - average_load
                )
                for count in daily_counts
            )

            penalty = imbalance * 1.5

            score -= penalty

            details[
                "daily_imbalance"
            ] = round(
                penalty,
                2
            )

        # Keep score between 0 and 100
        score = max(
            0,
            min(
                100,
                score
            )
        )

        if return_details:

            return (
                round(score, 2),
                details
            )

        return round(
            score,
            2
        )

    # =====================================================
    # TOURNAMENT SELECTION
    # =====================================================

    def selection(
        self,
        population,
        fitness_scores
    ):

        tournament_size = 5

        selected = []

        for _ in range(
            len(population)
        ):

            participants = random.sample(
                list(
                    zip(
                        population,
                        fitness_scores
                    )
                ),
                min(
                    tournament_size,
                    len(population)
                )
            )

            winner = max(
                participants,
                key=lambda x: x[1]
            )

            selected.append(
                winner[0]
            )

        return selected

    # =====================================================
    # TWO POINT CROSSOVER
    # =====================================================

    def crossover(
        self,
        parent1,
        parent2
    ):

        length = len(parent1)

        if length < 2:

            return (
                parent1[:],
                parent2[:]
            )

        point1, point2 = sorted(
            random.sample(
                range(length),
                2
            )
        )

        child1 = [None] * length
        child2 = [None] * length

        # Copy crossover section
        child1[
            point1:point2
        ] = parent1[
            point1:point2
        ]

        child2[
            point1:point2
        ] = parent2[
            point1:point2
        ]

        # Repair child
        def repair_child(
            child,
            parent
        ):

            used_ids = set()

            for gene in child:

                if gene is not None:

                    used_ids.add(
                        gene["id"]
                    )

            missing = []

            for gene in parent:

                if gene is None:
                    continue

                if gene["id"] not in used_ids:

                    missing.append(
                        gene
                    )

            missing_index = 0

            for i in range(length):

                if child[i] is None:

                    if (
                        missing_index
                        <
                        len(missing)
                    ):

                        child[i] = missing[
                            missing_index
                        ]

                        missing_index += 1

            return child

        child1 = repair_child(
            child1,
            parent2
        )

        child2 = repair_child(
            child2,
            parent1
        )

        return (
            child1,
            child2
        )

    # =====================================================
    # MUTATION
    # =====================================================

    def mutation(
        self,
        chromosome
    ):

        mutated = chromosome[:]

        if (
            random.random()
            <
            self.mutation_rate
        ):

            length = len(mutated)

            if length >= 2:

                index1, index2 = random.sample(
                    range(length),
                    2
                )

                mutated[index1], mutated[index2] = (
                    mutated[index2],
                    mutated[index1]
                )

        return mutated

    # =====================================================
    # ELITISM
    # =====================================================

    def get_elite(
        self,
        population,
        fitness_scores,
        elite_count=4
    ):

        combined = list(
            zip(
                population,
                fitness_scores
            )
        )

        combined.sort(
            key=lambda x: x[1],
            reverse=True
        )

        return [
            chromosome[:]
            for chromosome, fitness
            in combined[:elite_count]
        ]

    # =====================================================
    # CHROMOSOME TO TIMETABLE
    # =====================================================

    def chromosome_to_timetable(
        self,
        chromosome
    ):

        timetable = []

        index = 0

        for day in self.working_days:

            for time in self.time_slots:

                if index >= len(chromosome):
                    break

                gene = chromosome[index]

                if gene is None:

                    timetable.append({
                        "day": day,
                        "time": time,
                        "subject": "FREE",
                        "teacher": "-",
                        "room": "-",
                        "type": "Free"
                    })

                else:

                    # Lab room
                    if (
                        gene["type"].lower()
                        ==
                        "lab"
                    ):

                        if self.labs:
                            room = random.choice(
                                self.labs
                            )
                        else:
                            room = "Lab Required"

                    # Classroom
                    else:

                        if self.classrooms:
                            room = random.choice(
                                self.classrooms
                            )

                        elif self.labs:
                            room = random.choice(
                                self.labs
                            )

                        else:
                            room = "Room Required"

                    timetable.append({
                        "day": day,
                        "time": time,
                        "subject": gene["subject"],
                        "teacher": gene["teacher"],
                        "room": room,
                        "type": gene["type"]
                    })

                index += 1

        return timetable

    # =====================================================
    # RUN GENETIC ALGORITHM
    # =====================================================

    def run(self):

        print("\n")
        print(
            "=============================================="
        )
        print(
            "       AI GENETIC TIMETABLE OPTIMIZER"
        )
        print(
            "=============================================="
        )

        print(
            f"Population Size : {self.population_size}"
        )

        print(
            f"Generations     : {self.generations}"
        )

        print(
            f"Mutation Rate   : {self.mutation_rate}"
        )

        print(
            f"Total Lectures  : {len(self.lecture_pool)}"
        )

        print(
            f"Total Slots     : {self.total_slots}"
        )

        print(
            "=============================================="
        )

        # Initial population
        population = self.create_population()

        best_chromosome = None
        best_fitness = -1

        # Generations
        for generation in range(
            self.generations
        ):

            # Fitness evaluation
            fitness_scores = [
                self.calculate_fitness(
                    chromosome
                )
                for chromosome in population
            ]

            # Best chromosome
            generation_best_index = int(
                np.argmax(
                    fitness_scores
                )
            )

            generation_best_fitness = (
                fitness_scores[
                    generation_best_index
                ]
            )

            if (
                generation_best_fitness
                >
                best_fitness
            ):

                best_fitness = (
                    generation_best_fitness
                )

                best_chromosome = (
                    population[
                        generation_best_index
                    ][:]
                )

            self.fitness_history.append(
                best_fitness
            )

            print(
                f"Generation "
                f"{generation + 1:03d}"
                f" | Best Fitness: "
                f"{best_fitness:6.2f}%"
            )

            # Selection
            selected = self.selection(
                population,
                fitness_scores
            )

            # Elitism
            elite = self.get_elite(
                population,
                fitness_scores,
                elite_count=4
            )

            new_population = []

            new_population.extend(
                elite
            )

            # Crossover + Mutation
            while len(
                new_population
            ) < self.population_size:

                parent1 = random.choice(
                    selected
                )

                parent2 = random.choice(
                    selected
                )

                child1, child2 = self.crossover(
                    parent1,
                    parent2
                )

                child1 = self.mutation(
                    child1
                )

                child2 = self.mutation(
                    child2
                )

                new_population.append(
                    child1
                )

                if (
                    len(new_population)
                    <
                    self.population_size
                ):

                    new_population.append(
                        child2
                    )

            population = new_population

        # Final timetable
        timetable = self.chromosome_to_timetable(
            best_chromosome
        )

        final_fitness, details = (
            self.calculate_fitness(
                best_chromosome,
                return_details=True
            )
        )

        print(
            "=============================================="
        )
        print(
            "          OPTIMIZATION COMPLETE"
        )
        print(
            "=============================================="
        )

        print(
            f"Best Fitness : {final_fitness}%"
        )

        print(
            f"Generations  : {self.generations}"
        )

        print(
            "=============================================="
        )

        return {
            "timetable": timetable,
            "fitness": final_fitness,
            "fitness_history": self.fitness_history,
            "generations": self.generations,
            "population_size": self.population_size,
            "mutation_rate": self.mutation_rate,
            "fitness_details": details
        }