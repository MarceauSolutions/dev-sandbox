import SwiftUI

// MARK: - Keyboard Dismiss
extension View {
    func hideKeyboard() {
        UIApplication.shared.sendAction(#selector(UIResponder.resignFirstResponder), to:nil, from:nil, for:nil)
    }
}

struct DismissKeyboardOnDrag: ViewModifier {
    func body(content: Content) -> some View {
        content.gesture(DragGesture().onChanged { _ in
            UIApplication.shared.sendAction(#selector(UIResponder.resignFirstResponder), to:nil, from:nil, for:nil)
        })
    }
}

// MARK: - App Entry
@main
struct MarceauFitnessApp: App {
    @StateObject private var store = WorkoutStore()
    var body: some Scene {
        WindowGroup {
            ContentView()
                .environmentObject(store)
                .preferredColorScheme(.dark)
        }
    }
}

// MARK: - Colors
extension Color {
    static let gold = Color(red: 201/255, green: 150/255, blue: 60/255)
    static let goldDim = Color(red: 201/255, green: 150/255, blue: 60/255).opacity(0.15)
    static let bg = Color(red: 10/255, green: 10/255, blue: 10/255)
    static let bg2 = Color(red: 20/255, green: 20/255, blue: 20/255)
    static let bg3 = Color(red: 26/255, green: 26/255, blue: 26/255)
    static let dim = Color(red: 153/255, green: 153/255, blue: 153/255)
}

// MARK: - Data Models
struct Exercise: Identifiable, Codable {
    let id: String
    let name: String
    let category: String
    let muscles: [String]
    let equipment: [String]
    let difficulty: Int
    let icon: String
    let description: String
    let cues: [String]
}

struct ProgramExercise: Identifiable, Codable {
    var id: String { exerciseId + "\(sets)" }
    let exerciseId: String
    let sets: Int
    let reps: String
    let rest: Int
}

struct ProgramDay: Identifiable, Codable {
    var id: String { name }
    let name: String
    let focus: String
    let exercises: [ProgramExercise]
}

struct Program: Identifiable, Codable {
    let id: String
    let name: String
    let description: String
    let frequency: String
    let level: String
    let days: [ProgramDay]
}

struct SetLog: Codable, Identifiable {
    var id = UUID()
    var weight: String = ""
    var reps: String = ""
    var done: Bool = false
}

struct ActiveExercise: Identifiable, Codable {
    var id: String { exerciseId }
    let exerciseId: String
    let targetSets: Int
    let targetReps: String
    let rest: Int
    var sets: [SetLog]
}

struct WorkoutHistory: Identifiable, Codable {
    var id = UUID()
    let date: Date
    let name: String
    let exerciseCount: Int
    let volume: Int
    let duration: Int
}

struct FoodEntry: Identifiable, Codable {
    var id = UUID()
    var name: String = ""
    var calories: Int = 0
    var protein: Int = 0
    var carbs: Int = 0
    var fat: Int = 0
    var meal: String = "Meal 1"
    var date: Date = Date()
}

struct NutritionTargets: Codable {
    var calories: Int = 2800
    var protein: Int = 200
    var carbs: Int = 300
    var fat: Int = 80
}

struct BodyMetric: Identifiable, Codable {
    var id = UUID()
    var date: Date = Date()
    var weight: Double?
    var bodyFat: Double?
    var chest: Double?
    var waist: Double?
    var hips: Double?
    var arms: Double?
    var thighs: Double?
    var notes: String = ""
}

// MARK: - Store
class WorkoutStore: ObservableObject {
    @Published var history: [WorkoutHistory] = []
    @Published var totalWorkouts: Int = 0
    @Published var streak: Int = 0
    @Published var totalVolume: Int = 0
    @Published var activeWorkout: [ActiveExercise]? = nil
    @Published var activeWorkoutName: String = ""
    @Published var activeWorkoutStart: Date? = nil
    @Published var selectedProgram: String = "defy_the_odds"
    @Published var foodLog: [FoodEntry] = []
    @Published var nutritionTargets = NutritionTargets()
    @Published var bodyMetrics: [BodyMetric] = []

    var latestWeight: Double? { bodyMetrics.sorted { $0.date > $1.date }.first?.weight }
    var latestBodyFat: Double? { bodyMetrics.sorted { $0.date > $1.date }.first?.bodyFat }
    var weightChange: Double? {
        guard let first = bodyMetrics.sorted(by: { $0.date < $1.date }).first?.weight,
              let latest = latestWeight else { return nil }
        return latest - first
    }

    var todaysFoodLog: [FoodEntry] {
        let cal = Calendar.current
        return foodLog.filter { cal.isDateInToday($0.date) }
    }
    var todayCalories: Int { todaysFoodLog.reduce(0) { $0 + $1.calories } }
    var todayProtein: Int { todaysFoodLog.reduce(0) { $0 + $1.protein } }
    var todayCarbs: Int { todaysFoodLog.reduce(0) { $0 + $1.carbs } }
    var todayFat: Int { todaysFoodLog.reduce(0) { $0 + $1.fat } }

    init() { load() }

    func load() {
        if let d = UserDefaults.standard.data(forKey: "mf_history"),
           let h = try? JSONDecoder().decode([WorkoutHistory].self, from: d) { history = h }
        totalWorkouts = UserDefaults.standard.integer(forKey: "mf_workouts")
        streak = UserDefaults.standard.integer(forKey: "mf_streak")
        totalVolume = UserDefaults.standard.integer(forKey: "mf_volume")
        selectedProgram = UserDefaults.standard.string(forKey: "mf_program") ?? "defy_the_odds"
        if let d = UserDefaults.standard.data(forKey: "mf_foodlog"),
           let f = try? JSONDecoder().decode([FoodEntry].self, from: d) { foodLog = f }
        if let d = UserDefaults.standard.data(forKey: "mf_targets"),
           let t = try? JSONDecoder().decode(NutritionTargets.self, from: d) { nutritionTargets = t }
        if let d = UserDefaults.standard.data(forKey: "mf_metrics"),
           let m = try? JSONDecoder().decode([BodyMetric].self, from: d) { bodyMetrics = m }
    }

    func save() {
        if let d = try? JSONEncoder().encode(history) { UserDefaults.standard.set(d, forKey: "mf_history") }
        UserDefaults.standard.set(totalWorkouts, forKey: "mf_workouts")
        UserDefaults.standard.set(streak, forKey: "mf_streak")
        UserDefaults.standard.set(totalVolume, forKey: "mf_volume")
        UserDefaults.standard.set(selectedProgram, forKey: "mf_program")
        if let d = try? JSONEncoder().encode(foodLog) { UserDefaults.standard.set(d, forKey: "mf_foodlog") }
        if let d = try? JSONEncoder().encode(nutritionTargets) { UserDefaults.standard.set(d, forKey: "mf_targets") }
        if let d = try? JSONEncoder().encode(bodyMetrics) { UserDefaults.standard.set(d, forKey: "mf_metrics") }
    }

    func addFood(_ entry: FoodEntry) {
        foodLog.append(entry)
        save()
    }

    func deleteFood(_ entry: FoodEntry) {
        foodLog.removeAll { $0.id == entry.id }
        save()
    }

    func addMetric(_ metric: BodyMetric) {
        bodyMetrics.append(metric)
        bodyMetrics.sort { $0.date < $1.date }
        save()
    }

    func deleteMetric(_ metric: BodyMetric) {
        bodyMetrics.removeAll { $0.id == metric.id }
        save()
    }

    func startWorkout(day: ProgramDay) {
        activeWorkoutName = day.name
        activeWorkoutStart = Date()
        activeWorkout = day.exercises.map { ex in
            ActiveExercise(exerciseId: ex.exerciseId, targetSets: ex.sets, targetReps: ex.reps, rest: ex.rest,
                           sets: (0..<ex.sets).map { _ in SetLog() })
        }
    }

