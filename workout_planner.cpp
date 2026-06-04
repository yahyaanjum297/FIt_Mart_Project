/*
═══════════════════════════════════════════════════════════════
  FITMART — C++ Workout Plan Generator v2.0
  Compile:  g++ -O2 -std=c++17 -o workout.exe workout_planner.cpp
  Usage:    ./workout.exe  (reads from stdin)
  Input:    age\nweight\nheight\ninjury\ndisease\ngoal\nlocation\n
═══════════════════════════════════════════════════════════════
*/
#include <iostream>
#include <string>
#include <vector>
#include <map>
#include <cmath>
#include <sstream>
#include <algorithm>
#include <iomanip>

// ─── EXERCISE DATA ─────────────────────────────────────────
struct Exercise {
    std::string name;
    std::string muscle;
    std::string equipment;   // "barbell","dumbbell","bodyweight","machine","cable"
    int         sets;
    std::string reps;        // "8-12" or "12-15"
    std::string rest;        // "60s", "90s", "2-3min"
    bool        gymOnly;
};

std::vector<Exercise> GYM_EXERCISES = {
    // CHEST
    {"Barbell Bench Press",     "Chest",     "barbell",   4, "6-10",  "2-3min", true},
    {"Incline Dumbbell Press",  "Chest",     "dumbbell",  3, "10-12", "90s",    true},
    {"Cable Flyes",             "Chest",     "cable",     3, "12-15", "60s",    true},
    {"Dumbbell Pullover",       "Chest",     "dumbbell",  3, "12-15", "60s",    true},
    {"Chest Dips",              "Chest",     "bodyweight",3, "10-15", "90s",    false},
    // BACK
    {"Barbell Deadlift",        "Back",      "barbell",   4, "5-8",   "3min",   true},
    {"Pull-Ups",                "Back",      "bodyweight",4, "8-12",  "90s",    false},
    {"Lat Pulldown",            "Back",      "machine",   3, "10-12", "90s",    true},
    {"Seated Cable Row",        "Back",      "cable",     3, "10-12", "90s",    true},
    {"Dumbbell Row",            "Back",      "dumbbell",  3, "10-12", "90s",    false},
    // SHOULDERS
    {"Overhead Press",          "Shoulders", "barbell",   4, "8-10",  "2min",   true},
    {"Dumbbell Lateral Raises", "Shoulders", "dumbbell",  4, "12-15", "60s",    false},
    {"Face Pulls",              "Shoulders", "cable",     3, "15-20", "60s",    true},
    {"Rear Delt Flyes",         "Shoulders", "dumbbell",  3, "15-20", "60s",    false},
    // ARMS
    {"Barbell Curls",           "Biceps",    "barbell",   3, "10-12", "60s",    true},
    {"Hammer Curls",            "Biceps",    "dumbbell",  3, "10-12", "60s",    false},
    {"Tricep Pushdown",         "Triceps",   "cable",     3, "12-15", "60s",    true},
    {"Skull Crushers",          "Triceps",   "barbell",   3, "10-12", "90s",    true},
    {"Overhead Tricep Ext.",    "Triceps",   "dumbbell",  3, "12-15", "60s",    false},
    // LEGS
    {"Barbell Squat",           "Quads",     "barbell",   4, "6-10",  "2-3min", true},
    {"Romanian Deadlift",       "Hamstrings","barbell",   3, "10-12", "2min",   true},
    {"Leg Press",               "Quads",     "machine",   3, "12-15", "90s",    true},
    {"Leg Curl",                "Hamstrings","machine",   3, "12-15", "90s",    true},
    {"Calf Raises",             "Calves",    "machine",   4, "15-20", "60s",    true},
    {"Lunges",                  "Quads",     "bodyweight",3, "12/leg","90s",    false},
    // CORE
    {"Plank",                   "Core",      "bodyweight",3, "60s",   "60s",    false},
    {"Hanging Leg Raises",      "Core",      "bodyweight",3, "10-15", "60s",    false},
    {"Cable Crunches",          "Core",      "cable",     3, "15-20", "60s",    true},
};

std::vector<Exercise> HOME_EXERCISES = {
    {"Push-Ups",                "Chest",     "bodyweight",4, "15-20", "60s",    false},
    {"Wide Push-Ups",           "Chest",     "bodyweight",3, "12-15", "60s",    false},
    {"Pike Push-Ups",           "Shoulders", "bodyweight",3, "10-15", "60s",    false},
    {"Pull-Ups",                "Back",      "bodyweight",4, "8-12",  "90s",    false},
    {"Inverted Rows",           "Back",      "bodyweight",3, "12-15", "90s",    false},
    {"Dips",                    "Triceps",   "bodyweight",3, "12-15", "90s",    false},
    {"Diamond Push-Ups",        "Triceps",   "bodyweight",3, "10-15", "60s",    false},
    {"Bodyweight Squats",       "Quads",     "bodyweight",4, "20-25", "60s",    false},
    {"Jump Squats",             "Quads",     "bodyweight",3, "15-20", "90s",    false},
    {"Bulgarian Split Squat",   "Quads",     "bodyweight",3, "12/leg","90s",    false},
    {"Glute Bridge",            "Hamstrings","bodyweight",4, "15-20", "60s",    false},
    {"Nordic Curl",             "Hamstrings","bodyweight",3, "8-12",  "2min",   false},
    {"Lunges",                  "Quads",     "bodyweight",3, "12/leg","90s",    false},
    {"Calf Raises",             "Calves",    "bodyweight",4, "20-25", "60s",    false},
    {"Plank",                   "Core",      "bodyweight",3, "60s",   "60s",    false},
    {"Bicycle Crunches",        "Core",      "bodyweight",3, "20/side","60s",   false},
    {"Mountain Climbers",       "Core",      "bodyweight",3, "30s",   "60s",    false},
    {"Burpees",                 "Full Body", "bodyweight",3, "10-15", "90s",    false},
};

// ─── STRUCTS ───────────────────────────────────────────────
struct UserInput {
    int         age;
    double      weight;
    double      height;
    std::string injury;
    std::string disease;
    std::string goal;
    std::string location;
};

struct DayPlan {
    std::string name;
    std::string focus;
    std::vector<Exercise> exercises;
};

// ─── HELPERS ───────────────────────────────────────────────
double calcBMI(double w, double h) { return w / ((h / 100.0) * (h / 100.0)); }
double calcBMR(double w, double h, int age) { return 10*w + 6.25*h - 5*age + 5; }

std::string bmiCategory(double bmi) {
    if (bmi < 18.5) return "Underweight";
    if (bmi < 25.0) return "Normal Weight";
    if (bmi < 30.0) return "Overweight";
    return "Obese";
}

std::string lower(std::string s) {
    std::transform(s.begin(), s.end(), s.begin(), ::tolower);
    return s;
}

bool containsAny(const std::string& text, const std::vector<std::string>& keywords) {
    std::string lt = lower(text);
    for (const auto& kw : keywords) {
        if (lt.find(kw) != std::string::npos) return true;
    }
    return false;
}

// ─── INJURY / DISEASE MODIFIERS ──────────────────────────
bool shouldSkip(const Exercise& ex, const UserInput& u) {
    std::string inj = lower(u.injury);
    std::string dis = lower(u.disease);

    // Knee injuries → skip leg-heavy exercises
    if (containsAny(inj, {"knee","meniscus","acl","pcl","patellar"})) {
        if (ex.name.find("Squat") != std::string::npos ||
            ex.name.find("Lunge") != std::string::npos ||
            ex.name.find("Jump")  != std::string::npos) return true;
    }

    // Lower back → skip heavy deadlifts, bent-over rows
    if (containsAny(inj, {"back","spine","lumbar","disc","herniated"})) {
        if (ex.name.find("Deadlift") != std::string::npos && ex.muscle != "Hamstrings") return true;
    }

    // Shoulder injuries → skip overhead press
    if (containsAny(inj, {"shoulder","rotator","cuff","impingement"})) {
        if (ex.name.find("Overhead") != std::string::npos ||
            ex.name.find("Lateral")  != std::string::npos) return true;
    }

    // Diabetes → skip very high intensity (burpees, heavy compound)
    if (containsAny(dis, {"diabetes","diabetic"})) {
        if (ex.name.find("Burpee") != std::string::npos) return true;
    }

    // Heart condition → skip very high intensity
    if (containsAny(dis, {"heart","cardiac","hypertension","blood pressure"})) {
        if (ex.name.find("Jump") != std::string::npos ||
            ex.name.find("Burpee") != std::string::npos) return true;
    }

    return false;
}