    func finishWorkout() {
        guard let exercises = activeWorkout, let start = activeWorkoutStart else { return }
        let duration = Int(Date().timeIntervalSince(start) / 60)
        var volume = 0
        var exCount = 0
        for ex in exercises {
            var had = false
            for s in ex.sets where s.done {
                let w = Double(s.weight) ?? 0
                let r = Int(s.reps) ?? 0
                volume += Int(w) * r
                had = true
            }
            if had { exCount += 1 }
        }
        let entry = WorkoutHistory(date: Date(), name: activeWorkoutName, exerciseCount: exCount, volume: volume, duration: duration)
        history.insert(entry, at: 0)
        if history.count > 50 { history = Array(history.prefix(50)) }
        totalWorkouts += 1
        totalVolume += volume
        // Simple streak
        let cal = Calendar.current
        let lastDate = UserDefaults.standard.object(forKey: "mf_lastDate") as? Date
        if let last = lastDate, cal.isDateInYesterday(last) { streak += 1 }
        else if lastDate == nil || !cal.isDateInToday(lastDate!) { streak = 1 }
        UserDefaults.standard.set(Date(), forKey: "mf_lastDate")
        activeWorkout = nil
        activeWorkoutStart = nil
        save()
    }
}

// MARK: - Exercise Database
let exerciseDB: [Exercise] = [
    Exercise(id:"squat", name:"Squat", category:"Legs", muscles:["Quads","Glutes","Hamstrings","Core"], equipment:["Barbell","Bodyweight","Dumbbell"], difficulty:2, icon:"🦵", description:"A compound lower body exercise targeting quads, glutes, and hamstrings while engaging the core.", cues:["Keep chest up and core engaged","Knees track over toes","Hip crease below knee at bottom","Drive through heels to stand"]),
    Exercise(id:"deadlift", name:"Deadlift", category:"Back", muscles:["Hamstrings","Glutes","Lower Back","Traps"], equipment:["Barbell","Dumbbell"], difficulty:3, icon:"🏋️", description:"A compound pulling exercise developing posterior chain strength and overall power.", cues:["Maintain neutral spine throughout","Bar stays close to body","Hips and shoulders rise together","Squeeze glutes at top"]),
    Exercise(id:"bench_press", name:"Bench Press", category:"Chest", muscles:["Chest","Triceps","Front Delts"], equipment:["Barbell","Dumbbell","Bench"], difficulty:2, icon:"💪", description:"The primary horizontal pressing movement for chest, triceps, and shoulder strength.", cues:["Retract and depress shoulder blades","Feet flat on floor","Bar path diagonal to upper chest","Full lockout at top"]),
    Exercise(id:"bent_over_row", name:"Bent Over Row", category:"Back", muscles:["Lats","Rhomboids","Rear Delts","Biceps"], equipment:["Barbell","Dumbbell"], difficulty:2, icon:"🚣", description:"A horizontal pulling movement building back thickness and posture.", cues:["Maintain hip hinge with flat back","Pull elbows past torso","Squeeze shoulder blades at top","Control the negative"]),
    Exercise(id:"pullup", name:"Pull-Up", category:"Back", muscles:["Lats","Biceps","Rear Delts","Core"], equipment:["Pull-Up Bar"], difficulty:3, icon:"🧗", description:"A vertical pulling exercise building upper back width and grip strength.", cues:["Start from dead hang","Initiate with lat engagement","Chin clears bar at top","Control descent fully"]),
    Exercise(id:"overhead_press", name:"Overhead Press", category:"Shoulders", muscles:["Shoulders","Triceps","Core"], equipment:["Barbell","Dumbbell"], difficulty:2, icon:"🙌", description:"A vertical pressing movement for shoulder strength and stability.", cues:["Core braced throughout","Bar path straight up","Head moves back for bar path","Full lockout overhead"]),
    Exercise(id:"lunge", name:"Lunge", category:"Legs", muscles:["Quads","Glutes","Hamstrings","Core"], equipment:["Bodyweight","Dumbbell","Barbell"], difficulty:1, icon:"🦿", description:"A unilateral leg exercise building strength and balance.", cues:["Front knee tracks over toes","Back knee nearly touches floor","Torso stays upright","Push through front heel"]),
    Exercise(id:"hip_thrust", name:"Hip Thrust", category:"Glutes", muscles:["Glutes","Hamstrings","Core"], equipment:["Barbell","Bench"], difficulty:2, icon:"🍑", description:"A glute-focused exercise for hip power and strength.", cues:["Upper back on bench","Drive through heels","Squeeze glutes at top","Chin tucked throughout"]),
    Exercise(id:"lat_pulldown", name:"Lat Pulldown", category:"Back", muscles:["Lats","Biceps","Rear Delts"], equipment:["Cable Machine"], difficulty:1, icon:"⬇️", description:"A cable exercise mimicking pull-up motion for lat development.", cues:["Slight lean back","Pull to upper chest","Squeeze lats at bottom","Full stretch at top"]),
    Exercise(id:"leg_press", name:"Leg Press", category:"Legs", muscles:["Quads","Glutes","Hamstrings"], equipment:["Machine"], difficulty:1, icon:"🦵", description:"A machine-based compound leg exercise for lower body strength.", cues:["Full foot on platform","Knees track over toes","Control the negative","Don't lock knees at top"]),
    Exercise(id:"romanian_deadlift", name:"Romanian Deadlift", category:"Back", muscles:["Hamstrings","Glutes","Lower Back"], equipment:["Barbell","Dumbbell"], difficulty:2, icon:"🏋️", description:"A hip-hinge movement emphasizing hamstrings and glutes.", cues:["Slight knee bend maintained","Push hips back","Feel hamstring stretch","Squeeze glutes at top"]),
    Exercise(id:"dips", name:"Dips", category:"Chest", muscles:["Chest","Triceps","Shoulders"], equipment:["Parallel Bars"], difficulty:2, icon:"⬇️", description:"A compound pushing exercise for chest and tricep development.", cues:["Lean forward for chest emphasis","Elbows to 90 degrees","Control the descent","Full lockout at top"]),
    Exercise(id:"lateral_raise", name:"Lateral Raise", category:"Shoulders", muscles:["Side Delts"], equipment:["Dumbbell","Cable"], difficulty:1, icon:"🤷", description:"An isolation exercise for shoulder width.", cues:["Slight bend in elbows","Lead with elbows","Stop at shoulder height","Control the descent"]),
    Exercise(id:"face_pull", name:"Face Pull", category:"Shoulders", muscles:["Rear Delts","Rhomboids","Traps"], equipment:["Cable"], difficulty:1, icon:"🎯", description:"A pulling exercise for rear deltoid and upper back health.", cues:["Pull to face level","Elbows high and wide","External rotation at end","Squeeze rear delts"]),
    Exercise(id:"bicep_curl", name:"Bicep Curl", category:"Arms", muscles:["Biceps","Forearms"], equipment:["Dumbbell","Barbell","Cable"], difficulty:1, icon:"💪", description:"An isolation exercise targeting biceps.", cues:["Keep elbows at sides","Squeeze at top","Control the negative","Avoid swinging momentum"]),
    Exercise(id:"tricep_extension", name:"Tricep Extension", category:"Arms", muscles:["Triceps"], equipment:["Dumbbell","Cable"], difficulty:1, icon:"💪", description:"An isolation exercise for tricep development.", cues:["Keep elbows fixed","Full range of motion","Squeeze at lockout","Control the weight"]),
    Exercise(id:"pushup", name:"Push-Up", category:"Chest", muscles:["Chest","Triceps","Shoulders","Core"], equipment:["Bodyweight"], difficulty:1, icon:"🫸", description:"A fundamental bodyweight pushing exercise.", cues:["Body straight head to heels","Elbows at 45 degrees","Chest nearly touches floor","Full lockout at top"]),
    Exercise(id:"plank", name:"Plank", category:"Core", muscles:["Core","Shoulders","Glutes"], equipment:["Bodyweight"], difficulty:1, icon:"🧘", description:"An isometric core exercise building stability and endurance.", cues:["Body in straight line","Engage core and glutes","Don't let hips sag","Breathe steadily"]),
    Exercise(id:"incline_press", name:"Incline Press", category:"Chest", muscles:["Upper Chest","Front Delts","Triceps"], equipment:["Barbell","Dumbbell"], difficulty:2, icon:"💪", description:"An incline pressing movement emphasizing upper chest.", cues:["Bench at 30-45 degrees","Retract shoulder blades","Lower to upper chest","Press to lockout"]),
    Exercise(id:"cable_fly", name:"Cable Fly", category:"Chest", muscles:["Chest","Front Delts"], equipment:["Cable"], difficulty:1, icon:"🦅", description:"An isolation exercise for chest definition.", cues:["Slight bend in elbows","Squeeze chest at center","Control the stretch","Keep core engaged"]),
    Exercise(id:"leg_curl", name:"Leg Curl", category:"Legs", muscles:["Hamstrings"], equipment:["Machine"], difficulty:1, icon:"🦵", description:"An isolation exercise targeting hamstrings.", cues:["Full range of motion","Squeeze at contraction","Control the negative","Don't lift hips"]),
    Exercise(id:"leg_extension", name:"Leg Extension", category:"Legs", muscles:["Quads"], equipment:["Machine"], difficulty:1, icon:"🦵", description:"An isolation exercise targeting quadriceps.", cues:["Full extension at top","Squeeze quads at peak","Control the descent","Keep back against pad"]),
    Exercise(id:"calf_raise", name:"Calf Raise", category:"Legs", muscles:["Calves"], equipment:["Machine","Bodyweight"], difficulty:1, icon:"🦵", description:"An isolation exercise for calf development.", cues:["Full stretch at bottom","Pause at top","Control the negative","Both legs evenly loaded"]),
    Exercise(id:"mountain_climber", name:"Mountain Climber", category:"Core", muscles:["Core","Hip Flexors","Shoulders"], equipment:["Bodyweight"], difficulty:1, icon:"⛰️", description:"A dynamic core exercise with cardio conditioning.", cues:["Maintain plank position","Drive knees to chest","Keep hips level","Move with control"]),
    Exercise(id:"burpee", name:"Burpee", category:"Full Body", muscles:["Chest","Legs","Shoulders","Core"], equipment:["Bodyweight"], difficulty:2, icon:"🔥", description:"A full-body conditioning exercise combining squat, plank, and jump.", cues:["Squat down hands on floor","Jump feet back to plank","Perform pushup","Jump feet forward and up"]),
    // Defy the Odds exercises
    Exercise(id:"kb_swing", name:"Kettlebell Swing", category:"Full Body", muscles:["Glutes","Hamstrings","Core","Shoulders"], equipment:["Kettlebell"], difficulty:2, icon:"🔔", description:"Explosive hip hinge building posterior chain power and conditioning.", cues:["Hip hinge explosively","Squeeze glutes at top","Arms are just along for the ride","Bell to chest height"]),
    Exercise(id:"box_jump", name:"Box Jump", category:"Legs", muscles:["Quads","Glutes","Calves","Core"], equipment:["Plyo Box"], difficulty:2, icon:"📦", description:"Explosive lower body power exercise. Always step down to protect joints.", cues:["Land soft like a cat","Full hip extension at top","Step down — never jump down","Swing arms for momentum"]),
    Exercise(id:"goblet_squat", name:"Goblet Squat", category:"Legs", muscles:["Quads","Glutes","Core"], equipment:["Kettlebell","Dumbbell"], difficulty:1, icon:"🏆", description:"A squat variation using a front-loaded weight for better depth and posture.", cues:["Hold KB at chest","Elbows inside knees at bottom","Pause 2 sec at bottom","Drive through heels"]),
    Exercise(id:"front_squat", name:"Front Squat", category:"Legs", muscles:["Quads","Glutes","Core","Upper Back"], equipment:["Barbell"], difficulty:3, icon:"🦵", description:"A quad-dominant squat with front-loaded barbell demanding core stability.", cues:["Elbows high, bar on front delts","Controlled descent","Drive through heels","Keep torso upright"]),
    Exercise(id:"bulgarian_split_squat", name:"Bulgarian Split Squat", category:"Legs", muscles:["Quads","Glutes","Hamstrings","Core"], equipment:["Dumbbell","Bench"], difficulty:2, icon:"🦿", description:"The king of single-leg training. Controls side-to-side asymmetry — critical for dystonia management.", cues:["Rear foot elevated on bench","Lean slightly forward","Full depth","Don't push off back foot"]),
    Exercise(id:"single_leg_rdl", name:"Single-Leg RDL", category:"Legs", muscles:["Hamstrings","Glutes","Core"], equipment:["Kettlebell","Dumbbell"], difficulty:2, icon:"🏋️", description:"Balance + posterior chain + proprioception in one movement.", cues:["Hinge at hip","Free leg extends behind","Reach for the floor","Keep hips square"]),
    Exercise(id:"kb_push_press", name:"KB Push Press", category:"Shoulders", muscles:["Shoulders","Triceps","Core","Legs"], equipment:["Kettlebell"], difficulty:2, icon:"🔔", description:"Explosive overhead press using leg drive for power.", cues:["Use leg drive","Lock out overhead","Core braced","Control the descent"]),
    Exercise(id:"kb_floor_press", name:"KB Floor Press", category:"Chest", muscles:["Chest","Triceps","Shoulders"], equipment:["Kettlebell"], difficulty:1, icon:"🔔", description:"Limits ROM to protect shoulders. Pause at bottom eliminates bounce.", cues:["Pause at bottom","Eliminate bounce","Drive to lockout","Floor protects shoulder ROM"]),
    Exercise(id:"kb_gorilla_row", name:"KB Gorilla Row", category:"Back", muscles:["Lats","Rhomboids","Biceps","Core"], equipment:["Kettlebell"], difficulty:2, icon:"🦍", description:"Wide stance alternating KB rows with anti-rotation demand.", cues:["Wide stance over two KBs","Alternate rows","Minimize hip rotation","Pull to hip"]),
    Exercise(id:"kb_snatch", name:"KB Snatch", category:"Full Body", muscles:["Shoulders","Glutes","Core","Hamstrings"], equipment:["Kettlebell"], difficulty:3, icon:"🔔", description:"The tsar of kettlebell movements — full-body explosive power.", cues:["Hip drive first","Punch through at top","Don't curl it up","Control the drop"]),
    Exercise(id:"turkish_getup", name:"Turkish Get-Up", category:"Full Body", muscles:["Core","Shoulders","Glutes","Full Body"], equipment:["Kettlebell"], difficulty:3, icon:"🇹🇷", description:"The ultimate shoulder stability and full-body coordination exercise. Slow and controlled.", cues:["Eyes on the bell always","Master each position","Slow is better","Keep arm vertical"]),
    Exercise(id:"farmers_walk", name:"Farmer's Walk", category:"Full Body", muscles:["Grip","Core","Traps","Legs"], equipment:["Dumbbell","Kettlebell"], difficulty:1, icon:"🚶", description:"Loaded carry building grip, core stability, and total body strength. Use Fat Gripz on left hand for dystonia.", cues:["Tall posture","Shoulders packed","Walk with intention","Every step is single-leg stance"]),
    Exercise(id:"bear_crawl", name:"Bear Crawl", category:"Core", muscles:["Core","Shoulders","Quads","Hip Flexors"], equipment:["Bodyweight"], difficulty:2, icon:"🐻", description:"Quadruped locomotion building coordination and core stability.", cues:["Knees hover 2 inches","Opposite hand + foot move together","Slow is harder","Forward and backward"]),
    Exercise(id:"pallof_press", name:"Pallof Press", category:"Core", muscles:["Core","Obliques"], equipment:["Cable","Band"], difficulty:1, icon:"🎯", description:"Anti-rotation core exercise. Dystonia-friendly — trains stability without compression.", cues:["Core resists rotation","Arms extend, hold 2 sec","Don't let cable pull you","Squeeze abs throughout"]),
    Exercise(id:"trap_bar_deadlift", name:"Trap Bar Deadlift", category:"Legs", muscles:["Quads","Glutes","Hamstrings","Traps"], equipment:["Trap Bar"], difficulty:2, icon:"🏋️", description:"More athletic than barbell deadlift — neutral grip, balanced loading.", cues:["Drive through the floor","Neutral grip","Hips and shoulders rise together","Squeeze glutes at top"]),
    Exercise(id:"back_squat", name:"Back Squat", category:"Legs", muscles:["Quads","Glutes","Hamstrings","Core"], equipment:["Barbell"], difficulty:2, icon:"🦵", description:"The king of lower body strength. Full depth, controlled.", cues:["Bar on upper traps","Controlled descent","Full depth","Drive through heels"]),
    Exercise(id:"weighted_pullup", name:"Weighted Pull-Up", category:"Back", muscles:["Lats","Biceps","Core","Grip"], equipment:["Pull-Up Bar","Weight Belt"], difficulty:3, icon:"🧗", description:"Pull-up with added load for advanced back development.", cues:["Full dead hang start","Chin over bar","Control descent","Add weight progressively"]),
    Exercise(id:"chinup", name:"Chin-Up", category:"Back", muscles:["Biceps","Lats","Core"], equipment:["Pull-Up Bar"], difficulty:2, icon:"🧗", description:"Supinated grip pull-up emphasizing biceps and lats.", cues:["Supinated grip","Full ROM","Squeeze at top","Control the negative"]),
    Exercise(id:"half_kneeling_press", name:"Half-Kneeling KB Press", category:"Shoulders", muscles:["Shoulders","Core","Triceps"], equipment:["Kettlebell"], difficulty:2, icon:"🔔", description:"Overhead press from half-kneeling position for core engagement.", cues:["Core engagement","Vertical forearm","Press straight up","Don't lean back"]),
    Exercise(id:"renegade_row", name:"Renegade Row", category:"Back", muscles:["Lats","Core","Shoulders","Biceps"], equipment:["Kettlebell","Dumbbell"], difficulty:3, icon:"💪", description:"Plank position rows demanding anti-rotation core strength.", cues:["Plank position","Minimize hip rotation","Row to hip","Feet wide for balance"]),
    Exercise(id:"nordic_curl", name:"Nordic Curl", category:"Legs", muscles:["Hamstrings"], equipment:["Bodyweight"], difficulty:3, icon:"🦵", description:"Gold standard for hamstring strength and injury prevention.", cues:["Lower as slowly as possible","Control the eccentric","Push up if needed","Keep hips extended"]),
    Exercise(id:"lateral_bound", name:"Lateral Bound", category:"Legs", muscles:["Glutes","Quads","Adductors"], equipment:["Bodyweight"], difficulty:2, icon:"↔️", description:"Explosive lateral power. Frontal plane athleticism.", cues:["Bound sideways","STICK the landing 3 sec","Drive off outside foot","Absorb like a spring"]),
    Exercise(id:"kb_walking_lunge", name:"KB Walking Lunge", category:"Legs", muscles:["Quads","Glutes","Hamstrings","Core"], equipment:["Kettlebell"], difficulty:2, icon:"🚶", description:"Walking lunges with kettlebell in rack or farmer carry position.", cues:["Rack or farmer position","Full stride length","Back knee nearly touches","Drive through front heel"]),
    Exercise(id:"hang_clean", name:"Hang Clean", category:"Full Body", muscles:["Traps","Shoulders","Quads","Glutes"], equipment:["Barbell"], difficulty:3, icon:"🏋️", description:"Explosive pulling movement from hang position to front rack.", cues:["Start at mid-thigh","Triple extension","Fast elbows","Catch in front squat"]),
    Exercise(id:"push_press", name:"Push Press", category:"Shoulders", muscles:["Shoulders","Triceps","Core","Legs"], equipment:["Barbell"], difficulty:2, icon:"🙌", description:"Barbell overhead press with leg drive for heavier loads.", cues:["Dip and drive","Use leg power","Lock out overhead","Controlled descent"]),
    Exercise(id:"db_snatch", name:"DB Snatch", category:"Full Body", muscles:["Shoulders","Glutes","Core","Traps"], equipment:["Dumbbell"], difficulty:2, icon:"💪", description:"Single-arm explosive pull from floor to overhead.", cues:["Hip drive first","Pull close to body","Punch overhead","Alternate arms"]),
    Exercise(id:"plyo_pushup", name:"Plyo Push-Up", category:"Chest", muscles:["Chest","Triceps","Shoulders","Core"], equipment:["Bodyweight"], difficulty:3, icon:"🫸", description:"Explosive push-up where hands leave the ground.", cues:["Explosive press","Hands leave ground","Land soft","Full lockout between reps"]),
    Exercise(id:"single_leg_glute_bridge", name:"Single-Leg Glute Bridge", category:"Glutes", muscles:["Glutes","Hamstrings","Core"], equipment:["Bodyweight"], difficulty:1, icon:"🍑", description:"Unilateral glute activation for strength and symmetry.", cues:["Drive through heel","Squeeze at top","Keep hips level","Control the descent"]),
    Exercise(id:"copenhagen_plank", name:"Copenhagen Plank", category:"Core", muscles:["Adductors","Core","Obliques"], equipment:["Bench"], difficulty:2, icon:"🧘", description:"Adductor strength + core stability. Prevents groin injuries.", cues:["Top leg on bench","Bottom leg hovering","Hips level","Hold with control"]),
    // BoabFit Exercises — Julia's Program
    Exercise(id:"bf_bench_row", name:"Dumbbell Bench Row", category:"Back", muscles:["Lats","Rhomboids","Biceps"], equipment:["Dumbbell","Bench"], difficulty:1, icon:"🚣", description:"Single-arm row from bench for back thickness.", cues:["One knee and hand on bench","Pull dumbbell to hip like starting a lawnmower","Squeeze shoulder blade at top","Keep core tight, back flat"]),
    Exercise(id:"bf_squat_abduction", name:"Banded Squat Abduction", category:"Glutes", muscles:["Glutes","Quads","Abductors"], equipment:["Band"], difficulty:1, icon:"🍑", description:"Banded squat hold with knee drive for glute activation.", cues:["Band above knees","Squat down and HOLD","Push knees OUT against band","Stay low the whole time"]),
    Exercise(id:"bf_tricep_kickback", name:"Dumbbell Tricep Kickback", category:"Arms", muscles:["Triceps"], equipment:["Dumbbell"], difficulty:1, icon:"💪", description:"Isolation tricep exercise with hinge position.", cues:["Hinge forward at hips","Elbows pinned to sides","Extend arms straight back","SQUEEZE at the top"]),
    Exercise(id:"bf_ab_routine", name:"Ab Routine", category:"Core", muscles:["Core","Abs"], equipment:["Bodyweight"], difficulty:1, icon:"🧘", description:"Core circuit targeting abs with controlled breathing.", cues:["Ribs pulled down","Lower back pressed into floor","Abs pull IN, not neck cranking up","Breathe out on crunch"]),
    Exercise(id:"bf_donkey_kicks", name:"Donkey Kicks Routine", category:"Glutes", muscles:["Glutes"], equipment:["Bodyweight"], difficulty:1, icon:"🍑", description:"All-fours glute activation targeting upper glutes.", cues:["On all fours, knee bent 90 degrees","Push foot toward ceiling","Squeeze glute at top","Don't arch your back"]),
    Exercise(id:"bf_backwards_lunge", name:"Dumbbell Backwards Lunge", category:"Legs", muscles:["Glutes","Hamstrings","Quads"], equipment:["Dumbbell"], difficulty:1, icon:"🦿", description:"Reverse lunge targeting glutes and hamstrings.", cues:["Step BACK not forward","Drop back knee straight down","Push through front HEEL","Keep torso upright"]),
    Exercise(id:"bf_bench_hip_thrust", name:"Dumbbell Bench Hip Thrust", category:"Glutes", muscles:["Glutes","Hamstrings"], equipment:["Dumbbell","Bench"], difficulty:1, icon:"🍑", description:"Bench-supported hip thrust for max glute activation.", cues:["Upper back on bench","Drive through heels","Squeeze glutes at top — hold!","Chin tucked slightly"]),
    Exercise(id:"bf_sumo_squat", name:"Sumo Squat", category:"Legs", muscles:["Quads","Glutes","Adductors"], equipment:["Dumbbell"], difficulty:1, icon:"🦵", description:"Wide-stance squat targeting inner thighs and glutes.", cues:["Wide stance, toes at 45 degrees","Hold dumbbell in front","Sit straight DOWN","Squeeze inner thighs to stand"]),
    Exercise(id:"bf_side_lunge", name:"Dumbbell Side Lunge", category:"Legs", muscles:["Quads","Glutes","Adductors"], equipment:["Dumbbell"], difficulty:1, icon:"🦿", description:"Lateral lunge for inner thigh and glute strength.", cues:["Step wide to the side","Sit back into the hip","Keep other leg straight","Push back to center"]),
    Exercise(id:"bf_rdl", name:"Dumbbell RDL", category:"Legs", muscles:["Hamstrings","Glutes","Lower Back"], equipment:["Dumbbell"], difficulty:1, icon:"🏋️", description:"Romanian deadlift for hamstring and glute development.", cues:["Slight knee bend","Push hips BACK","Feel the hamstring stretch","Squeeze glutes to stand"]),
    Exercise(id:"bf_step_up", name:"Dumbbell Step-Up", category:"Legs", muscles:["Quads","Glutes"], equipment:["Dumbbell","Bench"], difficulty:1, icon:"🦵", description:"Step-up for unilateral leg strength.", cues:["Full foot on bench","Drive through the heel","Don't push off back foot","Control the step down"]),
    Exercise(id:"bf_curtsey_lunge", name:"Dumbbell Curtsey Lunge", category:"Legs", muscles:["Glutes","Quads","Adductors"], equipment:["Dumbbell"], difficulty:1, icon:"🦿", description:"Cross-behind lunge targeting glute medius.", cues:["Step back and across","Drop back knee toward floor","Keep front knee tracking forward","Push through front heel"]),
    Exercise(id:"bf_side_lunge_toe_touch", name:"Side Lunge Toe Touch", category:"Legs", muscles:["Hamstrings","Glutes","Adductors"], equipment:["Bodyweight"], difficulty:1, icon:"🦿", description:"Dynamic side lunge with toe touch for mobility.", cues:["Lunge to the side","Reach for your toe","Keep chest up","Push back to center"]),
    Exercise(id:"bf_overhead_tricep_ext", name:"Overhead Tricep Extension", category:"Arms", muscles:["Triceps"], equipment:["Dumbbell"], difficulty:1, icon:"💪", description:"Overhead tricep isolation for arm definition.", cues:["Hold dumbbell overhead","Lower behind head","Keep elbows close to ears","Extend fully at top"]),
    Exercise(id:"bf_back_arm_pulse", name:"Dumbbell Back Arm Pulse", category:"Arms", muscles:["Triceps","Rear Delts"], equipment:["Dumbbell"], difficulty:1, icon:"💪", description:"Small pulsing movements targeting rear arms.", cues:["Arms straight behind you","Small controlled pulses","Squeeze triceps","Don't swing"]),
    Exercise(id:"bf_hammer_curl", name:"Hammer Curl", category:"Arms", muscles:["Biceps","Forearms"], equipment:["Dumbbell"], difficulty:1, icon:"💪", description:"Neutral-grip curl for bicep and forearm development.", cues:["Palms face each other","Elbows at sides","Squeeze at top","Control the negative"]),
    Exercise(id:"bf_y_raise", name:"Y Raise", category:"Shoulders", muscles:["Rear Delts","Traps","Rotator Cuff"], equipment:["Dumbbell"], difficulty:1, icon:"🤷", description:"Y-shape raise for upper back and shoulder health.", cues:["Light weights","Raise arms in Y shape","Thumbs up","Squeeze upper back"]),
    Exercise(id:"bf_bent_over_lat_raise", name:"Bent Over Lateral Raise", category:"Shoulders", muscles:["Rear Delts","Rhomboids"], equipment:["Dumbbell"], difficulty:1, icon:"🤷", description:"Bent-over fly for rear deltoid development.", cues:["Hinge at hips","Raise arms to sides","Lead with elbows","Squeeze shoulder blades"]),
    Exercise(id:"bf_reverse_grip_row", name:"Reverse Grip Dumbbell Row", category:"Back", muscles:["Lats","Biceps","Rhomboids"], equipment:["Dumbbell"], difficulty:1, icon:"🚣", description:"Underhand grip row emphasizing lats and biceps.", cues:["Palms facing forward","Pull to lower chest","Squeeze lats","Control the descent"]),
    Exercise(id:"bf_girl_pushup", name:"Girl Push-Up", category:"Chest", muscles:["Chest","Triceps","Shoulders"], equipment:["Bodyweight"], difficulty:1, icon:"🫸", description:"Knee push-up for chest and tricep development.", cues:["Knees on ground","Body straight from knees to head","Lower chest to floor","Push up fully"]),
    Exercise(id:"bf_hex_press", name:"Dumbbell Hex Press", category:"Chest", muscles:["Chest","Triceps"], equipment:["Dumbbell"], difficulty:1, icon:"💪", description:"Dumbbells pressed together for inner chest activation.", cues:["Dumbbells touching throughout","Press straight up","Squeeze chest","Control the descent"]),
    Exercise(id:"bf_wall_raise", name:"Wall Raise", category:"Shoulders", muscles:["Shoulders","Traps","Rotator Cuff"], equipment:["Bodyweight"], difficulty:1, icon:"🤷", description:"Wall slide for shoulder mobility and activation.", cues:["Back flat against wall","Slide arms up","Keep contact with wall","Full range of motion"]),
]

func exerciseFor(_ id: String) -> Exercise? { exerciseDB.first { $0.id == id } }

// MARK: - Programs
let programDB: [Program] = [
    // William's Programs — Defy the Odds
    Program(id:"defy_the_odds", name:"Defy the Odds", description:"5-day athleticism & fluid movement — built for a body that fights back", frequency:"5 days/week", level:"Advanced", days:[
        ProgramDay(name:"Mon: Power + Locomotion", focus:"Explosive Power + Carries", exercises:[
            ProgramExercise(exerciseId:"kb_swing", sets:4, reps:"12", rest:60),
            ProgramExercise(exerciseId:"box_jump", sets:4, reps:"5", rest:90),
            ProgramExercise(exerciseId:"farmers_walk", sets:3, reps:"40 yds", rest:60),
            ProgramExercise(exerciseId:"bear_crawl", sets:3, reps:"20 yds ea", rest:60),
            ProgramExercise(exerciseId:"trap_bar_deadlift", sets:4, reps:"6", rest:120),
            ProgramExercise(exerciseId:"bulgarian_split_squat", sets:3, reps:"8/side", rest:90),
            ProgramExercise(exerciseId:"pallof_press", sets:3, reps:"10/side", rest:60),
        ]),
        ProgramDay(name:"Tue: Push", focus:"Push Power + Pressing", exercises:[
            ProgramExercise(exerciseId:"plyo_pushup", sets:4, reps:"5", rest:90),
            ProgramExercise(exerciseId:"bench_press", sets:4, reps:"6", rest:150),
            ProgramExercise(exerciseId:"kb_push_press", sets:4, reps:"6/side", rest:90),
            ProgramExercise(exerciseId:"incline_press", sets:3, reps:"10", rest:90),
            ProgramExercise(exerciseId:"kb_floor_press", sets:3, reps:"10/side", rest:60),
            ProgramExercise(exerciseId:"dips", sets:3, reps:"10", rest:60),
            ProgramExercise(exerciseId:"face_pull", sets:3, reps:"15", rest:45),
        ]),
        ProgramDay(name:"Wed: Pull", focus:"Back Power + Pulling", exercises:[
            ProgramExercise(exerciseId:"kb_snatch", sets:3, reps:"5/side", rest:90),
            ProgramExercise(exerciseId:"weighted_pullup", sets:4, reps:"6", rest:150),
            ProgramExercise(exerciseId:"kb_gorilla_row", sets:4, reps:"8/side", rest:90),
            ProgramExercise(exerciseId:"bent_over_row", sets:3, reps:"10", rest:60),
            ProgramExercise(exerciseId:"face_pull", sets:3, reps:"15", rest:45),
            ProgramExercise(exerciseId:"bicep_curl", sets:2, reps:"12", rest:45),
        ]),
        ProgramDay(name:"Thu: Upper Athletic", focus:"Explosive Upper + Stability", exercises:[
            ProgramExercise(exerciseId:"kb_snatch", sets:3, reps:"5/side", rest:90),
            ProgramExercise(exerciseId:"kb_push_press", sets:4, reps:"5/side", rest:90),
            ProgramExercise(exerciseId:"chinup", sets:4, reps:"6-8", rest:120),
            ProgramExercise(exerciseId:"half_kneeling_press", sets:3, reps:"8/side", rest:60),
            ProgramExercise(exerciseId:"renegade_row", sets:3, reps:"6/side", rest:90),
            ProgramExercise(exerciseId:"turkish_getup", sets:2, reps:"3/side", rest:90),
            ProgramExercise(exerciseId:"pallof_press", sets:3, reps:"10/side", rest:45),
        ]),
        ProgramDay(name:"Fri: Lower Strength", focus:"Heavy Lower + Power", exercises:[
            ProgramExercise(exerciseId:"kb_swing", sets:4, reps:"10", rest:60),
            ProgramExercise(exerciseId:"lateral_bound", sets:3, reps:"5/side", rest:60),
            ProgramExercise(exerciseId:"back_squat", sets:5, reps:"5", rest:180),
            ProgramExercise(exerciseId:"trap_bar_deadlift", sets:4, reps:"6", rest:150),
            ProgramExercise(exerciseId:"kb_walking_lunge", sets:3, reps:"10/side", rest:90),
            ProgramExercise(exerciseId:"single_leg_rdl", sets:3, reps:"8/side", rest:60),
            ProgramExercise(exerciseId:"nordic_curl", sets:3, reps:"5", rest:90),
            ProgramExercise(exerciseId:"calf_raise", sets:3, reps:"15", rest:45),
        ]),
    ]),
    Program(id:"defy_complexes", name:"Defy: Complexes", description:"Barbell, DB & KB complexes — full body integration day", frequency:"Add-on", level:"Advanced", days:[
        ProgramDay(name:"Barbell Complex", focus:"Hang Clean + Front Squat + Push Press", exercises:[
            ProgramExercise(exerciseId:"hang_clean", sets:3, reps:"5", rest:120),
            ProgramExercise(exerciseId:"front_squat", sets:3, reps:"5", rest:120),
            ProgramExercise(exerciseId:"push_press", sets:3, reps:"5", rest:120),
        ]),
        ProgramDay(name:"DB Complex", focus:"Snatch + Lunge + Renegade Row", exercises:[
            ProgramExercise(exerciseId:"db_snatch", sets:3, reps:"5/arm", rest:120),
            ProgramExercise(exerciseId:"lunge", sets:3, reps:"5/side", rest:90),
            ProgramExercise(exerciseId:"renegade_row", sets:3, reps:"5/side", rest:90),
        ]),
        ProgramDay(name:"KB Complex", focus:"Clean+Press + Goblet Squat + TGU", exercises:[
            ProgramExercise(exerciseId:"kb_push_press", sets:3, reps:"5/side", rest:90),
            ProgramExercise(exerciseId:"goblet_squat", sets:3, reps:"8", rest:60),
            ProgramExercise(exerciseId:"turkish_getup", sets:3, reps:"1/side", rest:90),
        ]),
    ]),
    // General Programs
    Program(id:"ppl", name:"Push Pull Legs", description:"Classic 6-day hypertrophy split", frequency:"6 days/week", level:"Intermediate", days:[
        ProgramDay(name:"Push A", focus:"Chest + Shoulders + Triceps", exercises:[
            ProgramExercise(exerciseId:"bench_press", sets:4, reps:"8-10", rest:120),
            ProgramExercise(exerciseId:"overhead_press", sets:3, reps:"8-10", rest:90),
            ProgramExercise(exerciseId:"incline_press", sets:3, reps:"10-12", rest:90),
            ProgramExercise(exerciseId:"lateral_raise", sets:3, reps:"12-15", rest:60),
            ProgramExercise(exerciseId:"tricep_extension", sets:3, reps:"10-12", rest:60),
        ]),
        ProgramDay(name:"Pull A", focus:"Back + Biceps", exercises:[
            ProgramExercise(exerciseId:"deadlift", sets:4, reps:"5-6", rest:180),
            ProgramExercise(exerciseId:"pullup", sets:3, reps:"6-10", rest:120),
            ProgramExercise(exerciseId:"bent_over_row", sets:3, reps:"8-10", rest:90),
            ProgramExercise(exerciseId:"face_pull", sets:3, reps:"15-20", rest:60),
            ProgramExercise(exerciseId:"bicep_curl", sets:3, reps:"10-12", rest:60),
        ]),
        ProgramDay(name:"Legs A", focus:"Quads + Glutes + Hamstrings", exercises:[
            ProgramExercise(exerciseId:"squat", sets:4, reps:"6-8", rest:180),
            ProgramExercise(exerciseId:"leg_press", sets:3, reps:"10-12", rest:120),
            ProgramExercise(exerciseId:"romanian_deadlift", sets:3, reps:"8-10", rest:90),
            ProgramExercise(exerciseId:"leg_extension", sets:3, reps:"12-15", rest:60),
            ProgramExercise(exerciseId:"calf_raise", sets:4, reps:"12-15", rest:60),
        ]),
        ProgramDay(name:"Push B", focus:"Shoulders + Chest + Triceps", exercises:[
            ProgramExercise(exerciseId:"overhead_press", sets:4, reps:"6-8", rest:120),
            ProgramExercise(exerciseId:"incline_press", sets:3, reps:"8-10", rest:90),
            ProgramExercise(exerciseId:"dips", sets:3, reps:"8-12", rest:90),
            ProgramExercise(exerciseId:"cable_fly", sets:3, reps:"12-15", rest:60),
            ProgramExercise(exerciseId:"lateral_raise", sets:4, reps:"12-15", rest:60),
        ]),
        ProgramDay(name:"Pull B", focus:"Back + Rear Delts + Biceps", exercises:[
            ProgramExercise(exerciseId:"bent_over_row", sets:4, reps:"6-8", rest:120),
            ProgramExercise(exerciseId:"lat_pulldown", sets:3, reps:"10-12", rest:90),
            ProgramExercise(exerciseId:"romanian_deadlift", sets:3, reps:"10-12", rest:90),
            ProgramExercise(exerciseId:"face_pull", sets:3, reps:"15-20", rest:60),
            ProgramExercise(exerciseId:"bicep_curl", sets:3, reps:"10-12", rest:60),
        ]),
        ProgramDay(name:"Legs B", focus:"Glutes + Hamstrings + Quads", exercises:[
            ProgramExercise(exerciseId:"hip_thrust", sets:4, reps:"8-10", rest:120),
            ProgramExercise(exerciseId:"lunge", sets:3, reps:"10-12 each", rest:90),
            ProgramExercise(exerciseId:"leg_curl", sets:3, reps:"10-12", rest:60),
            ProgramExercise(exerciseId:"leg_press", sets:3, reps:"12-15", rest:90),
            ProgramExercise(exerciseId:"calf_raise", sets:4, reps:"15-20", rest:60),
        ]),
    ]),
    Program(id:"upper_lower", name:"Upper / Lower", description:"4-day strength and hypertrophy", frequency:"4 days/week", level:"Beginner-Intermediate", days:[
        ProgramDay(name:"Upper A", focus:"Strength", exercises:[
            ProgramExercise(exerciseId:"bench_press", sets:4, reps:"5-6", rest:180),
            ProgramExercise(exerciseId:"bent_over_row", sets:4, reps:"5-6", rest:180),
            ProgramExercise(exerciseId:"overhead_press", sets:3, reps:"8-10", rest:120),
            ProgramExercise(exerciseId:"pullup", sets:3, reps:"6-10", rest:120),
            ProgramExercise(exerciseId:"face_pull", sets:3, reps:"15-20", rest:60),
        ]),
        ProgramDay(name:"Lower A", focus:"Strength", exercises:[
            ProgramExercise(exerciseId:"squat", sets:4, reps:"5-6", rest:180),
            ProgramExercise(exerciseId:"romanian_deadlift", sets:3, reps:"8-10", rest:120),
            ProgramExercise(exerciseId:"leg_press", sets:3, reps:"10-12", rest:90),
            ProgramExercise(exerciseId:"leg_curl", sets:3, reps:"10-12", rest:60),
            ProgramExercise(exerciseId:"calf_raise", sets:4, reps:"12-15", rest:60),
        ]),
        ProgramDay(name:"Upper B", focus:"Hypertrophy", exercises:[
            ProgramExercise(exerciseId:"incline_press", sets:4, reps:"8-10", rest:90),
            ProgramExercise(exerciseId:"lat_pulldown", sets:4, reps:"10-12", rest:90),
            ProgramExercise(exerciseId:"lateral_raise", sets:4, reps:"12-15", rest:60),
            ProgramExercise(exerciseId:"cable_fly", sets:3, reps:"12-15", rest:60),
            ProgramExercise(exerciseId:"bicep_curl", sets:3, reps:"10-12", rest:60),
            ProgramExercise(exerciseId:"tricep_extension", sets:3, reps:"10-12", rest:60),
        ]),
        ProgramDay(name:"Lower B", focus:"Hypertrophy", exercises:[
            ProgramExercise(exerciseId:"hip_thrust", sets:4, reps:"8-10", rest:120),
            ProgramExercise(exerciseId:"lunge", sets:3, reps:"10-12 each", rest:90),
            ProgramExercise(exerciseId:"leg_extension", sets:3, reps:"12-15", rest:60),
            ProgramExercise(exerciseId:"leg_curl", sets:3, reps:"12-15", rest:60),
            ProgramExercise(exerciseId:"calf_raise", sets:4, reps:"15-20", rest:60),
        ]),
    ]),
    Program(id:"full_body", name:"Full Body", description:"3-day total body training", frequency:"3 days/week", level:"Beginner", days:[
        ProgramDay(name:"Day 1", focus:"Compound Focus", exercises:[
            ProgramExercise(exerciseId:"squat", sets:4, reps:"6-8", rest:180),
            ProgramExercise(exerciseId:"bench_press", sets:4, reps:"6-8", rest:180),
            ProgramExercise(exerciseId:"bent_over_row", sets:3, reps:"8-10", rest:120),
            ProgramExercise(exerciseId:"plank", sets:3, reps:"45-60s", rest:60),
            ProgramExercise(exerciseId:"calf_raise", sets:3, reps:"15-20", rest:60),
        ]),
        ProgramDay(name:"Day 2", focus:"Hypertrophy", exercises:[
            ProgramExercise(exerciseId:"deadlift", sets:4, reps:"5-6", rest:180),
            ProgramExercise(exerciseId:"overhead_press", sets:3, reps:"8-10", rest:120),
            ProgramExercise(exerciseId:"pullup", sets:3, reps:"6-10", rest:120),
            ProgramExercise(exerciseId:"lunge", sets:3, reps:"10-12 each", rest:90),
            ProgramExercise(exerciseId:"face_pull", sets:3, reps:"15-20", rest:60),
        ]),
        ProgramDay(name:"Day 3", focus:"Strength + Accessories", exercises:[
            ProgramExercise(exerciseId:"hip_thrust", sets:4, reps:"8-10", rest:120),
            ProgramExercise(exerciseId:"incline_press", sets:3, reps:"8-10", rest:90),
            ProgramExercise(exerciseId:"lat_pulldown", sets:3, reps:"10-12", rest:90),
            ProgramExercise(exerciseId:"lateral_raise", sets:3, reps:"12-15", rest:60),
            ProgramExercise(exerciseId:"bicep_curl", sets:3, reps:"10-12", rest:60),
        ]),
    ]),
    // BoabFit — Julia's 6-Week Program
    Program(id:"boabfit_6week", name:"BoabFit 6-Week", description:"Sculpt + Tone — Dumbbells & Booty Band. 5 days on, 2 rest (Wed + Sun).", frequency:"5 days/week", level:"Beginner-Intermediate", days:[
        ProgramDay(name:"Mon: Full Body Sculpt + Tone", focus:"25 min — Feet grounded, core pulled in, chest lifted", exercises:[
            ProgramExercise(exerciseId:"bulgarian_split_squat", sets:3, reps:"1min, 8/side", rest:30),
            ProgramExercise(exerciseId:"bf_bench_row", sets:3, reps:"1min, 8/side", rest:30),
            ProgramExercise(exerciseId:"bf_squat_abduction", sets:3, reps:"1min, 8 total", rest:30),
            ProgramExercise(exerciseId:"single_leg_rdl", sets:3, reps:"1min, 8/side", rest:30),
            ProgramExercise(exerciseId:"lateral_raise", sets:3, reps:"1min, 8 total", rest:30),
            ProgramExercise(exerciseId:"bf_tricep_kickback", sets:3, reps:"1min, 8 total", rest:30),
            ProgramExercise(exerciseId:"bf_ab_routine", sets:3, reps:"1min", rest:30),
            ProgramExercise(exerciseId:"bf_donkey_kicks", sets:3, reps:"1min", rest:30),
        ]),
        ProgramDay(name:"Tue: Lower Body Build", focus:"25 min — Heels grounded, ribs down, squeeze glutes", exercises:[
            ProgramExercise(exerciseId:"bf_backwards_lunge", sets:3, reps:"1min, 8/leg", rest:30),
            ProgramExercise(exerciseId:"bf_bench_hip_thrust", sets:3, reps:"1min, 8 total", rest:30),
            ProgramExercise(exerciseId:"bf_sumo_squat", sets:3, reps:"1min, 8 total", rest:30),
            ProgramExercise(exerciseId:"bulgarian_split_squat", sets:3, reps:"1min, 8/side", rest:30),
            ProgramExercise(exerciseId:"bf_side_lunge", sets:3, reps:"1min, 8/side", rest:30),
            ProgramExercise(exerciseId:"bf_rdl", sets:3, reps:"1min, 8 total", rest:30),
            ProgramExercise(exerciseId:"bf_ab_routine", sets:3, reps:"1min", rest:30),
        ]),
        ProgramDay(name:"Thu: Upper Body Sculpt", focus:"22 min — Collarbones wide, shoulders relaxed", exercises:[
            ProgramExercise(exerciseId:"bf_reverse_grip_row", sets:3, reps:"30sec, 8 total", rest:30),
            ProgramExercise(exerciseId:"bf_girl_pushup", sets:3, reps:"30sec, 8 total", rest:30),
            ProgramExercise(exerciseId:"bf_hex_press", sets:3, reps:"30sec, 8 total", rest:30),
            ProgramExercise(exerciseId:"bf_tricep_kickback", sets:3, reps:"30sec, 8 total", rest:30),
            ProgramExercise(exerciseId:"bf_back_arm_pulse", sets:3, reps:"30sec, 8 total", rest:30),
            ProgramExercise(exerciseId:"bf_wall_raise", sets:3, reps:"30sec, 8 total", rest:30),
            ProgramExercise(exerciseId:"bf_donkey_kicks", sets:3, reps:"1min", rest:30),
        ]),
        ProgramDay(name:"Fri: Lower Body Sculpt", focus:"24 min — Full foot, inner thighs engaged, slow and controlled", exercises:[
            ProgramExercise(exerciseId:"bf_backwards_lunge", sets:3, reps:"1min, 8/leg", rest:30),
            ProgramExercise(exerciseId:"bf_step_up", sets:3, reps:"1min, 8/leg", rest:30),
            ProgramExercise(exerciseId:"goblet_squat", sets:3, reps:"1min, 8 total", rest:30),
            ProgramExercise(exerciseId:"bf_curtsey_lunge", sets:3, reps:"1min, 8/side", rest:30),
            ProgramExercise(exerciseId:"bf_side_lunge_toe_touch", sets:3, reps:"1min, 8/side", rest:30),
            ProgramExercise(exerciseId:"bf_squat_abduction", sets:3, reps:"1min, 8 total", rest:30),
            ProgramExercise(exerciseId:"bf_ab_routine", sets:3, reps:"1min", rest:30),
        ]),
        ProgramDay(name:"Sat: Upper Body Build", focus:"21 min — Stable core, power through arms, neck relaxed", exercises:[
            ProgramExercise(exerciseId:"bf_bench_row", sets:3, reps:"1min, 8/side", rest:30),
            ProgramExercise(exerciseId:"bf_overhead_tricep_ext", sets:3, reps:"1min, 8 total", rest:30),
            ProgramExercise(exerciseId:"bf_back_arm_pulse", sets:3, reps:"1min, 8 total", rest:30),
            ProgramExercise(exerciseId:"bf_hammer_curl", sets:3, reps:"1min, 8 total", rest:30),
            ProgramExercise(exerciseId:"bf_y_raise", sets:3, reps:"1min, 8 total", rest:30),
            ProgramExercise(exerciseId:"bf_bent_over_lat_raise", sets:3, reps:"1min, 8 total", rest:30),
            ProgramExercise(exerciseId:"bf_donkey_kicks", sets:3, reps:"1min", rest:30),
        ]),
    ]),
]

let categories = ["All","Legs","Back","Chest","Shoulders","Arms","Core","Glutes","Full Body"]

// MARK: - Content View (Tab Bar)
struct ContentView: View {
    @EnvironmentObject var store: WorkoutStore
    @State private var tab = 0
    var body: some View {
        ZStack(alignment: .bottom) {
            Group {
                switch tab {
                case 0: HomeView()
                case 1: ProgramsView()
                case 2: ExercisesView()
                case 3: NutritionView()
                case 4: MyProgressView()
                case 5: SettingsView()
                default: HomeView()
                }
            }

            // Custom tab bar
            HStack {
                tabItem(icon:"house.fill", label:"Home", idx:0)
                tabItem(icon:"square.grid.2x2.fill", label:"Programs", idx:1)
                tabItem(icon:"dumbbell.fill", label:"Exercises", idx:2)
                tabItem(icon:"fork.knife", label:"Nutrition", idx:3)
                tabItem(icon:"chart.line.uptrend.xyaxis", label:"Progress", idx:4)
                tabItem(icon:"gearshape.fill", label:"Settings", idx:5)
            }
            .padding(.top, 10)
            .padding(.bottom, 6)
            .background(.ultraThinMaterial)
            .overlay(Divider(), alignment:.top)
        }
        .ignoresSafeArea(.keyboard)
    }

    func tabItem(icon: String, label: String, idx: Int) -> some View {
        Button { tab = idx } label: {
            VStack(spacing:3) {
                Image(systemName: icon).font(.system(size:20))
                Text(label).font(.system(size:10, weight:.medium))
            }
            .foregroundColor(tab == idx ? .gold : .gray)
            .frame(maxWidth: .infinity)
        }
    }
}

// MARK: - Home View
struct HomeView: View {
    @EnvironmentObject var store: WorkoutStore
    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 16) {
                    // Stats
                    LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible())], spacing: 10) {
                        statCard(value:"\(store.totalWorkouts)", label:"Workouts")
                        statCard(value:"\(store.streak)", label:"Day Streak")
                        statCard(value: store.totalVolume > 1000 ? "\(store.totalVolume/1000)K" : "\(store.totalVolume)", label:"Total Volume")
                        statCard(value:"\(exerciseDB.count)", label:"Exercises")
                    }

                    // Today's Workout
                    VStack(alignment:.leading, spacing:8) {
                        Text("TODAY'S WORKOUT").font(.caption).fontWeight(.semibold).foregroundColor(.dim).tracking(1)
                        let today = todayWorkout()
                        NavigationLink { ProgramDayDetailView(day: today) } label: {
                            VStack(alignment:.leading, spacing:6) {
                                HStack {
                                    Text(today.name).font(.headline).fontWeight(.bold)
                                    Spacer()
                                    Text(today.focus).font(.caption).fontWeight(.semibold).foregroundColor(.gold)
                                        .padding(.horizontal, 10).padding(.vertical, 4).background(Color.goldDim).cornerRadius(12)
                                }
                                Text("\(today.exercises.count) exercises").font(.caption).foregroundColor(.dim)
                            }
                            .padding(16).background(Color.bg3).cornerRadius(14).overlay(RoundedRectangle(cornerRadius:14).stroke(Color(.systemGray5), lineWidth:1))
                        }
                        .buttonStyle(.plain)
                    }

                    // History
                    VStack(alignment:.leading, spacing:8) {
                        Text("RECENT HISTORY").font(.caption).fontWeight(.semibold).foregroundColor(.dim).tracking(1)
                        if store.history.isEmpty {
                            Text("Complete your first workout to see history here.").font(.subheadline).foregroundColor(.dim).frame(maxWidth:.infinity).padding(30)
                        } else {
                            ForEach(store.history.prefix(5)) { h in
                                VStack(alignment:.leading, spacing:4) {
                                    Text(h.date, style:.date).font(.caption).foregroundColor(.gold).fontWeight(.semibold)
                                    Text(h.name).font(.subheadline).fontWeight(.semibold)
                                    Text("\(h.exerciseCount) exercises  •  \(h.volume) lbs  •  \(h.duration) min")
                                        .font(.caption).foregroundColor(.dim)
                                }
                                .padding(14).frame(maxWidth:.infinity, alignment:.leading).background(Color.bg3).cornerRadius(12)
                                .overlay(RoundedRectangle(cornerRadius:12).stroke(Color(.systemGray5), lineWidth:1))
                            }
                        }
                    }
                }
                .padding()
            }
            .background(Color.bg)
            .navigationTitle("")
            .toolbar {
                ToolbarItem(placement:.principal) {
                    HStack(spacing:4) {
                        Text("MARCEAU").font(.headline).fontWeight(.black).foregroundColor(.gold)
                        Text("FITNESS").font(.headline).fontWeight(.bold)
                    }
                }
            }
        }
    }

    func todayWorkout() -> ProgramDay {
        let prog = programDB.first { $0.id == store.selectedProgram } ?? programDB[0]
        let idx = Calendar.current.component(.weekday, from: Date()) % prog.days.count
        return prog.days[idx]
    }

    func statCard(value: String, label: String) -> some View {
        VStack(spacing:4) {
            Text(value).font(.system(size:28, weight:.black)).foregroundColor(.gold)
            Text(label.uppercased()).font(.system(size:9, weight:.semibold)).foregroundColor(.dim).tracking(0.5)
        }
        .frame(maxWidth:.infinity).padding(16).background(Color.bg3).cornerRadius(14)
        .overlay(RoundedRectangle(cornerRadius:14).stroke(Color(.systemGray5), lineWidth:1))
    }
}