// ─── PLAN BUILDER ─────────────────────────────────────────
std::vector<DayPlan> buildPlan(const UserInput& u, const std::vector<Exercise>& pool) {
    std::vector<DayPlan> plan;

    bool isHome = (lower(u.location) == "home");
    bool isBeginner = u.age > 55 || u.weight > 120;

    auto filterExercises = [&](const std::string& muscle) {
        std::vector<Exercise> filtered;
        for (const auto& ex : pool) {
            if (ex.muscle == muscle && !shouldSkip(ex, u))
                filtered.push_back(ex);
        }
        return filtered;
    };

    auto pickN = [](std::vector<Exercise>& v, int n) {
        if ((int)v.size() > n) v.resize(n);
        return v;
    };

    if (lower(u.goal) == "weight loss") {
        // Circuit-style: full body 3x/week + cardio
        std::vector<std::string> muscles = {"Chest","Back","Shoulders","Quads","Core"};
        for (int day = 1; day <= 3; day++) {
            DayPlan d;
            d.name = "Day " + std::to_string(day) + " — Full Body Circuit";
            d.focus = "Full Body + Cardio";
            for (const auto& m : muscles) {
                auto exs = filterExercises(m);
                if (!exs.empty()) d.exercises.push_back(exs[0]);
            }
            plan.push_back(d);
        }
    } else if (lower(u.goal) == "muscle gain") {
        // Push/Pull/Legs split
        {
            DayPlan d;
            d.name = "Day 1 — Push (Chest, Shoulders, Triceps)";
            d.focus = "Chest + Shoulders + Triceps";
            auto ch = filterExercises("Chest"); pickN(ch, 3); for (auto& e : ch) d.exercises.push_back(e);
            auto sh = filterExercises("Shoulders"); pickN(sh, 2); for (auto& e : sh) d.exercises.push_back(e);
            auto tr = filterExercises("Triceps"); pickN(tr, 2); for (auto& e : tr) d.exercises.push_back(e);
            plan.push_back(d);
        }
        {
            DayPlan d;
            d.name = "Day 2 — Pull (Back, Biceps)";
            d.focus = "Back + Biceps";
            auto bk = filterExercises("Back"); pickN(bk, 4); for (auto& e : bk) d.exercises.push_back(e);
            auto bi = filterExercises("Biceps"); pickN(bi, 2); for (auto& e : bi) d.exercises.push_back(e);
            plan.push_back(d);
        }
        {
            DayPlan d;
            d.name = "Day 3 — Legs (Quads, Hamstrings, Calves)";
            d.focus = "Legs + Core";
            auto qd = filterExercises("Quads"); pickN(qd, 3); for (auto& e : qd) d.exercises.push_back(e);
            auto hm = filterExercises("Hamstrings"); pickN(hm, 2); for (auto& e : hm) d.exercises.push_back(e);
            auto ca = filterExercises("Calves"); pickN(ca, 1); for (auto& e : ca) d.exercises.push_back(e);
            auto co = filterExercises("Core"); pickN(co, 2); for (auto& e : co) d.exercises.push_back(e);
            plan.push_back(d);
        }
    } else if (lower(u.goal) == "strength") {
        // Upper/Lower split, heavy compounds
        {
            DayPlan d;
            d.name = "Day 1 — Upper Body Strength";
            d.focus = "Chest + Back + Shoulders";
            auto ch = filterExercises("Chest"); pickN(ch, 2); for (auto& e : ch) d.exercises.push_back(e);
            auto bk = filterExercises("Back"); pickN(bk, 2); for (auto& e : bk) d.exercises.push_back(e);
            auto sh = filterExercises("Shoulders"); pickN(sh, 2); for (auto& e : sh) d.exercises.push_back(e);
            plan.push_back(d);
        }
        {
            DayPlan d;
            d.name = "Day 2 — Lower Body Strength";
            d.focus = "Quads + Hamstrings + Core";
            auto qd = filterExercises("Quads"); pickN(qd, 3); for (auto& e : qd) d.exercises.push_back(e);
            auto hm = filterExercises("Hamstrings"); pickN(hm, 2); for (auto& e : hm) d.exercises.push_back(e);
            auto co = filterExercises("Core"); pickN(co, 2); for (auto& e : co) d.exercises.push_back(e);
            plan.push_back(d);
        }
    } else {
        // General Fitness / Endurance / Flexibility — 3-day full body
        std::vector<std::string> muscles = {"Chest","Back","Quads","Shoulders","Core"};
        for (int day = 1; day <= 3; day++) {
            DayPlan d;
            d.name = "Day " + std::to_string(day) + " — Full Body";
            d.focus = "Full Body";
            for (const auto& m : muscles) {
                auto exs = filterExercises(m);
                if (!exs.empty()) d.exercises.push_back(exs[0]);
            }
            plan.push_back(d);
        }
    }
    return plan;
}