// MARK: - Programs View
struct ProgramsView: View {
    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 12) {
                    Text("TRAINING PROGRAMS").font(.caption).fontWeight(.semibold).foregroundColor(.dim).tracking(1)
                        .frame(maxWidth:.infinity, alignment:.leading).padding(.horizontal)
                    ForEach(programDB) { prog in
                        NavigationLink { ProgramDetailView(program: prog) } label: {
                            VStack(alignment:.leading, spacing:6) {
                                HStack {
                                    Text(prog.name).font(.headline).fontWeight(.bold)
                                    Spacer()
                                    Text(prog.level).font(.caption).fontWeight(.semibold).foregroundColor(.gold)
                                        .padding(.horizontal,10).padding(.vertical,4).background(Color.goldDim).cornerRadius(12)
                                }
                                Text("\(prog.description)  •  \(prog.frequency)").font(.caption).foregroundColor(.dim)
                                Text(prog.days.map(\.name).joined(separator: ", ")).font(.caption2).foregroundColor(.dim)
                            }
                            .padding(16).background(Color.bg3).cornerRadius(14).overlay(RoundedRectangle(cornerRadius:14).stroke(Color(.systemGray5), lineWidth:1))
                        }
                        .buttonStyle(.plain).padding(.horizontal)
                    }
                }
                .padding(.top)
            }
            .background(Color.bg)
            .navigationTitle("")
            .toolbar {
                ToolbarItem(placement:.principal) {
                    HStack(spacing:4) {
                        Text("MARCEAU").font(.headline).fontWeight(.black).foregroundColor(.gold)
                        Text("FITNESS").font(.headline).fontWeight(.bold)
                    }
                }
            }
        }
    }
}

// MARK: - Program Detail
struct ProgramDetailView: View {
    @EnvironmentObject var store: WorkoutStore
    let program: Program
    var isActive: Bool { store.selectedProgram == program.id }
    var body: some View {
        ScrollView {
            VStack(alignment:.leading, spacing:16) {
                HStack {
                    VStack(alignment:.leading, spacing:4) {
                        Text(program.name).font(.title).fontWeight(.black)
                        Text("\(program.description)  •  \(program.frequency)").font(.subheadline).foregroundColor(.dim)
                    }
                    Spacer()
                    if isActive {
                        Text("ACTIVE").font(.caption).fontWeight(.bold).foregroundColor(.gold)
                            .padding(.horizontal, 10).padding(.vertical, 5).background(Color.goldDim).cornerRadius(8)
                    }
                }
                if !isActive {
                    Button {
                        store.selectedProgram = program.id
                        store.save()
                        UIImpactFeedbackGenerator(style:.medium).impactOccurred()
                    } label: {
                        Text("Set as Active Program")
                            .font(.subheadline).fontWeight(.bold).foregroundColor(.gold)
                            .frame(maxWidth:.infinity).padding(12)
                            .background(Color.goldDim).cornerRadius(12)
                            .overlay(RoundedRectangle(cornerRadius:12).stroke(Color.gold, lineWidth:1))
                    }
                }

                ForEach(Array(program.days.enumerated()), id:\.offset) { idx, day in
                    VStack(alignment:.leading, spacing:8) {
                        HStack(spacing:10) {
                            Text("\(idx+1)").font(.caption).fontWeight(.bold).foregroundColor(.black)
                                .frame(width:28, height:28).background(Color.gold).cornerRadius(7)
                            VStack(alignment:.leading) {
                                Text(day.name).font(.subheadline).fontWeight(.semibold)
                                Text(day.focus).font(.caption).foregroundColor(.dim)
                            }
                        }
                        ForEach(day.exercises) { ex in
                            if let e = exerciseFor(ex.exerciseId) {
                                HStack {
                                    Text("\(e.icon) \(e.name)").font(.subheadline)
                                    Spacer()
                                    Text("\(ex.sets)x\(ex.reps)").font(.caption).foregroundColor(.dim)
                                }
                                .padding(10).padding(.leading,38).background(Color.bg2).cornerRadius(8)
                            }
                        }
                        NavigationLink { ActiveWorkoutView(day: day) } label: {
                            Text("Start \(day.name)")
                                .font(.subheadline).fontWeight(.bold).foregroundColor(.black)
                                .frame(maxWidth:.infinity).padding(14).background(Color.gold).cornerRadius(12)
                                .padding(.leading, 38)
                        }
                    }
                }
            }
            .padding()
        }
        .background(Color.bg)
    }
}

// MARK: - Program Day Detail (from Home)
struct ProgramDayDetailView: View {
    let day: ProgramDay
    var body: some View {
        ScrollView {
            VStack(alignment:.leading, spacing:12) {
                Text(day.name).font(.title).fontWeight(.black)
                Text(day.focus).font(.subheadline).foregroundColor(.gold)
                ForEach(day.exercises) { ex in
                    if let e = exerciseFor(ex.exerciseId) {
                        NavigationLink { ExerciseDetailView(exercise: e) } label: {
                            HStack {
                                Text(e.icon).font(.title2).frame(width:40, height:40).background(Color.goldDim).cornerRadius(10)
                                VStack(alignment:.leading) {
                                    Text(e.name).font(.subheadline).fontWeight(.semibold)
                                    Text("\(ex.sets) sets x \(ex.reps)  •  \(ex.rest)s rest").font(.caption).foregroundColor(.dim)
                                }
                                Spacer()
                            }
                            .padding(12).background(Color.bg3).cornerRadius(12)
                            .overlay(RoundedRectangle(cornerRadius:12).stroke(Color(.systemGray5), lineWidth:1))
                        }
                        .buttonStyle(.plain)
                    }
                }
                NavigationLink { ActiveWorkoutView(day: day) } label: {
                    Text("Start Workout")
                        .font(.headline).fontWeight(.bold).foregroundColor(.black)
                        .frame(maxWidth:.infinity).padding(16).background(Color.gold).cornerRadius(14)
                }
                .padding(.top, 8)
            }
            .padding()
        }
        .background(Color.bg)
    }
}

// MARK: - Active Workout
struct ActiveWorkoutView: View {
    @EnvironmentObject var store: WorkoutStore
    @Environment(\.dismiss) var dismiss
    let day: ProgramDay
    @State private var exercises: [ActiveExercise] = []
    @State private var startTime = Date()
    @State private var expanded: Set<String> = []
    @State private var showSummary = false
    @State private var summaryData: WorkoutSummaryData? = nil
    // Rest timer
    @State private var restRemaining = 0
    @State private var restTotal = 0
    @State private var restTimer: Timer? = nil

    var body: some View {
        ZStack {
            ScrollView {
                VStack(alignment:.leading, spacing:12) {
                    Text(day.name).font(.title).fontWeight(.black)
                    Text("\(day.focus)  •  \(elapsed) min").font(.subheadline).foregroundColor(.dim)

                    ForEach(Array(exercises.indices), id:\.self) { ei in
                        let ex = exercises[ei]
                        if let e = exerciseFor(ex.exerciseId) {
                            VStack(spacing:0) {
                                Button {
                                    withAnimation { if expanded.contains(ex.id) { expanded.remove(ex.id) } else { expanded.insert(ex.id) } }
                                } label: {
                                    HStack {
                                        Text("\(e.icon) \(e.name)").font(.subheadline).fontWeight(.semibold)
                                        Spacer()
                                        let done = ex.sets.filter(\.done).count
                                        Text("\(done)/\(ex.targetSets)").font(.caption).foregroundColor(done == ex.targetSets ? .gold : .dim)
                                        Image(systemName: expanded.contains(ex.id) ? "chevron.up" : "chevron.down").font(.caption).foregroundColor(.dim)
                                    }
                                    .padding(14)
                                }
                                .buttonStyle(.plain)

                                if expanded.contains(ex.id) {
                                    VStack(spacing:8) {
                                        Text("Target: \(ex.targetSets)x\(ex.targetReps)  •  Rest: \(ex.rest)s")
                                            .font(.caption).foregroundColor(.dim)
                                        ForEach(Array(ex.sets.indices), id:\.self) { si in
                                            HStack(spacing:8) {
                                                Text("Set \(si+1)").font(.caption).foregroundColor(.dim).frame(width:44, alignment:.leading)
                                                TextField("lbs", text: $exercises[ei].sets[si].weight)
                                                    .keyboardType(.numberPad).textFieldStyle(.roundedBorder).frame(height:38)
                                                TextField("reps", text: $exercises[ei].sets[si].reps)
                                                    .keyboardType(.numberPad).textFieldStyle(.roundedBorder).frame(height:38)
                                                Button {
                                                    exercises[ei].sets[si].done.toggle()
                                                    if exercises[ei].sets[si].done {
                                                        UIImpactFeedbackGenerator(style:.medium).impactOccurred()
                                                        startRest(seconds: ex.rest)
                                                    }
                                                } label: {
                                                    Image(systemName: exercises[ei].sets[si].done ? "checkmark.circle.fill" : "circle")
                                                        .font(.title2).foregroundColor(exercises[ei].sets[si].done ? .gold : .gray)
                                                }
                                            }
                                        }
                                        VStack(alignment:.leading, spacing:4) {
                                            Text("FORM CUES").font(.system(size:10, weight:.semibold)).foregroundColor(.gold).tracking(0.5)
                                            ForEach(e.cues, id:\.self) { cue in
                                                HStack(alignment:.top, spacing:6) {
                                                    Circle().fill(Color.goldDim).frame(width:6, height:6).padding(.top,5)
                                                    Text(cue).font(.caption).foregroundColor(.dim)
                                                }
                                            }
                                        }
                                        .padding(12).background(Color.bg2).cornerRadius(10)
                                    }
                                    .padding(.horizontal, 14).padding(.bottom, 14)
                                }
                            }
                            .background(Color.bg3).cornerRadius(12)
                            .overlay(RoundedRectangle(cornerRadius:12).stroke(Color(.systemGray5), lineWidth:1))
                        }
                    }

                    Button { finishWorkout() } label: {
                        Text("Finish Workout")
                            .font(.headline).fontWeight(.bold).foregroundColor(.black)
                            .frame(maxWidth:.infinity).padding(16).background(Color.gold).cornerRadius(14)
                    }
                    .padding(.top, 12)
                    .padding(.bottom, restRemaining > 0 ? 80 : 0)
                }
                .padding()
            }
            .background(Color.bg)

            // Floating rest timer
            if restRemaining > 0 {
                VStack {
                    Spacer()
                    HStack(spacing: 12) {
                        ZStack {
                            Circle().stroke(Color(.systemGray5), lineWidth: 4).frame(width: 44, height: 44)
                            Circle().trim(from: 0, to: CGFloat(restRemaining) / CGFloat(max(restTotal, 1)))
                                .stroke(Color.gold, style: StrokeStyle(lineWidth: 4, lineCap: .round))
                                .frame(width: 44, height: 44).rotationEffect(.degrees(-90))
                            Text("\(restRemaining)").font(.system(size: 14, weight: .bold, design: .monospaced))
                        }
                        VStack(alignment: .leading, spacing: 2) {
                            Text("REST").font(.caption).fontWeight(.bold).foregroundColor(.gold).tracking(1)
                            Text("Next set in \(restRemaining)s").font(.caption).foregroundColor(.dim)
                        }
                        Spacer()
                        Button {
                            restTimer?.invalidate()
                            restRemaining = 0
                        } label: {
                            Text("Skip").font(.caption).fontWeight(.bold).foregroundColor(.gold)
                                .padding(.horizontal, 14).padding(.vertical, 8)
                                .background(Color.goldDim).cornerRadius(8)
                        }
                    }
                    .padding(16)
                    .background(.ultraThinMaterial)
                    .cornerRadius(16)
                    .padding(.horizontal)
                    .padding(.bottom, 8)
                }
                .transition(.move(edge: .bottom).combined(with: .opacity))
            }
        }
        .scrollDismissesKeyboard(.immediately)
        .toolbar { ToolbarItemGroup(placement:.keyboard) { Spacer(); Button("Done") { hideKeyboard() }.fontWeight(.semibold) } }
        .onAppear {
            if exercises.isEmpty {
                startTime = Date()
                expanded.insert(day.exercises.first?.exerciseId ?? "")
                exercises = day.exercises.map { ex in
                    ActiveExercise(exerciseId: ex.exerciseId, targetSets: ex.sets, targetReps: ex.reps, rest: ex.rest,
                                   sets: (0..<ex.sets).map { _ in SetLog() })
                }
            }
        }
        .onDisappear { restTimer?.invalidate() }
        .sheet(isPresented: $showSummary) {
            if let data = summaryData {
                WorkoutSummaryView(data: data) { dismiss() }
            }
        }
    }