// ─── OUTPUT ───────────────────────────────────────────────
void printSeparator(char c = '-', int n = 60) {
    std::cout << std::string(n, c) << "\n";
}

void printPlan(const UserInput& u) {
    double bmi = calcBMI(u.weight, u.height);
    double bmr = calcBMR(u.weight, u.height, u.age);
    double tdee = bmr * 1.55;
    int protein = (int)std::round(u.weight * (
        lower(u.goal) == "muscle gain" ? 2.2 :
        lower(u.goal) == "strength"    ? 2.0 : 1.6
    ));
    int calories = (int)std::round(
        lower(u.goal) == "weight loss"  ? tdee * 0.80 :
        lower(u.goal) == "muscle gain"  ? tdee * 1.15 :
        lower(u.goal) == "strength"     ? tdee * 1.10 : tdee
    );

    bool isHome = (lower(u.location) == "home");
    auto& pool = isHome ? HOME_EXERCISES : GYM_EXERCISES;
    auto plan = buildPlan(u, pool);

    // Header
    printSeparator('=');
    std::cout << "  FITMART — Personalised Workout Plan\n";
    printSeparator('=');

    // User profile
    std::cout << "\n📊 YOUR PROFILE\n";
    printSeparator();
    std::cout << std::fixed << std::setprecision(1);
    std::cout << "  Age:      " << u.age << " years\n";
    std::cout << "  Weight:   " << u.weight << " kg\n";
    std::cout << "  Height:   " << u.height << " cm\n";
    std::cout << "  BMI:      " << bmi << " (" << bmiCategory(bmi) << ")\n";
    std::cout << "  Goal:     " << u.goal << "\n";
    std::cout << "  Location: " << u.location << "\n";

    if (u.injury != "None" && !u.injury.empty()) {
        std::cout << "  Injury:   ⚠️  " << u.injury << " (exercises modified)\n";
    }
    if (u.disease != "None" && !u.disease.empty()) {
        std::cout << "  Condition: ⚕️  " << u.disease << " (intensity adjusted)\n";
    }

    // Nutrition
    std::cout << "\n🥗 DAILY NUTRITION TARGETS\n";
    printSeparator();
    std::cout << "  Calories: " << calories << " kcal/day\n";
    std::cout << "  Protein:  " << protein << "g/day\n";
    std::cout << "  Water:    " << std::setprecision(1) << (u.weight * 0.033) << "L/day\n";

    // Weekly schedule overview
    std::cout << "\n📅 WEEKLY SCHEDULE\n";
    printSeparator();
    for (int i = 0; i < (int)plan.size(); i++) {
        std::cout << "  Day " << (i+1) << ": " << plan[i].focus << "\n";
    }
    std::cout << "  Rest days: Active recovery, stretching, walking\n";

    // Detailed workout days
    for (const auto& day : plan) {
        std::cout << "\n" << day.name << "\n";
        printSeparator();
        if (day.exercises.empty()) {
            std::cout << "  (All exercises modified due to injury/condition — consult trainer)\n";
            continue;
        }
        std::cout << std::left;
        std::cout << "  " << std::setw(26) << "Exercise"
                  << std::setw(14) << "Muscle"
                  << std::setw(8) << "Sets"
                  << std::setw(10) << "Reps"
                  << "Rest\n";
        std::cout << "  " << std::string(66, '-') << "\n";
        for (const auto& ex : day.exercises) {
            std::cout << "  " << std::setw(26) << ex.name
                      << std::setw(14) << ex.muscle
                      << std::setw(8) << ex.sets
                      << std::setw(10) << ex.reps
                      << ex.rest << "\n";
        }
    }

    // Warm-up / cool-down
    std::cout << "\n🔥 WARM-UP (5-10 min before each session)\n";
    printSeparator();
    std::cout << "  • 3 min light cardio (jog, jump rope, or brisk walk)\n";
    std::cout << "  • Dynamic stretches: leg swings, arm circles, hip circles\n";
    std::cout << "  • 2 warm-up sets at 50% of working weight\n";

    std::cout << "\n❄️  COOL-DOWN (5 min after each session)\n";
    printSeparator();
    std::cout << "  • Static stretching for worked muscle groups (30s each)\n";
    std::cout << "  • Deep breathing for 1 min\n";
    std::cout << "  • Foam rolling if available\n";

    // Tips
    std::cout << "\n💡 PROGRESSIVE OVERLOAD GUIDELINES\n";
    printSeparator();
    std::cout << "  • Increase weight by 2.5-5kg when you hit the top rep range\n";
    std::cout << "  • Rest 48 hours between training the same muscle group\n";
    std::cout << "  • Track every workout — consistency beats intensity\n";
    std::cout << "  • Sleep 7-9 hours for optimal recovery\n";

    if (u.injury != "None" && !u.injury.empty()) {
        std::cout << "\n⚠️  INJURY NOTE\n";
        printSeparator();
        std::cout << "  Due to: " << u.injury << "\n";
        std::cout << "  • Always warm up thoroughly before training\n";
        std::cout << "  • Stop immediately if you feel pain (not just discomfort)\n";
        std::cout << "  • Consult a physiotherapist for exercise-specific guidance\n";
    }

    printSeparator('=');
    std::cout << "  Generated by FitMart — consult your doctor before starting\n";
    printSeparator('=');
    std::cout << std::endl;
}