    var elapsed: Int { Int(Date().timeIntervalSince(startTime) / 60) }

    func startRest(seconds: Int) {
        restTimer?.invalidate()
        restTotal = seconds
        restRemaining = seconds
        withAnimation { }
        restTimer = Timer.scheduledTimer(withTimeInterval: 1, repeats: true) { _ in
            if restRemaining > 1 {
                restRemaining -= 1
            } else {
                restTimer?.invalidate()
                withAnimation { restRemaining = 0 }
                UIImpactFeedbackGenerator(style: .heavy).impactOccurred()
            }
        }
    }

    func finishWorkout() {
        restTimer?.invalidate()
        restRemaining = 0
        let duration = Int(Date().timeIntervalSince(startTime) / 60)
        var volume = 0; var exCount = 0; var setsCompleted = 0
        for ex in exercises {
            var had = false
            for s in ex.sets where s.done {
                let w = Double(s.weight) ?? 0; let r = Int(s.reps) ?? 0
                volume += Int(w) * r; setsCompleted += 1; had = true
            }
            if had { exCount += 1 }
        }
        summaryData = WorkoutSummaryData(name: day.name, duration: duration, exerciseCount: exCount, setsCompleted: setsCompleted, totalVolume: volume)
        store.activeWorkout = exercises
        store.activeWorkoutName = day.name
        store.activeWorkoutStart = startTime
        store.finishWorkout()
        UINotificationFeedbackGenerator().notificationOccurred(.success)
        showSummary = true
    }
}

// MARK: - Workout Summary
struct WorkoutSummaryData {
    let name: String; let duration: Int; let exerciseCount: Int; let setsCompleted: Int; let totalVolume: Int
}

struct WorkoutSummaryView: View {
    let data: WorkoutSummaryData
    let onDismiss: () -> Void

    var body: some View {
        VStack(spacing: 24) {
            Spacer()
            Text("WORKOUT COMPLETE").font(.caption).fontWeight(.bold).foregroundColor(.gold).tracking(2)
            Text(data.name).font(.title).fontWeight(.black)

            LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible())], spacing: 14) {
                summaryCard(value: "\(data.duration)", label: "Minutes", icon: "clock.fill")
                summaryCard(value: "\(data.exerciseCount)", label: "Exercises", icon: "dumbbell.fill")
                summaryCard(value: "\(data.setsCompleted)", label: "Sets Done", icon: "checkmark.circle.fill")
                summaryCard(value: data.totalVolume > 1000 ? "\(data.totalVolume/1000)K" : "\(data.totalVolume)", label: "Volume (lbs)", icon: "flame.fill")
            }
            .padding(.horizontal)

            Spacer()

            Button { onDismiss() } label: {
                Text("Done")
                    .font(.headline).fontWeight(.bold).foregroundColor(.black)
                    .frame(maxWidth: .infinity).padding(16).background(Color.gold).cornerRadius(14)
            }
            .padding(.horizontal)
            .padding(.bottom, 30)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(Color.bg)
        .interactiveDismissDisabled()
    }

    func summaryCard(value: String, label: String, icon: String) -> some View {
        VStack(spacing: 8) {
            Image(systemName: icon).font(.title2).foregroundColor(.gold)
            Text(value).font(.system(size: 28, weight: .black)).foregroundColor(.white)
            Text(label.uppercased()).font(.system(size: 9, weight: .semibold)).foregroundColor(.dim).tracking(0.5)
        }
        .frame(maxWidth: .infinity).padding(20).background(Color.bg3).cornerRadius(14)
        .overlay(RoundedRectangle(cornerRadius: 14).stroke(Color(.systemGray5), lineWidth: 1))
    }
}

// MARK: - Exercises View
struct ExercisesView: View {
    @State private var filter = "All"
    @State private var search = ""
    var filtered: [Exercise] {
        exerciseDB.filter { ex in
            (filter == "All" || ex.category == filter) &&
            (search.isEmpty || ex.name.localizedCaseInsensitiveContains(search))
        }
    }
    var body: some View {
        NavigationStack {
            VStack(spacing:0) {
                // Filter pills
                ScrollView(.horizontal, showsIndicators:false) {
                    HStack(spacing:6) {
                        ForEach(categories, id:\.self) { cat in
                            Button { filter = cat } label: {
                                Text(cat).font(.caption).fontWeight(.medium).foregroundColor(filter == cat ? .gold : .dim)
                                    .padding(.horizontal,14).padding(.vertical,7)
                                    .background(filter == cat ? Color.goldDim : Color.bg3)
                                    .cornerRadius(20).overlay(RoundedRectangle(cornerRadius:20).stroke(filter == cat ? Color.gold : Color(.systemGray5), lineWidth:1))
                            }
                        }
                    }
                    .padding(.horizontal).padding(.vertical, 8)
                }

                ScrollView {
                    LazyVStack(spacing:8) {
                        ForEach(filtered) { ex in
                            NavigationLink { ExerciseDetailView(exercise: ex) } label: {
                                HStack(spacing:12) {
                                    Text(ex.icon).font(.title2).frame(width:44, height:44).background(Color.goldDim).cornerRadius(10)
                                    VStack(alignment:.leading, spacing:2) {
                                        Text(ex.name).font(.subheadline).fontWeight(.semibold)
                                        Text(ex.muscles.prefix(3).joined(separator:" • ")).font(.caption).foregroundColor(.dim)
                                    }
                                    Spacer()
                                    Image(systemName:"chevron.right").font(.caption).foregroundColor(.dim)
                                }
                                .padding(12).background(Color.bg3).cornerRadius(12)
                                .overlay(RoundedRectangle(cornerRadius:12).stroke(Color(.systemGray5), lineWidth:1))
                            }
                            .buttonStyle(.plain)
                        }
                    }
                    .padding(.horizontal)
                }
            }
            .background(Color.bg)
            .searchable(text: $search, prompt:"Search exercises")
            .navigationTitle("")
            .toolbar {
                ToolbarItem(placement:.principal) {
                    HStack(spacing:4) {
                        Text("MARCEAU").font(.headline).fontWeight(.black).foregroundColor(.gold)
                        Text("FITNESS").font(.headline).fontWeight(.bold)
                    }
                }
            }
        }
    }
}

// MARK: - Exercise Detail
struct ExerciseDetailView: View {
    let exercise: Exercise
    var body: some View {
        ScrollView {
            VStack(spacing:20) {
                // Header
                VStack(spacing:8) {
                    Text(exercise.icon).font(.system(size:50)).frame(width:80, height:80).background(Color.goldDim).cornerRadius(20)
                    Text(exercise.name).font(.title).fontWeight(.black)
                    Text(exercise.category).font(.subheadline).fontWeight(.semibold).foregroundColor(.gold)
                }
                .frame(maxWidth:.infinity).padding(.vertical)

                // Description
                section("About") { Text(exercise.description).font(.subheadline).foregroundColor(.dim) }

                // Difficulty
                section("Difficulty") {
                    HStack(spacing:4) {
                        ForEach(1...3, id:\.self) { d in
                            Circle().fill(d <= exercise.difficulty ? Color.gold : Color(.systemGray5)).frame(width:12, height:12)
                        }
                    }
                }

                // Muscles
                section("Target Muscles") {
                    FlowLayout(spacing:6) {
                        ForEach(exercise.muscles, id:\.self) { m in
                            Text(m).font(.caption).fontWeight(.medium).foregroundColor(.gold)
                                .padding(.horizontal,12).padding(.vertical,5).background(Color.goldDim).cornerRadius(20)
                        }
                    }
                }

                // Equipment
                section("Equipment") {
                    FlowLayout(spacing:6) {
                        ForEach(exercise.equipment, id:\.self) { eq in
                            Text(eq).font(.caption).fontWeight(.medium).foregroundColor(.dim)
                                .padding(.horizontal,12).padding(.vertical,5).background(Color.bg2).cornerRadius(20)
                                .overlay(RoundedRectangle(cornerRadius:20).stroke(Color(.systemGray5), lineWidth:1))
                        }
                    }
                }

                // Form cues
                section("Form Cues") {
                    VStack(alignment:.leading, spacing:6) {
                        ForEach(exercise.cues, id:\.self) { cue in
                            HStack(alignment:.top, spacing:8) {
                                Circle().fill(Color.goldDim).frame(width:6, height:6).padding(.top,6)
                                Text(cue).font(.subheadline).foregroundColor(.dim)
                            }
                        }
                    }
                    .padding(14).background(Color.bg3).cornerRadius(12)
                }
            }
            .padding()
        }
        .background(Color.bg)
    }

    func section(_ title: String, @ViewBuilder content: () -> some View) -> some View {
        VStack(alignment:.leading, spacing:8) {
            Text(title.uppercased()).font(.system(size:11, weight:.semibold)).foregroundColor(.gold).tracking(0.5)
            content()
        }
        .frame(maxWidth:.infinity, alignment:.leading)
    }
}

// MARK: - Timer View
struct TimerView: View {
    @State private var total = 90
    @State private var remaining = 90
    @State private var running = false
    @State private var timer: Timer? = nil
    let presets = [30, 60, 90, 120, 180, 300]

    var body: some View {
        NavigationStack {
            VStack(spacing:24) {
                Spacer()
                Text("REST TIMER").font(.caption).fontWeight(.semibold).foregroundColor(.dim).tracking(1)
                Text(timeString(remaining)).font(.system(size:72, weight:.black, design:.monospaced)).foregroundColor(.gold)
                HStack(spacing:12) {
                    Button { toggleTimer() } label: {
                        Text(running ? "Pause" : "Start")
                            .font(.headline).fontWeight(.bold).foregroundColor(.black)
                            .padding(.horizontal,32).padding(.vertical,14).background(Color.gold).cornerRadius(14)
                    }
                    Button { resetTimer() } label: {
                        Text("Reset")
                            .font(.headline).fontWeight(.bold).foregroundColor(.white)
                            .padding(.horizontal,32).padding(.vertical,14).background(Color.bg3).cornerRadius(14)
                            .overlay(RoundedRectangle(cornerRadius:14).stroke(Color(.systemGray5), lineWidth:1))
                    }
                }
                HStack(spacing:8) {
                    ForEach(presets, id:\.self) { p in
                        Button { setPreset(p) } label: {
                            Text(timeString(p)).font(.caption).fontWeight(.medium)
                                .foregroundColor(total == p ? .gold : .dim)
                                .padding(.horizontal,14).padding(.vertical,8).background(total == p ? Color.goldDim : Color.bg3)
                                .cornerRadius(20).overlay(RoundedRectangle(cornerRadius:20).stroke(total == p ? Color.gold : Color(.systemGray5), lineWidth:1))
                        }
                    }
                }
                Spacer()
            }
            .frame(maxWidth:.infinity)
            .background(Color.bg)
            .navigationTitle("")
            .toolbar {
                ToolbarItem(placement:.principal) {
                    HStack(spacing:4) {
                        Text("MARCEAU").font(.headline).fontWeight(.black).foregroundColor(.gold)
                        Text("FITNESS").font(.headline).fontWeight(.bold)
                    }
                }
            }
        }
    }

    func timeString(_ s: Int) -> String { "\(s/60):\(String(format:"%02d", s%60))" }
    func setPreset(_ p: Int) { timer?.invalidate(); running = false; total = p; remaining = p }
    func resetTimer() { timer?.invalidate(); running = false; remaining = total }
    func toggleTimer() {
        if running { timer?.invalidate(); running = false }
        else {
            running = true
            timer = Timer.scheduledTimer(withTimeInterval:1, repeats:true) { _ in
                remaining -= 1
                if remaining <= 0 {
                    timer?.invalidate(); running = false; remaining = total
                    UIImpactFeedbackGenerator(style:.heavy).impactOccurred()
                }
            }
        }
    }
}

// MARK: - Progress View
struct MyProgressView: View {
    @EnvironmentObject var store: WorkoutStore
    @State private var showAddMetric = false
    @State private var newWeight = ""
    @State private var newBodyFat = ""
    @State private var newWaist = ""
    @State private var newHips = ""
    @State private var newArms = ""
    @State private var newThighs = ""
    @State private var newNotes = ""

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 16) {
                    // Current Stats
                    HStack(spacing: 12) {
                        statCard(title: "Weight", value: store.latestWeight.map { String(format: "%.1f", $0) } ?? "--", unit: "lbs", change: store.weightChange)
                        statCard(title: "Body Fat", value: store.latestBodyFat.map { String(format: "%.1f", $0) } ?? "--", unit: "%", change: nil)
                    }
                    .padding(.horizontal)

                    // Weight Trend Chart
                    if store.bodyMetrics.count >= 2 {
                        VStack(alignment: .leading, spacing: 8) {
                            Text("WEIGHT TREND").font(.caption).fontWeight(.bold).foregroundColor(.dim)
                            WeightChartView(metrics: store.bodyMetrics)
                                .frame(height: 160)
                        }
                        .padding()
                        .background(Color.bg2)
                        .cornerRadius(16)
                        .padding(.horizontal)
                    }

                    // History
                    VStack(alignment: .leading, spacing: 10) {
                        Text("MEASUREMENT LOG").font(.caption).fontWeight(.bold).foregroundColor(.dim).padding(.horizontal)
                        if store.bodyMetrics.isEmpty {
                            Text("No measurements yet. Tap + to log your first one.")
                                .font(.subheadline).foregroundColor(.dim)
                                .frame(maxWidth: .infinity).padding(30)
                        } else {
                            ForEach(store.bodyMetrics.sorted { $0.date > $1.date }) { m in
                                metricRow(m)
                            }
                        }
                    }
                }
                .padding(.bottom, 100)
            }
            .background(Color.bg)
            .navigationTitle("Progress")
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button { showAddMetric = true } label: {
                        Image(systemName: "plus.circle.fill").foregroundColor(.gold).font(.title2)
                    }
                }
            }
            .sheet(isPresented: $showAddMetric) { addMetricSheet }
        }
    }

    func statCard(title: String, value: String, unit: String, change: Double?) -> some View {
        VStack(spacing: 6) {
            Text(title).font(.caption).fontWeight(.bold).foregroundColor(.dim)
            HStack(alignment: .lastTextBaseline, spacing: 2) {
                Text(value).font(.system(size: 32, weight: .black))
                Text(unit).font(.caption).foregroundColor(.dim)
            }
            if let change = change {
                HStack(spacing: 4) {
                    Image(systemName: change <= 0 ? "arrow.down.right" : "arrow.up.right")
                        .font(.caption2)
                    Text(String(format: "%+.1f lbs", change)).font(.caption).fontWeight(.semibold)
                }
                .foregroundColor(change <= 0 ? .green : .orange)
            }
        }
        .frame(maxWidth: .infinity)
        .padding()
        .background(Color.bg2)
        .cornerRadius(16)
    }

    func metricRow(_ m: BodyMetric) -> some View {
        HStack {
            VStack(alignment: .leading, spacing: 4) {
                Text(m.date, style: .date).font(.subheadline).fontWeight(.semibold)
                HStack(spacing: 12) {
                    if let w = m.weight { Label(String(format: "%.1f lbs", w), systemImage: "scalemass").font(.caption).foregroundColor(.dim) }
                    if let bf = m.bodyFat { Label(String(format: "%.1f%%", bf), systemImage: "percent").font(.caption).foregroundColor(.dim) }
                    if let wa = m.waist { Label(String(format: "%.1f\"", wa), systemImage: "ruler").font(.caption).foregroundColor(.dim) }
                }
                if !m.notes.isEmpty {
                    Text(m.notes).font(.caption).foregroundColor(.dim).lineLimit(1)
                }
            }
            Spacer()
            Button { store.deleteMetric(m) } label: {
                Image(systemName: "trash").font(.caption).foregroundColor(.red.opacity(0.6))
            }
        }
        .padding()
        .background(Color.bg2)
        .cornerRadius(12)
        .padding(.horizontal)
    }

    var addMetricSheet: some View {
        NavigationStack {
            Form {
                Section("Body") {
                    HStack { Text("Weight (lbs)"); Spacer(); TextField("", text: $newWeight).keyboardType(.decimalPad).multilineTextAlignment(.trailing).frame(width: 80) }
                    HStack { Text("Body Fat %"); Spacer(); TextField("", text: $newBodyFat).keyboardType(.decimalPad).multilineTextAlignment(.trailing).frame(width: 80) }
                }
                Section("Measurements (inches)") {
                    HStack { Text("Waist"); Spacer(); TextField("", text: $newWaist).keyboardType(.decimalPad).multilineTextAlignment(.trailing).frame(width: 80) }
                    HStack { Text("Hips"); Spacer(); TextField("", text: $newHips).keyboardType(.decimalPad).multilineTextAlignment(.trailing).frame(width: 80) }
                    HStack { Text("Arms"); Spacer(); TextField("", text: $newArms).keyboardType(.decimalPad).multilineTextAlignment(.trailing).frame(width: 80) }
                    HStack { Text("Thighs"); Spacer(); TextField("", text: $newThighs).keyboardType(.decimalPad).multilineTextAlignment(.trailing).frame(width: 80) }
                }
                Section("Notes") {
                    TextField("How are you feeling?", text: $newNotes)
                }
            }
            .scrollContentBackground(.hidden)
            .background(Color.bg)
            .navigationTitle("Log Measurement")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) { Button("Cancel") { showAddMetric = false } }
                ToolbarItem(placement: .confirmationAction) {
                    Button("Save") {
                        var metric = BodyMetric()
                        metric.weight = Double(newWeight)
                        metric.bodyFat = Double(newBodyFat)
                        metric.waist = Double(newWaist)
                        metric.hips = Double(newHips)
                        metric.arms = Double(newArms)
                        metric.thighs = Double(newThighs)
                        metric.notes = newNotes
                        store.addMetric(metric)
                        newWeight = ""; newBodyFat = ""; newWaist = ""; newHips = ""; newArms = ""; newThighs = ""; newNotes = ""
                        showAddMetric = false
                    }
                    .fontWeight(.bold).foregroundColor(.gold)
                }
            }
        }
    }
}

// MARK: - Weight Chart
struct WeightChartView: View {
    let metrics: [BodyMetric]
    var body: some View {
        let weights = metrics.compactMap { $0.weight }.suffix(30)
        if weights.count < 2 { return AnyView(EmptyView()) }
        let minW = (weights.min() ?? 0) - 2
        let maxW = (weights.max() ?? 0) + 2
        let range = max(maxW - minW, 1)
        return AnyView(
            GeometryReader { geo in
                let w = geo.size.width, h = geo.size.height
                let step = w / CGFloat(weights.count - 1)
                ZStack {
                    // Grid lines
                    ForEach(0..<4) { i in
                        let y = h * CGFloat(i) / 3
                        Path { p in p.move(to: CGPoint(x: 0, y: y)); p.addLine(to: CGPoint(x: w, y: y)) }
                            .stroke(Color.dim.opacity(0.15), lineWidth: 1)
                        let val = maxW - (range * Double(i) / 3)
                        Text(String(format: "%.0f", val)).font(.system(size: 9)).foregroundColor(.dim.opacity(0.5))
                            .position(x: 20, y: y - 8)
                    }
                    // Line
                    Path { path in
                        for (i, weight) in weights.enumerated() {
                            let x = step * CGFloat(i)
                            let y = h * (1 - CGFloat((weight - minW) / range))
                            if i == 0 { path.move(to: CGPoint(x: x, y: y)) }
                            else { path.addLine(to: CGPoint(x: x, y: y)) }
                        }
                    }
                    .stroke(Color.gold, style: StrokeStyle(lineWidth: 2.5, lineCap: .round, lineJoin: .round))
                    // Dots
                    ForEach(Array(weights.enumerated()), id: \.offset) { i, weight in
                        let x = step * CGFloat(i)
                        let y = h * (1 - CGFloat((weight - minW) / range))
                        Circle().fill(Color.gold).frame(width: 6, height: 6).position(x: x, y: y)
                    }
                }
            }
        )
    }
}

// MARK: - Nutrition View
struct NutritionView: View {
    @EnvironmentObject var store: WorkoutStore
    @State private var showAddFood = false
    let meals = ["Meal 1","Meal 2","Meal 3","Meal 4","Snack"]

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing:16) {
                    // Calorie Ring
                    VStack(spacing:8) {
                        ZStack {
                            Circle().stroke(Color(.systemGray5), lineWidth:12).frame(width:140, height:140)
                            Circle().trim(from:0, to: min(CGFloat(store.todayCalories) / CGFloat(max(store.nutritionTargets.calories,1)), 1.0))
                                .stroke(Color.gold, style: StrokeStyle(lineWidth:12, lineCap:.round))
                                .frame(width:140, height:140).rotationEffect(.degrees(-90))
                            VStack(spacing:2) {
                                Text("\(store.todayCalories)").font(.system(size:28, weight:.black)).foregroundColor(.gold)
                                Text("/ \(store.nutritionTargets.calories)").font(.caption).foregroundColor(.dim)
                                Text("cal").font(.caption2).foregroundColor(.dim)
                            }
                        }
                    }
                    .padding(.top, 8)

                    // Macro Bars
                    HStack(spacing:12) {
                        macroBar(label:"Protein", current:store.todayProtein, target:store.nutritionTargets.protein, color:.blue, unit:"g")
                        macroBar(label:"Carbs", current:store.todayCarbs, target:store.nutritionTargets.carbs, color:.orange, unit:"g")
                        macroBar(label:"Fat", current:store.todayFat, target:store.nutritionTargets.fat, color:.red, unit:"g")
                    }

                    // Add Food Button
                    Button { showAddFood = true } label: {
                        HStack {
                            Image(systemName:"plus.circle.fill").foregroundColor(.gold)
                            Text("Add Food").fontWeight(.semibold)
                        }
                        .frame(maxWidth:.infinity).padding(14).background(Color.bg3).cornerRadius(12)
                        .overlay(RoundedRectangle(cornerRadius:12).stroke(Color.gold, lineWidth:1))
                    }
                    .buttonStyle(.plain)

                    // Food Log by Meal
                    ForEach(meals, id:\.self) { meal in
                        let items = store.todaysFoodLog.filter { $0.meal == meal }
                        if !items.isEmpty {
                            VStack(alignment:.leading, spacing:8) {
                                HStack {
                                    Text(meal.uppercased()).font(.caption).fontWeight(.semibold).foregroundColor(.dim).tracking(1)
                                    Spacer()
                                    Text("\(items.reduce(0){$0+$1.calories}) cal").font(.caption).foregroundColor(.gold)
                                }
                                ForEach(items) { item in
                                    HStack {
                                        VStack(alignment:.leading, spacing:2) {
                                            Text(item.name).font(.subheadline).fontWeight(.medium)
                                            Text("\(item.calories) cal  •  P:\(item.protein)g  C:\(item.carbs)g  F:\(item.fat)g")
                                                .font(.caption).foregroundColor(.dim)
                                        }
                                        Spacer()
                                        Button { store.deleteFood(item) } label: {
                                            Image(systemName:"xmark.circle.fill").foregroundColor(.dim).font(.caption)
                                        }
                                    }
                                    .padding(12).background(Color.bg3).cornerRadius(10)
                                    .overlay(RoundedRectangle(cornerRadius:10).stroke(Color(.systemGray5), lineWidth:1))
                                }
                            }
                        }
                    }

                    // Targets Editor
                    NavigationLink { NutritionTargetsView() } label: {
                        HStack {
                            Image(systemName:"gearshape.fill").foregroundColor(.dim)
                            Text("Edit Daily Targets").font(.subheadline).foregroundColor(.dim)
                            Spacer()
                            Image(systemName:"chevron.right").foregroundColor(.dim).font(.caption)
                        }
                        .padding(14).background(Color.bg3).cornerRadius(12)
                        .overlay(RoundedRectangle(cornerRadius:12).stroke(Color(.systemGray5), lineWidth:1))
                    }
                    .buttonStyle(.plain)
                }
                .padding()
            }
            .background(Color.bg)
            .navigationTitle("")
            .toolbar {
                ToolbarItem(placement:.principal) {
                    HStack(spacing:4) {
                        Text("MARCEAU").font(.headline).fontWeight(.black).foregroundColor(.gold)
                        Text("NUTRITION").font(.headline).fontWeight(.bold)
                    }
                }
            }
            .sheet(isPresented: $showAddFood) { AddFoodView() }
        }
    }

    func macroBar(label: String, current: Int, target: Int, color: Color, unit: String) -> some View {
        VStack(spacing:6) {
            Text(label.uppercased()).font(.system(size:9, weight:.semibold)).foregroundColor(.dim).tracking(0.5)
            ZStack(alignment:.bottom) {
                RoundedRectangle(cornerRadius:6).fill(Color(.systemGray5)).frame(width:40, height:80)
                RoundedRectangle(cornerRadius:6).fill(color)
                    .frame(width:40, height: min(CGFloat(current)/CGFloat(max(target,1)) * 80, 80))
            }
            Text("\(current)").font(.system(size:14, weight:.bold)).foregroundColor(color)
            Text("/ \(target)\(unit)").font(.system(size:9)).foregroundColor(.dim)
        }
        .frame(maxWidth:.infinity)
    }
}