// ─── MAIN ─────────────────────────────────────────────────
int main() {
    UserInput u;
    std::string line;

    // Read from stdin: age\nweight\nheight\ninjury\ndisease\ngoal\nlocation
    try {
        std::getline(std::cin, line); u.age    = std::stoi(line);
        std::getline(std::cin, line); u.weight = std::stod(line);
        std::getline(std::cin, line); u.height = std::stod(line);
        std::getline(std::cin, u.injury);
        std::getline(std::cin, u.disease);
        std::getline(std::cin, u.goal);
        std::getline(std::cin, u.location);
    } catch (...) {
        // Defaults if parsing fails
        u.age = 25; u.weight = 70; u.height = 175;
        u.injury = "None"; u.disease = "None";
        u.goal = "General Fitness"; u.location = "Gym";
    }

    // Trim whitespace from strings
    auto trim = [](std::string& s) {
        s.erase(0, s.find_first_not_of(" \t\r\n"));
        s.erase(s.find_last_not_of(" \t\r\n") + 1);
    };
    trim(u.injury); trim(u.disease); trim(u.goal); trim(u.location);

    if (u.injury.empty())  u.injury  = "None";
    if (u.disease.empty()) u.disease = "None";
    if (u.goal.empty())    u.goal    = "General Fitness";
    if (u.location.empty()) u.location = "Gym";

    printPlan(u);
    return 0;
}