// MARK: - Add Food View
struct AddFoodView: View {
    @EnvironmentObject var store: WorkoutStore
    @Environment(\.dismiss) var dismiss
    @State private var name = ""
    @State private var calories = ""
    @State private var protein = ""
    @State private var carbs = ""
    @State private var fat = ""
    @State private var meal = "Meal 1"
    let meals = ["Meal 1","Meal 2","Meal 3","Meal 4","Snack"]

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing:16) {
                    VStack(alignment:.leading, spacing:6) {
                        Text("FOOD NAME").font(.caption).fontWeight(.semibold).foregroundColor(.dim).tracking(1)
                        TextField("e.g. Chicken Breast", text: $name)
                            .textFieldStyle(.roundedBorder).font(.subheadline)
                    }

                    VStack(alignment:.leading, spacing:6) {
                        Text("MEAL").font(.caption).fontWeight(.semibold).foregroundColor(.dim).tracking(1)
                        Picker("Meal", selection: $meal) {
                            ForEach(meals, id:\.self) { Text($0) }
                        }
                        .pickerStyle(.segmented)
                    }

                    HStack(spacing:12) {
                        macroField(label:"CALORIES", text:$calories, unit:"cal")
                        macroField(label:"PROTEIN", text:$protein, unit:"g")
                    }
                    HStack(spacing:12) {
                        macroField(label:"CARBS", text:$carbs, unit:"g")
                        macroField(label:"FAT", text:$fat, unit:"g")
                    }

                    // Quick Add Presets
                    VStack(alignment:.leading, spacing:8) {
                        Text("QUICK ADD").font(.caption).fontWeight(.semibold).foregroundColor(.dim).tracking(1)
                        LazyVGrid(columns:[GridItem(.flexible()), GridItem(.flexible())], spacing:8) {
                            quickPreset("Chicken Breast (6oz)", cal:280, p:52, c:0, f:6)
                            quickPreset("Rice (1 cup)", cal:205, p:4, c:45, f:0)
                            quickPreset("Eggs (3 large)", cal:210, p:18, c:1, f:15)
                            quickPreset("Protein Shake", cal:160, p:30, c:5, f:2)
                            quickPreset("Greek Yogurt", cal:130, p:17, c:7, f:4)
                            quickPreset("Banana", cal:105, p:1, c:27, f:0)
                            quickPreset("Oats (1 cup)", cal:300, p:10, c:54, f:5)
                            quickPreset("Steak (8oz)", cal:480, p:62, c:0, f:24)
                            quickPreset("Sweet Potato", cal:115, p:2, c:27, f:0)
                            quickPreset("Avocado (half)", cal:160, p:2, c:9, f:15)
                            quickPreset("Salmon (6oz)", cal:350, p:38, c:0, f:20)
                            quickPreset("PB (2 tbsp)", cal:190, p:7, c:7, f:16)
                        }
                    }
                }
                .padding()
            }
            .background(Color.bg)
            .scrollDismissesKeyboard(.immediately)
            .toolbar {
                ToolbarItem(placement:.keyboard) { HStack { Spacer(); Button("Done") { hideKeyboard() }.fontWeight(.semibold) } }
                ToolbarItem(placement:.cancellationAction) { Button("Cancel") { dismiss() } }
                ToolbarItem(placement:.confirmationAction) {
                    Button("Add") {
                        let entry = FoodEntry(name: name.isEmpty ? "Food" : name,
                                              calories: Int(calories) ?? 0, protein: Int(protein) ?? 0,
                                              carbs: Int(carbs) ?? 0, fat: Int(fat) ?? 0, meal: meal)
                        store.addFood(entry)
                        dismiss()
                    }
                    .fontWeight(.bold).foregroundColor(.gold)
                    .disabled(calories.isEmpty && protein.isEmpty)
                }
            }
            .navigationTitle("Add Food")
            .navigationBarTitleDisplayMode(.inline)
        }
    }

    func macroField(label: String, text: Binding<String>, unit: String) -> some View {
        VStack(alignment:.leading, spacing:4) {
            Text(label).font(.system(size:10, weight:.semibold)).foregroundColor(.dim).tracking(0.5)
            HStack {
                TextField("0", text: text).keyboardType(.numberPad).font(.title3).fontWeight(.bold)
                Text(unit).font(.caption).foregroundColor(.dim)
            }
            .padding(12).background(Color.bg3).cornerRadius(10)
            .overlay(RoundedRectangle(cornerRadius:10).stroke(Color(.systemGray5), lineWidth:1))
        }
    }

    func quickPreset(_ name: String, cal: Int, p: Int, c: Int, f: Int) -> some View {
        Button {
            self.name = name
            calories = "\(cal)"; protein = "\(p)"; carbs = "\(c)"; fat = "\(f)"
        } label: {
            VStack(alignment:.leading, spacing:2) {
                Text(name).font(.caption).fontWeight(.medium).lineLimit(1)
                Text("\(cal) cal • P:\(p)").font(.system(size:9)).foregroundColor(.dim)
            }
            .frame(maxWidth:.infinity, alignment:.leading).padding(10).background(Color.bg3).cornerRadius(8)
            .overlay(RoundedRectangle(cornerRadius:8).stroke(Color(.systemGray5), lineWidth:1))
        }
        .buttonStyle(.plain)
    }
}

// MARK: - Nutrition Targets View
struct NutritionTargetsView: View {
    @EnvironmentObject var store: WorkoutStore
    @State private var cal = ""
    @State private var pro = ""
    @State private var carb = ""
    @State private var fat = ""

    var body: some View {
        ScrollView {
            VStack(spacing:16) {
                Text("Set your daily macro targets").font(.subheadline).foregroundColor(.dim)
                targetField("CALORIES", text:$cal, current:store.nutritionTargets.calories)
                targetField("PROTEIN (g)", text:$pro, current:store.nutritionTargets.protein)
                targetField("CARBS (g)", text:$carb, current:store.nutritionTargets.carbs)
                targetField("FAT (g)", text:$fat, current:store.nutritionTargets.fat)

                Button {
                    store.nutritionTargets.calories = Int(cal) ?? store.nutritionTargets.calories
                    store.nutritionTargets.protein = Int(pro) ?? store.nutritionTargets.protein
                    store.nutritionTargets.carbs = Int(carb) ?? store.nutritionTargets.carbs
                    store.nutritionTargets.fat = Int(fat) ?? store.nutritionTargets.fat
                    store.save()
                } label: {
                    Text("Save Targets")
                        .font(.headline).fontWeight(.bold).foregroundColor(.black)
                        .frame(maxWidth:.infinity).padding(16).background(Color.gold).cornerRadius(14)
                }
            }
            .padding()
        }
        .background(Color.bg)
        .scrollDismissesKeyboard(.immediately)
        .toolbar { ToolbarItemGroup(placement:.keyboard) { Spacer(); Button("Done") { hideKeyboard() }.fontWeight(.semibold) } }
        .navigationTitle("Daily Targets")
        .onAppear {
            cal = "\(store.nutritionTargets.calories)"
            pro = "\(store.nutritionTargets.protein)"
            carb = "\(store.nutritionTargets.carbs)"
            fat = "\(store.nutritionTargets.fat)"
        }
    }

    func targetField(_ label: String, text: Binding<String>, current: Int) -> some View {
        VStack(alignment:.leading, spacing:4) {
            Text(label).font(.system(size:10, weight:.semibold)).foregroundColor(.dim).tracking(0.5)
            TextField("\(current)", text: text)
                .keyboardType(.numberPad).font(.title3).fontWeight(.bold)
                .padding(14).background(Color.bg3).cornerRadius(12)
                .overlay(RoundedRectangle(cornerRadius:12).stroke(Color(.systemGray5), lineWidth:1))
        }
    }
}

// MARK: - Settings View
struct SettingsView: View {
    @EnvironmentObject var store: WorkoutStore
    @State private var showResetAlert = false

    var activeProgram: Program? { programDB.first { $0.id == store.selectedProgram } }

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 16) {
                    // Profile Card
                    VStack(spacing: 8) {
                        ZStack {
                            Circle().fill(Color.goldDim).frame(width: 70, height: 70)
                            Text("MF").font(.title).fontWeight(.black).foregroundColor(.gold)
                        }
                        Text("MARCEAU FITNESS").font(.headline).fontWeight(.black).foregroundColor(.gold)
                        Text("Embrace the Pain & Defy the Odds").font(.caption).foregroundColor(.dim).italic()
                    }
                    .frame(maxWidth: .infinity).padding(24).background(Color.bg3).cornerRadius(16)
                    .overlay(RoundedRectangle(cornerRadius: 16).stroke(Color(.systemGray5), lineWidth: 1))

                    // Active Program
                    VStack(alignment: .leading, spacing: 10) {
                        Text("ACTIVE PROGRAM").font(.caption).fontWeight(.bold).foregroundColor(.dim).tracking(1)
                        if let prog = activeProgram {
                            HStack {
                                VStack(alignment: .leading, spacing: 4) {
                                    Text(prog.name).font(.subheadline).fontWeight(.bold)
                                    Text("\(prog.frequency)  •  \(prog.level)").font(.caption).foregroundColor(.dim)
                                }
                                Spacer()
                                NavigationLink { ProgramDetailView(program: prog) } label: {
                                    Text("View").font(.caption).fontWeight(.bold).foregroundColor(.gold)
                                        .padding(.horizontal, 12).padding(.vertical, 6).background(Color.goldDim).cornerRadius(8)
                                }
                            }
                            .padding(14).background(Color.bg3).cornerRadius(12)
                            .overlay(RoundedRectangle(cornerRadius: 12).stroke(Color.gold, lineWidth: 1))
                        }

                        Text("SWITCH PROGRAM").font(.caption).fontWeight(.bold).foregroundColor(.dim).tracking(1).padding(.top, 4)
                        ForEach(programDB.filter { $0.id != store.selectedProgram }) { prog in
                            Button {
                                store.selectedProgram = prog.id
                                store.save()
                                UIImpactFeedbackGenerator(style: .medium).impactOccurred()
                            } label: {
                                HStack {
                                    VStack(alignment: .leading, spacing: 2) {
                                        Text(prog.name).font(.subheadline).fontWeight(.semibold)
                                        Text(prog.frequency).font(.caption).foregroundColor(.dim)
                                    }
                                    Spacer()
                                    Image(systemName: "arrow.right.circle").foregroundColor(.dim)
                                }
                                .padding(14).background(Color.bg3).cornerRadius(12)
                                .overlay(RoundedRectangle(cornerRadius: 12).stroke(Color(.systemGray5), lineWidth: 1))
                            }
                            .buttonStyle(.plain)
                        }
                    }

                    // Stats Summary
                    VStack(alignment: .leading, spacing: 10) {
                        Text("LIFETIME STATS").font(.caption).fontWeight(.bold).foregroundColor(.dim).tracking(1)
                        HStack(spacing: 12) {
                            miniStat(value: "\(store.totalWorkouts)", label: "Workouts")
                            miniStat(value: "\(store.streak)", label: "Streak")
                            miniStat(value: store.totalVolume > 1000 ? "\(store.totalVolume/1000)K" : "\(store.totalVolume)", label: "Volume")
                        }
                    }

                    // Rest Timer (standalone)
                    NavigationLink { TimerView() } label: {
                        HStack {
                            Image(systemName: "timer").foregroundColor(.gold)
                            Text("Standalone Rest Timer").font(.subheadline).fontWeight(.medium)
                            Spacer()
                            Image(systemName: "chevron.right").font(.caption).foregroundColor(.dim)
                        }
                        .padding(14).background(Color.bg3).cornerRadius(12)
                        .overlay(RoundedRectangle(cornerRadius: 12).stroke(Color(.systemGray5), lineWidth: 1))
                    }
                    .buttonStyle(.plain)

                    // Reset
                    Button { showResetAlert = true } label: {
                        HStack {
                            Image(systemName: "arrow.counterclockwise").foregroundColor(.red.opacity(0.7))
                            Text("Reset All Data").font(.subheadline).foregroundColor(.red.opacity(0.7))
                            Spacer()
                        }
                        .padding(14).background(Color.bg3).cornerRadius(12)
                        .overlay(RoundedRectangle(cornerRadius: 12).stroke(Color(.systemGray5), lineWidth: 1))
                    }
                    .buttonStyle(.plain)

                    Text("Marceau Fitness v1.0").font(.caption).foregroundColor(.dim).padding(.top, 8)
                }
                .padding()
            }
            .background(Color.bg)
            .navigationTitle("")
            .toolbar {
                ToolbarItem(placement: .principal) {
                    HStack(spacing: 4) {
                        Text("MARCEAU").font(.headline).fontWeight(.black).foregroundColor(.gold)
                        Text("SETTINGS").font(.headline).fontWeight(.bold)
                    }
                }
            }
            .alert("Reset All Data?", isPresented: $showResetAlert) {
                Button("Cancel", role: .cancel) {}
                Button("Reset", role: .destructive) {
                    store.history = []; store.totalWorkouts = 0; store.streak = 0
                    store.totalVolume = 0; store.foodLog = []; store.bodyMetrics = []
                    store.selectedProgram = "defy_the_odds"; store.save()
                }
            } message: {
                Text("This will delete all workout history, nutrition logs, and body measurements. This cannot be undone.")
            }
        }
    }

    func miniStat(value: String, label: String) -> some View {
        VStack(spacing: 4) {
            Text(value).font(.system(size: 22, weight: .black)).foregroundColor(.gold)
            Text(label.uppercased()).font(.system(size: 9, weight: .semibold)).foregroundColor(.dim).tracking(0.5)
        }
        .frame(maxWidth: .infinity).padding(14).background(Color.bg3).cornerRadius(12)
        .overlay(RoundedRectangle(cornerRadius: 12).stroke(Color(.systemGray5), lineWidth: 1))
    }
}

// MARK: - Flow Layout
struct FlowLayout: Layout {
    var spacing: CGFloat = 6
    func sizeThatFits(proposal: ProposedViewSize, subviews: Subviews, cache: inout ()) -> CGSize {
        let result = arrange(proposal: proposal, subviews: subviews)
        return result.size
    }
    func placeSubviews(in bounds: CGRect, proposal: ProposedViewSize, subviews: Subviews, cache: inout ()) {
        let result = arrange(proposal: proposal, subviews: subviews)
        for (idx, pos) in result.positions.enumerated() {
            subviews[idx].place(at: CGPoint(x: bounds.minX + pos.x, y: bounds.minY + pos.y), proposal: .unspecified)
        }
    }
    struct ArrangeResult { var positions: [CGPoint]; var size: CGSize }
    func arrange(proposal: ProposedViewSize, subviews: Subviews) -> ArrangeResult {
        let maxW = proposal.width ?? .infinity
        var positions: [CGPoint] = []
        var x: CGFloat = 0; var y: CGFloat = 0; var rowH: CGFloat = 0; var maxX: CGFloat = 0
        for sub in subviews {
            let size = sub.sizeThatFits(.unspecified)
            if x + size.width > maxW && x > 0 { x = 0; y += rowH + spacing; rowH = 0 }
            positions.append(CGPoint(x: x, y: y))
            rowH = max(rowH, size.height); x += size.width + spacing; maxX = max(maxX, x)
        }
        return ArrangeResult(positions: positions, size: CGSize(width: maxX, height: y + rowH))
    }
}
